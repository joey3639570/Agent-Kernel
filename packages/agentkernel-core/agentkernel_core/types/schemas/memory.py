"""Memory-related schema definitions.

This module provides schemas for memory records, queries, and search results
used by the Memory Layer for both Vector RAG and Social Graph memory systems.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """Types of memory records.

    Attributes:
        EPISODIC: Event-based memories (what happened).
        SEMANTIC: Fact-based memories (what is known).
        PROCEDURAL: How-to memories (how to do things).
        SOCIAL: Relationship memories (who knows whom).
    """

    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    SOCIAL = "social"


class MemoryRecord(BaseModel):
    """A single memory record that can be stored and retrieved.

    Attributes:
        id: Unique identifier for the memory.
        agent_id: The agent that owns this memory.
        content: The textual content of the memory.
        memory_type: Type classification of the memory.
        tick: Simulation tick when the memory was created.
        timestamp: Wall-clock time when the memory was created.
        importance: Importance score (0.0 to 1.0).
        vector: Optional embedding vector for similarity search.
        metadata: Additional key-value metadata.
        related_agents: List of agent IDs mentioned/involved in this memory.
        related_memories: List of related memory IDs.
        access_count: Number of times this memory has been retrieved.
        last_accessed: Timestamp of last retrieval.
    """

    id: Optional[str] = None
    agent_id: str
    content: str
    memory_type: MemoryType = MemoryType.EPISODIC
    tick: int = 0
    timestamp: datetime = Field(default_factory=datetime.now)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    vector: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    related_agents: List[str] = Field(default_factory=list)
    related_memories: List[str] = Field(default_factory=list)
    access_count: int = 0
    last_accessed: Optional[datetime] = None

    def increment_access(self) -> None:
        """Update access statistics when this memory is retrieved."""
        self.access_count += 1
        self.last_accessed = datetime.now()


class MemoryQuery(BaseModel):
    """Query specification for memory retrieval.

    Attributes:
        query_text: The text query to search for.
        query_vector: Optional pre-computed query vector.
        agent_id: Optional filter by agent ID.
        memory_types: Optional filter by memory types.
        top_k: Maximum number of results to return.
        min_importance: Minimum importance threshold.
        time_range_start: Optional start of time range filter.
        time_range_end: Optional end of time range filter.
        tick_range_start: Optional start of tick range filter.
        tick_range_end: Optional end of tick range filter.
        include_related_agents: List of agent IDs that must be related.
        metadata_filters: Key-value filters on metadata.
        rerank: Whether to apply reranking to results.
    """

    query_text: Optional[str] = None
    query_vector: Optional[List[float]] = None
    agent_id: Optional[str] = None
    memory_types: Optional[List[MemoryType]] = None
    top_k: int = Field(default=10, ge=1, le=100)
    min_importance: float = Field(default=0.0, ge=0.0, le=1.0)
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    tick_range_start: Optional[int] = None
    tick_range_end: Optional[int] = None
    include_related_agents: List[str] = Field(default_factory=list)
    metadata_filters: Dict[str, Any] = Field(default_factory=dict)
    rerank: bool = False


class MemoryHit(BaseModel):
    """A single search result from memory retrieval.

    Attributes:
        record: The matched memory record.
        score: Similarity/relevance score.
        explanation: Optional explanation of why this result matched.
    """

    record: MemoryRecord
    score: float = Field(ge=0.0)
    explanation: Optional[str] = None


class MemoryContext(BaseModel):
    """Aggregated memory context ready for prompt injection.

    This is the output of MemoryManager.retrieve() and can be directly
    used to augment agent prompts with relevant memories.

    Attributes:
        memories: List of memory hits from RAG retrieval.
        social_context: Summary of relevant social relationships.
        total_hits: Total number of hits before truncation.
        query_time_ms: Time taken for the query in milliseconds.
    """

    memories: List[MemoryHit] = Field(default_factory=list)
    social_context: Optional[str] = None
    total_hits: int = 0
    query_time_ms: float = 0.0

    def to_prompt_text(self, max_length: int = 4000) -> str:
        """Convert memory context to text suitable for prompt injection.

        Args:
            max_length: Maximum character length of the output.

        Returns:
            Formatted text containing relevant memories and social context.
        """
        parts = []

        if self.social_context:
            parts.append(f"[Social Context]\n{self.social_context}\n")

        if self.memories:
            parts.append("[Relevant Memories]")
            for i, hit in enumerate(self.memories, 1):
                memory_text = f"{i}. [{hit.record.memory_type.value}] {hit.record.content}"
                if hit.record.related_agents:
                    memory_text += f" (involving: {', '.join(hit.record.related_agents)})"
                parts.append(memory_text)

        result = "\n".join(parts)
        if len(result) > max_length:
            result = result[: max_length - 3] + "..."
        return result

    def is_empty(self) -> bool:
        """Check if the context contains no information."""
        return not self.memories and not self.social_context

