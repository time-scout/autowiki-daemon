# Architectural Decision Record 04: The Global Index & Navigation

## The Problem (The Map-Reduce Failure & "Lost" Knowledge)
With the introduction of Auto-Sharding (ADR-03), our knowledge base will organically grow from a few large files into thousands of specialized Markdown files. 
When a new source arrives (e.g., an update on "Python Asyncio Event Loops"), the agent faces a critical routing problem: **Where does this information belong?**

If the agent doesn't know `wiki/Python_Asyncio_EventLoop.md` exists, it will likely create a redundant page or append the information to a higher-level hub like `wiki/Python.md`. 
Reading all 1000 files to find the right spot is impossible due to LLM context limits and token costs. Relying on a manually maintained `index.md` fails because the index itself will quickly exceed context limits.

## Proposed Solution: The Dual-Index Navigation System

To navigate a massive, fragmented codebase, the agent must be equipped with tools to "survey" the landscape *before* it decides where to read or write. We implement a two-tiered indexing system that sits outside the LLM's context window.

### Layer 1: The Entity Graph (Structural Index)
Before reading the content of the Wiki, the agent needs to know what "Entities" (topics, concepts, people) already exist and where they live.

*   **Implementation:** A lightweight metadata registry (e.g., `schema/entity_graph.json` or extracted dynamically from Markdown YAML frontmatter using a script).
*   **Structure:** Maps Entity Names/Aliases to File Paths.
    ```json
    {
      "Python": "wiki/Python.md",
      "Asyncio": "wiki/Python_Asyncio.md",
      "Event Loop": "wiki/Python_Asyncio_EventLoop.md",
      "GIL": "wiki/Python_GIL.md"
    }
    ```
*   **Agent Workflow:** When processing a new document about the "GIL", the agent first queries the Entity Graph tool: `find_entity("GIL")`. The tool returns `wiki/Python_GIL.md`. The agent now knows exactly which file to load into its context for the update.

### Layer 2: Semantic Search Engine (Content Index)
If the Entity Graph fails (e.g., the concept is mentioned as a passing thought inside a broader file but doesn't have its own page yet), the agent needs a fallback.

*   **Implementation:** A local, fast search engine that indexes the `wiki/` directory. (Andrej Karpathy mentions `qmd`, but any local BM25 + Vector embedding search works, e.g., local ChromaDB or a simple TF-IDF Python script).
*   **Agent Workflow:** If `find_entity("Memory Management in Python")` returns nothing, the agent uses a search tool: `semantic_search("How does Python handle memory?")`. 
*   **Result:** The tool returns the top 3 most relevant paragraphs and their file paths. The agent can then decide to update one of those files or create a new one if the existing context is insufficient.

## The Ingestion Routing Algorithm

With the Dual-Index in place, the ingestion of a new source follows this strict sequence:

1.  **Extract Concepts:** The agent reads the `raw/source.pdf` and extracts the core concepts (e.g., Concept A, Concept B).
2.  **Query Entity Graph:** For each concept, the agent checks the Structural Index.
    *   *Match Found:* Load the target Markdown file.
    *   *No Match:* Proceed to step 3.
3.  **Semantic Search (Fallback):** The agent searches the existing Wiki content for the concept.
    *   *Relevant Context Found:* Load the identified file(s).
    *   *No Context Found:* The agent is authorized to create a **New Markdown File** and register it in the Entity Graph.
4.  **Execute Update:** The agent performs the "Read-and-Compare" pass (ADR-02) and writes the update with proper provenance (ADR-01).

## Why This Solves The Bottleneck
*   **O(1) Routing:** The agent jumps directly to the correct file without map-reducing the entire directory.
*   **Prevents Redundancy:** By checking the Entity Graph first, the agent won't create `wiki/Async_Python.md` if `wiki/Python_Asyncio.md` already exists.
*   **Scalability:** The indexing tools run in the background (via Python/Node scripts) and only pass the necessary file paths or snippets into the LLM's expensive context window.

---
**Status:** Proposed
**Depends On:** Tool calling capabilities for the LLM (access to read JSON and execute local search).
**Next Sequence:** Addressing the final major bottleneck: Multi-Agent Race Conditions and Version Control (ADR-05).