"""Tool specification schema for standardized tool definitions.

This module provides the ToolSpec class that defines a unified interface
for tools that can be called by LLMs using function calling / tool use.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ToolSafety(BaseModel):
    """Safety metadata for a tool.

    Attributes:
        side_effect: Whether the tool has side effects (e.g., writes to DB).
        requires_network: Whether the tool requires network access.
        requires_fs: Whether the tool requires filesystem access.
        requires_sandbox: Whether the tool should run in a sandboxed environment.
        risk_level: Risk level from 0 (safe) to 3 (high risk).
        allowed_domains: List of allowed domains for network access (if applicable).
        audit_required: Whether tool calls should be logged for audit.
    """

    side_effect: bool = False
    requires_network: bool = False
    requires_fs: bool = False
    requires_sandbox: bool = False
    risk_level: int = Field(default=0, ge=0, le=3)
    allowed_domains: List[str] = Field(default_factory=list)
    audit_required: bool = False


class ToolSpec(BaseModel):
    """Standard tool specification compatible with OpenAI function calling.

    This schema defines a unified interface for all tools in the Agent-Kernel
    framework, whether they are FunctionToolPlugins, MCPToolPlugins, or
    built-in tools like Code Interpreter.

    Attributes:
        name: Unique identifier for the tool.
        description: Human-readable description of what the tool does.
        input_schema: JSON Schema describing the tool's input parameters.
        output_schema: Optional JSON Schema describing the tool's output.
        safety: Safety metadata for the tool.
        examples: Optional list of example invocations.
        tags: Optional tags for categorization.
    """

    name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(..., min_length=1, max_length=4096)
    input_schema: Dict[str, Any] = Field(default_factory=lambda: {"type": "object", "properties": {}})
    output_schema: Optional[Dict[str, Any]] = None
    safety: ToolSafety = Field(default_factory=ToolSafety)
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

    def to_openai_function(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format.

        Returns:
            Dict suitable for OpenAI's tools parameter.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }

    def to_anthropic_tool(self) -> Dict[str, Any]:
        """Convert to Anthropic tool format.

        Returns:
            Dict suitable for Anthropic's tools parameter.
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

    @classmethod
    def from_function(
        cls,
        func: Any,
        name: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs: Any,
    ) -> "ToolSpec":
        """Create a ToolSpec from a Python function using introspection.

        Args:
            func: The function to create a spec from.
            name: Override the function name.
            description: Override the function docstring.
            **kwargs: Additional ToolSpec fields.

        Returns:
            ToolSpec instance.
        """
        import inspect
        from typing import get_type_hints

        func_name = name or func.__name__
        func_desc = description or (inspect.getdoc(func) or f"Execute {func_name}")

        # Build input schema from type hints
        hints = get_type_hints(func) if hasattr(func, "__annotations__") else {}
        sig = inspect.signature(func)

        properties: Dict[str, Any] = {}
        required: List[str] = []

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue

            param_type = hints.get(param_name, Any)
            json_type = _python_type_to_json_schema(param_type)

            properties[param_name] = json_type

            if param.default is inspect.Parameter.empty:
                required.append(param_name)

        input_schema = {
            "type": "object",
            "properties": properties,
        }
        if required:
            input_schema["required"] = required

        return cls(
            name=func_name,
            description=func_desc,
            input_schema=input_schema,
            **kwargs,
        )


def _python_type_to_json_schema(python_type: Any) -> Dict[str, Any]:
    """Convert a Python type to JSON Schema type.

    Args:
        python_type: The Python type to convert.

    Returns:
        JSON Schema type definition.
    """
    import typing

    origin = typing.get_origin(python_type)
    args = typing.get_args(python_type)

    # Handle Optional
    if origin is typing.Union and type(None) in args:
        non_none_args = [a for a in args if a is not type(None)]
        if len(non_none_args) == 1:
            schema = _python_type_to_json_schema(non_none_args[0])
            return schema

    # Handle List
    if origin is list:
        item_type = args[0] if args else Any
        return {"type": "array", "items": _python_type_to_json_schema(item_type)}

    # Handle Dict
    if origin is dict:
        return {"type": "object"}

    # Basic types
    type_map = {
        str: {"type": "string"},
        int: {"type": "integer"},
        float: {"type": "number"},
        bool: {"type": "boolean"},
        type(None): {"type": "null"},
    }

    if python_type in type_map:
        return type_map[python_type]

    # Default to string for unknown types
    return {"type": "string"}

