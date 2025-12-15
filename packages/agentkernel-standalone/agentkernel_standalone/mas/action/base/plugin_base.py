"""Plugin base classes used by action components."""

import inspect
from abc import ABC, abstractmethod
from types import TracebackType
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Type

from ....toolkit.utils.annotation import ServiceCall

if TYPE_CHECKING:
    from ...controller import BaseController

from ....toolkit.models.router import ModelRouter
from fastmcp import Client

__all__ = ["ActionPlugin", "CommunicationPlugin", "MCPToolPlugin", "FunctionToolPlugin", "OtherActionsPlugin"]


class ActionPlugin(ABC):
    """Base class for all action plugins executed by a component."""

    COMPONENT_TYPE: str = "base"

    def __init__(self) -> None:
        """Initialize dependency placeholders for subclasses."""
        self.model: Optional[ModelRouter] = None
        self.controller: Optional["BaseController"] = None

    @abstractmethod
    async def init(
        self, model_router: Optional[ModelRouter] = None, controller: Optional["BaseController"] = None
    ) -> None:
        """
        Perform post-instantiation setup for the plugin.

        Args:
            model_router (Optional[ModelRouter]): Shared model router instance.
            controller (Optional["BaseController"]): Controller coordinating the component.
        """

    @abstractmethod
    async def _log_action(self, *args: Any, **kwargs: Any) -> None:
        """
        Record execution metadata for auditing.

        Args:
            *args (Any): Positional data to log.
            **kwargs (Any): Keyword data to log.
        """

    async def prepare(self, annotation_type: str) -> List[Dict[str, Any]]:
        """
        Build a list of annotated methods exposed by the plugin.

        Args:
            annotation_type (str): Annotation tag used to discover methods.

        Returns:
            List[Dict[str, Any]]: Metadata describing each callable with ToolSpec-compatible format.
        """
        methods: List[Dict[str, Any]] = []
        for method_name in dir(self):
            method = getattr(self, method_name)
            is_annotated = callable(method) and getattr(method, "_annotation", None) == annotation_type
            if not is_annotated:
                continue

            description = inspect.getdoc(method) or ""

            # Generate input_schema from method signature for ToolSpec compatibility
            input_schema = self._generate_input_schema(method)

            methods.append(
                {
                    "name": method_name,
                    "description": description.strip(),
                    "input_schema": input_schema,
                }
            )

        return methods

    def _generate_input_schema(self, method: Callable[..., Any]) -> Dict[str, Any]:
        """Generate JSON Schema for a method's parameters.

        Args:
            method: The method to introspect.

        Returns:
            JSON Schema dict describing the method's parameters.
        """
        from typing import get_type_hints, get_origin, get_args, Union

        sig = inspect.signature(method)
        try:
            hints = get_type_hints(method)
        except Exception:
            hints = {}

        properties: Dict[str, Any] = {}
        required: List[str] = []

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue

            param_type = hints.get(param_name)
            json_type = self._python_type_to_json_schema(param_type)
            properties[param_name] = json_type

            # Add description from docstring if available
            if param.default is inspect.Parameter.empty:
                required.append(param_name)

        schema: Dict[str, Any] = {
            "type": "object",
            "properties": properties,
        }
        if required:
            schema["required"] = required

        return schema

    def _python_type_to_json_schema(self, python_type: Any) -> Dict[str, Any]:
        """Convert a Python type to JSON Schema type.

        Args:
            python_type: The Python type to convert.

        Returns:
            JSON Schema type definition.
        """
        from typing import get_origin, get_args, Union

        if python_type is None:
            return {"type": "string"}

        origin = get_origin(python_type)
        args = get_args(python_type)

        # Handle Optional (Union with None)
        if origin is Union and type(None) in args:
            non_none_args = [a for a in args if a is not type(None)]
            if len(non_none_args) == 1:
                return self._python_type_to_json_schema(non_none_args[0])

        # Handle List
        if origin is list:
            item_type = args[0] if args else Any
            return {"type": "array", "items": self._python_type_to_json_schema(item_type)}

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

    async def execute(self, name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a method by name with provided arguments.

        Args:
            name (str): Name of the method to invoke.
            arguments (Dict[str, Any]): Keyword arguments forwarded to the method.

        Returns:
            Any: Result produced by the target method or an error string.
        """
        method_name = name

        if not hasattr(self, method_name):
            return f"Method {method_name} does not exist"

        method = getattr(self, method_name)
        if not callable(method):
            return f"Method {method_name} is not callable"

        try:
            if inspect.iscoroutinefunction(method):
                return await method(**arguments)
            return method(**arguments)
        except TypeError as e:
            return f"Parameter error: {str(e)}"

    @ServiceCall
    async def save_to_db(self) -> None:
        """
        (Optional) Save the plugin's persistent state to the database.

        Subclasses that require persistence should override this method.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError(f"Plugin {self.__class__.__name__} does not implement 'save_to_db'")

    @ServiceCall
    async def load_from_db(self) -> None:
        """
        (Optional) Load the plugin's persistent state from the database.

        Subclasses that require persistence should override this method.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError(f"Plugin {self.__class__.__name__} does not implement 'load_from_db'")


class CommunicationPlugin(ActionPlugin):
    """Base class for communication-focused action plugins."""

    COMPONENT_TYPE = "communication"

    async def init(
        self, model_router: Optional[ModelRouter] = None, controller: Optional["BaseController"] = None
    ) -> None:
        """
        Store injected dependencies for subclasses.

        Args:
            model_router (Optional[ModelRouter]): Shared model router instance.
            controller (Optional["BaseController"]): Controller coordinating the component.
        """
        self.model = model_router
        self.controller = controller


class MCPToolPlugin(ActionPlugin):
    """Base class for plugins that proxy calls to an MCP server."""

    COMPONENT_TYPE = "tools"

    def __init__(self, server_path: str) -> None:
        """
        Create an MCP client for the provided server path.

        Args:
            server_path (str): File system path to the MCP server definition.
        """
        super().__init__()
        self.client = Client(server_path)

    async def init(
        self, model_router: Optional[ModelRouter] = None, controller: Optional["BaseController"] = None
    ) -> None:
        """
        Store controller and model router references.

        Args:
            model_router (Optional[ModelRouter]): Shared model router instance.
            controller (Optional["BaseController"]): Controller coordinating the component.
        """
        self.model = model_router
        self.controller = controller

    async def __aenter__(self) -> "MCPToolPlugin":
        """
        Enter the asynchronous context by opening the MCP client.

        Returns:
            MCPToolPlugin: The initialized plugin instance.
        """
        await self.client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """
        Close the MCP client when exiting the context.

        Args:
            exc_type (Optional[Type[BaseException]]): Exception type raised within the context.
            exc_val (Optional[BaseException]): Exception instance raised within the context.
            exc_tb (Optional[TracebackType]): Traceback information for the exception.
        """
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def prepare(self, annotation_type: str) -> List[Dict[str, Any]]:
        """
        Fetch available tool definitions from the MCP server.

        Args:
            annotation_type (str): Unused annotation filter maintained for interface compatibility.

        Returns:
            List[Dict[str, Any]]: Metadata for each MCP tool.
        """
        raw_tools = await self.client.list_tools()
        tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in raw_tools
        ]
        return tools

    async def execute(self, name: str, arguments: Dict[str, Any]) -> Any:
        """
        Invoke a named MCP tool with the supplied arguments.

        Args:
            name (str): Target tool name registered on the server.
            arguments (Dict[str, Any]): Keyword arguments forwarded to the tool.

        Returns:
            Any: Result produced by the MCP tool invocation.
        """
        return await self.client.call_tool(name, arguments)


class FunctionToolPlugin(ActionPlugin):
    """Base class for function-based tool plugins."""

    COMPONENT_TYPE = "tools"

    async def init(
        self, model_router: Optional[ModelRouter] = None, controller: Optional["BaseController"] = None
    ) -> None:
        """
        Store shared dependencies for downstream usage.

        Args:
            model_router (Optional[ModelRouter]): Shared model router instance.
            controller (Optional["BaseController"]): Controller coordinating the component.
        """
        self.model = model_router
        self.controller = controller


class OtherActionsPlugin(ActionPlugin):
    """Base class for miscellaneous action plugins."""

    COMPONENT_TYPE = "otheractions"

    async def init(
        self, model_router: Optional[ModelRouter] = None, controller: Optional["BaseController"] = None
    ) -> None:
        """
        Store injected dependencies for subclasses.

        Args:
            model_router (Optional[ModelRouter]): Shared model router instance.
            controller (Optional["BaseController"]): Controller coordinating the component.
        """
        self.model = model_router
        self.controller = controller
