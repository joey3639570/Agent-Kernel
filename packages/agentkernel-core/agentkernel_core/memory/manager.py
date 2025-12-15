"""High-level Memory Manager for coordinating RAG and Social Graph memory.

This module provides the MemoryManager class that orchestrates memory
storage, retrieval, and prompt injection for agents.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Coroutine, Dict, List, Optional

from agentkernel_core.memory.interfaces import GraphMemoryModule, MemoryModule
from agentkernel_core.types.schemas.graph import RelationType, SocialSubgraph
from agentkernel_core.types.schemas.memory import (
    MemoryContext,
    MemoryHit,
    MemoryQuery,
    MemoryRecord,
    MemoryType,
)

logger = logging.getLogger(__name__)


class MemoryManager:
    """High-level manager for agent memory systems.

    This class coordinates:
    - Vector memory (RAG) for episodic/semantic recall
    - Graph memory for social relationships
    - Embedding generation
    - Prompt context assembly
    """

    def __init__(
        self,
        vector_memory: Optional[MemoryModule] = None,
        graph_memory: Optional[GraphMemoryModule] = None,
        embed_fn: Optional[Callable[[str], Coroutine[Any, Any, List[float]]]] = None,
    ) -> None:
        """Initialize the memory manager.

        Args:
            vector_memory: Optional vector memory backend.
            graph_memory: Optional graph memory backend.
            embed_fn: Async function to generate embeddings from text.
        """
        self._vector_memory = vector_memory
        self._graph_memory = graph_memory
        self._embed_fn = embed_fn

    def set_vector_memory(self, memory: MemoryModule) -> None:
        """Set the vector memory backend."""
        self._vector_memory = memory

    def set_graph_memory(self, memory: GraphMemoryModule) -> None:
        """Set the graph memory backend."""
        self._graph_memory = memory

    def set_embed_fn(
        self,
        fn: Callable[[str], Coroutine[Any, Any, List[float]]],
    ) -> None:
        """Set the embedding function."""
        self._embed_fn = fn

    # ========== Vector Memory Operations ==========

    async def store_memory(
        self,
        agent_id: str,
        content: str,
        memory_type: MemoryType = MemoryType.EPISODIC,
        tick: int = 0,
        importance: float = 0.5,
        related_agents: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Store a new memory for an agent.

        Args:
            agent_id: The agent storing the memory.
            content: The memory content.
            memory_type: Type classification.
            tick: Current simulation tick.
            importance: Importance score (0-1).
            related_agents: List of related agent IDs.
            metadata: Additional metadata.

        Returns:
            Memory ID if stored successfully, None otherwise.
        """
        if not self._vector_memory:
            logger.warning("No vector memory backend configured")
            return None

        # Generate embedding if available
        vector = None
        if self._embed_fn:
            try:
                vector = await self._embed_fn(content)
            except Exception as e:
                logger.warning("Failed to generate embedding: %s", e)

        record = MemoryRecord(
            agent_id=agent_id,
            content=content,
            memory_type=memory_type,
            tick=tick,
            importance=importance,
            vector=vector,
            related_agents=related_agents or [],
            metadata=metadata or {},
        )

        try:
            memory_id = await self._vector_memory.store(record, generate_embedding=vector is None)
            logger.debug("Stored memory %s for agent %s", memory_id, agent_id)
            return memory_id
        except Exception as e:
            logger.error("Failed to store memory: %s", e)
            return None

    async def retrieve_memories(
        self,
        agent_id: str,
        query_text: str,
        top_k: int = 5,
        memory_types: Optional[List[MemoryType]] = None,
        min_importance: float = 0.0,
        include_related_agents: Optional[List[str]] = None,
    ) -> List[MemoryHit]:
        """Retrieve relevant memories for an agent.

        Args:
            agent_id: The agent querying memories.
            query_text: The query text.
            top_k: Maximum results to return.
            memory_types: Filter by memory types.
            min_importance: Minimum importance threshold.
            include_related_agents: Filter by related agents.

        Returns:
            List of memory hits sorted by relevance.
        """
        if not self._vector_memory:
            return []

        # Generate query embedding
        query_vector = None
        if self._embed_fn:
            try:
                query_vector = await self._embed_fn(query_text)
            except Exception as e:
                logger.warning("Failed to generate query embedding: %s", e)

        query = MemoryQuery(
            query_text=query_text,
            query_vector=query_vector,
            agent_id=agent_id,
            memory_types=memory_types,
            top_k=top_k,
            min_importance=min_importance,
            include_related_agents=include_related_agents or [],
        )

        try:
            return await self._vector_memory.retrieve(query)
        except Exception as e:
            logger.error("Failed to retrieve memories: %s", e)
            return []

    # ========== Graph Memory Operations ==========

    async def add_agent_to_graph(
        self,
        agent_id: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Add an agent to the social graph.

        Args:
            agent_id: The agent ID.
            properties: Optional agent properties.

        Returns:
            True if added successfully.
        """
        if not self._graph_memory:
            return False

        try:
            return await self._graph_memory.add_agent(agent_id, properties)
        except Exception as e:
            logger.error("Failed to add agent to graph: %s", e)
            return False

    async def add_relationship(
        self,
        agent_a: str,
        agent_b: str,
        relation_type: RelationType,
        weight: float = 0.0,
        bidirectional: bool = True,
    ) -> bool:
        """Add or update a relationship between agents.

        Args:
            agent_a: First agent ID.
            agent_b: Second agent ID.
            relation_type: Type of relationship.
            weight: Relationship strength.
            bidirectional: Whether relationship is mutual.

        Returns:
            True if added successfully.
        """
        if not self._graph_memory:
            return False

        try:
            return await self._graph_memory.add_relation(
                source_id=agent_a,
                target_id=agent_b,
                relation_type=relation_type,
                weight=weight,
                bidirectional=bidirectional,
            )
        except Exception as e:
            logger.error("Failed to add relationship: %s", e)
            return False

    async def record_interaction(
        self,
        agent_a: str,
        agent_b: str,
        sentiment: float = 0.0,
        context: Optional[str] = None,
    ) -> bool:
        """Record an interaction between agents.

        Args:
            agent_a: First agent.
            agent_b: Second agent.
            sentiment: Interaction sentiment (-1 to 1).
            context: Optional context description.

        Returns:
            True if recorded successfully.
        """
        if not self._graph_memory:
            return False

        try:
            return await self._graph_memory.record_interaction(
                source_id=agent_a,
                target_id=agent_b,
                sentiment=sentiment,
                context=context,
            )
        except Exception as e:
            logger.error("Failed to record interaction: %s", e)
            return False

    async def get_social_context(
        self,
        agent_id: str,
        encounter_agent_ids: Optional[List[str]] = None,
        depth: int = 1,
    ) -> SocialSubgraph:
        """Get social context for an agent.

        Args:
            agent_id: The agent to get context for.
            encounter_agent_ids: Specific agents encountered (prioritized).
            depth: Graph traversal depth.

        Returns:
            SocialSubgraph with relevant relationships.
        """
        if not self._graph_memory:
            return SocialSubgraph(center_agent_id=agent_id)

        try:
            return await self._graph_memory.get_social_subgraph(
                agent_id=agent_id,
                depth=depth,
            )
        except Exception as e:
            logger.error("Failed to get social context: %s", e)
            return SocialSubgraph(center_agent_id=agent_id)

    # ========== Combined Context Retrieval ==========

    async def get_context_for_planning(
        self,
        agent_id: str,
        current_situation: str,
        encounter_agents: Optional[List[str]] = None,
        top_k_memories: int = 5,
        include_social: bool = True,
    ) -> MemoryContext:
        """Get combined memory context for agent planning.

        This is the main entry point for injecting memory context
        into agent decision-making.

        Args:
            agent_id: The planning agent.
            current_situation: Description of current situation.
            encounter_agents: Agents currently encountered.
            top_k_memories: Number of memories to retrieve.
            include_social: Whether to include social context.

        Returns:
            MemoryContext ready for prompt injection.
        """
        start_time = time.perf_counter()
        context = MemoryContext()

        # Retrieve relevant episodic/semantic memories
        memories = await self.retrieve_memories(
            agent_id=agent_id,
            query_text=current_situation,
            top_k=top_k_memories,
            include_related_agents=encounter_agents,
        )
        context.memories = memories
        context.total_hits = len(memories)

        # Get social context if requested and we have encounters
        if include_social and (encounter_agents or self._graph_memory):
            subgraph = await self.get_social_context(
                agent_id=agent_id,
                encounter_agent_ids=encounter_agents,
            )
            if not subgraph.edges:
                context.social_context = None
            else:
                context.social_context = subgraph.to_summary()

        context.query_time_ms = (time.perf_counter() - start_time) * 1000
        return context

    # ========== Lifecycle ==========

    async def close(self) -> None:
        """Close all memory backends."""
        if self._vector_memory:
            await self._vector_memory.close()
        if self._graph_memory:
            await self._graph_memory.close()

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics from all memory backends.

        Returns:
            Combined statistics dictionary.
        """
        stats: Dict[str, Any] = {}

        if self._vector_memory:
            try:
                stats["vector"] = await self._vector_memory.get_stats()
            except Exception as e:
                stats["vector"] = {"error": str(e)}

        if self._graph_memory:
            try:
                stats["graph"] = await self._graph_memory.get_stats()
            except Exception as e:
                stats["graph"] = {"error": str(e)}

        return stats

