"""Abstract base class for asynchronous database adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class DatabaseAdapter(ABC):
    """Common interface implemented by all database adapters."""

    @abstractmethod
    async def connect(self, config: Dict[str, Any], pool: Optional[Any] = None) -> None:
        """Establish a connection to the underlying data store.

        Args:
            config: Adapter-specific configuration dictionary.
            pool: Optional connection pool or shared resource.
        """
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        """Close any open connections and release resources."""
        raise NotImplementedError

    @abstractmethod
    async def is_connected(self) -> bool:
        """Determine whether the adapter currently holds an active connection.

        Returns:
            True when a connection is active.
        """
        raise NotImplementedError

    @abstractmethod
    async def import_data(self, data: Any) -> None:
        """Import a dataset into the backing store.

        Args:
            data: Adapter-defined data structure.
        """
        raise NotImplementedError

    @abstractmethod
    async def export_data(self, *args: Any, **kwargs: Any) -> Any:
        """Export data from the backing store.

        Returns:
            Adapter-defined data structure.
        """
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> bool:
        """Remove all data from the backing store.

        Returns:
            True when data was cleared successfully.
        """
        raise NotImplementedError

