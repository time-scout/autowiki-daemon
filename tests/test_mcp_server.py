import json
from mcp.server.fastmcp import FastMCP
import autowiki.mcp.server as mcp_server
from autowiki.core.db import StateManager
from autowiki.core.compiler import MarkdownCompiler
import pytest

def test_read_inbox(temp_workspace):
    # Set CWD to workspace for MCP to find folders 
    import os
    os.chdir(temp_workspace)
    
    mcp_server.WORKSPACE_DIR = temp_workspace
    # Try empty inbox
    assert "Inbox is empty." in mcp_server.read_inbox()

    # Create test file
    (temp_workspace / "inbox" / "article.md").write_text("Test content for parsing.")

    result = mcp_server.read_inbox()
    data = json.loads(result)
    assert len(data) == 1
    assert data[0]["filename"] == "article.md"
    assert data[0]["content"] == "Test content for parsing."

def test_get_entity_knowledge(temp_workspace):
    import os
    os.chdir(temp_workspace)
    
    mcp_server.WORKSPACE_DIR = temp_workspace
    manager = StateManager(temp_workspace)
    # File doesn't exist
    assert json.loads(mcp_server.get_entity_knowledge(["AI"])) == {"AI": "EMPTY_ENTITY"}

    # Create file
    (temp_workspace / "wiki" / "AI.md").write_text("Facts about AI")
    manager.add_entity("AI", "wiki/AI.md")

    result = json.loads(mcp_server.get_entity_knowledge(["AI", "Unknown"]))
    assert "Facts about AI" in result["AI"]
    assert result["Unknown"] == "EMPTY_ENTITY"

def test_commit_updates(temp_workspace):
    import os
    os.chdir(temp_workspace)
    
    mcp_server.WORKSPACE_DIR = temp_workspace
    mcp_server.WORKSPACE_DIR = temp_workspace
    (temp_workspace / "inbox" / "valid_file.md").write_text("Raw info")
    
    payload = {
        "source_metadata": {"filename": "valid_file.md", "trust_weight": 1.0},
        "updates": [
            {
                "entity": "System",
                "status": "NEW",
                "text": "Valid test.",
                "sources": []
            }
        ]
    }
    
    # Needs to be JSON string
    response = mcp_server.commit_updates(json.dumps(payload))
    assert "Successfully processed 1 entities" in response
    assert not (temp_workspace / "inbox" / "valid_file.md").exists()
    assert (temp_workspace / "archive" / "valid_file.md").exists()
    assert (temp_workspace / "wiki" / "System.md").exists()
