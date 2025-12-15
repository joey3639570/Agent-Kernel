"""Agent-Kernel Core: Shared abstractions, schemas, and interfaces.

This package provides the foundational types and interfaces used by both
agentkernel-standalone and agentkernel-distributed runtimes.

Modules:
    - types.schemas: Message, Tool, Memory, Graph, and VectorDB schemas
    - memory: Memory interfaces and implementations (Vector RAG, Social Graph)
    - tools: Tool specification, dispatcher, and sandboxed code execution
    - plugins: Sensor and tool plugins (Vision, Code Interpreter)
    - extensions: Vertical solutions (Game Bridge, QA Simulator, Policy Sandbox)
"""

__version__ = "0.1.0"

# Core types
from agentkernel_core.types.schemas.message import Message, MessageContent, MessageKind
from agentkernel_core.tools.spec import ToolSpec, ToolSafety
from agentkernel_core.tools.result import ToolResult, ToolResultStatus
from agentkernel_core.tools.dispatcher import ToolDispatcher

# Memory
from agentkernel_core.memory.interfaces import MemoryModule, GraphMemoryModule
from agentkernel_core.memory.manager import MemoryManager
from agentkernel_core.memory.vector import VectorMemory
from agentkernel_core.memory.graph import GraphMemory

# Extensions
from agentkernel_core.extensions.game_bridge import GameBridge, GameAction, GameEvent, GameState
from agentkernel_core.extensions.qa_simulator import QASimulator, UserPersona, BrowserAction
from agentkernel_core.extensions.policy_sandbox import PolicySandbox, GlobalState, SimulationMetrics

__all__ = [
    "__version__",
    # Message types
    "Message",
    "MessageContent",
    "MessageKind",
    # Tool types
    "ToolSpec",
    "ToolSafety",
    "ToolResult",
    "ToolResultStatus",
    "ToolDispatcher",
    # Memory
    "MemoryModule",
    "GraphMemoryModule",
    "MemoryManager",
    "VectorMemory",
    "GraphMemory",
    # Extensions
    "GameBridge",
    "GameAction",
    "GameEvent",
    "GameState",
    "QASimulator",
    "UserPersona",
    "BrowserAction",
    "PolicySandbox",
    "GlobalState",
    "SimulationMetrics",
]

