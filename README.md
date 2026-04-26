![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![MCP](https://img.shields.io/badge/protocol-MCP-orange) ![License](https://img.shields.io/badge/license-MIT-green)

# 🧠 AutoWiki Daemon: The Thin State Machine for LLMs

**Stop letting LLMs hallucinate over your notes.** 

AutoWiki is a deterministic Model Context Protocol (MCP) server that transforms any LLM (Claude, Cursor, Gemini, Windsurf) from a chaotic text-generator into a strict, verifiable **Knowledge Base Compiler**. 

No silent overwrites. No hallucinated facts. Just pure, traceable knowledge evolution.

## 🔥 Why AutoWiki? The Problem with AI Agents
When you ask an AI to update your personal Wiki, it usually fails:
- ❌ **Silent Overwrites:** It deletes old (but vital) facts to make room for new ones.
- ❌ **Hallucinations:** It bridges knowledge gaps by making things up.
- ❌ **Lost Sources:** You have no idea *which* PDF or web search a specific sentence came from.

**AutoWiki fixes this.** It acts as a strict database layer between the LLM and your hard drive. 

## 🛡️ The "Iron Standard" Features
- **Strict Provenance:** The LLM is mathematically forbidden from adding a fact without an attached **Source Passport**. Every line in your Wiki ends with a traceable tag (e.g., `^[src_8F2A]`).
- **Knowledge Evolution Protocol:** We do not delete. If a fact changes, AutoWiki archives the old version inline. If two sources contradict, it flags a `#NEEDS_HUMAN_RESOLUTION` caution block.
- **Git-Backed Audit Trail:** Every semantic update is automatically committed to a local Git repository.
- **MCP Native:** Drop-in integration with Claude Desktop, Cursor, Gemini CLI, Windsurf, Roo Code, and other MCP-compatible clients.

## 🚀 Quickstart (Zero to Wiki in 60 seconds)

### 1. Install the Daemon
```bash
git clone https://github.com/timescrapper/autowiki-daemon.git
cd autowiki-daemon
pip install -e .
```

### 2. Connect to your AI Client
Add this to your Claude Desktop config, Cursor, Gemini CLI, Windsurf, or Roo Code MCP settings:
```json
{
  "mcpServers": {
    "autowiki": {
      "command": "autowiki",
      "args": ["start"]
    }
  }
}
```

### 3. The Magic (Talk to your AI)
Open your AI Client (Claude, Cursor, Gemini CLI, etc.) and type:
> *"Initialize my workspace at ~/Desktop/MyBrain. Then search the web for 'Latest Python 3.13 features' and compile it into the wiki."*

**Watch what happens:**
1. AutoWiki sets up `/inbox`, `/wiki`, and `/archive`.
2. The AI fetches the data, but AutoWiki forces it to write a stamped **Source Passport** into `/inbox` first.
3. AutoWiki compiles the facts into beautifully interlinked Markdown in `/wiki` with robust source citations.

## 📁 Architecture

The system operates on three primary directories:
- `/inbox`: Drop your raw data (text, messy notes) here. The LLM reads from here.
- `/wiki`: Your pristine, compiled, interlinked knowledge base.
- `/archive`: Processed sources are automatically historically preserved here.
- `/.autowiki`: Internal SQLite database mapping the graph of entities.

## 📜 Technical Documentation (ADR)
Detailed architectural decisions are available in the `docs/` folder:
- [00: Problem Statement](docs/00-PROBLEM-STATEMENT.md)
- [01: Provenance & Traceability](docs/01-PROVENANCE-AND-TRACEABILITY.md)
- [02: Conflict Resolution](docs/02-CONFLICT-RESOLUTION.md)
- [03: Concurrency & Control](docs/03-CONCURRENCY-AND-CONTROL.md)

## ⚖️ License
Distributed under the MIT License. See `LICENSE` for more information.