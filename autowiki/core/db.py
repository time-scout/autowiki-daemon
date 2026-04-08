import sqlite3
import json
import re
from pathlib import Path
from typing import Optional, Dict
from pydantic import BaseModel, field_validator

DB_NAME = ".autowiki/state.db"
CONFIG_DIR = Path.home() / ".autowiki"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Iron Standard Regex: YYYYMMDD_HASH_SLUG.txt (e.g., 20260408_A1B2_George_Benson.txt)
NAMING_PATTERN = r"^\d{8}_[A-F0-9]{4}_[A-Za-z0-9_-]+\.txt$"

class ConfigManager:
    @staticmethod
    def get_config() -> Optional[Dict]:
        if not CONFIG_FILE.exists():
            return None
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            return None

    @staticmethod
    def set_workspace(path: str):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        config = {"root_path": str(Path(path).expanduser().resolve())}
        CONFIG_FILE.write_text(json.dumps(config, indent=2))
        return config

class SourceManifest(BaseModel):
    id: str
    filename: str
    hash: str
    trust_weight: float = 1.0

    @field_validator("filename")
    @classmethod
    def validate_iron_standard(cls, v: str) -> str:
        if not re.match(NAMING_PATTERN, v):
            raise ValueError(
                f"Invalid filename format: '{v}'. "
                f"Must follow the Iron Standard: YYYYMMDD_HASH_SLUG.txt "
                f"(e.g., 20260408_A1B2_Topic_Name.txt)"
            )
        return v

class StateManager:
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.db_path = workspace_dir / DB_NAME
        
        # Ensure workspace subfolders exist
        (workspace_dir / "inbox").mkdir(parents=True, exist_ok=True)
        (workspace_dir / "wiki").mkdir(parents=True, exist_ok=True)
        (workspace_dir / "archive").mkdir(parents=True, exist_ok=True)
        
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources_manifest (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                hash TEXT NOT NULL,
                trust_weight REAL DEFAULT 1.0,
                ingestion_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entity_graph (
                entity_name TEXT PRIMARY KEY COLLATE NOCASE,
                target_file_path TEXT NOT NULL,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def register_source(self, source: SourceManifest):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO sources_manifest 
            (id, filename, hash, trust_weight)
            VALUES (?, ?, ?, ?)
        """, (source.id, source.filename, source.hash, source.trust_weight))
        self.conn.commit()

    def get_source_weight(self, source_id: str) -> float:
        cursor = self.conn.cursor()
        cursor.execute("SELECT trust_weight FROM sources_manifest WHERE id = ?", (source_id,))
        row = cursor.fetchone()
        return row[0] if row else 0.0

    def add_entity(self, entity_name: str, target_file_path: str):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO entity_graph (entity_name, target_file_path, last_updated)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (entity_name, target_file_path))
        self.conn.commit()

    def find_entity_file(self, entity_name: str) -> Optional[str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT target_file_path FROM entity_graph WHERE entity_name = ?", (entity_name,))
        row = cursor.fetchone()
        return row[0] if row else None

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()
