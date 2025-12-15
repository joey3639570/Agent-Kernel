# agentkernel-core

Core abstractions, schemas, and interfaces for the Agent-Kernel framework.

## Overview

This package provides the shared foundation for both `agentkernel-standalone` and `agentkernel-distributed` runtimes:

- **Types & Schemas**: Pydantic models for messages, tools, memory, and graphs
- **Memory Interfaces**: Abstract interfaces for Vector RAG and Social Graph memory systems
- **Tool Abstractions**: Standard tool specification (JSON Schema) and async dispatcher
- **Storage Adapters**: Pluggable backends for Vector DBs (Milvus, Qdrant) and Graph DBs (Neo4j, NetworkX)

## Installation

```bash
pip install agentkernel-core
```

## Structure

```
agentkernel_core/
├── types/
│   └── schemas/
│       ├── message.py      # Multi-modal message schema
│       ├── tool.py         # Tool specification (JSON Schema)
│       ├── memory.py       # Memory record types
│       ├── graph.py        # Graph node/edge schemas
│       └── vectordb.py     # Vector document schemas
├── memory/
│   ├── interfaces.py       # MemoryModule, GraphMemoryModule ABCs
│   ├── manager.py          # High-level MemoryManager
│   └── types.py            # Memory-specific types
├── tools/
│   ├── spec.py             # ToolSpec definition
│   ├── dispatcher.py       # Async tool dispatcher
│   ├── result.py           # ToolResult schema
│   └── sandbox/            # Code interpreter sandboxes
├── toolkit/
│   └── storages/
│       ├── vectordb_adapters/
│       │   ├── base.py
│       │   ├── milvus.py
│       │   └── qdrant.py
│       └── graph_adapters/
│           ├── base.py
│           ├── networkx.py
│           └── neo4j.py
└── plugins/
    ├── tools/
    │   ├── interpreter.py
    │   └── web_search.py
    └── sensors/
        └── vision.py
```

## Usage

```python
from agentkernel_core.types.schemas.message import Message, MessageContent
from agentkernel_core.memory.interfaces import MemoryModule, GraphMemoryModule
from agentkernel_core.tools.spec import ToolSpec
from agentkernel_core.tools.dispatcher import ToolDispatcher
```

## License

Apache 2.0

