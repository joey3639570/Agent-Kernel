"""Kubernetes-based sandbox for code execution.

This module provides a secure Kubernetes Pod-based sandbox for
executing untrusted code with enterprise-grade isolation.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, Dict, Optional

from agentkernel_core.tools.sandbox.base import (
    SandboxBase,
    SandboxConfig,
    SandboxResult,
)

logger = logging.getLogger(__name__)


class K8sSandbox(SandboxBase):
    """Kubernetes-based sandbox for secure code execution.

    This sandbox runs code in isolated Kubernetes Pods with:
    - Resource limits (CPU, memory)
    - Network policies
    - Pod security standards
    - Ephemeral pods (auto-cleanup)
    - Audit logging

    Requires kubernetes client and cluster access.
    """

    def __init__(
        self,
        config: Optional[SandboxConfig] = None,
        namespace: str = "agentkernel-sandbox",
        service_account: str = "sandbox-runner",
    ) -> None:
        """Initialize the Kubernetes sandbox.

        Args:
            config: Sandbox configuration.
            namespace: Kubernetes namespace for sandbox pods.
            service_account: Service account for pods.
        """
        super().__init__(config)
        self.namespace = namespace
        self.service_account = service_account
        self._core_v1: Optional[Any] = None
        self._batch_v1: Optional[Any] = None

    async def _get_clients(self) -> tuple[Any, Any]:
        """Get or create Kubernetes clients.

        Returns:
            Tuple of (CoreV1Api, BatchV1Api) clients.

        Raises:
            ImportError: If kubernetes package is not installed.
            RuntimeError: If cluster is not accessible.
        """
        if self._core_v1 is None or self._batch_v1 is None:
            try:
                from kubernetes import client, config as k8s_config

                # Try in-cluster config first, then local kubeconfig
                try:
                    k8s_config.load_incluster_config()
                except k8s_config.ConfigException:
                    k8s_config.load_kube_config()

                self._core_v1 = client.CoreV1Api()
                self._batch_v1 = client.BatchV1Api()

            except ImportError:
                raise ImportError("kubernetes package is required. Install with: pip install kubernetes")
            except Exception as e:
                raise RuntimeError(f"Kubernetes cluster not accessible: {e}")

        return self._core_v1, self._batch_v1

    async def is_available(self) -> bool:
        """Check if Kubernetes cluster is available.

        Returns:
            True if cluster can be used.
        """
        try:
            core_v1, _ = await self._get_clients()
            # Try to list namespaces to verify access
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: core_v1.list_namespace(limit=1),
            )
            return True
        except Exception as e:
            logger.warning("Kubernetes not available: %s", e)
            return False

    async def execute(
        self,
        code: str,
        language: str = "python",
        **kwargs: Any,
    ) -> SandboxResult:
        """Execute code in a Kubernetes Pod.

        Args:
            code: The code to execute.
            language: Programming language (currently only "python").
            **kwargs: Additional parameters (e.g., agent_id, tick for audit).

        Returns:
            SandboxResult with execution outcome.
        """
        from kubernetes import client

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
            core_v1, batch_v1 = await self._get_clients()
        except Exception as e:
            return SandboxResult(
                success=False,
                error_message=f"Kubernetes not available: {e}",
                code_hash=code_hash,
            )

        # Generate unique job name
        job_name = f"sandbox-{uuid.uuid4().hex[:12]}"

        # Create wrapper script
        import base64
        wrapper_script = f'''
import sys
import json
import traceback

try:
    _result = None
    _locals = {{}}
    
    exec("""
{code}
""", _locals)
    
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
        encoded_script = base64.b64encode(wrapper_script.encode()).decode()

        # Build Job spec
        job_spec = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(
                name=job_name,
                namespace=self.namespace,
                labels={
                    "app": "agentkernel-sandbox",
                    "agent-id": kwargs.get("agent_id", "unknown")[:63],
                },
            ),
            spec=client.V1JobSpec(
                ttl_seconds_after_finished=60,  # Auto-cleanup
                backoff_limit=0,  # No retries
                active_deadline_seconds=self.config.timeout_seconds,
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={"app": "agentkernel-sandbox"},
                    ),
                    spec=client.V1PodSpec(
                        service_account_name=self.service_account,
                        restart_policy="Never",
                        automount_service_account_token=False,
                        security_context=client.V1PodSecurityContext(
                            run_as_non_root=True,
                            run_as_user=1000,
                            run_as_group=1000,
                            fs_group=1000,
                            seccomp_profile=client.V1SeccompProfile(
                                type="RuntimeDefault",
                            ),
                        ),
                        containers=[
                            client.V1Container(
                                name="sandbox",
                                image=self.config.image,
                                command=[
                                    "sh", "-c",
                                    f"echo {encoded_script} | base64 -d | python",
                                ],
                                resources=client.V1ResourceRequirements(
                                    limits={
                                        "cpu": self.config.cpu_limit,
                                        "memory": f"{self.config.memory_limit_mb}Mi",
                                    },
                                    requests={
                                        "cpu": "100m",
                                        "memory": "64Mi",
                                    },
                                ),
                                security_context=client.V1SecurityContext(
                                    allow_privilege_escalation=False,
                                    read_only_root_filesystem=self.config.read_only_fs,
                                    capabilities=client.V1Capabilities(
                                        drop=["ALL"],
                                    ),
                                ),
                            ),
                        ],
                    ),
                ),
            ),
        )

        try:
            # Create the Job
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: batch_v1.create_namespaced_job(
                    namespace=self.namespace,
                    body=job_spec,
                ),
            )

            # Wait for completion
            completed = False
            pod_name = None
            exit_code = -1

            for _ in range(self.config.timeout_seconds * 2):  # Poll every 0.5s
                await asyncio.sleep(0.5)

                # Check job status
                job = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: batch_v1.read_namespaced_job_status(
                        name=job_name,
                        namespace=self.namespace,
                    ),
                )

                if job.status.succeeded:
                    completed = True
                    exit_code = 0
                    break
                elif job.status.failed:
                    completed = True
                    exit_code = 1
                    break

                # Get pod name for logs
                if pod_name is None:
                    pods = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: core_v1.list_namespaced_pod(
                            namespace=self.namespace,
                            label_selector=f"job-name={job_name}",
                        ),
                    )
                    if pods.items:
                        pod_name = pods.items[0].metadata.name

            # Get logs
            stdout = ""
            stderr = ""
            if pod_name:
                try:
                    logs = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: core_v1.read_namespaced_pod_log(
                            name=pod_name,
                            namespace=self.namespace,
                        ),
                    )
                    stdout = logs
                except Exception as e:
                    logger.warning("Failed to get pod logs: %s", e)

        finally:
            # Clean up job (TTL will handle it, but let's be explicit)
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: batch_v1.delete_namespaced_job(
                        name=job_name,
                        namespace=self.namespace,
                        propagation_policy="Background",
                    ),
                )
            except Exception as e:
                logger.warning("Failed to delete job %s: %s", job_name, e)

        execution_time = (time.perf_counter() - start_time) * 1000

        if not completed:
            return SandboxResult(
                success=False,
                error_message=f"Execution timed out after {self.config.timeout_seconds}s",
                execution_time_ms=execution_time,
                code_hash=code_hash,
            )

        # Parse output
        stdout, stdout_truncated = self._truncate_output(stdout)

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
            error_message=None if success else f"Execution failed with exit code {exit_code}",
            truncated=stdout_truncated,
            code_hash=code_hash,
        )

    async def cleanup(self) -> None:
        """Clean up Kubernetes resources."""
        # Nothing to clean up - pods are ephemeral
        pass

