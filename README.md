# SecondSelf - Your Personal AI Second Brain 🧠

SecondSelf is a personal knowledge management system designed to make note-taking, link bookmarking, and document indexing actionable. Rather than letting notes sit in unorganized folders, SecondSelf uses LLMs to automatically classify and structure inputs, applies embeddings to discover similarity connections, renders an interactive force-directed graph to visualize your mind, and enables retrieval-augmented Q&A (RAG) over your notes.

---

## Features

- **Ingestion Pipeline**: CLI and UI tools to capture plain-text notes, scraped web links, and file uploads.
- **PARA Categorization**: Automatically classifies raw captures into Projects, Areas, Resources, or Archives using Llama-3 via Groq.
- **Auto-Semantic Linking**: Employs local sentence embeddings (`all-MiniLM-L6-v2`) to measure note similarities and build bidirectional links.
- **Living Brain Graph**: Visualizes the knowledge base as an interactive, draggable, zoomable force-directed graph using `vis-network.js`.
- **Natural Language RAG (Ask Your Brain)**: Answer synthesis over your knowledge base with citation support.

---

## Repository Structure

```text
secondself/
├── raw/                 # Ingested raw captures (temp/JSON)
├── wiki/                # Structured PARA markdown notes
│   ├── Projects/
│   ├── Areas/
│   ├── Resources/
│   └── Archives/
├── capture.py           # Capture pipeline CLI utility
├── classify.py          # PARA classification module via Groq
├── link.py              # Semantic embedding & link generator
├── build_graph.py       # Graph.json builder utility
├── graph.json           # Output representation of nodes & edges
├── ask.py               # RAG Q&A engine
├── app.py               # Unified Streamlit application
├── requirements.txt     # Dependency list
└── README.md            # Documentation
```

---

## Installation & Setup

### 1. Clone & Scaffolding
Ensure Python 3.10+ is installed on your system. Navigate to the `secondself` folder and install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Keys
SecondSelf utilizes Groq for lightning-fast, free-tier LLM inference. Get a free API key from [Console Groq](https://console.groq.com/) and export it:

#### Windows PowerShell:
```powershell
$env:GROQ_API_KEY="your-api-key-here"
```

#### macOS/Linux:
```bash
export GROQ_API_KEY="your-api-key-here"
```

---

## Usage

### Option A: The Streamlit Web App (Recommended)
Launch the unified interface which handles ingestion, processing, graph representation, and Q&A dynamically:

```bash
streamlit run app.py
```

### Option B: The CLI Pipeline

1. **Capture Note**:
   ```bash
   python capture.py note "Review visual analytics tools for Python next Monday."
   ```

2. **Capture URL (Auto-Scrape)**:
   ```bash
   python capture.py link "https://github.com/trending"
   ```

3. **Capture File**:
   ```bash
   python capture.py file "c:\path\to\document.pdf"
   ```

4. **Classify Raw Ingests**:
   ```bash
   python classify.py
   ```

5. **Compute & Build Relationships**:
   ```bash
   python link.py
   ```

6. **Assemble Graph JSON**:
   ```bash
   python build_graph.py
   ```

7. **Q&A Retrieval**:
   ```bash
   python ask.py "What were my notes on visual tools?"
   ```
