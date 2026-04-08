# Architectural Decision Record 02: Conflict Resolution & Knowledge Evolution

## The Problem (The Override Dilemma)
In a naive LLM-Wiki, when an agent ingests `Source B` which contradicts information already written in the Wiki from `Source A`, the agent usually fails in one of three ways:
1.  **Silent Overwrite:** It deletes the old fact and writes the new one, losing historical context and potentially replacing truth with a hallucination or an inferior source.
2.  **Cognitive Dissonance:** It appends the new fact next to the old one without acknowledging the contradiction (e.g., "The API rate limit is 100 req/min. The API rate limit is 50 req/min.").
3.  **Hallucinated Compromise:** It tries to blend them into a false statement (e.g., "The API rate limit is between 50 and 100 req/min.").

## Proposed Solution: The "Truth Verification & Evolution" Protocol

To maintain semantic integrity, the agent must shift from a "Write" mindset to a "Compare & Merge" mindset. We implement a specific prompt pattern and workflow triggered whenever an agent updates an existing Wiki page.

### The Workflow

**1. The Read-and-Compare Pass (`get_entity_knowledge`)**
Before making any updates, the LLM is explicitly required by the Server's system prompt to call `get_entity_knowledge()`. This tool fetches the current state of a given entity (e.g., the existing `Python.md` page). The LLM reads the existing facts and logically compares its *New Claims* against the *Existing Claims*.

**2. The Evolution Engine (Four Statuses)**
Instead of just saying "Edit this file," the LLM must submit an array of specific facts (entities) via `commit_updates(JSON)`. The MCP server enforces four strict status codes for every fact:

#### Case 1: Status `KEEP` (Consensus)
*   **Condition:** The new source confirms an existing fact without changing its meaning.
*   **Action:** The LLM assigns `status: "KEEP"`.
*   **Server Behavior:** The server does not change the text but appends the new `^[src_B]` ID to the existing `^[src_A]` IDs, increasing the factual weight and confirming consensus.

#### Case 2: Status `NEW` (Addition)
*   **Condition:** The new source provides a totally new fact or section not present in the current doc.
*   **Action:** The LLM assigns `status: "NEW"`.
*   **Server Behavior:** The server simply appends the new paragraph/bullet with its source tag.

#### Case 3: Status `UPDATE` (Evolution)
*   **Condition:** A fact has organically evolved (e.g., changing from API v1.0 to v2.0, or updating a performance metric).
*   **Action:** The LLM assigns `status: "UPDATE"`. Crucially, it must provide *both* the new "text" and the "old_text".
*   **Server Behavior:** We DO NOT DELETE. The server renders the new fact but explicitly archives the old one inline for context.
*   **Output Example:**
    > The rate limit is now 50 req/min. ^[src_B] *(Evolution: previously described as "The rate limit is 100 req/min.")*

#### Case 4: Status `CONFLICT` (The Hard Stop)
*   **Condition:** The new source directly contradicts critical logic, infrastructure, or facts from the existing source in a way that implies an error on one side, not an evolution. (e.g., Source A says a setting is true, Source B vehemently says it is false).
*   **Action:** The LLM assigns `status: "CONFLICT"`. The LLM is explicitly forbidden from trying to merge them.
*   **Server Behavior:** The server injects a prominent warning block into the Markdown file, tagging it for human review.
*   **Output Example:**
    ```markdown
    > [!CAUTION] KNOWLEDGE CONFLICT
    > New evidence from ^[src_B] contradicts existing record:
    > **New Fact:** The setting `use_tls` must be set to false.
    > #NEEDS_HUMAN_RESOLUTION
    ```

## Why This Works
*   **Absolute Traceability:** Combined with ADR-01, the system mathematically tracks exactly what changed, when, and because of what specific source file.
*   **Zero Loss of Context:** The `UPDATE` protocol ensures that the context of "why" something changed is forever baked into the document.
*   **Human-in-the-Loop Safeguards:** AI hallucinations or bad source documents cannot quietly corrupt the entire Wiki; `CONFLICT` automatically flags anomalies for the user.

---
**Status:** Implemented in `autowiki/core/compiler.py` and the `compile_knowledge_base` system prompt.
