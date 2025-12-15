"""Graph memory implementation using Graph adapters.

This module provides the GraphMemory class that implements the GraphMemoryModule
interface using pluggable graph database adapters (Neo4j, NetworkX, etc.).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from agentkernel_core.memory.interfaces import GraphMemoryModule
from agentkernel_core.toolkit.storages.graph_adapters.base import BaseGraphAdapter
from agentkernel_core.types.schemas.graph import (
    GraphNode,
    RelationEdge,
    RelationType,
    SocialSubgraph,
)

logger = logging.getLogger(__name__)


class GraphMemory(GraphMemoryModule):
    """Graph-based social relationship memory using Graph adapters.

    This class implements the GraphMemoryModule interface by translating
    agent and relationship operations to graph operations on the
    underlying adapter.
    """

    def __init__(self, adapter: BaseGraphAdapter) -> None:
        """Initialize graph memory.

        Args:
            adapter: The graph database adapter to use.
        """
        self._adapter = adapter

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
        props = properties or {}
        props["label"] = props.get("label", agent_id)
        props["node_type"] = "agent"

        return await self._adapter.create_node(agent_id, props)

    async def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent and all their relationships.

        Args:
            agent_id: The agent to remove.

        Returns:
            True if removed successfully.
        """
        return await self._adapter.delete_node(agent_id)

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
        return await self._adapter.update_node(agent_id, properties)

    async def get_agent(self, agent_id: str) -> Optional[GraphNode]:
        """Get an agent's node data.

        Args:
            agent_id: The agent to retrieve.

        Returns:
            GraphNode if found, None otherwise.
        """
        props = await self._adapter.get_node(agent_id)
        if not props:
            return None

        return GraphNode(
            id=agent_id,
            label=props.get("label", agent_id),
            node_type=props.get("node_type", "agent"),
            properties={k: v for k, v in props.items() if k not in ("label", "node_type", "created_at", "updated_at")},
            created_at=datetime.fromisoformat(props["created_at"]) if props.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(props["updated_at"]) if props.get("updated_at") else datetime.now(),
        )

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
        props = properties or {}
        props["relation_type"] = relation_type.value
        props["weight"] = weight
        props["interaction_count"] = 0

        # Create forward edge
        success = await self._adapter.create_edge(source_id, target_id, props)

        # Create reverse edge if bidirectional
        if success and bidirectional:
            await self._adapter.create_edge(target_id, source_id, props)

        return success

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
        success = await self._adapter.delete_edge(source_id, target_id)

        if bidirectional:
            await self._adapter.delete_edge(target_id, source_id)

        return success

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
        props = await self._adapter.get_edge(source_id, target_id)
        if not props:
            return None

        return RelationEdge(
            source_id=source_id,
            target_id=target_id,
            relation_type=RelationType(props.get("relation_type", "neutral")),
            weight=props.get("weight", 0.0),
            bidirectional=True,  # Assume bidirectional
            properties={k: v for k, v in props.items() if k not in ("relation_type", "weight", "interaction_count", "created_at", "updated_at")},
            interaction_count=props.get("interaction_count", 0),
            created_at=datetime.fromisoformat(props["created_at"]) if props.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(props["updated_at"]) if props.get("updated_at") else datetime.now(),
        )

    async def record_interaction(
        self,
        source_id: str,
        target_id: str,
        sentiment: float = 0.0,
        context: Optional[str] = None,
    ) -> bool:
        """Record an interaction between agents.

        Args:
            source_id: Source agent ID.
            target_id: Target agent ID.
            sentiment: Interaction sentiment (-1.0 to 1.0).
            context: Optional description of the interaction.

        Returns:
            True if recorded successfully.
        """
        # Get existing relationship
        edge = await self.get_relation(source_id, target_id)

        if edge:
            # Update existing relationship
            edge.record_interaction(sentiment)
            props = {
                "weight": edge.weight,
                "interaction_count": edge.interaction_count,
                "last_interaction": datetime.now().isoformat(),
            }
            if context:
                props["last_interaction_context"] = context

            await self._adapter.update_edge(source_id, target_id, props)
            await self._adapter.update_edge(target_id, source_id, props)
            return True
        else:
            # Create new relationship based on sentiment
            if sentiment > 0.3:
                rel_type = RelationType.FRIEND
            elif sentiment < -0.3:
                rel_type = RelationType.ENEMY
            else:
                rel_type = RelationType.NEUTRAL

            return await self.add_relation(
                source_id=source_id,
                target_id=target_id,
                relation_type=rel_type,
                weight=sentiment,
                properties={"last_interaction_context": context} if context else None,
                bidirectional=True,
            )

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
        subgraph = SocialSubgraph(center_agent_id=agent_id, depth=depth)

        # Get center node
        center_node = await self.get_agent(agent_id)
        if center_node:
            subgraph.nodes.append(center_node)

        # Get neighbors
        neighbor_ids = await self._adapter.get_neighbors(agent_id, direction="both", max_depth=depth)

        # Get neighbor nodes
        for neighbor_id in neighbor_ids:
            node = await self.get_agent(neighbor_id)
            if node:
                subgraph.nodes.append(node)

        # Get all edges involving these nodes
        all_node_ids = {agent_id} | set(neighbor_ids)
        for node_id in all_node_ids:
            out_edges = await self._adapter.get_node_out_edges(node_id)
            for edge_data in out_edges:
                target_id = edge_data.get("target_id")
                if target_id not in all_node_ids:
                    continue

                weight = edge_data.get("weight", 0.0)
                rel_type_str = edge_data.get("relation_type", "neutral")

                # Apply filters
                if min_weight is not None and abs(weight) < min_weight:
                    continue

                try:
                    rel_type = RelationType(rel_type_str)
                except ValueError:
                    rel_type = RelationType.CUSTOM

                if relation_types and rel_type not in relation_types:
                    continue

                edge = RelationEdge(
                    source_id=node_id,
                    target_id=target_id,
                    relation_type=rel_type,
                    weight=weight,
                    interaction_count=edge_data.get("interaction_count", 0),
                )
                subgraph.edges.append(edge)

        return subgraph

    async def get_relations_for_agent(
        self,
        agent_id: str,
        direction: str = "both",
    ) -> List[RelationEdge]:
        """Get all relationships for an agent.

        Args:
            agent_id: The agent to query.
            direction: Edge direction to include.

        Returns:
            List of relationship edges.
        """
        edges = []

        if direction in ("out", "both"):
            out_edges = await self._adapter.get_node_out_edges(agent_id)
            for edge_data in out_edges:
                rel_type_str = edge_data.get("relation_type", "neutral")
                try:
                    rel_type = RelationType(rel_type_str)
                except ValueError:
                    rel_type = RelationType.CUSTOM

                edge = RelationEdge(
                    source_id=agent_id,
                    target_id=edge_data.get("target_id", ""),
                    relation_type=rel_type,
                    weight=edge_data.get("weight", 0.0),
                    interaction_count=edge_data.get("interaction_count", 0),
                )
                edges.append(edge)

        if direction in ("in", "both"):
            in_edges = await self._adapter.get_node_in_edges(agent_id)
            for edge_data in in_edges:
                rel_type_str = edge_data.get("relation_type", "neutral")
                try:
                    rel_type = RelationType(rel_type_str)
                except ValueError:
                    rel_type = RelationType.CUSTOM

                edge = RelationEdge(
                    source_id=edge_data.get("source_id", ""),
                    target_id=agent_id,
                    relation_type=rel_type,
                    weight=edge_data.get("weight", 0.0),
                    interaction_count=edge_data.get("interaction_count", 0),
                )
                edges.append(edge)

        return edges

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
        return await self._adapter.find_shortest_path(source_id, target_id, max_depth)

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the social graph.

        Returns:
            Dictionary containing graph statistics.
        """
        node_count = await self._adapter.get_total_nodes()
        edge_count = await self._adapter.get_total_edges()

        return {
            "backend": "graph",
            "node_count": node_count,
            "edge_count": edge_count,
        }

    async def close(self) -> None:
        """Close connections and release resources."""
        await self._adapter.disconnect()

