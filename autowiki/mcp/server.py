from mcp.server.fastmcp import FastMCP
from autowiki.core.db import StateManager
from autowiki.core.compiler import MarkdownCompiler
from pathlib import Path
import json

# Initialize MCP Server (The Thin Server)
mcp = FastMCP("AutoWiki MCP Server")

WORKSPACE_DIR = Path(".").resolve()

# --- PROMPT (System Instruction for the LLM) ---
@mcp.prompt()
def compile_knowledge_base() -> str:
    """Инструкция для оператора базы знаний (LLM)"""
    return """Ты — оператор базы знаний. Твоя задача — инкрементально переносить данные из /inbox в структурированную базу. 
1) Вызови read_inbox(). 
2) Извлеки сущности. 
3) Вызови get_entity_knowledge(), чтобы понять текущий контекст. 
4) Сравни факты логически. 
5) ВСЕГДА используй commit_updates(JSON) для сохранения изменений. 
ЗАПРЕЩАЕТСЯ самостоятельно создавать или редактировать файлы в папке /wiki."""

# --- TOOLS (Actions for the LLM) ---
@mcp.tool()
def read_inbox() -> str:
    """Сканирует папку /inbox/ и возвращает список файлов и их содержимое."""
    inbox_dir = WORKSPACE_DIR / "inbox"
    if not inbox_dir.exists():
        return "Inbox directory does not exist."
        
    files = list(inbox_dir.glob("*"))
    files = [f for f in files if f.is_file() and not f.name.startswith(".")]
    
    if not files:
        return "Inbox is empty."
        
    result = []
    for f in files:
        content = f.read_text()
        if len(content) > 10000:
            content = content[:10000] + "\n...[TRUNCATED]..."
        result.append({"filename": f.name, "content": content})
        
    return json.dumps(result, ensure_ascii=False)

@mcp.tool()
def get_entity_knowledge(entity_names: list[str]) -> str:
    """Для запрошенных сущностей ищет файлы в /wiki и возвращает текущие факты."""
    state_manager = StateManager(WORKSPACE_DIR)
    results = {}
    
    for name in entity_names:
        file_path = state_manager.find_entity_file(name)
        if not file_path:
            results[name] = "EMPTY_ENTITY"
            continue
            
        full_path = WORKSPACE_DIR / file_path
        if full_path.exists():
            content = full_path.read_text()
            results[name] = content
        else:
            results[name] = "EMPTY_ENTITY"
            
    return json.dumps(results, ensure_ascii=False)

@mcp.tool()
def commit_updates(payload_json: str) -> str:
    """
    Принимает JSON с обновлениями и фиксирует их в Wiki.
    Ожидаемая схема (Payload):
    {
      "source_metadata": {"filename": "...", "trust_weight": 1.0},
      "updates": [
        {
          "entity": "Python",
          "status": "KEEP|UPDATE|NEW|CONFLICT",
          "text": "Текст факта",
          "sources": ["src_old_123"]
        }
      ]
    }
    """
    state_manager = StateManager(WORKSPACE_DIR)
    compiler = MarkdownCompiler(WORKSPACE_DIR, state_manager)
    
    try:
        payload = json.loads(payload_json)
        
        if "source_metadata" not in payload or "updates" not in payload:
            return "VALIDATION ERROR: payload must contain 'source_metadata' and 'updates'."
            
        result = compiler.process_updates(payload)
        return result
    except json.JSONDecodeError:
        return "VALIDATION ERROR: Invalid JSON payload."
    except Exception as e:
        return f"ERROR: {str(e)}"

def start_mcp_server():
    """Starts the MCP server via stdio"""
    mcp.run()
