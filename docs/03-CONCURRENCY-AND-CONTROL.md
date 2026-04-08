# Architectural Decision Record 05: Concurrency & The Single Writer Principle

## The Problem (Race Conditions & Mutating State)
If multiple LLM agents (e.g., a "Research Agent" and an "Update Agent"), or an agent and a human, attempt to edit the same Markdown file simultaneously, we face classic race conditions:
1.  **Lost Updates:** Agent A reads `File.md`. Agent B reads `File.md`. Agent A writes changes. Agent B writes its changes (overwriting Agent A's work).
2.  **Rule Bypass:** If a human edits the file manually and forgets to add the `^[src_id]` provenance tags (ADR-01), the semantic integrity of the entire system is broken.

Attempting to build complex Git-style merge-conflict resolution logic *inside* an LLM's prompt is unreliable and mathematically unsafe.

## Proposed Solution: The "Single Writer" Pipeline & Ingestion Queue

To guarantee absolute semantic integrity and prevent race conditions, we must enforce a strict **Single Writer Architecture**. The `wiki/` directory must be treated like a production database, not a shared Google Doc.

### 1. The Ingestion Queue (Event-Driven Architecture)
Instead of agents writing directly to the Wiki, all incoming information (new documents, web clippings, human notes) is placed into a centralized **Ingestion Queue** (e.g., a `raw/inbox/` folder or a simple SQLite table).

### 2. The Master "Compiler" Agent (The Mutex Lock)
There is only **ONE** entity authorized to write to the `wiki/` directory: The Master Compiler Agent (or a single sequential orchestration script).

*   **Sequential Processing:** The Compiler reads one task from the Ingestion Queue at a time.
*   **The Pipeline:** For that single task, it executes the full pipeline:
    1.  Looks up entities in the Global Index (ADR-04).
    2.  Performs Read-and-Compare for conflicts (ADR-02).
    3.  Writes the update with Provenance tags (ADR-01).
    4.  Triggers Auto-Sharding if necessary (ADR-03).
*   **Locking:** While the Compiler is processing an item, the Wiki state is effectively locked. No other process can alter it.

### 3. Human Interaction Protocol (Drafts, Not Direct Edits)
Humans should not edit the `wiki/` files directly if they want the system to remain self-compiling and verifiable. 
If a human wants to add knowledge or correct a mistake:
*   They write a note in a `raw/human_notes/` folder (e.g., `correction_2024.md`).
*   This note is added to the Ingestion Queue.
*   The Master Compiler processes the human's note, treating the human as a highly-weighted source (`trust_weight: 1.0`), and applies the changes following all structural rules (Provenance, Indexing).

### 4. Version Control (Git as an Audit Trail, Not a Collaboration Tool)
While we use Git, we do NOT use it for branching and merging between agents.
*   **Automated Commits:** The Master Compiler commits to the `main` branch after *every* successful task processed from the queue.
*   **Rollback:** Git serves purely as a linear "Time Machine" to roll back the entire Wiki if the Compiler makes a catastrophic error or a malicious source was ingested.

## Why This Solves The Bottleneck
*   **Zero Race Conditions:** By forcing sequential, single-threaded writes, file collisions are mathematically impossible.
*   **Guaranteed Rule Enforcement:** Because only the Master Compiler writes to the disk, we guarantee that ADRs 01-04 are applied to *every single edit*. A human cannot accidentally break the Provenance chain.
*   **Predictable State:** At any given moment, the Wiki is in a fully consistent, compiled state.

---
**Status:** Proposed
**Depends On:** Implementation of a queuing mechanism (e.g., watching a directory for new files).
**Conclusion:** This concludes the foundational architectural blueprints required to solve the gaps in the "Naive LLM-Wiki" implementation.