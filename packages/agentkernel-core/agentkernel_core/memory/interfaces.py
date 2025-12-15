"""Abstract interfaces for memory systems.

This module defines the abstract base classes for:
- MemoryModule: Vector-based memory storage and retrieval (RAG)
- GraphMemoryModule: Graph-based social relationship memory
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from agentkernel_core.types.schemas.memory import (
    MemoryContext,
    MemoryHit,
    MemoryQuery,
    MemoryRecord,
)
from agentkernel_core.types.schemas.graph import (
    GraphNode,
    RelationEdge,
    RelationType,
    SocialSubgraph,
)


class MemoryModule(ABC):
    """Abstract base class for vector-based memory storage and retrieval.

    This interface provides the foundation for RAG (Retrieval-Augmented Generation)
    memory systems, supporting embedding-based similarity search.
    """

    @abstractmethod
    async def store(
        self,
        record: MemoryRecord,
        generate_embedding: bool = True,
    ) -> str:
        """Store a memory record.

        Args:
            record: The memory record to store.
            generate_embedding: Whether to generate embedding from content.

        Returns:
            The ID of the stored record.
        """

    @abstractmethod
    async def store_batch(
        self,
        records: List[MemoryRecord],
        generate_embeddings: bool = True,
    ) -> List[str]:
        """Store multiple memory records in batch.

        Args:
            records: List of memory records to store.
            generate_embeddings: Whether to generate embeddings.

        Returns:
            List of stored record IDs.
        """

    @abstractmethod
    async def retrieve(
        self,
        query: MemoryQuery,
    ) -> List[MemoryHit]:
        """Retrieve memories matching a query.

        Args:
            query: The query specification.

        Returns:
            List of memory hits sorted by relevance.
        """

    @abstractmethod
    async def get_by_id(self, memory_id: str) -> Optional[MemoryRecord]:
        """Retrieve a specific memory by ID.

        Args:
            memory_id: The ID of the memory to retrieve.

        Returns:
            The memory record if found, None otherwise.
        """

    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """Delete a memory record.

        Args:
            memory_id: The ID of the memory to delete.

        Returns:
            True if deleted successfully.
        """

    @abstractmethod
    async def update(
        self,
        memory_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """Update a memory record.

        Args:
            memory_id: The ID of the memory to update.
            updates: Dictionary of fields to update.

        Returns:
            True if updated successfully.
        """

    @abstractmethod
    async def get_agent_memories(
        self,
        agent_id: str,
        limit: int = 100,
    ) -> List[MemoryRecord]:
        """Get all memories for a specific agent.

        Args:
            agent_id: The agent ID.
            limit: Maximum number of memories to return.

        Returns:
            List of memory records.
        """

    @abstractmethod
    async def clear_agent_memories(self, agent_id: str) -> int:
        """Clear all memories for an agent.

        Args:
            agent_id: The agent ID.

        Returns:
            Number of memories deleted.
        """

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the memory store.

        Returns:
            Dictionary containing store statistics.
        """

    @abstractmethod
    async def close(self) -> None:
        """Close connections and release resources."""


class GraphMemoryModule(ABC):
    """Abstract base class for graph-based social relationship memory.

    This interface provides the foundation for tracking and querying
    social relationships between agents.
    """

    @abstractmethod
    async def add_agent(
        self,
        agent_id: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Add an agent node to the graph.

        Args:
            agent_id: The agent's unique identifier.
            properties: Optional properties for the node.

        Returns:
            True if added successfully.
        """

    @abstractmethod
    async def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent and all their relationships.

        Args:
            agent_id: The agent to remove.

        Returns:
            True if removed successfully.
        """

    @abstractmethod
    async def update_agent(
        self,
        agent_id: str,
        properties: Dict[str, Any],
    ) -> bool:
        """Update an agent's properties.

        Args:
            agent_id: The agent to update.
            properties: New properties to set.

        Returns:
            True if updated successfully.
        """

    @abstractmethod
    async def get_agent(self, agent_id: str) -> Optional[GraphNode]:
        """Get an agent's node data.

        Args:
            agent_id: The agent to retrieve.

        Returns:
            GraphNode if found, None otherwise.
        """

    @abstractmethod
    async def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        weight: float = 0.0,
        properties: Optional[Dict[str, Any]] = None,
        bidirectional: bool = True,
    ) -> bool:
        """Add or update a relationship between agents.

        Args:
            source_id: Source agent ID.
            target_id: Target agent ID.
            relation_type: Type of relationship.
            weight: Relationship strength (-1.0 to 1.0).
            properties: Additional edge properties.
            bidirectional: Whether to create reverse edge.

        Returns:
            True if added successfully.
        """

    @abstractmethod
    async def remove_relation(
        self,
        source_id: str,
        target_id: str,
        bidirectional: bool = True,
    ) -> bool:
        """Remove a relationship between agents.

        Args:
            source_id: Source agent ID.
            target_id: Target agent ID.
            bidirectional: Whether to remove reverse edge.

        Returns:
            True if removed successfully.
        """

    @abstractmethod
    async def get_relation(
        self,
        source_id: str,
        target_id: str,
    ) -> Optional[RelationEdge]:
        """Get relationship data between two agents.

        Args:
            source_id: Source agent ID.
            target_id: Target agent ID.

        Returns:
            RelationEdge if found, None otherwise.
        """

    @abstractmethod
    async def record_interaction(
        self,
        source_id: str,
        target_id: str,
        sentiment: float = 0.0,
        context: Optional[str] = None,
    ) -> bool:
        """Record an interaction between agents.

        This updates the relationship weight based on interaction sentiment.

        Args:
            source_id: Source agent ID.
            target_id: Target agent ID.
            sentiment: Interaction sentiment (-1.0 to 1.0).
            context: Optional description of the interaction.

        Returns:
            True if recorded successfully.
        """

    @abstractmethod
    async def get_social_subgraph(
        self,
        agent_id: str,
        depth: int = 1,
        min_weight: Optional[float] = None,
        relation_types: Optional[List[RelationType]] = None,
    ) -> SocialSubgraph:
        """Get the social subgraph centered on an agent.

        Args:
            agent_id: The center agent.
            depth: How many hops to traverse.
            min_weight: Minimum relationship weight to include.
            relation_types: Filter by relationship types.

        Returns:
            SocialSubgraph containing relevant nodes and edges.
        """

    @abstractmethod
    async def get_relations_for_agent(
        self,
        agent_id: str,
        direction: str = "both",  # "in", "out", "both"
    ) -> List[RelationEdge]:
        """Get all relationships for an agent.

        Args:
            agent_id: The agent to query.
            direction: Edge direction to include.

        Returns:
            List of relationship edges.
        """

    @abstractmethod
    async def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5,
    ) -> Optional[List[str]]:
        """Find shortest path between two agents.

        Args:
            source_id: Starting agent.
            target_id: Target agent.
            max_depth: Maximum path length.

        Returns:
            List of agent IDs in the path, or None if no path exists.
        """

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the social graph.

        Returns:
            Dictionary containing graph statistics.
        """

    @abstractmethod
    async def close(self) -> None:
        """Close connections and release resources."""

