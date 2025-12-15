"""Qdrant vector database adapter.

This adapter provides integration with Qdrant for vector similarity search,
suitable for both local development and production deployments.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional, Sequence

from agentkernel_core.toolkit.storages.vectordb_adapters.base import BaseVectorDBAdapter
from agentkernel_core.types.schemas.vectordb import (
    VectorDocument,
    VectorSearchRequest,
    VectorSearchResult,
    VectorStoreInfo,
)

logger = logging.getLogger(__name__)


class QdrantAdapter(BaseVectorDBAdapter):
    """Qdrant vector database adapter.

    Supports both local (in-memory or file-based) and remote Qdrant instances.

    Configuration options:
        - host: Qdrant server host (default: localhost)
        - port: Qdrant server port (default: 6333)
        - collection_name: Collection to use (default: agentkernel)
        - vector_dim: Vector dimensions (default: 1536)
        - metric: Distance metric (cosine, euclid, dot)
        - path: Local storage path (for local mode)
        - in_memory: Use in-memory storage (for testing)
        - api_key: Optional API key for Qdrant Cloud
    """

    def __init__(self) -> None:
        """Initialize the adapter without connection."""
        self._client: Optional[Any] = None
        self._collection_name: str = "agentkernel"
        self._vector_dim: int = 1536
        self._metric: str = "cosine"
        self._config: Dict[str, Any] = {}

    async def connect(
        self,
        config: Dict[str, Any],
        pool: Optional[Any] = None,
    ) -> None:
        """Connect to Qdrant.

        Args:
            config: Connection configuration.
            pool: Ignored for Qdrant.
        """
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
        except ImportError:
            raise ImportError("qdrant-client is required. Install with: pip install qdrant-client")

        self._config = config
        self._collection_name = config.get("collection_name", "agentkernel")
        self._vector_dim = config.get("vector_dim", 1536)
        self._metric = config.get("metric", "cosine")

        # Determine connection mode
        if config.get("in_memory", False):
            self._client = QdrantClient(":memory:")
            logger.info("Connected to Qdrant in-memory mode")
        elif config.get("path"):
            self._client = QdrantClient(path=config["path"])
            logger.info("Connected to Qdrant local storage: %s", config["path"])
        else:
            host = config.get("host", "localhost")
            port = config.get("port", 6333)
            api_key = config.get("api_key")
            
            self._client = QdrantClient(
                host=host,
                port=port,
                api_key=api_key,
            )
            logger.info("Connected to Qdrant at %s:%s", host, port)

        # Ensure collection exists
        await self._ensure_collection()

    async def _ensure_collection(self) -> None:
        """Create collection if it doesn't exist."""
        from qdrant_client.models import Distance, VectorParams

        distance_map = {
            "cosine": Distance.COSINE,
            "euclid": Distance.EUCLID,
            "dot": Distance.DOT,
        }

        collections = self._client.get_collections().collections
        exists = any(c.name == self._collection_name for c in collections)

        if not exists:
            self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=VectorParams(
                    size=self._vector_dim,
                    distance=distance_map.get(self._metric, Distance.COSINE),
                ),
            )
            logger.info("Created collection: %s", self._collection_name)

    async def disconnect(self) -> None:
        """Close the Qdrant connection."""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("Disconnected from Qdrant")

    async def is_connected(self) -> bool:
        """Check if connected to Qdrant."""
        if not self._client:
            return False
        try:
            self._client.get_collections()
            return True
        except Exception:
            return False

    async def upsert(
        self,
        documents: Sequence[VectorDocument],
        **kwargs: Any,
    ) -> List[str]:
        """Upsert documents to Qdrant.

        Args:
            documents: Documents to upsert.
            **kwargs: Additional parameters.

        Returns:
            List of document IDs.
        """
        from qdrant_client.models import PointStruct

        if not self._client:
            raise RuntimeError("Not connected to Qdrant")

        points = []
        ids = []

        for doc in documents:
            if doc.vector is None:
                logger.warning("Skipping document without vector: %s", doc.id)
                continue

            doc_id = doc.id or str(uuid.uuid4())
            ids.append(doc_id)

            payload = {
                "content": doc.content,
                "tick": doc.tick,
                "timestamp": doc.timestamp,
            }
            if doc.metadata:
                payload["metadata"] = doc.metadata
            if doc.agent_id:
                payload["agent_id"] = doc.agent_id
            if doc.doc_type:
                payload["doc_type"] = doc.doc_type

            points.append(
                PointStruct(
                    id=doc_id,
                    vector=doc.vector,
                    payload=payload,
                )
            )

        if points:
            self._client.upsert(
                collection_name=self._collection_name,
                points=points,
            )
            logger.debug("Upserted %d documents to Qdrant", len(points))

        return ids

    async def delete(
        self,
        ids: Sequence[str],
        **kwargs: Any,
    ) -> bool:
        """Delete documents by ID.

        Args:
            ids: Document IDs to delete.
            **kwargs: Additional parameters.

        Returns:
            True if successful.
        """
        from qdrant_client.models import PointIdsList

        if not self._client:
            raise RuntimeError("Not connected to Qdrant")

        self._client.delete(
            collection_name=self._collection_name,
            points_selector=PointIdsList(points=list(ids)),
        )
        logger.debug("Deleted %d documents from Qdrant", len(ids))
        return True

    async def search(
        self,
        request: VectorSearchRequest,
        **kwargs: Any,
    ) -> List[VectorSearchResult]:
        """Search for similar documents.

        Args:
            request: Search request.
            **kwargs: Additional parameters.

        Returns:
            List of search results.
        """
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        if not self._client:
            raise RuntimeError("Not connected to Qdrant")

        # Handle query (vector or text)
        if isinstance(request.query, list):
            query_vector = request.query
        else:
            # Text query requires external embedding
            raise ValueError("Text query requires embedding. Provide query vector instead.")

        # Build filter conditions
        filter_conditions = []
        
        if request.agent_id:
            filter_conditions.append(
                FieldCondition(
                    key="agent_id",
                    match=MatchValue(value=request.agent_id),
                )
            )
        
        if request.doc_type:
            filter_conditions.append(
                FieldCondition(
                    key="doc_type",
                    match=MatchValue(value=request.doc_type),
                )
            )

        query_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Execute search
        results = self._client.search(
            collection_name=self._collection_name,
            query_vector=query_vector,
            limit=request.top_k,
            query_filter=query_filter,
            score_threshold=request.min_score,
        )

        # Convert to VectorSearchResult
        search_results = []
        for hit in results:
            payload = hit.payload or {}
            doc = VectorDocument(
                id=str(hit.id),
                content=payload.get("content", ""),
                tick=payload.get("tick", 0),
                timestamp=payload.get("timestamp"),
                metadata=payload.get("metadata"),
                agent_id=payload.get("agent_id"),
                doc_type=payload.get("doc_type"),
                vector=hit.vector if hasattr(hit, "vector") else None,
            )
            search_results.append(
                VectorSearchResult(document=doc, score=hit.score)
            )

        return search_results

    async def retrieve_by_id(
        self,
        ids: Sequence[str],
        **kwargs: Any,
    ) -> List[VectorDocument]:
        """Retrieve documents by ID.

        Args:
            ids: Document IDs.
            **kwargs: Additional parameters.

        Returns:
            List of documents.
        """
        if not self._client:
            raise RuntimeError("Not connected to Qdrant")

        points = self._client.retrieve(
            collection_name=self._collection_name,
            ids=list(ids),
            with_vectors=True,
        )

        documents = []
        for point in points:
            payload = point.payload or {}
            doc = VectorDocument(
                id=str(point.id),
                content=payload.get("content", ""),
                tick=payload.get("tick", 0),
                timestamp=payload.get("timestamp"),
                metadata=payload.get("metadata"),
                agent_id=payload.get("agent_id"),
                doc_type=payload.get("doc_type"),
                vector=point.vector,
            )
            documents.append(doc)

        return documents

    async def get_info(self) -> VectorStoreInfo:
        """Get collection information.

        Returns:
            Store info.
        """
        if not self._client:
            raise RuntimeError("Not connected to Qdrant")

        info = self._client.get_collection(self._collection_name)

        return VectorStoreInfo(
            doc_count=info.points_count or 0,
            vector_dim=self._vector_dim,
            backend="qdrant",
            collection_name=self._collection_name,
            metric_type=self._metric,
        )

    async def import_data(self, data: Any) -> None:
        """Import data (list of VectorDocuments).

        Args:
            data: List of VectorDocument objects.
        """
        if isinstance(data, list):
            await self.upsert(data)

    async def export_data(
        self,
        page_size: int = 1000,
        **kwargs: Any,
    ) -> List[VectorDocument]:
        """Export all documents.

        Args:
            page_size: Page size for scrolling.
            **kwargs: Additional parameters.

        Returns:
            List of all documents.
        """
        if not self._client:
            raise RuntimeError("Not connected to Qdrant")

        documents = []
        offset = None

        while True:
            points, offset = self._client.scroll(
                collection_name=self._collection_name,
                limit=page_size,
                offset=offset,
                with_vectors=True,
            )

            for point in points:
                payload = point.payload or {}
                doc = VectorDocument(
                    id=str(point.id),
                    content=payload.get("content", ""),
                    tick=payload.get("tick", 0),
                    timestamp=payload.get("timestamp"),
                    metadata=payload.get("metadata"),
                    agent_id=payload.get("agent_id"),
                    doc_type=payload.get("doc_type"),
                    vector=point.vector,
                )
                documents.append(doc)

            if offset is None:
                break

        return documents

    async def clear(self) -> bool:
        """Clear all documents from the collection.

        Returns:
            True if successful.
        """
        if not self._client:
            raise RuntimeError("Not connected to Qdrant")

        # Delete and recreate collection
        self._client.delete_collection(self._collection_name)
        await self._ensure_collection()
        logger.info("Cleared collection: %s", self._collection_name)
        return True

