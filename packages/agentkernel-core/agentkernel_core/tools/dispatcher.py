"""Async tool dispatcher with concurrency control, timeouts, and tracing.

This module provides the ToolDispatcher class that manages tool execution
with proper async coordination, circuit breaking, and observability.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Coroutine, Dict, List, Optional

from agentkernel_core.tools.result import ToolResult, ToolResultStatus
from agentkernel_core.tools.spec import ToolSpec

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreakerState:
    """State tracking for circuit breaker pattern.

    Attributes:
        failure_count: Number of consecutive failures.
        last_failure_time: Timestamp of the last failure.
        is_open: Whether the circuit is currently open (blocking requests).
        half_open_allowed: Whether a test request is allowed in half-open state.
    """

    failure_count: int = 0
    last_failure_time: Optional[float] = None
    is_open: bool = False
    half_open_allowed: bool = True


@dataclass
class DispatcherConfig:
    """Configuration for the ToolDispatcher.

    Attributes:
        max_concurrent: Maximum number of concurrent tool executions.
        default_timeout: Default timeout for tool execution in seconds.
        retry_count: Number of retries for failed executions.
        retry_delay: Delay between retries in seconds.
        circuit_breaker_threshold: Failures before opening circuit.
        circuit_breaker_timeout: Time before attempting recovery.
        enable_tracing: Whether to enable OpenTelemetry tracing.
        audit_enabled: Whether to log all tool calls for audit.
    """

    max_concurrent: int = 10
    default_timeout: float = 60.0
    retry_count: int = 1
    retry_delay: float = 1.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 30.0
    enable_tracing: bool = False
    audit_enabled: bool = True


class ToolDispatcher:
    """Async dispatcher for tool execution with concurrency control.

    This class provides:
    - Semaphore-based concurrency limiting
    - Timeout management
    - Retry logic with exponential backoff
    - Circuit breaker pattern
    - OpenTelemetry tracing integration
    - Audit logging
    """

    def __init__(self, config: Optional[DispatcherConfig] = None) -> None:
        """Initialize the dispatcher.

        Args:
            config: Optional configuration override.
        """
        self.config = config or DispatcherConfig()
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self._circuit_breakers: Dict[str, CircuitBreakerState] = {}
        self._tools: Dict[str, ToolSpec] = {}
        self._handlers: Dict[str, Callable[..., Coroutine[Any, Any, Any]]] = {}
        self._tracer: Optional[Any] = None

        if self.config.enable_tracing:
            self._init_tracing()

    def _init_tracing(self) -> None:
        """Initialize OpenTelemetry tracing if available."""
        try:
            from opentelemetry import trace

            self._tracer = trace.get_tracer("agentkernel.tools")
        except ImportError:
            logger.warning("OpenTelemetry not available, tracing disabled")

    def register_tool(
        self,
        spec: ToolSpec,
        handler: Callable[..., Coroutine[Any, Any, Any]],
    ) -> None:
        """Register a tool with its specification and handler.

        Args:
            spec: The tool specification.
            handler: Async function that executes the tool.
        """
        self._tools[spec.name] = spec
        self._handlers[spec.name] = handler
        self._circuit_breakers[spec.name] = CircuitBreakerState()
        logger.debug("Registered tool: %s", spec.name)

    def unregister_tool(self, name: str) -> None:
        """Unregister a tool.

        Args:
            name: Name of the tool to unregister.
        """
        self._tools.pop(name, None)
        self._handlers.pop(name, None)
        self._circuit_breakers.pop(name, None)

    def get_tool_specs(self) -> List[ToolSpec]:
        """Get all registered tool specifications.

        Returns:
            List of registered ToolSpec objects.
        """
        return list(self._tools.values())

    def get_tool_spec(self, name: str) -> Optional[ToolSpec]:
        """Get a specific tool specification.

        Args:
            name: Name of the tool.

        Returns:
            ToolSpec if found, None otherwise.
        """
        return self._tools.get(name)

    async def dispatch(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: Optional[float] = None,
        trace_id: Optional[str] = None,
        caller_agent_id: Optional[str] = None,
        current_tick: Optional[int] = None,
    ) -> ToolResult:
        """Dispatch a tool execution.

        Args:
            tool_name: Name of the tool to execute.
            arguments: Arguments to pass to the tool.
            timeout: Optional timeout override.
            trace_id: Optional trace ID for observability.
            caller_agent_id: ID of the agent calling the tool.
            current_tick: Current simulation tick.

        Returns:
            ToolResult with execution outcome.
        """
        trace_id = trace_id or str(uuid.uuid4())
        started_at = datetime.now()
        start_time = time.perf_counter()

        # Check if tool exists
        if tool_name not in self._handlers:
            return ToolResult.error(
                tool_name=tool_name,
                error_message=f"Tool '{tool_name}' not found",
                error_type="ToolNotFoundError",
                trace_id=trace_id,
            )

        # Check circuit breaker
        cb = self._circuit_breakers.get(tool_name)
        if cb and self._is_circuit_open(cb):
            return ToolResult.error(
                tool_name=tool_name,
                error_message="Circuit breaker open, tool temporarily unavailable",
                error_type="CircuitBreakerOpen",
                trace_id=trace_id,
            )

        # Execute with concurrency control
        async with self._semaphore:
            result = await self._execute_with_retry(
                tool_name=tool_name,
                arguments=arguments,
                timeout=timeout or self.config.default_timeout,
                trace_id=trace_id,
            )

        # Update timing
        execution_time_ms = (time.perf_counter() - start_time) * 1000
        result.execution_time_ms = execution_time_ms
        result.started_at = started_at
        result.completed_at = datetime.now()
        result.trace_id = trace_id

        # Update circuit breaker
        self._update_circuit_breaker(tool_name, result.is_success())

        # Audit logging
        if self.config.audit_enabled:
            self._audit_log(
                tool_name=tool_name,
                arguments=arguments,
                result=result,
                caller_agent_id=caller_agent_id,
                current_tick=current_tick,
            )

        return result

    async def _execute_with_retry(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: float,
        trace_id: str,
    ) -> ToolResult:
        """Execute tool with retry logic.

        Args:
            tool_name: Name of the tool.
            arguments: Tool arguments.
            timeout: Execution timeout.
            trace_id: Trace ID for logging.

        Returns:
            ToolResult from execution.
        """
        handler = self._handlers[tool_name]
        last_error: Optional[Exception] = None

        for attempt in range(self.config.retry_count + 1):
            try:
                result = await asyncio.wait_for(
                    self._execute_single(handler, arguments, trace_id),
                    timeout=timeout,
                )
                return result

            except asyncio.TimeoutError:
                logger.warning(
                    "Tool %s timed out (attempt %d/%d)",
                    tool_name,
                    attempt + 1,
                    self.config.retry_count + 1,
                )
                if attempt == self.config.retry_count:
                    return ToolResult.timeout(tool_name=tool_name, trace_id=trace_id)

            except Exception as e:
                last_error = e
                logger.warning(
                    "Tool %s failed (attempt %d/%d): %s",
                    tool_name,
                    attempt + 1,
                    self.config.retry_count + 1,
                    str(e),
                )
                if attempt < self.config.retry_count:
                    await asyncio.sleep(self.config.retry_delay * (2**attempt))

        return ToolResult.error(
            tool_name=tool_name,
            error_message=str(last_error) if last_error else "Unknown error",
            error_type=type(last_error).__name__ if last_error else "UnknownError",
            trace_id=trace_id,
        )

    async def _execute_single(
        self,
        handler: Callable[..., Coroutine[Any, Any, Any]],
        arguments: Dict[str, Any],
        trace_id: str,
    ) -> ToolResult:
        """Execute a single tool invocation.

        Args:
            handler: The async handler function.
            arguments: Arguments for the handler.
            trace_id: Trace ID.

        Returns:
            ToolResult from the handler.
        """
        if self._tracer:
            # OpenTelemetry tracing
            from opentelemetry import trace

            with self._tracer.start_as_current_span(
                "tool_execution",
                attributes={"trace_id": trace_id},
            ) as span:
                result = await handler(**arguments)
                if isinstance(result, ToolResult):
                    span.set_attribute("status", result.status.value)
                return result
        else:
            result = await handler(**arguments)
            return result

    def _is_circuit_open(self, cb: CircuitBreakerState) -> bool:
        """Check if circuit breaker is open.

        Args:
            cb: Circuit breaker state.

        Returns:
            True if circuit is open and should block requests.
        """
        if not cb.is_open:
            return False

        # Check if timeout has passed (half-open state)
        if cb.last_failure_time:
            elapsed = time.time() - cb.last_failure_time
            if elapsed >= self.config.circuit_breaker_timeout:
                if cb.half_open_allowed:
                    cb.half_open_allowed = False
                    return False  # Allow one test request

        return True

    def _update_circuit_breaker(self, tool_name: str, success: bool) -> None:
        """Update circuit breaker state after execution.

        Args:
            tool_name: Name of the tool.
            success: Whether execution was successful.
        """
        cb = self._circuit_breakers.get(tool_name)
        if not cb:
            return

        if success:
            cb.failure_count = 0
            cb.is_open = False
            cb.half_open_allowed = True
        else:
            cb.failure_count += 1
            cb.last_failure_time = time.time()

            if cb.failure_count >= self.config.circuit_breaker_threshold:
                cb.is_open = True
                logger.warning("Circuit breaker opened for tool: %s", tool_name)

    def _audit_log(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: ToolResult,
        caller_agent_id: Optional[str],
        current_tick: Optional[int],
    ) -> None:
        """Log tool execution for audit.

        Args:
            tool_name: Name of the tool.
            arguments: Arguments passed to the tool.
            result: Execution result.
            caller_agent_id: Calling agent ID.
            current_tick: Current simulation tick.
        """
        import json

        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "agent_id": caller_agent_id,
            "tick": current_tick,
            "status": result.status.value,
            "execution_time_ms": result.execution_time_ms,
            "trace_id": result.trace_id,
            # Don't log full arguments/output for security
            "argument_keys": list(arguments.keys()),
            "has_output": result.output is not None,
            "error_type": result.error_type,
        }

        logger.info("TOOL_AUDIT: %s", json.dumps(audit_entry))

    async def close(self) -> None:
        """Clean up dispatcher resources."""
        self._tools.clear()
        self._handlers.clear()
        self._circuit_breakers.clear()

