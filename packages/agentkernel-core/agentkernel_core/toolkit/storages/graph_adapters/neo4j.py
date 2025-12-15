"""Neo4j graph adapter for distributed/enterprise deployments.

This adapter provides integration with Neo4j for production-grade
graph storage and queries.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from agentkernel_core.toolkit.storages.graph_adapters.base import BaseGraphAdapter

logger = logging.getLogger(__name__)


class Neo4jAdapter(BaseGraphAdapter):
    """Neo4j graph database adapter.

    Configuration options:
        - uri: Neo4j connection URI (default: bolt://localhost:7687)
        - user: Database user (default: neo4j)
        - password: Database password
        - database: Database name (default: neo4j)
        - node_label: Label for agent nodes (default: Agent)
        - edge_label: Label for relationships (default: RELATES_TO)
    """

    def __init__(self) -> None:
        """Initialize the adapter without connection."""
        self._driver: Optional[Any] = None
        self._database: str = "neo4j"
        self._node_label: str = "Agent"
        self._edge_label: str = "RELATES_TO"
        self._config: Dict[str, Any] = {}

    async def connect(
        self,
        config: Dict[str, Any],
        pool: Optional[Any] = None,
    ) -> None:
        """Connect to Neo4j.

        Args:
            config: Connection configuration.
            pool: Optional shared driver instance.
        """
        try:
            from neo4j import AsyncGraphDatabase
        except ImportError:
            raise ImportError("neo4j is required. Install with: pip install neo4j")

        self._config = config
        self._database = config.get("database", "neo4j")
        self._node_label = config.get("node_label", "Agent")
        self._edge_label = config.get("edge_label", "RELATES_TO")

        if pool:
            self._driver = pool
        else:
            uri = config.get("uri", "bolt://localhost:7687")
            user = config.get("user", "neo4j")
            password = config.get("password", "")

            self._driver = AsyncGraphDatabase.driver(
                uri,
                auth=(user, password),
            )

        # Verify connection
        async with self._driver.session(database=self._database) as session:
            await session.run("RETURN 1")

        logger.info("Connected to Neo4j at %s", config.get("uri", "bolt://localhost:7687"))

    async def disconnect(self) -> None:
        """Close the Neo4j connection."""
        if self._driver:
            await self._driver.close()
            self._driver = None
            logger.info("Disconnected from Neo4j")

    async def is_connected(self) -> bool:
        """Check if connected to Neo4j."""
        if not self._driver:
            return False
        try:
            async with self._driver.session(database=self._database) as session:
                await session.run("RETURN 1")
            return True
        except Exception:
            return False

    async def create_node(
        self,
        node_id: str,
        properties: Dict[str, Any],
    ) -> bool:
        """Create a node in Neo4j.

        Args:
            node_id: Node identifier.
            properties: Node properties.

        Returns:
            True if created.
        """
        if not self._driver:
            raise RuntimeError("Not connected to Neo4j")

        props = dict(properties)
        props["id"] = node_id
        props["created_at"] = datetime.now().isoformat()
        props["updated_at"] = props["created_at"]

        query = f"""
        MERGE (n:{self._node_label} {{id: $node_id}})
        SET n += $props
        RETURN n
        """

        async with self._driver.session(database=self._database) as session:
            await session.run(query, node_id=node_id, props=props)

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
        if not self._driver:
            raise RuntimeError("Not connected to Neo4j")

        props = dict(properties)
        props["updated_at"] = datetime.now().isoformat()

        query = f"""
        MATCH (n:{self._node_label} {{id: $node_id}})
        SET n += $props
        RETURN n
        """

        async with self._driver.session(database=self._database) as session:
            result = await session.run(query, node_id=node_id, props=props)
            record = await result.single()

        if record:
            logger.debug("Updated node: %s", node_id)
            return True
        return False

    async def delete_node(self, node_id: str) -> bool:
        """Delete a node and its relationships.

        Args:
            node_id: Node identifier.

        Returns:
            True if deleted.
        """
        if not self._driver:
            raise RuntimeError("Not connected to Neo4j")

        query = f"""
        MATCH (n:{self._node_label} {{id: $node_id}})
        DETACH DELETE n
        RETURN count(n) as deleted
        """

        async with self._driver.session(database=self._database) as session:
            result = await session.run(query, node_id=node_id)
            record = await result.single()

        if record and record["deleted"] > 0:
            logger.debug("Deleted node: %s", node_id)
            return True
        return False

    async def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a node's properties.

        Args:
            node_id: Node identifier.

        Returns:
            Node properties or None.
        """
        if not self._driver:
            raise RuntimeError("Not connected to Neo4j")

        query = f"""
        MATCH (n:{self._node_label} {{id: $node_id}})
        RETURN n
        """

        async with self._driver.session(database=self._database) as session:
            result = await session.run(query, node_id=node_id)
            record = await result.single()

        if record:
            return dict(record["n"])
        return None

    async def create_edge(
        self,
        source_id: str,
        target_id: str,
        properties: Dict[str, Any],
    ) -> bool:
        """Create a relationship.

        Args:
            source_id: Source node.
            target_id: Target node.
            properties: Edge properties.

        Returns:
            True if created.
        """
        if not self._driver:
            raise RuntimeError("Not connected to Neo4j")

        props = dict(properties)
        props["created_at"] = datetime.now().isoformat()
        props["updated_at"] = props["created_at"]

        query = f"""
        MATCH (a:{self._node_label} {{id: $source_id}})
        MATCH (b:{self._node_label} {{id: $target_id}})
        MERGE (a)-[r:{self._edge_label}]->(b)
        SET r += $props
        RETURN r
        """

        async with self._driver.session(database=self._database) as session:
            await session.run(query, source_id=source_id, target_id=target_id, props=props)

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
        if not self._driver:
            raise RuntimeError("Not connected to Neo4j")

        props = dict(properties)
        props["updated_at"] = datetime.now().isoformat()

        query = f"""
        MATCH (a:{self._node_label} {{id: $source_id}})-[r:{self._edge_label}]->(b:{self._node_label} {{id: $target_id}})
        SET r += $props
        RETURN r
        """

        async with self._driver.session(database=self._database) as session:
            result = await session.run(query, source_id=source_id, target_id=target_id, props=props)
            record = await result.single()

        if record:
            logger.debug("Updated edge: %s -> %s", source_id, target_id)
            return True
        return False

    async def delete_edge(
        self,
        source_id: str,
        target_id: str,
    ) -> bool:
        """Delete a relationship.

        Args:
            source_id: Source node.
            target_id: Target node.

        Returns:
            True if deleted.
        """
        if not self._driver:
            raise RuntimeError("Not connected to Neo4j")

        query = f"""
        MATCH (a:{self._node_label} {{id: $source_id}})-[r:{self._edge_label}]->(b:{self._node_label} {{id: $target_id}})
        DELETE r
        RETURN count(r) as deleted
        """

        async with self._driver.session(database=self._database) as session:
            result = await session.run(query, source_id=source_id, target_id=target_id)
            record = await result.single()

        if record and record["deleted"] > 0:
            logger.debug("Deleted edge: %s -> %s", source_id, target_id)
            return True
        return False

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
        if not self._driver:
            raise RuntimeError("Not connected to Neo4j")

        query = f"""
        MATCH (a:{self._node_label} {{id: $source_id}})-[r:{self._edge_label}]->(b:{self._node_label} {{id: $target_id}})
        RETURN r
        """

        async with self._driver.session(database=self._database) as session:
            result = await session.run(query, source_id=source_id, target_id=target_id)
            record = await result.single()

        if record:
            return dict(record["r"])
        return None

    async def get_node_out_edges(self, node_id: str) -> List[Dict[str, Any]]:
        """Get outgoing edges.

        Args:
            node_id: Node identifier.

        Returns:
            List of edge dictionaries.
        """
        if not self._driver:
            raise RuntimeError("Not connected to Neo4j")

        query = f"""
        MATCH (a:{self._node_label} {{id: $node_id}})-[r:{self._edge_label}]->(b:{self._node_label})
        RETURN r, b.id as target_id
        """

        async with self._driver.session(database=self._database) as session:
            result = await session.run(query, node_id=node_id)
            records = await result.data()

        edges = []
        for record in records:
            edge_data = dict(record["r"])
            edge_data["source_id"] = node_id
            edge_data["target_id"] = record["target_id"]
            edges.append(edge_data)

        return edges

    async def get_node_in_edges(self, node_id: str) -> List[Dict[str, Any]]:
        """Get incoming edges.

        Args:
            node_id: Node identifier.

        Returns:
            List of edge dictionaries.
        """
        if not self._driver:
            raise RuntimeError("Not connected to Neo4j")

        query = f"""
        MATCH (a:{self._node_label})-[r:{self._edge_label}]->(b:{self._node_label} {{id: $node_id}})
        RETURN r, a.id as source_id
        """

        async with self._driver.session(database=self._database) as session:
            result = await session.run(query, node_id=node_id)
            records = await result.data()

        edges = []
        for record in records:
            edge_data = dict(record["r"])
            edge_data["source_id"] = record["source_id"]
            edge_data["target_id"] = node_id
            edges.append(edge_data)

        return edges

    async def get_total_nodes(self) -> int:
        """Get total node count."""
        if not self._driver:
            return 0

        query = f"MATCH (n:{self._node_label}) RETURN count(n) as count"

        async with self._driver.session(database=self._database) as session:
            result = await session.run(query)
            record = await result.single()

        return record["count"] if record else 0

    async def get_total_edges(self) -> int:
        """Get total edge count."""
        if not self._driver:
            return 0

        query = f"MATCH ()-[r:{self._edge_label}]->() RETURN count(r) as count"

        async with self._driver.session(database=self._database) as session:
            result = await session.run(query)
            record = await result.single()

        return record["count"] if record else 0

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
        if not self._driver:
            return []

        if direction == "out":
            arrow = f"-[:{self._edge_label}*1..{max_depth}]->"
        elif direction == "in":
            arrow = f"<-[:{self._edge_label}*1..{max_depth}]-"
        else:
            arrow = f"-[:{self._edge_label}*1..{max_depth}]-"

        query = f"""
        MATCH (a:{self._node_label} {{id: $node_id}}){arrow}(b:{self._node_label})
        WHERE a <> b
        RETURN DISTINCT b.id as neighbor_id
        """

        async with self._driver.session(database=self._database) as session:
            result = await session.run(query, node_id=node_id)
            records = await result.data()

        return [r["neighbor_id"] for r in records]

    async def find_shortest_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 10,
    ) -> Optional[List[str]]:
        """Find shortest path.

        Args:
            source_id: Starting node.
            target_id: Target node.
            max_depth: Maximum path length.

        Returns:
            List of node IDs or None.
        """
        if not self._driver:
            return None

        query = f"""
        MATCH path = shortestPath(
            (a:{self._node_label} {{id: $source_id}})-[:{self._edge_label}*..{max_depth}]-(b:{self._node_label} {{id: $target_id}})
        )
        RETURN [n IN nodes(path) | n.id] as node_ids
        """

        async with self._driver.session(database=self._database) as session:
            result = await session.run(query, source_id=source_id, target_id=target_id)
            record = await result.single()

        if record:
            return record["node_ids"]
        return None

    async def import_data(self, data: Any) -> None:
        """Import graph data.

        Args:
            data: Dictionary with 'nodes' and 'edges' lists.
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        for node in data.get("nodes", []):
            await self.create_node(node["id"], node.get("properties", {}))

        for edge in data.get("edges", []):
            await self.create_edge(
                edge["source"],
                edge["target"],
                edge.get("properties", {}),
            )

    async def export_data(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Export all graph data.

        Returns:
            Dictionary with 'nodes' and 'edges' lists.
        """
        if not self._driver:
            return {"nodes": [], "edges": []}

        nodes_query = f"MATCH (n:{self._node_label}) RETURN n"
        edges_query = f"""
        MATCH (a:{self._node_label})-[r:{self._edge_label}]->(b:{self._node_label})
        RETURN a.id as source, b.id as target, r
        """

        async with self._driver.session(database=self._database) as session:
            nodes_result = await session.run(nodes_query)
            nodes_data = await nodes_result.data()

            edges_result = await session.run(edges_query)
            edges_data = await edges_result.data()

        nodes = [
            {"id": r["n"]["id"], "properties": dict(r["n"])}
            for r in nodes_data
        ]

        edges = [
            {"source": r["source"], "target": r["target"], "properties": dict(r["r"])}
            for r in edges_data
        ]

        return {"nodes": nodes, "edges": edges}

    async def clear(self) -> bool:
        """Clear all nodes and relationships."""
        if not self._driver:
            return False

        query = f"MATCH (n:{self._node_label}) DETACH DELETE n"

        async with self._driver.session(database=self._database) as session:
            await session.run(query)

        logger.info("Cleared all nodes with label: %s", self._node_label)
        return True

