"""Storage adapters for Agent-Kernel Core.

This module provides pluggable storage backends for:
- Vector databases (Milvus, Qdrant)
- Graph databases (Neo4j, NetworkX)
"""

from agentkernel_core.toolkit.storages.base import DatabaseAdapter

__all__ = ["DatabaseAdapter"]

