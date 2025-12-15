"""NetworkX graph adapter for local/in-memory graph storage.

This adapter is ideal for development, testing, and single-node deployments.
For distributed deployments, use the Neo4j adapter instead.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from agentkernel_core.toolkit.storages.graph_adapters.base import BaseGraphAdapter

logger = logging.getLogger(__name__)


class NetworkXAdapter(BaseGraphAdapter):
    """NetworkX-based graph adapter for local storage.

    This adapter uses NetworkX for in-memory graph operations with optional
    persistence to JSON files.

    Configuration options:
        - persist_path: Path to JSON file for persistence (optional)
        - directed: Whether to use directed graph (default: True)
    """

    def __init__(self) -> None:
        """Initialize the adapter without graph."""
        self._graph: Optional[Any] = None
        self._persist_path: Optional[str] = None
        self._directed: bool = True
        self._config: Dict[str, Any] = {}

    async def connect(
        self,
        config: Dict[str, Any],
        pool: Optional[Any] = None,
    ) -> None:
        """Initialize the NetworkX graph.

        Args:
            config: Configuration options.
            pool: Ignored for NetworkX.
        """
        try:
            import networkx as nx
        except ImportError:
            raise ImportError("networkx is required. Install with: pip install networkx")

        self._config = config
        self._persist_path = config.get("persist_path")
        self._directed = config.get("directed", True)

        if self._directed:
            self._graph = nx.DiGraph()
        else:
            self._graph = nx.Graph()

        # Load existing data if persistence path exists
        if self._persist_path:
            await self._load_from_file()

        logger.info("NetworkX graph adapter initialized (directed=%s)", self._directed)

    async def _load_from_file(self) -> None:
        """Load graph data from JSON file."""
        import os

        if not self._persist_path or not os.path.exists(self._persist_path):
            return

        try:
            with open(self._persist_path, "r") as f:
                data = json.load(f)

            for node in data.get("nodes", []):
                self._graph.add_node(node["id"], **node.get("properties", {}))

            for edge in data.get("edges", []):
                self._graph.add_edge(
                    edge["source"],
                    edge["target"],
                    **edge.get("properties", {}),
                )

            logger.info("Loaded graph from %s", self._persist_path)
        except Exception as e:
            logger.warning("Failed to load graph from file: %s", e)

    async def _save_to_file(self) -> None:
        """Save graph data to JSON file."""
        if not self._persist_path or not self._graph:
            return

        try:
            nodes = [
                {"id": node, "properties": dict(self._graph.nodes[node])}
                for node in self._graph.nodes()
            ]

            edges = [
                {
                    "source": u,
                    "target": v,
                    "properties": dict(self._graph.edges[u, v]),
                }
                for u, v in self._graph.edges()
            ]

            data = {"nodes": nodes, "edges": edges}

            with open(self._persist_path, "w") as f:
                json.dump(data, f, indent=2, default=str)

            logger.debug("Saved graph to %s", self._persist_path)
        except Exception as e:
            logger.warning("Failed to save graph to file: %s", e)

    async def disconnect(self) -> None:
        """Save and clear the graph."""
        if self._persist_path:
            await self._save_to_file()
        self._graph = None
        logger.info("NetworkX adapter disconnected")

    async def is_connected(self) -> bool:
        """Check if graph is initialized."""
        return self._graph is not None

    async def create_node(
        self,
        node_id: str,
        properties: Dict[str, Any],
    ) -> bool:
        """Create a node.

        Args:
            node_id: Node identifier.
            properties: Node properties.

        Returns:
            True if created.
        """
        if not self._graph:
            raise RuntimeError("Graph not initialized")

        props = dict(properties)
        props["created_at"] = datetime.now().isoformat()
        props["updated_at"] = props["created_at"]

        self._graph.add_node(node_id, **props)
        logger.debug("Created node: %s", node_id)
        return True

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
            True if updated.
        """
        if not self._graph:
            raise RuntimeError("Graph not initialized")

        if node_id not in self._graph:
            return False

        props = dict(properties)
        props["updated_at"] = datetime.now().isoformat()

        self._graph.nodes[node_id].update(props)
        logger.debug("Updated node: %s", node_id)
        return True

    async def delete_node(self, node_id: str) -> bool:
        """Delete a node and its edges.

        Args:
            node_id: Node identifier.

        Returns:
            True if deleted.
        """
        if not self._graph:
            raise RuntimeError("Graph not initialized")

        if node_id not in self._graph:
            return False

        self._graph.remove_node(node_id)
        logger.debug("Deleted node: %s", node_id)
        return True

    async def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a node's properties.

        Args:
            node_id: Node identifier.

        Returns:
            Node properties or None.
        """
        if not self._graph:
            raise RuntimeError("Graph not initialized")

        if node_id not in self._graph:
            return None

        return dict(self._graph.nodes[node_id])

    async def create_edge(
        self,
        source_id: str,
        target_id: str,
        properties: Dict[str, Any],
    ) -> bool:
        """Create an edge.

        Args:
            source_id: Source node.
            target_id: Target node.
            properties: Edge properties.

        Returns:
            True if created.
        """
        if not self._graph:
            raise RuntimeError("Graph not initialized")

        props = dict(properties)
        props["created_at"] = datetime.now().isoformat()
        props["updated_at"] = props["created_at"]

        self._graph.add_edge(source_id, target_id, **props)
        logger.debug("Created edge: %s -> %s", source_id, target_id)
        return True

    async def update_edge(
        self,
        source_id: str,
        target_id: str,
        properties: Dict[str, Any],
    ) -> bool:
        """Update an edge's properties.

        Args:
            source_id: Source node.
            target_id: Target node.
            properties: Properties to update.

        Returns:
            True if updated.
        """
        if not self._graph:
            raise RuntimeError("Graph not initialized")

        if not self._graph.has_edge(source_id, target_id):
            return False

        props = dict(properties)
        props["updated_at"] = datetime.now().isoformat()

        self._graph.edges[source_id, target_id].update(props)
        logger.debug("Updated edge: %s -> %s", source_id, target_id)
        return True

    async def delete_edge(
        self,
        source_id: str,
        target_id: str,
    ) -> bool:
        """Delete an edge.

        Args:
            source_id: Source node.
            target_id: Target node.

        Returns:
            True if deleted.
        """
        if not self._graph:
            raise RuntimeError("Graph not initialized")

        if not self._graph.has_edge(source_id, target_id):
            return False

        self._graph.remove_edge(source_id, target_id)
        logger.debug("Deleted edge: %s -> %s", source_id, target_id)
        return True

    async def get_edge(
        self,
        source_id: str,
        target_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get an edge's properties.

        Args:
            source_id: Source node.
            target_id: Target node.

        Returns:
            Edge properties or None.
        """
        if not self._graph:
            raise RuntimeError("Graph not initialized")

        if not self._graph.has_edge(source_id, target_id):
            return None

        return dict(self._graph.edges[source_id, target_id])

    async def get_node_out_edges(self, node_id: str) -> List[Dict[str, Any]]:
        """Get outgoing edges for a node.

        Args:
            node_id: Node identifier.

        Returns:
            List of edge dictionaries.
        """
        if not self._graph:
            raise RuntimeError("Graph not initialized")

        if node_id not in self._graph:
            return []

        edges = []
        for _, target in self._graph.out_edges(node_id):
            edge_data = dict(self._graph.edges[node_id, target])
            edge_data["source_id"] = node_id
            edge_data["target_id"] = target
            edges.append(edge_data)

        return edges

    async def get_node_in_edges(self, node_id: str) -> List[Dict[str, Any]]:
        """Get incoming edges for a node.

        Args:
            node_id: Node identifier.

        Returns:
            List of edge dictionaries.
        """
        if not self._graph:
            raise RuntimeError("Graph not initialized")

        if node_id not in self._graph:
            return []

        edges = []
        for source, _ in self._graph.in_edges(node_id):
            edge_data = dict(self._graph.edges[source, node_id])
            edge_data["source_id"] = source
            edge_data["target_id"] = node_id
            edges.append(edge_data)

        return edges

    async def get_total_nodes(self) -> int:
        """Get total node count."""
        if not self._graph:
            return 0
        return self._graph.number_of_nodes()

    async def get_total_edges(self) -> int:
        """Get total edge count."""
        if not self._graph:
            return 0
        return self._graph.number_of_edges()

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
        import networkx as nx

        if not self._graph or node_id not in self._graph:
            return []

        if max_depth == 1:
            if direction == "out":
                return list(self._graph.successors(node_id))
            elif direction == "in":
                return list(self._graph.predecessors(node_id))
            else:
                return list(set(self._graph.successors(node_id)) | set(self._graph.predecessors(node_id)))

        # BFS for multi-hop
        visited = set()
        visited.add(node_id)
        frontier = [node_id]

        for _ in range(max_depth):
            next_frontier = []
            for current in frontier:
                if direction in ("out", "both"):
                    for neighbor in self._graph.successors(current):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            next_frontier.append(neighbor)
                if direction in ("in", "both"):
                    for neighbor in self._graph.predecessors(current):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            next_frontier.append(neighbor)
            frontier = next_frontier

        visited.discard(node_id)
        return list(visited)

    async def find_shortest_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 10,
    ) -> Optional[List[str]]:
        """Find shortest path between nodes.

        Args:
            source_id: Starting node.
            target_id: Target node.
            max_depth: Maximum path length.

        Returns:
            List of node IDs or None.
        """
        import networkx as nx

        if not self._graph:
            return None

        if source_id not in self._graph or target_id not in self._graph:
            return None

        try:
            path = nx.shortest_path(
                self._graph,
                source=source_id,
                target=target_id,
            )
            if len(path) <= max_depth + 1:
                return path
            return None
        except nx.NetworkXNoPath:
            return None

    async def import_data(self, data: Any) -> None:
        """Import graph data.

        Args:
            data: Dictionary with 'nodes' and 'edges' lists.
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary with 'nodes' and 'edges'")

        for node in data.get("nodes", []):
            await self.create_node(node["id"], node.get("properties", {}))

        for edge in data.get("edges", []):
            await self.create_edge(
                edge["source"],
                edge["target"],
                edge.get("properties", {}),
            )

    async def export_data(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Export graph data.

        Returns:
            Dictionary with 'nodes' and 'edges' lists.
        """
        if not self._graph:
            return {"nodes": [], "edges": []}

        nodes = [
            {"id": node, "properties": dict(self._graph.nodes[node])}
            for node in self._graph.nodes()
        ]

        edges = [
            {
                "source": u,
                "target": v,
                "properties": dict(self._graph.edges[u, v]),
            }
            for u, v in self._graph.edges()
        ]

        return {"nodes": nodes, "edges": edges}

    async def clear(self) -> bool:
        """Clear all nodes and edges."""
        if not self._graph:
            return False

        self._graph.clear()
        logger.info("Cleared graph")
        return True

