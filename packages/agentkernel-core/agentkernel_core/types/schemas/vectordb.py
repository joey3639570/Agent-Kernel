"""Schemas for vector database documents and operations.

This module provides schemas compatible with the existing agentkernel
vectordb_adapters while adding additional fields for the Memory Layer.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class VectorDocument(BaseModel):
    """Represents a document containing a vector.

    Attributes:
        id: The unique identifier for the document. If None,
            it will be generated automatically upon insertion.
        tick: Current tick when the document is upserted.
        content: The original text content of the document, which is
            the source for vectorization.
        timestamp: The timestamp when the document was added
            to the database, generated automatically upon insertion.
        vector: The vector representation of the document.
            Becomes optional as it can be generated from content.
        metadata: Additional metadata for storing extra information.
        agent_id: Optional agent ID that owns this document.
        doc_type: Optional document type for filtering.
    """

    id: Optional[str] = None
    tick: int = 0
    content: str
    timestamp: Optional[float] = None
    vector: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None
    agent_id: Optional[str] = None
    doc_type: Optional[str] = None


class VectorSearchRequest(BaseModel):
    """Encapsulates a vector similarity search request.

    Attributes:
        query: The vector or text to use for the query.
        top_k: The number of most similar results to return.
        filter: A Milvus-compatible filter expression string
            (e.g., 'genre == "sci-fi" and year > 2020').
        agent_id: Optional agent ID filter.
        doc_type: Optional document type filter.
        min_score: Minimum similarity score threshold.
    """

    query: Union[str, List[float]]
    top_k: int = Field(default=10, ge=1, le=100)
    filter: Optional[str] = None
    agent_id: Optional[str] = None
    doc_type: Optional[str] = None
    min_score: Optional[float] = None


class VectorSearchResult(BaseModel):
    """Represents a single hit from a vector search.

    Attributes:
        document: The matching vector document.
        score: The similarity or distance score. A higher score
            typically indicates greater similarity, depending on the
            implementation.
    """

    document: VectorDocument
    score: float


class VectorStoreInfo(BaseModel):
    """Describes the status information of the vector store.

    Attributes:
        doc_count: The total number of documents in the store.
        vector_dim: The dimension of the vectors stored.
        backend: The name of the backend (e.g., 'milvus', 'qdrant').
        collection_name: The name of the collection/index.
        metric_type: The distance metric used (e.g., 'cosine', 'l2').
    """

    doc_count: int
    vector_dim: int
    backend: str = "unknown"
    collection_name: str = "default"
    metric_type: str = "cosine"


class VectorDBConfig(BaseModel):
    """Configuration for vector database connection.

    Attributes:
        backend: The backend type ('milvus' or 'qdrant').
        host: Database host address.
        port: Database port.
        collection_name: Name of the collection to use.
        vector_dim: Dimension of vectors to store.
        metric_type: Distance metric ('cosine', 'l2', 'ip').
        api_key: Optional API key for cloud services.
        extra_params: Additional backend-specific parameters.
    """

    backend: str = "qdrant"
    host: str = "localhost"
    port: int = 6333
    collection_name: str = "agentkernel_memories"
    vector_dim: int = 1536
    metric_type: str = "cosine"
    api_key: Optional[str] = None
    extra_params: Dict[str, Any] = Field(default_factory=dict)

