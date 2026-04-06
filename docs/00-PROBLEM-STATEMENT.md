# Problem Statement: The Gap Between "Naive LLM-Wiki" and "Ideal Self-Compiling Knowledge Base"

## Context & Vision
This document outlines the critical challenges in implementing the **LLM Wiki** design pattern as proposed by Andrej Karpathy ([Gist Link](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)). 

The vision is a **Self-Compiling Knowledge Base** where an LLM agent transforms raw, unstructured data into a persistent, structured, and interlinked Wiki. However, current implementations are often "naive"—they handle simple data ingestion but stumble on real-world complexity, data lifecycle, and semantic integrity.

---

## 1. Data Evolution & Semantic Integrity (The Core Conflict)
Most current solutions assume data is additive. In reality, information is volatile.

### A. The Update/Clarification Trap
*   **Problem:** New data rarely just "adds" to the old. It often **updates, refines, or makes previous statements more massive/volume-heavy.**
*   **The Stumble:** Agents often treat updates as new entries, leading to internal contradictions within a single page or across the Wiki.
*   **The Ideal:** A "surgical rewrite" that preserves nuance while removing obsolete facts, maintaining a record of *how* and *why* the information evolved.

### B. Logical Contradictions
*   **Problem:** Source A says "X is True," Source B says "X is False." 
*   **The Stumble:** Agents either ignore the conflict, hallucinate a compromise, or overwrite one with the other without flagging the discrepancy.
*   **The Ideal:** A "Truth Verification" protocol that flags conflicts, forks viewpoints, or requests human intervention instead of silently failing.

### C. Duplication & "Information Echo"
*   **Problem:** Receiving the same information from multiple sources (Partial or Full Duplication).
*   **The Stumble:** Agents create "mirror pages" or redundant paragraphs, cluttering the search space and diluting the authoritative value of the Wiki.
*   **The Ideal:** Semantic deduplication that recognizes existing facts and merely adds "Confirmation" or "Source Weight" to them.

---

## 2. Structural Architecture & Scalability
How a Wiki grows is as important as what it contains.

### A. Information Bloat (The "Giant File" Problem)
*   **Problem:** Pages like `Python.md` become unreadably long as more data is ingested.
*   **The Stumble:** Once a file exceeds the agent's optimal context window, the quality of synthesis drops, and the agent begins to lose track of earlier sections.
*   **The Ideal:** Automatic "Semantic Splitting"—the agent should proactively refactor the structure, creating sub-pages and hierarchies when a topic becomes too dense.

### B. Granularity vs. Synthesis
*   **Problem:** Finding the right "atomic unit" of knowledge.
*   **The Stumble:** Too granular = thousands of tiny files with no connections. Too broad = giant files with lost details.
*   **The Ideal:** A dynamic balance where the agent manages both "High-level Summaries" and "Deep-dive Details" concurrently.

---

## 3. Provenance & Metadata (The "Black Box" Knowledge)
Knowledge without a source is just a claim.

### A. Traceability (Lineage)
*   **Problem:** In an LLM-written Wiki, it's hard to tell *which* raw document a specific fact came from.
*   **The Stumble:** Once "compiled," the connection to the `Raw/` folder is often severed.
*   **The Ideal:** Every fact or paragraph should be linked back to its source (Hash/ID) for auditing and potential "rollback" if a source is found to be unreliable.

### B. Staleness & Recency
*   **Problem:** Knowledge decays. What was true in 2024 (e.g., an API version) may be false in 2026.
*   **The Stumble:** Agents prioritize what they see first or what they find in the current context, often mixing old and new versions of technical data.
*   **The Ideal:** Mandatory temporal metadata (`source_date`, `last_verified`) used as a primary sorting/weighting factor for all edits.

---

## 4. Technical & Operational Bottlenecks
The infrastructure limits of current Agentic AI.

### A. Context Starvation (The "Map-Reduce" Failure)
*   **Problem:** To update the Wiki correctly, the agent needs to know what is *already* there. But it can't read 1000 files at once.
*   **The Stumble:** Agents make local edits that break global consistency (e.g., broken cross-links, redundant entity creation).
*   **The Ideal:** A robust "Global Index/Map" that the agent uses to navigate before acting.

### B. Multi-Agent Race Conditions
*   **Problem:** Two agents (or an agent and a human) editing the same Wiki page.
*   **The Stumble:** Overwrites and "lost updates."
*   **The Ideal:** A version control system (like Git) integrated into the agent's workflow for branching and merging knowledge.

---

## Summary
The "Ideal LLM-Wiki" is not just a collection of Markdown files; it is a **Living Knowledge Ecosystem** that requires:
1.  **Conflict Resolution Protocol** (Handling contradictions).
2.  **Semantic Refactoring Logic** (Managing structure).
3.  **Provenance Tracking** (Tracing sources).
4.  **Temporal Awareness** (Managing updates).

Current "Gist-based" implementations are mostly **Write-Only** or **Naive-Add**. The real work—the "Wiki-Patrolling"—is currently missing.
