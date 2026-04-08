import json
import pytest
from pathlib import Path
from autowiki.core.db import StateManager
from autowiki.core.compiler import MarkdownCompiler

def test_process_updates_missing_file(temp_workspace):
    manager = StateManager(temp_workspace)
    compiler = MarkdownCompiler(temp_workspace, manager)
    
    payload = {
        "source_metadata": {"filename": "missing.md", "trust_weight": 1.0},
        "updates": []
    }
    
    with pytest.raises(FileNotFoundError):
        compiler.process_updates(payload)

def test_process_updates_success(temp_workspace):
    manager = StateManager(temp_workspace)
    compiler = MarkdownCompiler(temp_workspace, manager)
    
    # Create test file in inbox
    inbox_file = temp_workspace / "inbox" / "hello.md"
    inbox_file.write_text("Hello World Content")
    
    payload = {
        "source_metadata": {
            "filename": "hello.md",
            "trust_weight": 1.0
        },
        "updates": [
            {
                "entity": "Python",
                "status": "NEW",
                "text": "Python is a programming language.",
                "sources": []
            }
        ]
    }
    
    # Process
    result = compiler.process_updates(payload)
    
    assert "Successfully processed 1 entities" in result
    
    # Check if file was moved to archive
    assert not (temp_workspace / "inbox" / "hello.md").exists()
    assert (temp_workspace / "archive" / "hello.md").exists()
    
    # Check if wiki file was created
    wiki_file = temp_workspace / "wiki" / "Python.md"
    assert wiki_file.exists()
    
    # Check wiki file content for correct Markdown and Source tag insertion
    content = wiki_file.read_text()
    assert "# Python" in content
    assert "Python is a programming language." in content
    assert "^[src_" in content  # Source tag should be auto-appended for NEW
    
    # Check Git commit
    from git import Repo
    repo = Repo(temp_workspace)
    assert not repo.is_dirty()
    last_commit_msg = repo.head.commit.message
    assert "hello.md" in last_commit_msg

def test_conflict_rendering(temp_workspace):
    manager = StateManager(temp_workspace)
    compiler = MarkdownCompiler(temp_workspace, manager)
    
    # Let's directly test the render function
    updates = [
        {
            "status": "CONFLICT",
            "text": "Facts contradict each other here.",
            "sources": ["src_A"]
        }
    ]
    
    result = compiler._render_markdown("Contested Entity", updates, "src_B")
    
    assert "# Contested Entity" in result
    assert "> [!WARNING] CONFLICT DETECTED" in result
    assert "Facts contradict each other here. ^[src_B]" in result
    assert "> #NEEDS_HUMAN_RESOLUTION" in result
