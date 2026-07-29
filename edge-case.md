# Edge Cases & Mitigation Strategies: SecondSelf 🛡️

This document registers potential corner cases, system vulnerabilities, and edge-case scenarios within the **SecondSelf** pipeline, along with the corresponding mitigation strategies implemented or proposed.

---

## 1. Ingestion Layer (`capture.py`)

| Corner Case / Edge Case | Risk | Mitigation Strategy |
| :--- | :--- | :--- |
| **Empty or Whitespace-only Input** | Saving blank files, cluttering the knowledge base. | Validate inputs before capture. Raise errors or show UI warnings for blank text notes or empty URLs. |
| **Scraper Blocking / Network Outages** | Fetching empty pages, crashing the capture pipeline. | Wrap `requests.get` in try-except blocks. Default to user-agent spoofing (Chrome/Mozilla headers). If fetching fails, save the raw URL string as a fallback note instead of raising a crash. |
| **Extremely Large Web Pages** | Exceeding token context windows or taking excessive system memory during classification. | Limit the text extracted to the first 8,000 characters. Decompose large script/style trees before text retrieval. |
| **Non-UTF-8 Encoded Files** | Character encoding errors (`UnicodeDecodeError`) when reading files. | Open files using `errors='ignore'` or `errors='replace'` flags, and default to `utf-8` encoding. |
| **Binary/Non-text Files (Scanned PDFs, Images)** | Empty content fields in raw staging, making classification impossible. | Check file extensions. Copy the raw file to target destination, but write metadata JSON stating the file is binary. Provide descriptive placeholders in the content field. |
| **Illegal Filename Characters** | Windows OS filesystem crashes when copying files with illegal characters (`<`, `>`, `:`, `"`, `/`, `\`, `\|`, `?`, `*`). | Sanitize original filenames before copying to the target destination by replacing special characters with underscores (`_`). |

---

## 2. Enrichment & Classification Layer (`classify.py`)

| Corner Case / Edge Case | Risk | Mitigation Strategy |
| :--- | :--- | :--- |
| **Groq API Rate Limits / Outage** | Process crashes midway, leaving staging files unorganized. | Implement fallback endpoints. Attempt to call high-tier models first (`llama-3.3-70b-versatile`), and catch rate limits to fallback to fast models (`llama-3.1-8b-instant`). |
| **Malformed JSON from LLM** | Parsing crashes when extracting category, tags, and summary. | Use Groq's native `response_format={"type": "json_object"}`. Wrap `json.loads` in error handlers and default to the `Resources` category with placeholder title/tags if parsing fails. |
| **LLM Category Hallucinations** | Notes sorted into non-standard folders (e.g. "Personal", "Work" instead of PARA). | Enforce whitelist verification. If the LLM returns an invalid category string, default the target classification to `Resources`. |
| **Special Characters in LLM Output** | YAML parser crashes when writing generated metadata to Markdown. | Use structured serialization tools like `pyyaml` (`yaml.dump`) to format frontmatter, rather than manual string building. This automatically escapes problematic quotes or special characters. |
| **Double Processing / Race Conditions** | Notes get classified twice, leading to duplicate markdown files. | Before classification, verify whether the unique ID file already exists in any of the four PARA folders under `wiki/`. |

---

## 3. Semantic Linking Layer (`link.py`)

| Corner Case / Edge Case | Risk | Mitigation Strategy |
| :--- | :--- | :--- |
| **Zero or One Note in Wiki** | Matrix calculations fail (division by zero or empty similarity lists). | Check the length of notes lists at execution start. If less than 2, log an informational warning and exit safely. |
| **High Document Scale (500+ Notes)** | Exponential scaling ($O(N^2)$) of cosine similarity computation causes performance delays. | Limit similarity calculations to a batch-wise workflow, or pre-filter connections using category matches and simple keyword matches before running embedding operations. |
| **Duplicate Links in YAML** | Redundant linkages cluttering graph connections and rendering multiple edges. | Ensure the link addition logic checks `if target_id not in note['frontmatter']['links']` before writing. |
| **Corrupted Frontmatter Syntax** | User manual edits break YAML formatting, causing parser crashes. | Use try-except blocks around `yaml.safe_load`. If parsing fails, output detailed syntax warning logs and skip the corrupted file to prevent program crashes. |

---

## 4. Graph Construction (`build_graph.py`)

| Corner Case / Edge Case | Risk | Mitigation Strategy |
| :--- | :--- | :--- |
| **Orphan Notes** | Nodes sitting completely isolated on the graph. | Vis-network supports rendering orphan nodes. This is an expected pattern in second brains and does not require elimination. |
| **Dangling Edge References** | Edges linking to note IDs that have been renamed, deleted, or categorized differently. | Maintain an active index of valid node IDs during traversal. Only create edges if both the source and target node IDs exist in the active index. |
| **Self-Referential Links** | Notes pointing to themselves, forming self-loops. | Filter out edges where `from` equals `to`. |

---

## 5. Q&A Retrieval (RAG) & Interface (`ask.py` / `app.py`)

| Corner Case / Edge Case | Risk | Mitigation Strategy |
| :--- | :--- | :--- |
| **Irrelevant / Nonsensical Queries** | RAG retrieval fetches unrelated notes and LLM hallucinates answers. | Set a hard similarity threshold (e.g. `similarity > 0.15`) for retrieved context notes. If no notes meet the threshold, bypass LLM synthesis and immediately output: *"Based on your notes, I couldn't find an answer."* |
| **Context Window Overflow** | Querying fetches too many large documents, breaking token limitations. | Cap retrieval to $K=3$ context notes, and restrict context snippets to the first 1,500 characters of each note's body. |
| **Serverless Deployment Ephemerality** | Files saved locally during cloud runtimes disappear on container spin-down. | For true cloud deployment, use database storage (like Supabase or Git-backed persistence) instead of local folders. Clarify in deployment documentation that the free Streamlit Cloud deployment acts as a session-only demo. |
| **Groq API Key Absent** | Q&A interface crashes. | Read keys safely. Display warnings in the Streamlit UI showing API configuration status (Missing / Set) rather than letting backend errors crash the interface. |
