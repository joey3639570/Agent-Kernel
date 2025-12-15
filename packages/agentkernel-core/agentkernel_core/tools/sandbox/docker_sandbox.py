"""Docker-based sandbox for code execution.

This module provides a secure Docker container-based sandbox for
executing untrusted code with resource limits and isolation.
"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import time
from typing import Any, Optional

from agentkernel_core.tools.sandbox.base import (
    SandboxBase,
    SandboxConfig,
    SandboxResult,
)

logger = logging.getLogger(__name__)


class DockerSandbox(SandboxBase):
    """Docker-based sandbox for secure code execution.

    This sandbox runs code in isolated Docker containers with:
    - Resource limits (CPU, memory, time)
    - Network isolation (optional)
    - Read-only filesystem (optional)
    - No privileged access
    - Audit logging

    Requires Docker to be installed and accessible.
    """

    def __init__(self, config: Optional[SandboxConfig] = None) -> None:
        """Initialize the Docker sandbox.

        Args:
            config: Sandbox configuration.
        """
        super().__init__(config)
        self._docker_client: Optional[Any] = None

    async def _get_client(self) -> Any:
        """Get or create Docker client.

        Returns:
            Docker client instance.

        Raises:
            ImportError: If docker package is not installed.
            RuntimeError: If Docker is not available.
        """
        if self._docker_client is None:
            try:
                import docker
                self._docker_client = docker.from_env()
                # Test connection
                self._docker_client.ping()
            except ImportError:
                raise ImportError("docker package is required. Install with: pip install docker")
            except Exception as e:
                raise RuntimeError(f"Docker is not available: {e}")

        return self._docker_client

    async def is_available(self) -> bool:
        """Check if Docker is available.

        Returns:
            True if Docker can be used.
        """
        try:
            await self._get_client()
            return True
        except Exception as e:
            logger.warning("Docker not available: %s", e)
            return False

    async def execute(
        self,
        code: str,
        language: str = "python",
        **kwargs: Any,
    ) -> SandboxResult:
        """Execute code in a Docker container.

        Args:
            code: The code to execute.
            language: Programming language (currently only "python").
            **kwargs: Additional parameters (e.g., agent_id, tick for audit).

        Returns:
            SandboxResult with execution outcome.
        """
        start_time = time.perf_counter()
        code_hash = self._compute_code_hash(code)

        # Validate code
        validation_error = self._validate_code(code)
        if validation_error:
            return SandboxResult(
                success=False,
                error_message=validation_error,
                code_hash=code_hash,
            )

        if language != "python":
            return SandboxResult(
                success=False,
                error_message=f"Unsupported language: {language}",
                code_hash=code_hash,
            )

        try:
            client = await self._get_client()
        except Exception as e:
            return SandboxResult(
                success=False,
                error_message=f"Docker not available: {e}",
                code_hash=code_hash,
            )

        # Create wrapper script that captures output
        wrapper_script = f'''
import sys
import json
import traceback

try:
    # Redirect to capture output
    _result = None
    _locals = {{}}
    
    exec("""
{code}
""", _locals)
    
    # Try to get the last expression result
    if "_result" in _locals:
        _result = _locals["_result"]
    
    print("__SANDBOX_SUCCESS__")
    if _result is not None:
        print("__RESULT_START__")
        print(json.dumps(_result, default=str))
        print("__RESULT_END__")

except Exception as e:
    print("__SANDBOX_ERROR__", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
'''

        # Write script to temp file
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
        ) as f:
            f.write(wrapper_script)
            script_path = f.name

        try:
            # Build container configuration
            container_config = {
                "image": self.config.image,
                "command": ["python", "/sandbox/script.py"],
                "volumes": {
                    script_path: {
                        "bind": "/sandbox/script.py",
                        "mode": "ro",
                    }
                },
                "working_dir": self.config.working_directory,
                "mem_limit": f"{self.config.memory_limit_mb}m",
                "nano_cpus": int(float(self.config.cpu_limit) * 1e9),
                "network_disabled": not self.config.network_enabled,
                "read_only": self.config.read_only_fs,
                "detach": True,
                "remove": False,  # We'll remove manually after getting logs
                "security_opt": ["no-new-privileges:true"],
                "cap_drop": ["ALL"],
            }

            # Add environment variables
            if self.config.environment:
                container_config["environment"] = self.config.environment

            # Run in thread pool to avoid blocking
            container = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.containers.run(**container_config),
            )

            try:
                # Wait for container with timeout
                exit_code = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: container.wait()["StatusCode"],
                    ),
                    timeout=self.config.timeout_seconds,
                )

                # Get logs
                stdout = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: container.logs(stdout=True, stderr=False).decode("utf-8"),
                )
                stderr = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: container.logs(stdout=False, stderr=True).decode("utf-8"),
                )

            except asyncio.TimeoutError:
                # Kill container on timeout
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    container.kill,
                )
                execution_time = (time.perf_counter() - start_time) * 1000
                return SandboxResult(
                    success=False,
                    error_message=f"Execution timed out after {self.config.timeout_seconds}s",
                    execution_time_ms=execution_time,
                    code_hash=code_hash,
                )
            finally:
                # Remove container
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: container.remove(force=True),
                )

        finally:
            # Clean up temp file
            os.unlink(script_path)

        execution_time = (time.perf_counter() - start_time) * 1000

        # Parse output
        stdout, stdout_truncated = self._truncate_output(stdout)
        stderr, stderr_truncated = self._truncate_output(stderr)

        # Check for success marker
        success = "__SANDBOX_SUCCESS__" in stdout and exit_code == 0

        # Extract return value if present
        return_value = None
        if "__RESULT_START__" in stdout and "__RESULT_END__" in stdout:
            try:
                start_marker = stdout.index("__RESULT_START__") + len("__RESULT_START__")
                end_marker = stdout.index("__RESULT_END__")
                return_value = stdout[start_marker:end_marker].strip()
            except (ValueError, IndexError):
                pass

        # Clean up stdout markers
        for marker in ["__SANDBOX_SUCCESS__", "__SANDBOX_ERROR__", "__RESULT_START__", "__RESULT_END__"]:
            stdout = stdout.replace(marker, "")
        stdout = stdout.strip()

        return SandboxResult(
            success=success,
            stdout=stdout,
            stderr=stderr,
            return_value=return_value,
            execution_time_ms=execution_time,
            exit_code=exit_code,
            error_message=stderr.strip() if not success and stderr else None,
            truncated=stdout_truncated or stderr_truncated,
            code_hash=code_hash,
        )

    async def cleanup(self) -> None:
        """Clean up Docker resources."""
        if self._docker_client:
            self._docker_client.close()
            self._docker_client = None

