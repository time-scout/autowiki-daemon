# Problem Statement: The Hallucination-Free LLM-Wiki

## The Pain 
You connect an LLM to your notes, tell it to "manage my wiki," and within days, it creates an untraceable, hallucinated mess. 

LLMs are incredible at synthesizing information, but they are terrible at maintaining strict persistent state. When naive AI agents update a knowledge base, they:
1. **Delete History:** Silently overwrite old facts with new ones, destroying context.
2. **Hallucinate:** Invent compromises when two sources contradict.
3. **Lose Provenance:** Orphan facts from their original sources, making the wiki untrustworthy.

Andrej Karpathy proposed the "LLM Wiki" design pattern ([Gist Link](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)) to address this. However, implementing this vision in the real world requires a strict "Database Layer" between the LLM and the file system. That is the exact pain AutoWiki solves.

---

## 1. Data Evolution & Semantic Integrity (The Core Conflict)
Most current solutions assume data is additive. In reality, information is volatile.

### A. The "Never Delete" Evolution Protocol
*   **The Problem:** When an API updates from v1 to v2, naive agents delete the v1 documentation to make room for v2.
*   **The Solution:** Knowledge is a journey. Agents must NEVER delete. Instead, they apply a "surgical update" that preserves the old fact inline as historical context (`*(Evolution: previously described as...)*`). 

### B. Logical Contradictions
*   **The Problem:** Source A says "X is True," Source B says "X is False." 
*   **The Solution:** A "Truth Verification" protocol. The server forces the agent to explicitly flag the contradiction with a `#NEEDS_HUMAN_RESOLUTION` caution block, rather than hallucinating a false compromise.

---

## 2. Omnivorous Agent Ingestion (Beyond Local Files)
*   **The Problem:** Wikis shouldn't just be limited to text files a human manually drops into a folder. 
*   **The Solution:** The `/inbox` is an API, not just a static folder. If the connected Agent has external capabilities (Web Browsing, YouTube Transcripts, GitHub access, Image Vision), it can fetch that external data on its own. Before writing to the Wiki, the Agent is simply forced to generate a "Source Passport" in the `/inbox` containing the raw external data, giving the system a formal local anchor for provenance.

---

## 3. Provenance & Metadata (The "Iron Standard")
Knowledge without a source is just a claim.

### A. Absolute Traceability
*   **The Problem:** In a typical LLM-written Wiki, it's impossible to tell *which* web page or PDF a specific fact came from.
*   **The Solution:** The "Iron Standard". The LLM is mathematically forbidden from adding a fact to the Wiki without a verified Source Passport. Every individual fact in the compiled Wiki must end with a traceable tag (e.g., `^[src_8F2A]`).

---

## 4. Multi-Agent Race Conditions
*   **The Problem:** Two agents (or an agent and a human) editing the same Markdown file simultaneously leads to overwritten logic.
*   **The Solution:** A strict Model Context Protocol (MCP) server architecture. The server acts as a single-writer State Machine, queuing updates and committing them to a local Git repository to guarantee an uncorrupted audit trail.
