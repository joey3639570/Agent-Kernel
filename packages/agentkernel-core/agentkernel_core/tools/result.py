"""Tool execution result schema.

This module provides the ToolResult class that standardizes the output
of all tool executions in the Agent-Kernel framework.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ToolResultStatus(str, Enum):
    """Status of a tool execution.

    Attributes:
        SUCCESS: Tool executed successfully.
        ERROR: Tool execution failed with an error.
        TIMEOUT: Tool execution timed out.
        CANCELLED: Tool execution was cancelled.
        PENDING: Tool execution is still in progress.
    """

    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    PENDING = "pending"


class ToolResult(BaseModel):
    """Standardized result from tool execution.

    Attributes:
        tool_name: Name of the tool that was executed.
        status: Execution status.
        output: Structured output data from the tool.
        stdout: Standard output captured during execution.
        stderr: Standard error captured during execution.
        error_message: Error message if execution failed.
        error_type: Type/class of the error if execution failed.
        execution_time_ms: Time taken to execute in milliseconds.
        started_at: When execution started.
        completed_at: When execution completed.
        trace_id: Optional trace ID for observability.
        metadata: Additional key-value metadata.
    """

    tool_name: str
    status: ToolResultStatus = ToolResultStatus.SUCCESS
    output: Optional[Any] = None
    stdout: str = ""
    stderr: str = ""
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    execution_time_ms: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    trace_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def is_success(self) -> bool:
        """Check if the execution was successful."""
        return self.status == ToolResultStatus.SUCCESS

    def is_error(self) -> bool:
        """Check if the execution failed."""
        return self.status in (ToolResultStatus.ERROR, ToolResultStatus.TIMEOUT)

    def get_output_text(self) -> str:
        """Get a text representation of the output for LLM consumption.

        Returns:
            String representation of the tool output.
        """
        if self.is_error():
            error_text = f"Error: {self.error_message or 'Unknown error'}"
            if self.stderr:
                error_text += f"\nStderr: {self.stderr}"
            return error_text

        parts = []
        if self.output is not None:
            if isinstance(self.output, str):
                parts.append(self.output)
            else:
                import json
                try:
                    parts.append(json.dumps(self.output, indent=2, default=str))
                except Exception:
                    parts.append(str(self.output))

        if self.stdout:
            parts.append(f"Stdout:\n{self.stdout}")

        return "\n".join(parts) if parts else "Tool executed successfully with no output."

    @classmethod
    def success(
        cls,
        tool_name: str,
        output: Any = None,
        stdout: str = "",
        execution_time_ms: float = 0.0,
        **kwargs: Any,
    ) -> "ToolResult":
        """Create a successful tool result."""
        return cls(
            tool_name=tool_name,
            status=ToolResultStatus.SUCCESS,
            output=output,
            stdout=stdout,
            execution_time_ms=execution_time_ms,
            **kwargs,
        )

    @classmethod
    def error(
        cls,
        tool_name: str,
        error_message: str,
        error_type: Optional[str] = None,
        stderr: str = "",
        execution_time_ms: float = 0.0,
        **kwargs: Any,
    ) -> "ToolResult":
        """Create an error tool result."""
        return cls(
            tool_name=tool_name,
            status=ToolResultStatus.ERROR,
            error_message=error_message,
            error_type=error_type,
            stderr=stderr,
            execution_time_ms=execution_time_ms,
            **kwargs,
        )

    @classmethod
    def timeout(
        cls,
        tool_name: str,
        execution_time_ms: float = 0.0,
        **kwargs: Any,
    ) -> "ToolResult":
        """Create a timeout tool result."""
        return cls(
            tool_name=tool_name,
            status=ToolResultStatus.TIMEOUT,
            error_message="Tool execution timed out",
            execution_time_ms=execution_time_ms,
            **kwargs,
        )

