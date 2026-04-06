# Architectural Decision Record 03: Auto-Sharding (Semantic Splitting)

## The Problem (Information Bloat & Context Starvation)
In a growing knowledge base, broad topics (e.g., `Python.md`, `Machine_Learning.md`) naturally attract more information. In a naive LLM-Wiki, the agent simply appends new sections to these files. 
As a file grows past optimal context limits (e.g., > 4000-8000 tokens):
1.  **Context Starvation:** The LLM "forgets" earlier sections of the document when making edits, leading to contradictions within the same file.
2.  **Increased Latency & Cost:** Re-reading and rewriting a massive file for every minor update is inefficient and expensive.
3.  **Loss of Granularity:** The file becomes a "wall of text" that is hard for humans to read and for other agents to target with specific queries.

## Proposed Solution: The Auto-Sharding Protocol

We must implement an automated "Semantic Splitting" mechanism. When a file crosses a defined threshold, the LLM must proactively refactor the document into a parent "Hub" page and multiple child "Spoke" pages.

### The Sharding Workflow

**1. Threshold Detection (The Trigger)**
A lightweight script (or the MCP server) monitors the size of all files in the `wiki/` directory.
*   **Metric:** Word count, Token count, or simply File Size (KB).
*   **Threshold:** E.g., > 3000 words.
When a file (e.g., `wiki/Python.md`) hits the threshold, it is flagged with a `#NEEDS_SHARDING` tag or added to a refactoring queue.

**2. The Semantic Split (Agent Action)**
A specialized "Refactoring Agent" (or the main agent in a specific mode) is invoked on the flagged file. Its instruction is NOT to add new knowledge, but purely to restructure.

*   **Step A: Topic Analysis:** The agent analyzes the headings (H2, H3) to identify natural fault lines. For `Python.md`, it might find large sections on `Asyncio`, `Data Models`, and `Web Frameworks`.
*   **Step B: Extraction:** The agent extracts these massive sections into new, granular files:
    *   `wiki/Python_Asyncio.md`
    *   `wiki/Python_Data_Models.md`
    *   `wiki/Python_Web_Frameworks.md`
*   **Step C: Hub Creation:** The agent replaces the extracted content in the original `wiki/Python.md` with concise summaries and Wiki-links (`[[...]]`) to the new child pages.

**Example `wiki/Python.md` (Post-Sharding):**
```markdown
# Python

Python is a high-level, general-purpose programming language.

## Asynchronous Programming
Python handles concurrent execution primarily through the `asyncio` library. For detailed implementation, event loop mechanics, and examples, see:
👉 [[Python_Asyncio]]

## Data Models
For information on dunder methods and object-oriented features, see:
👉 [[Python_Data_Models]]
```

**3. The Link Refactoring Pass (Global Consistency)**
This is the most critical and difficult step. When `Python.md` is split, other files in the Wiki might have been linking to `# Python Asyncio` inside the old giant file. 

The system must run a "Link Update" protocol:
*   A script searches for mentions or links to the old sections.
*   The agent is instructed to update those links to point to the newly created `[[Python_Asyncio]]` file.

## Why This Solves The Bottleneck
*   **Maintains Optimal Context:** Files remain small, focused, and easily digestible by both LLMs and humans.
*   **Enables Deep Dives:** Child pages can now grow and eventually be sharded themselves (e.g., `Python_Asyncio.md` -> `Python_Asyncio_EventLoop.md`), creating an organic, infinitely scalable fractal structure.
*   **Cost Efficiency:** Future updates only require loading the specific child page, not the entire history of the language.

---
**Status:** Proposed
**Depends On:** Basic File I/O and linking capabilities.
**Next Sequence:** Addressing the Global Indexing problem—how the agent navigates this expanding universe of small files without loading them all (ADR-04).