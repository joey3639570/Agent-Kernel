"""Graph schema definitions for social graph memory.

This module provides schemas for graph nodes and edges used by the
Social Graph memory system to track agent relationships.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RelationType(str, Enum):
    """Types of relationships between agents.

    Attributes:
        FRIEND: Friendly relationship.
        ENEMY: Hostile relationship.
        NEUTRAL: Neutral/stranger relationship.
        FAMILY: Family relationship.
        COLLEAGUE: Work/task relationship.
        ALLY: Alliance relationship.
        RIVAL: Competitive relationship.
        MENTOR: Mentor-mentee relationship.
        CUSTOM: Custom relationship type.
    """

    FRIEND = "friend"
    ENEMY = "enemy"
    NEUTRAL = "neutral"
    FAMILY = "family"
    COLLEAGUE = "colleague"
    ALLY = "ally"
    RIVAL = "rival"
    MENTOR = "mentor"
    CUSTOM = "custom"


class GraphNode(BaseModel):
    """A node in the social graph representing an agent.

    Attributes:
        id: Unique identifier (typically agent_id).
        label: Display label for the node.
        node_type: Type of node (usually "agent").
        properties: Key-value properties of the node.
        created_at: When the node was created.
        updated_at: When the node was last updated.
    """

    id: str
    label: str
    node_type: str = "agent"
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def update(self, properties: Dict[str, Any]) -> None:
        """Update node properties and timestamp."""
        self.properties.update(properties)
        self.updated_at = datetime.now()


class RelationEdge(BaseModel):
    """An edge in the social graph representing a relationship.

    Attributes:
        source_id: ID of the source agent.
        target_id: ID of the target agent.
        relation_type: Type of the relationship.
        weight: Strength of the relationship (-1.0 to 1.0).
        bidirectional: Whether the relationship is mutual.
        properties: Additional key-value properties.
        created_at: When the relationship was established.
        updated_at: When the relationship was last modified.
        interaction_count: Number of interactions between agents.
        last_interaction: Timestamp of last interaction.
    """

    source_id: str
    target_id: str
    relation_type: RelationType = RelationType.NEUTRAL
    weight: float = Field(default=0.0, ge=-1.0, le=1.0)
    bidirectional: bool = True
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    interaction_count: int = 0
    last_interaction: Optional[datetime] = None

    def record_interaction(self, sentiment: float = 0.0) -> None:
        """Record an interaction and update relationship metrics.

        Args:
            sentiment: Sentiment of the interaction (-1.0 to 1.0).
        """
        self.interaction_count += 1
        self.last_interaction = datetime.now()
        self.updated_at = datetime.now()

        # Gradually adjust weight based on interaction sentiment
        decay = 0.1
        self.weight = (1 - decay) * self.weight + decay * sentiment
        self.weight = max(-1.0, min(1.0, self.weight))

    def is_positive(self) -> bool:
        """Check if this is a positive relationship."""
        return self.weight > 0.2

    def is_negative(self) -> bool:
        """Check if this is a negative relationship."""
        return self.weight < -0.2

    def to_summary(self) -> str:
        """Generate a human-readable summary of the relationship."""
        strength = "strong" if abs(self.weight) > 0.6 else "moderate" if abs(self.weight) > 0.3 else "weak"
        sentiment = "positive" if self.weight > 0 else "negative" if self.weight < 0 else "neutral"
        return f"{self.source_id} has a {strength} {sentiment} {self.relation_type.value} relationship with {self.target_id}"


class SocialSubgraph(BaseModel):
    """A subgraph of social relationships centered on an agent.

    Attributes:
        center_agent_id: The agent at the center of the subgraph.
        nodes: List of nodes in the subgraph.
        edges: List of edges in the subgraph.
        depth: How many hops from center this subgraph covers.
    """

    center_agent_id: str
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[RelationEdge] = Field(default_factory=list)
    depth: int = 1

    def get_direct_relations(self) -> List[RelationEdge]:
        """Get edges directly connected to the center agent."""
        return [
            e
            for e in self.edges
            if e.source_id == self.center_agent_id or e.target_id == self.center_agent_id
        ]

    def get_friends(self) -> List[str]:
        """Get IDs of agents with positive relationships."""
        friends = []
        for edge in self.get_direct_relations():
            if edge.is_positive():
                other_id = edge.target_id if edge.source_id == self.center_agent_id else edge.source_id
                friends.append(other_id)
        return friends

    def get_enemies(self) -> List[str]:
        """Get IDs of agents with negative relationships."""
        enemies = []
        for edge in self.get_direct_relations():
            if edge.is_negative():
                other_id = edge.target_id if edge.source_id == self.center_agent_id else edge.source_id
                enemies.append(other_id)
        return enemies

    def to_summary(self, max_relations: int = 5) -> str:
        """Generate a human-readable summary of the social context.

        Args:
            max_relations: Maximum number of relationships to include.

        Returns:
            Summary text describing the agent's social relationships.
        """
        direct_edges = self.get_direct_relations()
        if not direct_edges:
            return f"{self.center_agent_id} has no known relationships."

        # Sort by absolute weight (strongest first)
        sorted_edges = sorted(direct_edges, key=lambda e: abs(e.weight), reverse=True)[:max_relations]

        summaries = [e.to_summary() for e in sorted_edges]
        return "\n".join(summaries)

