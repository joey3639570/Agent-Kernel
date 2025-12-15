"""Base interface for code execution sandboxes.

This module defines the abstract interface and common types for
all sandbox implementations (Docker, Kubernetes, etc.).
"""

from __future__ import annotations

import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SandboxConfig:
    """Configuration for a sandbox environment.

    Attributes:
        image: Docker image to use for execution.
        timeout_seconds: Maximum execution time.
        memory_limit_mb: Memory limit in megabytes.
        cpu_limit: CPU limit (e.g., "0.5" for half a core).
        network_enabled: Whether to allow network access.
        allowed_domains: Whitelist of allowed domains (if network enabled).
        read_only_fs: Whether filesystem should be read-only.
        allowed_imports: Whitelist of allowed Python imports.
        max_output_size_kb: Maximum output size in kilobytes.
        working_directory: Working directory inside container.
        environment: Environment variables to set.
    """

    image: str = "python:3.11-slim"
    timeout_seconds: int = 30
    memory_limit_mb: int = 256
    cpu_limit: str = "0.5"
    network_enabled: bool = False
    allowed_domains: List[str] = field(default_factory=list)
    read_only_fs: bool = True
    allowed_imports: List[str] = field(default_factory=lambda: [
        "math", "statistics", "random", "datetime", "json", "re",
        "collections", "itertools", "functools", "operator",
        "string", "textwrap", "unicodedata",
        "decimal", "fractions", "numbers",
        "csv", "io", "base64", "hashlib", "hmac",
    ])
    max_output_size_kb: int = 100
    working_directory: str = "/workspace"
    environment: Dict[str, str] = field(default_factory=dict)


@dataclass
class SandboxResult:
    """Result from code execution in sandbox.

    Attributes:
        success: Whether execution completed successfully.
        stdout: Captured standard output.
        stderr: Captured standard error.
        return_value: Serialized return value (if any).
        execution_time_ms: Execution time in milliseconds.
        exit_code: Process exit code.
        error_message: Error message if execution failed.
        truncated: Whether output was truncated due to size limits.
        code_hash: SHA256 hash of executed code (for audit).
        timestamp: When execution occurred.
    """

    success: bool
    stdout: str = ""
    stderr: str = ""
    return_value: Optional[str] = None
    execution_time_ms: float = 0.0
    exit_code: int = 0
    error_message: Optional[str] = None
    truncated: bool = False
    code_hash: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def to_audit_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for audit logging."""
        return {
            "success": self.success,
            "exit_code": self.exit_code,
            "execution_time_ms": self.execution_time_ms,
            "truncated": self.truncated,
            "code_hash": self.code_hash,
            "timestamp": self.timestamp.isoformat(),
            "has_error": self.error_message is not None,
            "stdout_length": len(self.stdout),
            "stderr_length": len(self.stderr),
        }


class SandboxBase(ABC):
    """Abstract base class for code execution sandboxes.

    All sandbox implementations must provide:
    - Secure isolation from the host system
    - Resource limits (CPU, memory, time)
    - Output capture and size limiting
    - Audit logging capabilities
    """

    def __init__(self, config: Optional[SandboxConfig] = None) -> None:
        """Initialize the sandbox.

        Args:
            config: Sandbox configuration. Uses defaults if not provided.
        """
        self.config = config or SandboxConfig()

    @abstractmethod
    async def execute(
        self,
        code: str,
        language: str = "python",
        **kwargs: Any,
    ) -> SandboxResult:
        """Execute code in the sandbox.

        Args:
            code: The code to execute.
            language: Programming language (currently only "python" supported).
            **kwargs: Additional execution parameters.

        Returns:
            SandboxResult with execution outcome.
        """

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the sandbox backend is available.

        Returns:
            True if the sandbox can be used.
        """

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up any sandbox resources."""

    def _validate_code(self, code: str) -> Optional[str]:
        """Validate code before execution.

        Args:
            code: The code to validate.

        Returns:
            Error message if validation fails, None if valid.
        """
        # Check for dangerous patterns
        dangerous_patterns = [
            "subprocess",
            "os.system",
            "eval(",
            "exec(",
            "__import__",
            "importlib",
            "open(",
            "file(",
        ]

        if not self.config.network_enabled:
            dangerous_patterns.extend([
                "socket",
                "urllib",
                "requests",
                "http.client",
                "ftplib",
            ])

        code_lower = code.lower()
        for pattern in dangerous_patterns:
            if pattern.lower() in code_lower:
                return f"Blocked pattern detected: {pattern}"

        # Validate imports if allowlist is specified
        if self.config.allowed_imports:
            import ast
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            module = alias.name.split(".")[0]
                            if module not in self.config.allowed_imports:
                                return f"Import not allowed: {module}"
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            module = node.module.split(".")[0]
                            if module not in self.config.allowed_imports:
                                return f"Import not allowed: {module}"
            except SyntaxError as e:
                return f"Syntax error in code: {e}"

        return None

    def _compute_code_hash(self, code: str) -> str:
        """Compute SHA256 hash of code for audit.

        Args:
            code: The code to hash.

        Returns:
            Hex-encoded SHA256 hash.
        """
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    def _truncate_output(self, output: str) -> tuple[str, bool]:
        """Truncate output if it exceeds the size limit.

        Args:
            output: The output string to potentially truncate.

        Returns:
            Tuple of (possibly truncated output, whether truncation occurred).
        """
        max_chars = self.config.max_output_size_kb * 1024
        if len(output) > max_chars:
            return output[:max_chars] + "\n... [OUTPUT TRUNCATED]", True
        return output, False

