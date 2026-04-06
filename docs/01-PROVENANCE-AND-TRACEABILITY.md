# Architectural Decision Record 01: Provenance & Traceability

## The Problem (The "Black Box" Knowledge)
In a naive LLM-Wiki, when an agent reads `raw/source.pdf` and updates `wiki/Concept.md`, the connection between the extracted fact and its origin is lost. This creates several unresolvable issues down the line:
1.  **Verification Impossibility:** A human cannot easily check if the LLM hallucinated a fact without re-reading the entire source document.
2.  **Orphaned Facts on Source Deletion/Update:** If `source.pdf` is found to be false and deleted, the agent has no systemic way to find and purge *only* the facts derived from it without accidentally deleting manually verified data.
3.  **Conflict Resolution Blindness:** When Source A says "X=True" and Source B says "X=False", the system cannot programmatically weigh them if it doesn't know *which* text block came from *which* source.

## Proposed Solution: Block-Level Citation Syntax & Source Manifest

To build a self-compiling knowledge base that can heal itself, we must introduce a **mandatory, machine-readable citation syntax** at the paragraph/block level, coupled with a central registry of ingested sources.

### Part 1: The Source Manifest (`schema/sources.json` or YAML)
Before any source is ingested into the Wiki, it must be registered with a unique ID and critical metadata.

```json
{
  "src_uuid_12345": {
    "filename": "raw/2024_api_docs.pdf",
    "ingestion_date": "2024-10-26T10:00:00Z",
    "publication_date": "2024-01-01",
    "author_or_origin": "Acme Corp",
    "trust_weight": 0.9, // Configurable weight for conflict resolution later
    "hash": "a1b2c3d4..." // File hash to detect if raw source changed
  }
}
```

### Part 2: Markdown Block-Level Citations (`^[src_id]`)
We enforce a strict rule for the LLM: **Every informational paragraph or list item generated in the `wiki/` directory MUST end with a machine-readable citation.**

We can use the standard Markdown footnote syntax or a custom inline syntax. A clean approach for agents and humans is: `^[src_id]`.

**Example `wiki/Python_Asyncio.md`:**
```markdown
# Asyncio in Python

Asyncio is a library to write concurrent code using the async/await syntax. It is used as a foundation for multiple Python asynchronous frameworks. ^[src_uuid_12345]

## Event Loop
The event loop is the core of every asyncio application. Event loops run asynchronous tasks and callbacks, perform network IO operations, and run subprocesses. ^[src_uuid_12345] ^[src_uuid_67890]
```

*Note: If a paragraph is a synthesis of two sources, both IDs are appended.*

### Part 3: The "Linting" Enforcement (The Hook)
We cannot just ask the LLM nicely to do this; it will forget. We need a programmatic safety net.
When the LLM attempts to save a file to the `wiki/` folder, a script (or the MCP server itself) runs a validation check:
1.  **Regex Check:** Does every non-heading block end with `\^\[src_[a-zA-Z0-9_]+\]`?
2.  **ID Validation:** Do the cited IDs exist in the Source Manifest?
3.  **Rejection:** If the validation fails, the save is rejected, and the LLM receives an error prompt: *"Error: Missing or invalid provenance citation in paragraph 2. You must cite your source."*

## Why This Solves The First Bottleneck

By forcing the LLM to write `^[src_id]` at the end of every synthesized thought:
*   **Foundation for Conflict Resolution (Next Step):** If the LLM tries to update the "Event Loop" paragraph with contradicting data from `src_new_999`, it (or an orchestrator script) can see that the existing text came from `src_uuid_12345`. It can compare the `publication_date` and `trust_weight` of both sources in the manifest before deciding to overwrite, append, or flag a conflict.
*   **Surgical Deletion:** If `src_uuid_12345` is deprecated, a simple script can `grep` for `\^\[src_uuid_12345\]` across the entire wiki and instruct the LLM: *"Rewrite these specific paragraphs, removing the influence of source 12345."*

---
**Status:** Proposed
**Next Sequence:** How to handle Contradictions and Truth Verification (ADR-02), relying on this Provenance system.
