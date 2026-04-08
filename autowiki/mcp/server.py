from mcp.server.fastmcp import FastMCP
from autowiki.core.db import StateManager, ConfigManager, SourceManifest
from autowiki.core.compiler import MarkdownCompiler
from pathlib import Path
import json
import os
import hashlib
import re
from datetime import datetime

# Initialize MCP Server
mcp = FastMCP("AutoWiki MCP Server")

def get_workspace() -> Path:
    config = ConfigManager.get_config()
    if config and "root_path" in config:
        return Path(config["root_path"])
    return None

# --- PROMPT (The "Soul" of the Server - Enforcing the Iron Standard & Evolution) ---
@mcp.prompt()
def compile_knowledge_base() -> str:
    """The mandatory instruction for any LLM using this server."""
    return """You are a Senior Knowledge Editor. Your mission is to maintain a high-fidelity, traceable knowledge base.

### 🛡️ IRON STANDARD SOURCE PROTOCOL (MANDATORY)
You are FORBIDDEN from committing facts without a verifiable Source Passport in the archive.

1. **EXTERNAL DATA (Web, YouTube, Research):**
   - You MUST create a "Source Passport" file in `/inbox` BEFORE calling commit_updates.
   - **NAMING CONVENTION:** `YYYYMMDD_HASH_SLUG.txt`
     - **PRO TIP:** Use the `format_filename` tool to generate a perfect name automatically.
   - **PASSPORT CONTENT:** Include PRIMARY URL, Metadata, Timestamp, and a RAW TEXT SNIPPET.

### 🧠 KNOWLEDGE EVOLUTION PROTOCOL
We do not delete. We accumulate and document change.

1. **NO DELETION:** Never delete old facts. Knowledge is a journey.
2. **CONSENSUS (KEEP/NEW):** 
   - If a new source confirms an existing fact, use `status: "KEEP"` and add the new source to the `sources` list.
3. **EVOLUTION (UPDATE):** 
   - If a fact changes (e.g., Version 1.0 -> 2.0), use `status: "UPDATE"`.
   - Provide the current fact in `text` and the previous version in `old_text`.
4. **CONFLICT (CONFLICT):** 
   - If a new source contradicts an existing one, use `status: "CONFLICT"`.
   - Do NOT choose a winner. Document the contradiction for the human user.
5. **KNOWLEDGE INTEGRITY:**
   - Always call get_entity_knowledge() first to avoid duplicates and understand current state."""

# --- TOOLS ---

@mcp.tool()
def setup_workspace(path: str) -> str:
    """Initializes workspace folders and config."""
    try:
        p = Path(path).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        StateManager(p)
        ConfigManager.set_workspace(str(p))
        return f"✅ Success! Knowledge base at: {p}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

@mcp.tool()
def format_filename(title: str) -> str:
    """Helper to generate an Iron Standard compliant filename."""
    date_str = datetime.now().strftime("%Y%m%d")
    slug = re.sub(r'[^A-Za-z0-9_-]', '_', title)
    slug = re.sub(r'_+', '_', slug).strip('_')
    hash_val = hashlib.md5(slug.encode()).hexdigest()[:4].upper()
    return f"{date_str}_{hash_val}_{slug}.txt"

@mcp.tool()
def read_inbox() -> str:
    """Scans /inbox/ for files."""
    workspace = get_workspace()
    if not workspace: return "Workspace not configured."
    inbox_dir = workspace / "inbox"
    if not inbox_dir.exists(): inbox_dir.mkdir(parents=True, exist_ok=True)
    files = [f for f in inbox_dir.glob("*") if f.is_file() and not f.name.startswith(".")]
    if not files: return "Inbox is empty."
    result = [{"filename": f.name, "content": f.read_text()[:10000]} for f in files]
    return json.dumps(result, ensure_ascii=False)

@mcp.tool()
def get_entity_knowledge(entity_names: list[str]) -> str:
    """Searches /wiki for current facts."""
    workspace = get_workspace()
    if not workspace: return "Workspace not configured."
    sm = StateManager(workspace)
    results = {name: (workspace / p).read_text() if (p := sm.find_entity_file(name)) and (workspace / p).exists() else "EMPTY_ENTITY" for name in entity_names}
    return json.dumps(results, ensure_ascii=False)

@mcp.tool()
def commit_updates(payload_json: str) -> str:
    """
    Commits updates to Wiki.
    REQUIRED SCHEMA:
    {
      "source_metadata": { "filename": "20260408_A1B2_Topic.txt", "trust_weight": 1.0 },
      "updates": [
        {
          "entity": "Topic Name",
          "status": "KEEP|UPDATE|NEW|CONFLICT",
          "text": "Current fact text",
          "old_text": "Previous text (only for UPDATE)",
          "sources": ["src_existing_123"]
        }
      ]
    }
    """
    workspace = get_workspace()
    if not workspace: return "Workspace not configured."
    sm = StateManager(workspace)
    compiler = MarkdownCompiler(workspace, sm)
    try:
        payload = json.loads(payload_json)
        return compiler.process_updates(payload)
    except Exception as e:
        return f"❌ VALIDATION ERROR: {str(e)}"

def start_mcp_server():
    mcp.run()
