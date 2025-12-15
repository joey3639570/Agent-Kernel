"""Abstract base class for graph database adapters."""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Dict, List, Optional

from agentkernel_core.toolkit.storages.base import DatabaseAdapter


class BaseGraphAdapter(DatabaseAdapter):
    """Abstract base class for graph database adapters.

    This class provides a unified interface for graph storage and queries
    across different backend implementations (Neo4j, NetworkX, etc.).
    """

    @abstractmethod
    async def create_node(
        self,
        node_id: str,
        properties: Dict[str, Any],
    ) -> bool:
        """Create a node with the given identifier and properties.

        Args:
            node_id: Unique identifier for the node.
            properties: Node properties.

        Returns:
            True if created successfully.
        """

    @abstractmethod
    async def update_node(
        self,
        node_id: str,
        properties: Dict[str, Any],
    ) -> bool:
        """Update a node's properties.

        Args:
            node_id: Node identifier.
            properties: Properties to update.

        Returns:
            True if updated successfully.
        """

    @abstractmethod
    async def delete_node(self, node_id: str) -> bool:
        """Delete a node and all associated edges.

        Args:
            node_id: Node identifier.

        Returns:
            True if deleted successfully.
        """

    @abstractmethod
    async def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a node and its properties.

        Args:
            node_id: Node identifier.

        Returns:
            Node properties or None if not found.
        """

    @abstractmethod
    async def create_edge(
        self,
        source_id: str,
        target_id: str,
        properties: Dict[str, Any],
    ) -> bool:
        """Create a directed edge between two nodes.

        Args:
            source_id: Source node identifier.
            target_id: Target node identifier.
            properties: Edge properties.

        Returns:
            True if created successfully.
        """

    @abstractmethod
    async def update_edge(
        self,
        source_id: str,
        target_id: str,
        properties: Dict[str, Any],
    ) -> bool:
        """Update an existing edge.

        Args:
            source_id: Source node identifier.
            target_id: Target node identifier.
            properties: Properties to update.

        Returns:
            True if updated successfully.
        """

    @abstractmethod
    async def delete_edge(
        self,
        source_id: str,
        target_id: str,
    ) -> bool:
        """Delete a directed edge.

        Args:
            source_id: Source node identifier.
            target_id: Target node identifier.

        Returns:
            True if deleted successfully.
        """

    @abstractmethod
    async def get_edge(
        self,
        source_id: str,
        target_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get edge properties.

        Args:
            source_id: Source node identifier.
            target_id: Target node identifier.

        Returns:
            Edge properties or None if not found.
        """

    @abstractmethod
    async def get_node_out_edges(self, node_id: str) -> List[Dict[str, Any]]:
        """Get all outgoing edges for a node.

        Args:
            node_id: Node identifier.

        Returns:
            List of edge dictionaries.
        """

    @abstractmethod
    async def get_node_in_edges(self, node_id: str) -> List[Dict[str, Any]]:
        """Get all incoming edges for a node.

        Args:
            node_id: Node identifier.

        Returns:
            List of edge dictionaries.
        """

    @abstractmethod
    async def get_total_nodes(self) -> int:
        """Get total number of nodes.

        Returns:
            Node count.
        """

    @abstractmethod
    async def get_total_edges(self) -> int:
        """Get total number of edges.

        Returns:
            Edge count.
        """

    @abstractmethod
    async def get_neighbors(
        self,
        node_id: str,
        direction: str = "both",
        max_depth: int = 1,
    ) -> List[str]:
        """Get neighbor node IDs.

        Args:
            node_id: Center node.
            direction: "in", "out", or "both".
            max_depth: Traversal depth.

        Returns:
            List of neighbor node IDs.
        """

    @abstractmethod
    async def find_shortest_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 10,
    ) -> Optional[List[str]]:
        """Find shortest path between two nodes.

        Args:
            source_id: Starting node.
            target_id: Target node.
            max_depth: Maximum path length.

        Returns:
            List of node IDs in path, or None if no path exists.
        """

