"""Agent component for memory retrieval and context injection.

This component integrates with the Memory Layer to provide:
- RAG-based memory retrieval
- Social relationship context
- Automatic context injection into the planning pipeline
"""

from typing import Any, Dict, List, Optional

from ....toolkit.logger import get_logger
from ..base.component_base import AgentComponent
from ..base.plugin_base import MemoryPlugin

__all__ = ["MemoryComponent"]

logger = get_logger(__name__)


class MemoryComponent(AgentComponent["MemoryPlugin"]):
    """A component that manages agent memory retrieval and context.

    This component runs before the planning component to inject relevant
    memories and social context into the agent's decision-making process.
    """

    COMPONENT_NAME = "memory"

    def __init__(self) -> None:
        """Initialize the memory component."""
        super().__init__()
        self._memory_context: Optional[Dict[str, Any]] = None
        self._social_context: Optional[str] = None
        self._retrieved_memories: List[Dict[str, Any]] = []

    @property
    def memory_context(self) -> Optional[Dict[str, Any]]:
        """Return the most recent memory context."""
        return self._memory_context

    @memory_context.setter
    def memory_context(self, context: Optional[Dict[str, Any]]) -> None:
        """Set the memory context."""
        self._memory_context = context

    @property
    def social_context(self) -> Optional[str]:
        """Return the most recent social context summary."""
        return self._social_context

    @social_context.setter
    def social_context(self, context: Optional[str]) -> None:
        """Set the social context."""
        self._social_context = context

    @property
    def retrieved_memories(self) -> List[Dict[str, Any]]:
        """Return the list of retrieved memory records."""
        return self._retrieved_memories

    async def get_context_for_planning(self) -> Dict[str, Any]:
        """Get memory context formatted for the planning component.

        Returns:
            Dictionary containing memory and social context.
        """
        return {
            "memory_context": self._memory_context,
            "social_context": self._social_context,
            "retrieved_memories": self._retrieved_memories,
        }

    async def execute(self, current_tick: int) -> None:
        """Execute the memory retrieval for the given simulation tick.

        Args:
            current_tick: Simulation tick used when invoking the plugin.
        """
        if not self._plugin:
            logger.debug("No plugin found in MemoryComponent, skipping.")
            return

        await self._plugin.execute(current_tick)

        # Copy results from plugin
        self._memory_context = self._plugin.memory_context
        self._social_context = self._plugin.social_context
        self._retrieved_memories = self._plugin.retrieved_memories

