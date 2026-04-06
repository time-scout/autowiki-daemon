import uuid
import hashlib
import shutil
from pathlib import Path
from git import Repo

from autowiki.core.db import StateManager, SourceManifest

class MarkdownCompiler:
    """
    Модуль 3: Компилятор Markdown и Git-менеджер.
    Набор чистых функций, вызываемых из MCP.
    (Реализация ADR-01, ADR-02, ADR-05)
    """
    def __init__(self, workspace_dir: Path, state_manager: StateManager):
        self.workspace_dir = workspace_dir
        self.wiki_dir = workspace_dir / "wiki"
        self.inbox_dir = workspace_dir / "inbox"
        self.archive_dir = workspace_dir / "archive"
        self.archive_dir.mkdir(exist_ok=True)
        self.state_manager = state_manager
        
        try:
            self.repo = Repo(self.workspace_dir)
        except:
            self.repo = Repo.init(self.workspace_dir)

    def process_updates(self, payload: dict) -> str:
        """
        Основной метод применения изменений (ADR-01, ADR-02, ADR-05).
        Выполняется синхронно, исключая гонки.
        """
        source_meta = payload.get("source_metadata", {})
        filename = source_meta.get("filename")
        trust_weight = float(source_meta.get("trust_weight", 1.0))
        
        if not filename:
            raise ValueError("Missing 'filename' in source_metadata")
            
        inbox_file = self.inbox_dir / filename
        if not inbox_file.exists():
            raise FileNotFoundError(f"File {filename} not found in /inbox")
            
        # 1. Register Source
        raw_text = inbox_file.read_text()
        source_id = f"src_{uuid.uuid4().hex[:8]}"
        file_hash = hashlib.sha256(raw_text.encode()).hexdigest()
        
        self.state_manager.register_source(SourceManifest(
            id=source_id,
            filename=filename,
            hash=file_hash,
            trust_weight=trust_weight
        ))
        
        updates = payload.get("updates", [])
        entities_processed = []

        # 2. Process each entity update
        # Group updates by entity
        updates_by_entity = {}
        for update in updates:
            ent = update.get("entity")
            if not ent: continue
            if ent not in updates_by_entity:
                updates_by_entity[ent] = []
            updates_by_entity[ent].append(update)
            
        for entity_name, entity_updates in updates_by_entity.items():
            target_file = self.state_manager.find_entity_file(entity_name)
            if not target_file:
                safe_name = entity_name.replace(" ", "_")
                target_file = f"wiki/{safe_name}.md"
                self.state_manager.add_entity(entity_name, target_file)
                
            target_path = self.workspace_dir / target_file
            
            # Render Markdown with provenance tags
            final_markdown = self._render_markdown(entity_name, entity_updates, source_id)
            target_path.write_text(final_markdown)
            entities_processed.append(entity_name)
            
        # 3. Archive the raw file to prevent reprocessing
        shutil.move(str(inbox_file), str(self.archive_dir / filename))
        
        # 4. Git Commit (Audit Trail)
        self._git_commit(f"AutoWiki: Update via MCP from {filename}")
        
        return f"Successfully processed {len(entities_processed)} entities from {filename}."

    def _render_markdown(self, entity_name: str, updates: list[dict], new_source_id: str) -> str:
        """Сборка Markdown с гарантированными тегами provenance."""
        lines = [f"# {entity_name}\n"]
        
        for up in updates:
            status = up.get("status")
            text = up.get("text")
            sources = up.get("sources", [])
            
            if status in ["UPDATE", "NEW"]:
                if new_source_id not in sources:
                    sources.append(new_source_id)
                    
            if status == 'CONFLICT':
                lines.append("> [!WARNING] CONFLICT DETECTED")
                lines.append(f"> {text} ^[{new_source_id}]")
                lines.append("> #NEEDS_HUMAN_RESOLUTION\n")
            else:
                sources_str = " ".join([f"^[{s}]" for s in sources if s])
                lines.append(f"{text} {sources_str}\n")
                
        return "\n".join(lines)

    def _git_commit(self, message: str):
        self.repo.git.add(A=True)
        if self.repo.is_dirty():
            self.repo.index.commit(message)
