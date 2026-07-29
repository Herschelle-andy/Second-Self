import os
import sys
import yaml
import pickle
from functools import lru_cache
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

@lru_cache(maxsize=1)
def get_embedding_model():
    print("Loading local SentenceTransformer model (cached)...")
    return SentenceTransformer('all-MiniLM-L6-v2')

def load_all_notes(wiki_dir):
    """Recursively search for all .md files in the wiki directory and load them."""
    notes = []
    if not os.path.exists(wiki_dir):
        print(f"Wiki directory does not exist: {wiki_dir}")
        return notes
        
    for root, dirs, files in os.walk(wiki_dir):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        frontmatter_str = parts[1]
                        body = parts[2]
                        frontmatter = yaml.safe_load(frontmatter_str)
                        
                        notes.append({
                            "path": file_path,
                            "frontmatter": frontmatter,
                            "body": body,
                            "id": frontmatter.get("id"),
                            "title": frontmatter.get("title", ""),
                            "summary": frontmatter.get("summary", ""),
                            "category": frontmatter.get("category", "")
                        })
                except Exception as e:
                    print(f"Error loading note {file_path}: {e}")
                    
    return notes

def save_note(note):
    """Write the updated frontmatter and body back to the note file."""
    try:
        yaml_str = yaml.dump(note["frontmatter"], sort_keys=False, allow_unicode=True)
        new_content = f"---\n{yaml_str}---\n{note['body']}"
        with open(note["path"], 'w', encoding='utf-8') as f:
            f.write(new_content)
    except Exception as e:
        print(f"Error saving note {note['path']}: {e}")

def link_notes(wiki_dir, similarity_threshold=0.5):
    """Compute embeddings and link related notes."""
    print("Loading all wiki notes...")
    notes = load_all_notes(wiki_dir)
    
    if len(notes) < 2:
        print(f"Found {len(notes)} notes. At least 2 notes are needed to compute links.")
        return
        
    cache_path = os.path.join(os.path.dirname(wiki_dir), 'embeddings.pkl')
    embeddings_cache = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'rb') as f:
                embeddings_cache = pickle.load(f)
        except Exception as e:
            print(f"Warning: Failed to load embeddings cache: {e}")

    embeddings = []
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
            embeddings.append(cached_entry["embedding"])
        else:
            if model is None:
                model = get_embedding_model()
            
            print(f"Computing embedding for note: {note['title']}...")
            emb = model.encode([combined_text], convert_to_numpy=True)[0]
            embeddings.append(emb)
            embeddings_cache[note_id] = {
                "mtime": mtime,
                "embedding": emb
            }
            cache_updated = True
            
    if cache_updated:
        print("Saving updated embeddings cache to embeddings.pkl...")
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(embeddings_cache, f)
        except Exception as e:
            print(f"Warning: Failed to save embeddings cache: {e}")
            
    embeddings = np.array(embeddings)
    
    print("Calculating cosine similarities...")
    sim_matrix = cosine_similarity(embeddings)
    
    links_added = 0
    # Keep track of links we intend to add to prevent concurrent modification mismatch
    # (though list edits are in-place, let's make it clean)
    for i in range(len(notes)):
        note_a = notes[i]
        id_a = note_a["id"]
        
        # Initialize links list if not present
        if "links" not in note_a["frontmatter"] or not isinstance(note_a["frontmatter"]["links"], list):
            note_a["frontmatter"]["links"] = []
            
        for j in range(i + 1, len(notes)):
            note_b = notes[j]
            id_b = note_b["id"]
            
            if "links" not in note_b["frontmatter"] or not isinstance(note_b["frontmatter"]["links"], list):
                note_b["frontmatter"]["links"] = []
                
            similarity = sim_matrix[i][j]
            
            if similarity >= similarity_threshold:
                # Add links bidirectional
                added = False
                if id_b not in note_a["frontmatter"]["links"]:
                    note_a["frontmatter"]["links"].append(id_b)
                    added = True
                if id_a not in note_b["frontmatter"]["links"]:
                    note_b["frontmatter"]["links"].append(id_a)
                    added = True
                    
                if added:
                    print(f"Auto-linked: '{note_a['title']}' <-> '{note_b['title']}' (similarity: {similarity:.3f})")
                    links_added += 1

    if links_added > 0:
        print(f"Saving changes to files...")
        for note in notes:
            save_note(note)
        print(f"Auto-linking complete. Established {links_added} new bi-directional link connections.")
    else:
        print("No new links added above the similarity threshold.")

if __name__ == "__main__":
    base_directory = os.path.dirname(os.path.abspath(__file__))
    wiki_directory = os.path.join(base_directory, 'wiki')
    
    # Allow threshold override via arguments
    threshold = 0.5
    if len(sys.argv) > 1:
        try:
            threshold = float(sys.argv[1])
            print(f"Using custom similarity threshold: {threshold}")
        except ValueError:
            print(f"Invalid threshold argument. Defaulting to {threshold}")
            
    link_notes(wiki_directory, threshold)
