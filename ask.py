import os
import sys
import yaml
import pickle
from functools import lru_cache
import numpy as np
from groq import Groq
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

@lru_cache(maxsize=1)
def get_embedding_model():
    print("Loading local SentenceTransformer model (cached)...")
    return SentenceTransformer('all-MiniLM-L6-v2')

# Load local environment files
from lib.utils import load_env, load_yaml_frontmatter
load_env(os.path.dirname(os.path.abspath(__file__)))

def get_groq_client():
    """Retrieve Groq API key and instantiate Groq client."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY environment variable is not set.")
        sys.exit(1)
    return Groq(api_key=api_key)

def load_all_notes(wiki_dir):
    """Load all notes recursively from the wiki directory."""
    notes = []
    if not os.path.exists(wiki_dir):
        return notes
        
    for root, dirs, files in os.walk(wiki_dir):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                try:
                    frontmatter, body = load_yaml_frontmatter(file_path)
                    if frontmatter:
                        note_id = frontmatter.get("id") or os.path.splitext(file)[0]
                        from lib.utils import is_seed_note
                        is_seed = is_seed_note(note_id)
                        notes.append({
                            "id": note_id,
                            "title": frontmatter.get("title", "Untitled Note"),
                            "summary": frontmatter.get("summary", ""),
                            "category": frontmatter.get("category", ""),
                            "captured_at": frontmatter.get("captured_at", ""),
                            "source": "seed" if is_seed else "app_capture",
                            "tags": frontmatter.get("tags", []),
                            "links": frontmatter.get("links", []),
                            "body": body.strip(),
                            "path": file_path
                        })
                except Exception as e:
                    print(f"Error loading note {file_path}: {e}", file=sys.stderr)
    return notes

def ask_brain(query, wiki_dir, top_k=3):
    """Embed the query, retrieve top_k matching notes, and synthesize answer via Groq LLM."""
    notes = load_all_notes(wiki_dir)
    if not notes:
        return "No knowledge base notes found. Please capture and classify some information first.", []
        
    client = get_groq_client()
    
    cache_path = os.path.join(os.path.dirname(wiki_dir), 'embeddings.pkl')
    embeddings_cache = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'rb') as f:
                embeddings_cache = pickle.load(f)
        except Exception as e:
            print(f"Warning: Failed to load embeddings cache: {e}", file=sys.stderr)

    note_embeddings = []
    cache_updated = False
    model = None
    
    for note in notes:
        note_id = note["id"]
        note_path = note["path"]
        mtime = os.path.getmtime(note_path)
        
        title = note["title"]
        summary = note["summary"]
        body_snippet = note["body"][:1500].strip()
        combined_text = f"Title: {title}\nSummary: {summary}\nContent:\n{body_snippet}"
        
        cached_entry = embeddings_cache.get(note_id)
        if cached_entry and cached_entry.get("mtime") == mtime and "embedding" in cached_entry:
            note_embeddings.append(cached_entry["embedding"])
        else:
            if model is None:
                model = get_embedding_model()
            
            emb = model.encode([combined_text], convert_to_numpy=True)[0]
            note_embeddings.append(emb)
            embeddings_cache[note_id] = {
                "mtime": mtime,
                "embedding": emb
            }
            cache_updated = True
            
    if cache_updated:
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(embeddings_cache, f)
        except Exception as e:
            print(f"Warning: Failed to save embeddings cache: {e}", file=sys.stderr)
            
    note_embeddings = np.array(note_embeddings)
    
    # Embed query (we load the model if not loaded yet)
    if model is None:
        model = get_embedding_model()
    query_embedding = model.encode([query], convert_to_numpy=True)
    
    # Calculate similarities
    similarities = cosine_similarity(query_embedding, note_embeddings)[0]
    
    # Rank notes by similarity
    ranked_indices = np.argsort(similarities)[::-1]
    
    # Select top_k notes
    retrieved_notes = []
    context_blocks = []
    
    for rank in range(min(top_k, len(notes))):
        idx = ranked_indices[rank]
        score = similarities[idx]
        
        # We can set a soft threshold for relevancy (e.g. > 0.15 to avoid pulling completely irrelevant notes)
        if score < 0.15:
            continue
            
        note = notes[idx]
        retrieved_notes.append({
            "id": note["id"],
            "title": note["title"],
            "category": note["category"],
            "score": float(score)
        })
        
        context_blocks.append(
            f"--- Note ID: {note['id']} ---\n"
            f"Title: {note['title']}\n"
            f"Category: {note['category']}\n"
            f"Content:\n{note['body']}\n"
        )
        
    if not context_blocks:
        return "I couldn't find any relevant notes matching your query in the knowledge base.", []
        
    context = "\n".join(context_blocks)
    
    # Build System Prompt and RAG call
    system_prompt = (
        "You are 'SecondSelf', a personal AI second brain. "
        "Answer the user's question using ONLY the provided notes context from their wiki. "
        "If you synthesize information from a note, ALWAYS cite the note's Title/ID in brackets, e.g. [Project Alpha Launch Plan]. "
        "Keep your response concise, structured, and informative. "
        "If the answer cannot be answered or inferred from the notes, clearly say: "
        "'Based on your notes, I couldn't find an answer to this question.'"
    )
    
    user_prompt = f"NOTES CONTEXT:\n{context}\n\nUSER QUESTION: {query}"
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant", # Fast and reliable for QA synthesis
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=800
        )
        answer = completion.choices[0].message.content
        return answer, retrieved_notes
    except Exception as e:
        return f"Error synthesizing answer from Groq: {e}", retrieved_notes

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ask.py \"your question here\"")
        sys.exit(1)
        
    query_str = sys.argv[1]
    base_directory = os.path.dirname(os.path.abspath(__file__))
    wiki_directory = os.path.join(base_directory, 'wiki')
    answer_text, sources = ask_brain(query_str, wiki_directory)
    print("\n=== SecondSelf Response ===")
    print(answer_text)
    print("\n=== Sources ===")
    for src in sources:
        print(f"- {src['title']} ({src['category']}) - Match Score: {src['score']:.2f}")
