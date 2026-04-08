import sqlite3
import json
from pathlib import Path
from typing import Optional, Dict
from pydantic import BaseModel, field_validator

DB_NAME = ".autowiki/state.db"

NAMING_PATTERN = r"^\d{8}_[A-F0-9]{4}_[A-Za-z0-9_-]+\.txt$"

def init_workspace(workspace_dir: str = ".") -> Path:
    """Инициализирует папки базы знаний."""
    workspace_path = Path(workspace_dir).resolve()
    # BUGFIX: parents=True is critical if user passes a deep path
    (workspace_path / "inbox").mkdir(parents=True, exist_ok=True)
    (workspace_path / "wiki").mkdir(parents=True, exist_ok=True)
    (workspace_path / "archive").mkdir(parents=True, exist_ok=True)
    
    StateManager(workspace_path)
    
    readme_path = workspace_path / "README.md"
    if not readme_path.exists():
        readme_path.write_text("# AutoWiki Knowledge Base\nDrop files into `/inbox` and run compilation via your MCP client.")
    return workspace_path

class ConfigManager:
    @staticmethod
    def get_config() -> Optional[Dict]:
        """Ищет .autowiki/state.db начиная с текущей директории и вверх."""
        current_dir = Path.cwd().resolve()
        for parent in [current_dir] + list(current_dir.parents):
            if (parent / DB_NAME).exists():
                return {"root_path": str(parent)}
        return None

class SourceManifest(BaseModel):
    id: str
    filename: str
    hash: str
    trust_weight: float = 1.0

    @field_validator("filename")
    @classmethod
    def validate_iron_standard(cls, v: str) -> str:
        import re
        if not re.match(NAMING_PATTERN, v):
            raise ValueError(f"Filename {v} must match {NAMING_PATTERN}")
        return v

class StateManager:
    def __init__(self, workspace_dir: Path):
        self.db_path = workspace_dir / DB_NAME
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    name TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    last_updated TEXT NOT NULL
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL UNIQUE,
                    hash TEXT NOT NULL,
                    trust_weight REAL DEFAULT 1.0,
                    commit_timestamp TEXT NOT NULL
                )
            """)

    def file_exists_in_wiki(self, entity_name: str) -> bool:
        cur = self.conn.execute("SELECT 1 FROM entities WHERE name = ?", (entity_name,))
        return cur.fetchone() is not None

    def upsert_entity(self, entity_name: str, file_path: str):
        import datetime
        now = datetime.datetime.now().isoformat()
        with self.conn:
            self.conn.execute("""
                INSERT INTO entities (name, file_path, last_updated)
                VALUES (?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    file_path = excluded.file_path,
                    last_updated = excluded.last_updated
            """, (entity_name, file_path, now))

    def save_source(self, manifest: dict):
        import datetime
        now = datetime.datetime.now().isoformat()
        with self.conn:
            self.conn.execute("""
                INSERT OR IGNORE INTO sources (id, filename, hash, trust_weight, commit_timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (manifest["id"], manifest["filename"], manifest["hash"], manifest.get("trust_weight", 1.0), now))

    def find_entity_file(self, entity_name: str) -> Optional[str]:
        cur = self.conn.execute("SELECT file_path FROM entities WHERE name = ?", (entity_name,))
        row = cur.fetchone()
        return row["file_path"] if row else None
