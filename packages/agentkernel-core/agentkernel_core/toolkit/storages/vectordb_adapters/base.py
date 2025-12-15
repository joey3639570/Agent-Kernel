"""Base class for asynchronous vector database adapters."""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Sequence

from agentkernel_core.toolkit.storages.base import DatabaseAdapter
from agentkernel_core.types.schemas.vectordb import (
    VectorDocument,
    VectorSearchRequest,
    VectorSearchResult,
    VectorStoreInfo,
)


class BaseVectorDBAdapter(DatabaseAdapter):
    """Abstract base class for vector database adapters.

    This class provides a unified interface for vector similarity search
    across different backend implementations (Milvus, Qdrant, etc.).
    """

    @abstractmethod
    async def upsert(
        self,
        documents: Sequence[VectorDocument],
        **kwargs: Any,
    ) -> List[str]:
        """Insert or update vector documents.

        Args:
            documents: Documents to upsert.
            **kwargs: Backend-specific parameters.

        Returns:
            List of successfully processed document IDs.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(
        self,
        ids: Sequence[str],
        **kwargs: Any,
    ) -> bool:
        """Delete documents by ID.

        Args:
            ids: Document IDs to delete.
            **kwargs: Backend-specific parameters.

        Returns:
            True if successful.
        """
        raise NotImplementedError

    @abstractmethod
    async def search(
        self,
        request: VectorSearchRequest,
        **kwargs: Any,
    ) -> List[VectorSearchResult]:
        """Perform similarity search.

        Args:
            request: Search request specification.
            **kwargs: Backend-specific parameters.

        Returns:
            List of search results sorted by similarity.
        """
        raise NotImplementedError

    @abstractmethod
    async def retrieve_by_id(
        self,
        ids: Sequence[str],
        **kwargs: Any,
    ) -> List[VectorDocument]:
        """Retrieve documents by ID.

        Args:
            ids: Document IDs to retrieve.
            **kwargs: Backend-specific parameters.

        Returns:
            List of found documents.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_info(self) -> VectorStoreInfo:
        """Get store status information.

        Returns:
            Store info including document count and vector dimensions.
        """
        raise NotImplementedError

    @abstractmethod
    async def export_data(
        self,
        page_size: int = 1000,
        **kwargs: Any,
    ) -> List[VectorDocument]:
        """Export all documents from the store.

        Args:
            page_size: Documents per page for internal pagination.
            **kwargs: Backend-specific parameters.

        Returns:
            List of all documents.
        """
        raise NotImplementedError

