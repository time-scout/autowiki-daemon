from mcp.server.fastmcp import FastMCP
from autowiki.core.db import StateManager, ConfigManager, SourceManifest, init_workspace
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

# --- PROMPT ---
@mcp.prompt()
def compile_knowledge_base() -> str:
    """The mandatory instruction for any LLM using this server."""
    if not get_workspace():
        return (
            "AutoWiki is NOT initialized. \n"
            "CRITICAL INSTRUCTION: You MUST call the `check_autowiki_status` tool IMMEDIATELY. "
            "Do NOT attempt to use any other tools (like format_filename or commit_updates) until setup is complete."
        )

    return """You are a Senior Knowledge Editor. Your mission is to maintain a high-fidelity, traceable knowledge base.

### 🛑 CORE RULE #1: INITIALIZATION CHECK (MANDATORY)
BEFORE starting any task, if you are unsure if the workspace is ready, call `check_autowiki_status`.
If the status is NOT_INITIALIZED, you MUST present the returned onboarding question to the user WORD-FOR-WORD and wait for their answer.
Do NOT proceed with the user's task or invent steps until setup is complete.

### 🧠 KNOWLEDGE EXTRACTION & ENTITY DESIGN
You must strike the perfect balance between granularity and interconnectedness. Apply these universal principles:

1. **NO SYNTHETIC UMBRELLA TOPICS:**
   - Never invent arbitrary, generic categories (e.g., "Music History", "Tech Trends", "General Facts") to dump multiple distinct subjects into one file.
   - If an article discusses 5 different software tools, 5 different historical figures, or 5 distinct theorems, create 5 separate entities.

2. **THE "STANDALONE VALUE" RULE (When to create an entity):**
   - Create a new entity ONLY if the subject (person, organization, concept, product, or specific historical event) has standalone significance and could logically be referenced by other future documents.
   - Do NOT create separate entities for hyper-specific events, single statistics, sub-components, or minor actors whose only relevance is inextricably tied to the primary subject (unless they clearly demand their own expansive page). Nest these facts *inside* the primary entity.

3. **MAXIMUM FACT DENSITY, ZERO FLUFF:**
   - Extract ALL hard, verifiable, granular facts: names, exact dates, statistics, definitions, causal relationships, and concrete outcomes.
   - DISCARD authorial fluff, rhetorical formatting, storytelling, analogies, and emotional filler.
   - Write like a dry, high-density encyclopedia (using bullet points, raw facts, structured paragraphs). Do NOT write essays or summaries.

### 🧠 KNOWLEDGE EXTRACTION & ENTITY DESIGN
You must strike the perfect balance between granularity and interconnectedness. Apply these universal principles:

1. **NO SYNTHETIC UMBRELLA TOPICS:**
   - Never invent arbitrary, generic categories (e.g., "Music History", "Tech Trends", "General Facts") to dump multiple distinct subjects into one file.
   - If an article discusses 5 different software tools, 5 different historical figures, or 5 distinct theorems, create 5 separate entities.

2. **THE "STANDALONE VALUE" RULE (When to create an entity):**
   - Create a new entity ONLY if the subject (person, organization, concept, product, or specific historical event) has standalone significance and could logically be referenced by other future documents.
   - Do NOT create separate entities for hyper-specific events, single statistics, sub-components, or minor actors whose only relevance is inextricably tied to the primary subject (unless they clearly demand their own expansive page). Nest these facts *inside* the primary entity.

3. **MAXIMUM FACT DENSITY, ZERO FLUFF:**
   - Extract ALL hard, verifiable, granular facts: names, exact dates, statistics, definitions, causal relationships, and concrete outcomes.
   - DISCARD authorial fluff, rhetorical formatting, storytelling, analogies, and emotional filler.
   - Write like a dry, high-density encyclopedia (using bullet points, raw facts, structured paragraphs). Do NOT write essays or summaries.

### 🧠 KNOWLEDGE MODELING & EXTRACTION (MANDATORY)
Your task is to extract concrete facts, NOT to write narrative summaries.
To build a high-fidelity, high-density knowledge base, apply these rules when deciding what becomes an "Entity" (a separate `.md` file) vs a "Fact" (text inside an entity):

1. **THE INDEPENDENT VALUE RULE (Entity Selection):**
   - Create an Entity ONLY for distinct, concrete subjects that have value independently of the current source document (e.g., people, organizations, specific technologies, historical events, physical locations, defined concepts).
   - NEVER create "Umbrella" or "Summary" entities invented by you to group things together (e.g., DO NOT create "R&B History" to hold 10 different bands; DO NOT create "DevOps Tips" to hold facts about Docker and Kubernetes). Create 10 distinct entities for the bands, or separate entities for Docker and Kubernetes.

2. **THE FACT PLACEMENT RULE (Nesting):**
   - Specific details, dates, statistics, quotes, or sub-components belong *inside* the Entity they describe.
   - Do NOT spin off minor details into their own Entities unless they are significant enough to warrant their own comprehensive page.

3. **MAXIMUM DENSITY, ZERO FLUFF:**
   - Extract ALL verifiable data points: names, dates, metrics, causal relationships, clear definitions. Do NOT lose details.
   - Discard all rhetorical formatting, authorial emotions, and narrative filler. The resulting text for an entity must read like a dense, dry, factual encyclopedia entry.

### 🧠 KNOWLEDGE MODELING & EXTRACTION (MANDATORY)
Your task is to extract concrete facts, NOT to write narrative summaries.
To build a high-fidelity, high-density knowledge base, apply these rules when deciding what becomes an "Entity" (a separate `.md` file) vs a "Fact" (text inside an entity):

1. **THE INDEPENDENT VALUE RULE (Entity Selection):**
   - Create an Entity ONLY for distinct, concrete subjects that have value independently of the current source document (e.g., people, organizations, specific technologies, historical events, physical locations, defined concepts).
   - NEVER create "Umbrella" or "Summary" entities invented by you to group things together (e.g., DO NOT create "R&B History" to hold 10 different bands; DO NOT create "DevOps Tips" to hold facts about Docker and Kubernetes). Create 10 distinct entities for the bands, or separate entities for Docker and Kubernetes.

2. **THE FACT PLACEMENT RULE (Nesting):**
   - Specific details, dates, statistics, quotes, or sub-components belong *inside* the Entity they describe.
   - Do NOT spin off minor details into their own Entities unless they are significant enough to warrant their own comprehensive page.

3. **MAXIMUM DENSITY, ZERO FLUFF:**
   - Extract ALL verifiable data points: names, dates, metrics, causal relationships, clear definitions. Do NOT lose details.
   - Discard all rhetorical formatting, authorial emotions, and narrative filler. The resulting text for an entity must read like a dense, dry, factual encyclopedia entry.

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

# --- ONBOARDING & STATUS TOOLS ---

@mcp.tool()
def check_autowiki_status() -> str:
    """CRITICAL: Always call this first when starting a task. Returns database status."""
    workspace = get_workspace()

    if workspace:
        return f"INITIALIZED (Path: {workspace})"

    return (
        "NOT_INITIALIZED.\n\n"
        "FATAL SYSTEM DIRECTIVE: The user's workspace is missing. You CANNOT perform any knowledge tasks.\n"
        "1. STOP your current plan completely.\n"
        "2. Print the exact text between the dashed lines below word-for-word to the user.\n"
        "3. DO NOT paraphrase. DO NOT ask additional questions. DO NOT guess paths.\n"
        "4. WAIT for the user to type a reply (e.g., '1' or an absolute path).\n"
        "5. Once they reply, pass their answer exactly as-is to the `autowiki_onboarding` tool.\n\n"
        "----------------------------------------\n"
        "**Welcome to AutoWiki! 📚✨**\n\n"
        "I see you're ready to start building your AI-managed knowledge base. "
        "AutoWiki helps you save, organize, and evolve facts automatically, so we never lose context again.\n\n"
        "To get started, I just need to initialize the workspace (creating the `/inbox`, `/wiki`, and `/archive` folders).\n\n"
        "**Where would you like to set this up?**\n\n"
        "1. **Right here** in the current directory (Recommended for project-specific knowledge).\n"
        "2. **Somewhere else** (Please provide the absolute path, e.g., `/Users/name/Documents/MyWiki` or `C:\\MyWiki`).\n\n"
        "*Just tell me your choice (1 or 2), and I'll handle the rest immediately so we can get to work!*\n"
        "----------------------------------------"
    )

@mcp.tool()
def autowiki_onboarding(path_choice: str = "") -> str:
    """
    Continues the AutoWiki initialization process.
    Call this ONLY when you are providing the user's choice for the workspace path.
    'path_choice' can be '1' for current directory, or a specific absolute path.
    """
    # Prevent repeated onboarding calls without args if it's already missing
    if not get_workspace() and not path_choice.strip():
        # Fallback just in case an erratic agent calls this directly instead of check status
        return check_autowiki_status()

    # Perform initialization based on choice
    try:
        target_path = "." if path_choice.strip() in ["1", "here", ""] else path_choice
        rendered_path = Path(target_path).resolve()

        # 1. Create the workspace directories and DB
        workspace_path = init_workspace(str(rendered_path))

        # 2. VITAL: Change the MCP server's current working directory to the new workspace.
        # This ensures ConfigManager.get_config() (which searches up from cwd) finds the new DB instantly
        # for all subsequent tool calls in this session.
        os.chdir(workspace_path)

        return (
            f"✅ Awesome! AutoWiki successfully initialized at `{workspace_path}`.\n"
            f"Please inform the user: 'AutoWiki is set up and ready to go!'\n"
            f"NOTE: All AutoWiki tools are now unlocked. You MUST now proceed with the user's original request seamlessly."
        )
    except Exception as e:
        return f"❌ Oops, there was an error initializing AutoWiki at '{path_choice}': {str(e)}"

# --- NORMAL TOOLS WITH OMNIPRESENT ONBOARDING TRIGGER ---

@mcp.tool()
def format_filename(title: str) -> str:
    """Helper to generate an Iron Standard compliant filename."""
    # We do not block filename generation, it's just strings
    date_str = datetime.now().strftime("%Y%m%d")
    slug = re.sub(r'[^A-Za-z0-9_-]', '_', title)
    slug = re.sub(r'_+', '_', slug).strip('_')
    hash_val = hashlib.md5(slug.encode()).hexdigest()[:4].upper()
    return f"{date_str}_{hash_val}_{slug}.txt"

@mcp.tool()
def read_inbox() -> str:
    """Scans /inbox/ for files."""
    workspace = get_workspace()

    if not workspace:
        return (
            "ERROR: WORKSPACE_NOT_INITIALIZED.\n"
            "You CANNOT read the inbox yet. Stop this task immediately and call `check_autowiki_status` without any further actions."
        )

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

    if not workspace:
        return (
            "ERROR: WORKSPACE_NOT_INITIALIZED.\n"
            "You CANNOT fetch entities yet. Stop this task immediately and call `check_autowiki_status` without any further actions."
        )

    sm = StateManager(workspace)
    results = {name: (workspace / p).read_text() if (p := sm.find_entity_file(name)) and (workspace / p).exists() else "EMPTY_ENTITY" for name in entity_names}
    return json.dumps(results, ensure_ascii=False)

@mcp.tool()
def commit_updates(payload_json: str) -> str:
    """
    Commits updates to Wiki.
    The payload_json MUST follow this EXACT structure:
    {
      "source_metadata": {
        "filename": "YYYYMMDD_HASH_SLUG.txt",  <-- MUST be a file existing in /inbox
        "trust_weight": 1.0                    <-- Optional, float
      },
      "updates": [                             <-- Array of entity updates
        {
          "entity": "Name of Subject/Topic",   <-- MUST be provided
          "status": "NEW" | "KEEP" | "UPDATE" | "CONFLICT",
          "text": "The new or confirmed fact text",
          "old_text": "Previous fact (if UPDATE or CONFLICT)", <-- Optional
          "sources": []                        <-- Array of existing source IDs, optional
        }
      ]
    }
    """
    workspace = get_workspace()

    if not workspace:
        return (
            "ERROR: WORKSPACE_NOT_INITIALIZED.\n"
            "You CANNOT commit updates yet. Stop this task immediately and call `check_autowiki_status` without any further actions."
        )

    sm = StateManager(workspace)
    compiler = MarkdownCompiler(workspace, sm)
    try:
        payload = json.loads(payload_json)
        return compiler.process_updates(payload)
    except Exception as e:
        return f"❌ VALIDATION ERROR: {str(e)}"

def start_mcp_server():
    mcp.run()

if __name__ == "__main__":
    start_mcp_server()
