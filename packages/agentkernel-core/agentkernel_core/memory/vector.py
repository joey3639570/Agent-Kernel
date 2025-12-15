"""Vector memory implementation using VectorDB adapters.

This module provides the VectorMemory class that implements the MemoryModule
interface using pluggable vector database adapters (Qdrant, Milvus, etc.).
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Callable, Coroutine, Dict, List, Optional

from agentkernel_core.memory.interfaces import MemoryModule
from agentkernel_core.toolkit.storages.vectordb_adapters.base import BaseVectorDBAdapter
from agentkernel_core.types.schemas.memory import (
    MemoryHit,
    MemoryQuery,
    MemoryRecord,
    MemoryType,
)
from agentkernel_core.types.schemas.vectordb import (
    VectorDocument,
    VectorSearchRequest,
)

logger = logging.getLogger(__name__)


class VectorMemory(MemoryModule):
    """Vector-based memory storage using VectorDB adapters.

    This class implements the MemoryModule interface by translating
    MemoryRecord operations to VectorDocument operations on the
    underlying adapter.
    """

    def __init__(
        self,
        adapter: BaseVectorDBAdapter,
        embed_fn: Optional[Callable[[str], Coroutine[Any, Any, List[float]]]] = None,
    ) -> None:
        """Initialize vector memory.

        Args:
            adapter: The vector database adapter to use.
            embed_fn: Optional async function to generate embeddings.
        """
        self._adapter = adapter
        self._embed_fn = embed_fn

    def set_embed_fn(
        self,
        fn: Callable[[str], Coroutine[Any, Any, List[float]]],
    ) -> None:
        """Set the embedding function."""
        self._embed_fn = fn

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
        # Generate embedding if needed
        vector = record.vector
        if generate_embedding and vector is None and self._embed_fn:
            try:
                vector = await self._embed_fn(record.content)
            except Exception as e:
                logger.warning("Failed to generate embedding: %s", e)

        # Generate ID if not provided
        doc_id = record.id or str(uuid.uuid4())

        # Convert to VectorDocument
        doc = VectorDocument(
            id=doc_id,
            content=record.content,
            tick=record.tick,
            timestamp=record.timestamp.timestamp() if record.timestamp else None,
            vector=vector,
            agent_id=record.agent_id,
            doc_type=record.memory_type.value,
            metadata={
                "importance": record.importance,
                "related_agents": record.related_agents,
                "related_memories": record.related_memories,
                "access_count": record.access_count,
                **(record.metadata or {}),
            },
        )

        ids = await self._adapter.upsert([doc])
        return ids[0] if ids else doc_id

    async def store_batch(
        self,
        records: List[MemoryRecord],
        generate_embeddings: bool = True,
    ) -> List[str]:
        """Store multiple memory records.

        Args:
            records: List of memory records to store.
            generate_embeddings: Whether to generate embeddings.

        Returns:
            List of stored record IDs.
        """
        docs = []
        for record in records:
            vector = record.vector
            if generate_embeddings and vector is None and self._embed_fn:
                try:
                    vector = await self._embed_fn(record.content)
                except Exception as e:
                    logger.warning("Failed to generate embedding for %s: %s", record.id, e)

            doc_id = record.id or str(uuid.uuid4())
            doc = VectorDocument(
                id=doc_id,
                content=record.content,
                tick=record.tick,
                timestamp=record.timestamp.timestamp() if record.timestamp else None,
                vector=vector,
                agent_id=record.agent_id,
                doc_type=record.memory_type.value,
                metadata={
                    "importance": record.importance,
                    "related_agents": record.related_agents,
                    "related_memories": record.related_memories,
                    **(record.metadata or {}),
                },
            )
            docs.append(doc)

        return await self._adapter.upsert(docs)

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
        # Get query vector
        query_vector = query.query_vector
        if query_vector is None and query.query_text and self._embed_fn:
            try:
                query_vector = await self._embed_fn(query.query_text)
            except Exception as e:
                logger.warning("Failed to generate query embedding: %s", e)
                return []

        if query_vector is None:
            logger.warning("No query vector available for retrieval")
            return []

        # Build search request
        request = VectorSearchRequest(
            query=query_vector,
            top_k=query.top_k,
            agent_id=query.agent_id,
            doc_type=query.memory_types[0].value if query.memory_types else None,
        )

        # Execute search
        results = await self._adapter.search(request)

        # Convert to MemoryHit
        hits = []
        for result in results:
            doc = result.document
            metadata = doc.metadata or {}

            # Filter by importance if specified
            importance = metadata.get("importance", 0.5)
            if importance < query.min_importance:
                continue

            # Filter by related agents if specified
            related_agents = metadata.get("related_agents", [])
            if query.include_related_agents:
                if not any(a in related_agents for a in query.include_related_agents):
                    continue

            record = MemoryRecord(
                id=doc.id,
                agent_id=doc.agent_id or "",
                content=doc.content,
                memory_type=MemoryType(doc.doc_type) if doc.doc_type else MemoryType.EPISODIC,
                tick=doc.tick,
                importance=importance,
                vector=doc.vector,
                related_agents=related_agents,
                related_memories=metadata.get("related_memories", []),
                metadata={k: v for k, v in metadata.items() if k not in ("importance", "related_agents", "related_memories")},
            )

            # Update access statistics
            record.increment_access()

            hits.append(MemoryHit(record=record, score=result.score))

        return hits

    async def get_by_id(self, memory_id: str) -> Optional[MemoryRecord]:
        """Retrieve a specific memory by ID.

        Args:
            memory_id: The ID of the memory to retrieve.

        Returns:
            The memory record if found, None otherwise.
        """
        docs = await self._adapter.retrieve_by_id([memory_id])
        if not docs:
            return None

        doc = docs[0]
        metadata = doc.metadata or {}

        return MemoryRecord(
            id=doc.id,
            agent_id=doc.agent_id or "",
            content=doc.content,
            memory_type=MemoryType(doc.doc_type) if doc.doc_type else MemoryType.EPISODIC,
            tick=doc.tick,
            importance=metadata.get("importance", 0.5),
            vector=doc.vector,
            related_agents=metadata.get("related_agents", []),
            related_memories=metadata.get("related_memories", []),
            metadata={k: v for k, v in metadata.items() if k not in ("importance", "related_agents", "related_memories")},
        )

    async def delete(self, memory_id: str) -> bool:
        """Delete a memory record.

        Args:
            memory_id: The ID of the memory to delete.

        Returns:
            True if deleted successfully.
        """
        return await self._adapter.delete([memory_id])

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
        # Get existing record
        record = await self.get_by_id(memory_id)
        if not record:
            return False

        # Apply updates
        for key, value in updates.items():
            if hasattr(record, key):
                setattr(record, key, value)

        # Re-store
        await self.store(record, generate_embedding=False)
        return True

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
        # This is a simplification - in production you'd want a proper filter
        all_docs = await self._adapter.export_data(page_size=limit)
        records = []

        for doc in all_docs:
            if doc.agent_id == agent_id:
                metadata = doc.metadata or {}
                record = MemoryRecord(
                    id=doc.id,
                    agent_id=doc.agent_id or "",
                    content=doc.content,
                    memory_type=MemoryType(doc.doc_type) if doc.doc_type else MemoryType.EPISODIC,
                    tick=doc.tick,
                    importance=metadata.get("importance", 0.5),
                    vector=doc.vector,
                    related_agents=metadata.get("related_agents", []),
                    related_memories=metadata.get("related_memories", []),
                    metadata={k: v for k, v in metadata.items() if k not in ("importance", "related_agents", "related_memories")},
                )
                records.append(record)
                if len(records) >= limit:
                    break

        return records

    async def clear_agent_memories(self, agent_id: str) -> int:
        """Clear all memories for an agent.

        Args:
            agent_id: The agent ID.

        Returns:
            Number of memories deleted.
        """
        memories = await self.get_agent_memories(agent_id, limit=10000)
        ids = [m.id for m in memories if m.id]
        if ids:
            await self._adapter.delete(ids)
        return len(ids)

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the memory store.

        Returns:
            Dictionary containing store statistics.
        """
        info = await self._adapter.get_info()
        return {
            "backend": "vector",
            "adapter": info.backend,
            "doc_count": info.doc_count,
            "vector_dim": info.vector_dim,
            "collection": info.collection_name,
        }

    async def close(self) -> None:
        """Close connections and release resources."""
        await self._adapter.disconnect()

