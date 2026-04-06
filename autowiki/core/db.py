import sqlite3
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

DB_NAME = ".autowiki/state.db"

class SourceManifest(BaseModel):
    id: str
    filename: str
    hash: str
    trust_weight: float = 1.0

class StateManager:
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.db_path = workspace_dir / DB_NAME
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
