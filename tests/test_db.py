from autowiki.core.db import StateManager, SourceManifest

def test_db_schema_creation(temp_workspace):
    manager = StateManager(temp_workspace)
    assert (temp_workspace / ".autowiki" / "state.db").exists()

def test_register_and_get_source(temp_workspace):
    manager = StateManager(temp_workspace)
    
    assert manager.get_source_weight("unknown_id") == 0.0
    
    source = SourceManifest(
        id="src_123",
        filename="notes.md",
        hash="abcdef123456",
        trust_weight=1.5
    )
    manager.register_source(source)
    
    assert manager.get_source_weight("src_123") == 1.5

def test_add_and_find_entity(temp_workspace):
    manager = StateManager(temp_workspace)
    
    assert manager.find_entity_file("Python") is None
    
    manager.add_entity("Python", "wiki/Python.md")
    assert manager.find_entity_file("Python") == "wiki/Python.md"
    
    manager.add_entity("Python", "wiki/Python_Language.md")
    assert manager.find_entity_file("Python") == "wiki/Python_Language.md"
