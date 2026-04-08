import pytest
import shutil
import tempfile
from pathlib import Path
from git import Repo

# Fixture for a temporary workspace with standard folder structure
@pytest.fixture
def temp_workspace():
    temp_dir = tempfile.mkdtemp()
    workspace_path = Path(temp_dir)
    
    # Create the standard autowiki structure
    (workspace_path / "inbox").mkdir()
    (workspace_path / "wiki").mkdir()
    (workspace_path / "archive").mkdir()
    (workspace_path / ".autowiki").mkdir()
    
    # Initialize a git repo for testing git commits
    Repo.init(workspace_path)
    
    yield workspace_path
    
    # Cleanup after test
    shutil.rmtree(temp_dir)
