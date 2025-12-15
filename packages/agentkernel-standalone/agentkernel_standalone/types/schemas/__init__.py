from .agent import (
    PerceptionData,
    ActionOutcome,
    ActionRecord,
    CurrentAction,
)
from .message import Message, MessageKind
from .vectordb import (
    VectorDocument,
    VectorSearchRequest,
    VectorSearchResult,
    VectorStoreInfo,
)
from .action import ActionResult, CallStatus

# Re-export from agentkernel-core for new types
try:
    from agentkernel_core.types.schemas.message import MessageContent
    from agentkernel_core.types.schemas.tool import ToolSpec, ToolSafety
    from agentkernel_core.types.schemas.memory import (
        MemoryRecord,
        MemoryQuery,
        MemoryHit,
        MemoryContext,
        MemoryType,
    )
    from agentkernel_core.types.schemas.graph import (
        GraphNode,
        RelationEdge,
        RelationType,
        SocialSubgraph,
    )
    from agentkernel_core.tools.result import ToolResult, ToolResultStatus

    _CORE_AVAILABLE = True
except ImportError:
    _CORE_AVAILABLE = False
    # Define stubs for when core is not available
    MessageContent = None
    ToolSpec = None
    ToolSafety = None
    MemoryRecord = None
    MemoryQuery = None
    MemoryHit = None
    MemoryContext = None
    MemoryType = None
    GraphNode = None
    RelationEdge = None
    RelationType = None
    SocialSubgraph = None
    ToolResult = None
    ToolResultStatus = None

__all__ = [
    # Agent types
    "PerceptionData",
    "ActionOutcome",
    "ActionRecord",
    "CurrentAction",
    # Message types
    "Message",
    "MessageKind",
    "MessageContent",
    # Action types
    "ActionResult",
    "CallStatus",
    # VectorDB types
    "VectorDocument",
    "VectorSearchRequest",
    "VectorSearchResult",
    "VectorStoreInfo",
    # Tool types (from core)
    "ToolSpec",
    "ToolSafety",
    "ToolResult",
    "ToolResultStatus",
    # Memory types (from core)
    "MemoryRecord",
    "MemoryQuery",
    "MemoryHit",
    "MemoryContext",
    "MemoryType",
    # Graph types (from core)
    "GraphNode",
    "RelationEdge",
    "RelationType",
    "SocialSubgraph",
]
