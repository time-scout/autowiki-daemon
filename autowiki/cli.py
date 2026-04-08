import typer
from pathlib import Path
from rich.console import Console

from autowiki.core.db import StateManager, init_workspace
from autowiki.mcp.server import start_mcp_server

app = typer.Typer()
console = Console()

@app.command()
def init(workspace: str = "."):
    """
    Инициализирует структуру AutoWiki в указанной директории.
    """
    workspace_path = init_workspace(workspace)
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
