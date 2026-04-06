# Architectural Decision Record 02: Conflict Resolution & Semantic Integrity

## The Problem (The Override Dilemma)
In a naive LLM-Wiki, when an agent ingests `Source B` which contradicts information already written in the Wiki from `Source A`, the agent usually fails in one of three ways:
1.  **Silent Overwrite:** It deletes the old fact and writes the new one, losing historical context and potentially replacing truth with a hallucination or an inferior source.
2.  **Cognitive Dissonance:** It appends the new fact next to the old one without acknowledging the contradiction (e.g., "The API rate limit is 100 req/min. The API rate limit is 50 req/min.").
3.  **Hallucinated Compromise:** It tries to blend them into a false statement (e.g., "The API rate limit is between 50 and 100 req/min.").

## Proposed Solution: The "Truth Verification" Protocol

To maintain semantic integrity, the agent must shift from a "Write" mindset to a "Compare & Merge" mindset. We implement a specific prompt pattern and workflow triggered whenever an agent updates an existing Wiki page.

### The Workflow

**1. The Read-and-Compare Pass**
Before writing, the agent must extract the facts from the existing Wiki page related to the topic of the new source. It then explicitly compares the *New Claims* against the *Existing Claims*.

**2. Conflict Detection**
If the agent detects a direct logical contradiction, it must HALT the standard ingestion process and trigger the Conflict Resolution Protocol.

### The Resolution Protocol (Relying on ADR-01 Provenance)

When a contradiction is found, the agent must look up the `src_id` attached to the existing text (from ADR-01) in the **Source Manifest**. It then compares the metadata of the *Old Source* and the *New Source*.

The agent must follow one of three paths based on this comparison:

#### Path A: Temporal or Authority Override
*   **Condition:** The New Source has a significantly newer `publication_date` OR a higher `trust_weight` (e.g., Official Documentation vs. a Reddit post).
*   **Action:** The agent overwrites the existing fact with the new one.
*   **Traceability:** It replaces the old citation `^[src_A]` with the new one `^[src_B]`. 
*   **Logging:** It MUST write an entry in a central `changelog.md` or a specific section on the page: *"Updated [Fact X] to [Fact Y] because [Source B] is more recent/authoritative than [Source A]."*

#### Path B: The "Rashomon" Fork (Viewpoint Forking)
*   **Condition:** Both sources have similar weight/dates, or the contradiction represents a difference in opinion, methodology, or edge cases rather than a strict binary truth.
*   **Action:** The agent explicitly refactors the section to present BOTH viewpoints objectively.
*   **Example Output:**
    ```markdown
    ### Performance Characteristics
    There is a divergence in observed performance for this module:
    * According to internal benchmarks, the throughput is 500 ops/sec. ^[src_internal_tests]
    * However, third-party audits claim the maximum throughput is only 300 ops/sec under load. ^[src_external_audit]
    ```

#### Path C: Human Escalation (The "Hard Stop")
*   **Condition:** The conflict involves critical infrastructure, security, or core business logic where both sources are highly trusted but mutually exclusive (e.g., "Use Port 8080" vs "Use Port 443").
*   **Action:** The agent does NOT alter the existing text. Instead, it injects a prominent warning block and tags the file.
*   **Example Output:**
    ```markdown
    > [!WARNING] CONFLICT DETECTED
    > Existing documentation claims X ^[src_old]. New ingestion attempt from ^[src_new] claims Y. 
    > **Action Required:** Human review needed to resolve port configuration.
    
    #NEEDS_HUMAN_RESOLUTION
    ```

## Implementation Requirements
*   **System Prompt Update:** The LLM's core instructions must explicitly detail Paths A, B, and C.
*   **Tooling:** The agent needs read access to `schema/sources.json` (The Source Manifest) to compare dates and weights *before* making the edit decision.
*   **CI/CD or Git Hooks:** A script that scans the Wiki for `#NEEDS_HUMAN_RESOLUTION` tags and alerts the repository owner.

---
**Status:** Proposed
**Depends On:** ADR-01 (Provenance & Traceability)
**Next Sequence:** Addressing Information Bloat through Auto-Sharding (Semantic Splitting) when files grow too large (ADR-03).