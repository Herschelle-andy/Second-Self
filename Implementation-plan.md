# Phase-wise Implementation Plan: SecondSelf 🚀

This document maps out the structured, phase-wise implementation plan for building and verifying **SecondSelf**, based on the established system architecture and weekly problem statements.

---

## Roadmap Overview

```
┌────────────────────────────────┐
│   Phase 1: The Archivist       │ ──> Ingest notes, links, and files to raw/
└────────────────────────────────┘
                │
                ▼
┌────────────────────────────────┐
│   Phase 2: The Librarian       │ ──> PARA AI Classification & semantic linking
└────────────────────────────────┘
                │
                ▼
┌────────────────────────────────┐
│   Phase 3: The Cartographer    │ ──> Graph generation & interactive vis-network canvas
└────────────────────────────────┘
                │
                ▼
┌────────────────────────────────┐
│   Phase 4: The Oracle          │ ──> RAG-powered Q&A & Streamlit dashboard deployment
└────────────────────────────────┘
```

---

## Detailed Phases

### Phase 1: The Archivist (Capture Pipeline)

**Goal:** Establish the foundation. Build a single, robust CLI capture mechanism that can ingest any note, link, or file from any location on the system and place it securely into a raw staging directory.

#### Tasks & Implementation Details
1. **Scaffold Directory Structure**:
   - Create directories: `raw/` and `wiki/`.
   - Initialize `requirements.txt` with core modules (`streamlit`, `sentence-transformers`, `groq`, etc.).
2. **Develop Ingestion Core (`capture.py`)**:
   - **Text Note Capture**: Parse CLI argument string, generate timestamp-based ID, and write a JSON metadata file containing raw content.
   - **Web Link Capture**: Accept URLs, scrape text and title using `requests` and `beautifulsoup4` (removing script/style tags), and save text body to JSON.
   - **File Capture**: Copy files to `raw/`, prefix with unique ID. Read text content directly for flat files (`.txt`, `.md`); log metadata for binary formats.
3. **Robustness Safeguards**:
   - Use high-resolution millisecond timestamps (`note_1785013412694`) to prevent naming collisions.
   - Prepend `https://` if user inputs a URL missing a protocol scheme.
   - Implement user-agent headers to bypass scraper blocking on standard websites.

#### Verification Criteria
- [ ] Running capture CLI with a note, URL, and local file outputs matching success logs.
- [ ] Folder `raw/` contains `.json` files conforming to the raw capture schema.
- [ ] Scraping extracts the structural body text instead of raw HTML script syntax.

---

### Phase 2: The Librarian (Self-Organizing Wiki)

**Goal:** Transform the raw captures folder into a clean, categorized, and interlinked knowledge base (`wiki/`) using PARA framework classification and semantic embeddings.

#### Tasks & Implementation Details
1. **Develop LLM Categorizer (`classify.py`)**:
   - Read unclassified `.json` files from `raw/`.
   - Feed note contents to the Groq API (e.g. `llama-3.1-8b-instant` or `llama-3.3-70b-versatile`) under strict instructions to return a JSON object with:
     - `title` (AI generated headline)
     - `category` (Projects, Areas, Resources, or Archives)
     - `tags` (array of keywords)
     - `summary` (1-line description)
   - Save parsed contents as Markdown under `wiki/<Category>/<id>.md` using YAML frontmatter templates.
2. **Develop Auto-Linker (`link.py`)**:
   - Parse YAML frontmatter and load all notes in `wiki/`.
   - Embed note details (Title + Summary + Content snippet) using local `SentenceTransformer('all-MiniLM-L6-v2')`.
   - Compute pairwise cosine similarity scores.
   - If similarity exceeds `0.5`, update both notes' YAML `links` arrays bidirectionally.
3. **Execution Guardrails**:
   - Ensure the system checks if a note ID already exists in `wiki/` before calling the LLM to prevent double-spending tokens.
   - Run fallback mechanisms to lighter LLM models if Groq rate limits are hit.

#### Verification Criteria
- [ ] Run `classify.py` and verify notes are sorted into the correct subfolders (`wiki/Projects/`, `wiki/Areas/`, etc.).
- [ ] Run `link.py` and inspect YAML frontmatter links in generated markdown files to verify similarity connections are populated.

---

### Phase 3: The Cartographer (Graph Visualization)

**Goal:** Compile notes and references into a graph database structure and render it on an interactive force-directed canvas.

#### Tasks & Implementation Details
1. **Develop Graph Data Builder (`build_graph.py`)**:
   - Traverse the `wiki/` directory recursively to locate all `.md` files.
   - Read the ID, Title (label), Category, Summary, and Tags from the YAML frontmatter.
   - Accumulate unique edges by matching links to existing nodes.
   - Export compiled elements to `graph.json`.
2. **Develop Graph Visualization (embedded in `app.py`)**:
   - Integrate `vis-network.js` via an HTML/JS template injected in a Streamlit frame.
   - Map PARA categories to distinct colors:
     - **Projects**: Blue
     - **Areas**: Green
     - **Resources**: Yellow
     - **Archives**: Grey
   - Configure physics settings (gravitational constants, spring constants) to dynamically stabilize the nodes.
   - Setup hover tooltip behaviors showcasing node titles, categories, summaries, and tags.

#### Verification Criteria
- [ ] `graph.json` contains valid array structures for `nodes` and `edges`.
- [ ] Streamlit rendering displays nodes with correct visual representations.
- [ ] Double-clicking/dragging works smoothly without breaking physics layouts.

---

### Phase 4: The Oracle (RAG Q&A & Streamlit Dashboard)

**Goal:** Build a retrieval-augmented query console allowing natural language search over the knowledge base and unify the entire ingestion, visualization, and search interface into a single, deployable app.

#### Tasks & Implementation Details
1. **Develop RAG Engine (`ask.py`)**:
   - Compute embedding of user question.
   - Compute embeddings of all wiki notes, measure cosine similarity, and retrieve the top $K$ relevant notes.
   - Format retrieved notes into context segments and inject into a system prompt.
   - Instruct the LLM to answer the user query based **only** on the context and cite note titles in brackets.
2. **Integrate Streamlit App (`app.py`)**:
   - Sidebar: Forms for text notes, scraper links, and file uploads.
   - Sidebar executes `capture.py` -> `classify.py` -> `link.py` -> `build_graph.py` pipeline immediately on submit and triggers `st.rerun()` to update.
   - Main Canvas: Displays the `vis-network` interactive layout.
   - Search tab: Console executing `ask.py` and rendering response text alongside citation cards.
   - Note browser tab: Interactive browse interface grouped by PARA categories.
3. **Deployment**:
   - Configure `requirements.txt` for serverless runtimes.
   - Deploy to **Streamlit Community Cloud** or **Hugging Face Spaces**.
   - Manage secrets by placing the `GROQ_API_KEY` into Streamlit's secrets manager.

#### Verification Criteria
- [ ] Submitting a question correctly retrieves context, returns an answer citing sources, and gracefully handles queries outside the knowledge base.
- [ ] Capturing a new note dynamically updates the graph visualizer.
- [ ] The app successfully boots and runs in the cloud.
