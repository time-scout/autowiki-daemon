import typer
from pathlib import Path
from rich.console import Console

from autowiki.core.db import StateManager
from autowiki.mcp.server import start_mcp_server

app = typer.Typer(help="AutoWiki MCP Server: The Thin State Machine")
console = Console()

@app.command()
def init(workspace: str = "."):
    """
    Инициализирует структуру AutoWiki в указанной директории.
    """
    workspace_path = Path(workspace).resolve()
    (workspace_path / "inbox").mkdir(exist_ok=True)
    (workspace_path / "wiki").mkdir(exist_ok=True)
    (workspace_path / "archive").mkdir(exist_ok=True)
    
    StateManager(workspace_path)
    
    readme_path = workspace_path / "README.md"
    if not readme_path.exists():
        readme_path.write_text("# AutoWiki Knowledge Base\nDrop files into `/inbox` and run compilation via your MCP client.")

    console.print(f"[bold green]✓ AutoWiki initialized at {workspace_path}[/bold green]")
    console.print("Directories created: /inbox, /wiki, /archive, /.autowiki")

@app.command()
def start():
    """
    Запускает MCP-сервер AutoWiki (stdio).
    Для подключения из Cursor, Claude Desktop, и др.
    """
    start_mcp_server()

if __name__ == "__main__":
    app()
