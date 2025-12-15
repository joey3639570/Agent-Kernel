"""Code Interpreter tool for executing Python code in a sandbox.

This module provides a secure code execution tool that can be used
by agents to solve computational problems, analyze data, and more.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from agentkernel_core.tools.result import ToolResult
from agentkernel_core.tools.sandbox.base import SandboxBase, SandboxConfig, SandboxResult
from agentkernel_core.tools.sandbox.docker_sandbox import DockerSandbox
from agentkernel_core.tools.sandbox.k8s_sandbox import K8sSandbox
from agentkernel_core.tools.spec import ToolSpec, ToolSafety

logger = logging.getLogger(__name__)


# Standard ToolSpec for the Code Interpreter
CODE_INTERPRETER_SPEC = ToolSpec(
    name="code_interpreter",
    description=(
        "Execute Python code in a secure sandbox environment. "
        "Useful for mathematical calculations, data analysis, string manipulation, "
        "and other computational tasks. The code runs in an isolated environment "
        "with limited imports and no network access by default."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The Python code to execute. Use _result to return a value.",
            },
            "timeout": {
                "type": "integer",
                "description": "Maximum execution time in seconds (default: 30).",
                "default": 30,
            },
        },
        "required": ["code"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "output": {"type": "string"},
            "result": {"type": "string"},
            "error": {"type": "string"},
        },
    },
    safety=ToolSafety(
        side_effect=False,
        requires_network=False,
        requires_fs=False,
        requires_sandbox=True,
        risk_level=2,
        audit_required=True,
    ),
    tags=["computation", "code", "sandbox"],
)


class CodeInterpreter:
    """Code Interpreter tool for executing Python code securely.

    This class provides a high-level interface for code execution
    that automatically selects the appropriate sandbox backend
    (Docker for local, K8s for distributed).
    """

    def __init__(
        self,
        sandbox: Optional[SandboxBase] = None,
        config: Optional[SandboxConfig] = None,
        prefer_k8s: bool = False,
    ) -> None:
        """Initialize the Code Interpreter.

        Args:
            sandbox: Optional pre-configured sandbox to use.
            config: Sandbox configuration (used if sandbox not provided).
            prefer_k8s: Whether to prefer K8s over Docker when available.
        """
        self._sandbox = sandbox
        self._config = config or SandboxConfig()
        self._prefer_k8s = prefer_k8s
        self._audit_log: list[Dict[str, Any]] = []

    async def _get_sandbox(self) -> SandboxBase:
        """Get or create the appropriate sandbox.

        Returns:
            A sandbox instance.

        Raises:
            RuntimeError: If no sandbox backend is available.
        """
        if self._sandbox:
            return self._sandbox

        # Try K8s first if preferred
        if self._prefer_k8s:
            k8s_sandbox = K8sSandbox(self._config)
            if await k8s_sandbox.is_available():
                self._sandbox = k8s_sandbox
                logger.info("Using Kubernetes sandbox")
                return self._sandbox

        # Try Docker
        docker_sandbox = DockerSandbox(self._config)
        if await docker_sandbox.is_available():
            self._sandbox = docker_sandbox
            logger.info("Using Docker sandbox")
            return self._sandbox

        # Try K8s as fallback
        if not self._prefer_k8s:
            k8s_sandbox = K8sSandbox(self._config)
            if await k8s_sandbox.is_available():
                self._sandbox = k8s_sandbox
                logger.info("Using Kubernetes sandbox (fallback)")
                return self._sandbox

        raise RuntimeError(
            "No sandbox backend available. "
            "Please ensure Docker or Kubernetes is configured."
        )

    @property
    def spec(self) -> ToolSpec:
        """Get the tool specification."""
        return CODE_INTERPRETER_SPEC

    async def execute(
        self,
        code: str,
        timeout: Optional[int] = None,
        agent_id: Optional[str] = None,
        tick: Optional[int] = None,
    ) -> ToolResult:
        """Execute Python code in the sandbox.

        Args:
            code: The Python code to execute.
            timeout: Optional timeout override.
            agent_id: ID of the calling agent (for audit).
            tick: Current simulation tick (for audit).

        Returns:
            ToolResult with execution outcome.
        """
        started_at = datetime.now()

        try:
            sandbox = await self._get_sandbox()

            # Override timeout if specified
            if timeout:
                sandbox.config.timeout_seconds = timeout

            # Execute in sandbox
            result = await sandbox.execute(
                code=code,
                language="python",
                agent_id=agent_id,
                tick=tick,
            )

            # Create audit entry
            audit_entry = {
                "timestamp": started_at.isoformat(),
                "agent_id": agent_id,
                "tick": tick,
                "code_hash": result.code_hash,
                **result.to_audit_dict(),
            }
            self._audit_log.append(audit_entry)
            logger.info("CODE_INTERPRETER_AUDIT: %s", json.dumps(audit_entry))

            # Convert SandboxResult to ToolResult
            if result.success:
                output_parts = []
                if result.stdout:
                    output_parts.append(result.stdout)
                if result.return_value:
                    output_parts.append(f"Result: {result.return_value}")

                return ToolResult.success(
                    tool_name="code_interpreter",
                    output={
                        "success": True,
                        "output": "\n".join(output_parts) if output_parts else "Code executed successfully.",
                        "result": result.return_value,
                    },
                    stdout=result.stdout,
                    execution_time_ms=result.execution_time_ms,
                    metadata={
                        "code_hash": result.code_hash,
                        "truncated": result.truncated,
                    },
                )
            else:
                return ToolResult.error(
                    tool_name="code_interpreter",
                    error_message=result.error_message or "Execution failed",
                    stderr=result.stderr,
                    execution_time_ms=result.execution_time_ms,
                    metadata={
                        "code_hash": result.code_hash,
                        "exit_code": result.exit_code,
                    },
                )

        except Exception as e:
            logger.exception("Code interpreter error")
            return ToolResult.error(
                tool_name="code_interpreter",
                error_message=str(e),
                error_type=type(e).__name__,
            )

    async def close(self) -> None:
        """Clean up sandbox resources."""
        if self._sandbox:
            await self._sandbox.cleanup()
            self._sandbox = None

    def get_audit_log(self) -> list[Dict[str, Any]]:
        """Get the audit log of all executions.

        Returns:
            List of audit entries.
        """
        return self._audit_log.copy()

    def clear_audit_log(self) -> None:
        """Clear the audit log."""
        self._audit_log.clear()

