# AutoWiki Daemon: The Thin State Machine MCP Server

AutoWiki is a deterministic **LLM-Wiki orchestrator** and **Knowledge Base compiler** implemented as a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server. 

Instead of letting an LLM hallucinate file edits, AutoWiki acts as a **reliable intermediary** that enforces data evolution, semantic integrity, and source traceability (provenance).

## 🚀 Key Features

- **Thin State Machine:** The LLM extracts entities and facts, but the **server** decides how to commit them to the Wiki.
- **Source Traceability (Provenance):** Every fact in your Wiki is tagged with its source ID (`^[src_...]`).
- **Conflict Resolution:** Flags logical contradictions between sources and marks them for human review (`#NEEDS_HUMAN_RESOLUTION`).
- **Git-Backed Audit Trail:** Automatically commits every change to a local Git repo for version control and rollbacks.
- **SQLite Backend:** Manages a global index of entities and their source lineage.
- **MCP Native:** Works out-of-the-box with **Claude Desktop**, **Cursor**, and other MCP clients.

## 📁 Architecture

The system operates on three primary directories:
- `/inbox`: Drop your raw data (PDFs, Markdown, text) here.
- `/wiki`: Your compiled, interlinked knowledge base.
- `/archive`: Processed source files are moved here to avoid redundancy.
- `/.autowiki`: Internal SQLite state and configurations.

## 🛠️ Getting Started

### Prerequisites
- Python >= 3.12
- Git

### Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -e .
   ```

### Usage

**1. Initialize the workspace:**
```bash
autowiki init .
```

**2. Start the MCP Server:**
```bash
autowiki start
```

## 📜 Technical Documentation (ADR)
Detailed architectural decisions are available in the `docs/` folder:
- [00: Problem Statement](docs/00-PROBLEM-STATEMENT.md)
- [01: Provenance & Traceability](docs/01-PROVENANCE-AND-TRACEABILITY.md)
- [02: Conflict Resolution](docs/02-CONFLICT-RESOLUTION.md)
- [03: Auto-Sharding](docs/03-AUTO-SHARDING.md)
- [04: Global Index](docs/04-GLOBAL-INDEX.md)
- [05: Concurrency & Control](docs/05-CONCURRENCY-AND-CONTROL.md)

## ⚖️ License
Distributed under the MIT License. See `LICENSE` for more information.
