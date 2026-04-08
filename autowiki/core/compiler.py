import uuid
import hashlib
import shutil
from pathlib import Path
from git import Repo

from autowiki.core.db import StateManager, SourceManifest

class MarkdownCompiler:
    """
    Module 3: Markdown Compiler & Git Manager.
    (Realizing ADR-01, ADR-02, ADR-05 with Evolution Logic)
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
        except Exception as repo_err:
            try:
                self.repo = Repo.init(self.workspace_dir)
            except Exception as init_err:
                # If git is not installed, or other fatal error
                self.repo = None
                print(f"Warning: Git initialization failed. Version control is disabled. Error: {init_err}")

    def process_updates(self, payload: dict) -> str:
        source_meta = payload.get("source_metadata", {})
        filename = source_meta.get("filename")
        trust_weight = float(source_meta.get("trust_weight", 1.0))
        
        if not filename:
            raise ValueError("Missing 'filename' in source_metadata")
            
        inbox_file = self.inbox_dir / filename
        if not inbox_file.exists():
            raise FileNotFoundError(f"File {filename} not found in /inbox")
            
        raw_text = inbox_file.read_text()
        source_id = f"src_{uuid.uuid4().hex[:8]}"
        file_hash = hashlib.sha256(raw_text.encode()).hexdigest()
        
        self.state_manager.save_source(SourceManifest(
            id=source_id,
            filename=filename,
            hash=file_hash,
            trust_weight=trust_weight
        ).model_dump())
        
        updates = payload.get("updates", [])
        entities_processed = []

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
                self.state_manager.upsert_entity(entity_name, target_file)

            target_path = self.workspace_dir / target_file
            final_markdown = self._render_markdown(entity_name, entity_updates, source_id)
            target_path.write_text(final_markdown)
            entities_processed.append(entity_name)

        shutil.move(str(inbox_file), str(self.archive_dir / filename))
        if self.repo:
            self._git_commit(f"AutoWiki: Update via MCP from {filename}")

        return f"Successfully processed {len(entities_processed)} entities from {filename}."

    def _render_markdown(self, entity_name: str, updates: list[dict], new_source_id: str) -> str:
        """Assembles Markdown with provenance and evolution tracking."""
        lines = [f"# {entity_name}\n"]
        
        for up in updates:
            status = up.get("status")
            text = up.get("text")
            old_text = up.get("old_text", "")
            sources = up.get("sources", [])
            
            if status in ["UPDATE", "NEW", "KEEP"]:
                if new_source_id not in sources:
                    sources.append(new_source_id)
            
            sources_str = " ".join([f"^[{s}]" for s in sources if s])

            if status == 'CONFLICT':
                lines.append("> [!CAUTION] KNOWLEDGE CONFLICT")
                lines.append(f"> New evidence from ^[{new_source_id}] contradicts existing record:")
                lines.append(f"> **New Fact:** {text}")
                lines.append("> #NEEDS_HUMAN_RESOLUTION\n")
            elif status == 'UPDATE' and old_text:
                # Evolution tracking: Don't just replace, document the change
                lines.append(f"{text} {sources_str} *(Evolution: previously described as \"{old_text}\")*\n")
            else:
                lines.append(f"{text} {sources_str}\n")
                
        return "\n".join(lines)

    def _git_commit(self, message: str):
        self.repo.git.add(A=True)
        if self.repo.is_dirty():
            self.repo.index.commit(message)
