import os
import sys
import yaml

def ensure_dirs(base_dir):
    """Ensure raw/ and wiki/ directories exist."""
    raw_dir = os.path.join(base_dir, 'raw')
    wiki_dir = os.path.join(base_dir, 'wiki')
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(wiki_dir, exist_ok=True)
    return raw_dir, wiki_dir

def load_yaml_frontmatter(file_path):
    """Parse Markdown file splitting YAML frontmatter and body."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter_str = parts[1]
            body = parts[2]
            frontmatter = yaml.safe_load(frontmatter_str)
            return frontmatter, body
    except Exception as e:
        print(f"Error loading YAML frontmatter from {file_path}: {e}", file=sys.stderr)
    return None, None

def save_yaml_frontmatter(file_path, frontmatter, body):
    """Save updated YAML frontmatter and Markdown body back to note file."""
    try:
        yaml_str = yaml.dump(frontmatter, sort_keys=False, allow_unicode=True)
        new_content = f"---\n{yaml_str}---\n{body}"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    except Exception as e:
        print(f"Error writing YAML frontmatter to {file_path}: {e}", file=sys.stderr)
    return False

def get_secret(key_name, default=None):
    """Retrieve secret safely from environment variables or Streamlit secrets."""
    if key_name in os.environ and os.environ[key_name]:
        return os.environ[key_name]
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    return default

def get_env_key(key_name, default=None):
    """Retrieve environment variable key safely."""
    return get_secret(key_name, default)

def load_env(base_dir):
    """Load environment variables from a local .env file in the base directory."""
    env_path = os.path.join(base_dir, '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, val = line.split('=', 1)
                        key = key.strip()
                        val = val.strip()
                        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                            val = val[1:-1]
                        os.environ[key] = val
        except Exception as e:
            print(f"Warning: Failed to load .env file: {e}", file=sys.stderr)

def sync_to_github(base_dir, commit_message="Sync SecondSelf wiki updates via app"):
    """Auto-commit and push wiki changes to GitHub repository."""
    import subprocess
    try:
        gh_token = get_secret("GITHUB_TOKEN") or get_secret("GH_TOKEN")
        
        # 1. Ensure git user identity is configured (essential in fresh cloud containers)
        subprocess.run(["git", "config", "user.email", "secondself-app@users.noreply.github.com"], cwd=base_dir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "SecondSelf Cloud App"], cwd=base_dir, capture_output=True)
        
        # 2. Configure remote URL with token if token is provided
        if gh_token:
            repo_url = f"https://{gh_token}@github.com/Herschelle-andy/Second-Self.git"
            subprocess.run(["git", "remote", "set-url", "origin", repo_url], cwd=base_dir, capture_output=True)
        else:
            return False, "GITHUB_TOKEN not configured. Please add GITHUB_TOKEN to Streamlit Cloud Secrets / .env to persist cloud captures."
            
        # 3. Stage wiki notes (including deletions) and commit FIRST
        subprocess.run(["git", "add", "-A", "wiki/"], cwd=base_dir, capture_output=True)
        commit_res = subprocess.run(
            ["git", "commit", "-m", commit_message], 
            cwd=base_dir, 
            capture_output=True, 
            text=True
        )
        
        # 4. Pull and rebase remote changes with local commits preserved
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], cwd=base_dir, capture_output=True)
        
        # 5. Push to GitHub main branch
        push_res = subprocess.run(
            ["git", "push", "origin", "main"], 
            cwd=base_dir, 
            capture_output=True, 
            text=True
        )
        
        if push_res.returncode == 0:
            return True, "Synced to GitHub successfully."
        else:
            err_msg = (push_res.stderr or push_res.stdout or "").strip()
            return False, f"Git push failed: {err_msg}"
    except Exception as e:
        return False, str(e)

def delete_note(base_dir, note_id):
    """Delete an app-captured note from wiki directory and remove its links across all other notes."""
    wiki_dir = os.path.join(base_dir, 'wiki')
    categories = ['Projects', 'Areas', 'Resources', 'Archives']
    target_file = None
    
    # 1. Find the target note file
    for cat in categories:
        candidate_file = os.path.join(wiki_dir, cat, f"{note_id}.md")
        if os.path.exists(candidate_file):
            target_file = candidate_file
            break
            
    if not target_file:
        return False, f"Note {note_id} not found."
        
    # Check if note is protected (seed / pre-existing)
    fm, body = load_yaml_frontmatter(target_file)
    if not fm or fm.get("source") != "app_capture":
        return False, "Protected Note: Seed and pre-existing knowledge base notes cannot be deleted."
        
    # Remove file
    try:
        os.remove(target_file)
    except Exception as e:
        return False, f"Failed to delete file: {e}"
        
    # 2. Clean up bidirectional links in other notes
    for root, dirs, files in os.walk(wiki_dir):
        for file in files:
            if file.endswith('.md'):
                fpath = os.path.join(root, file)
                try:
                    fm, body = load_yaml_frontmatter(fpath)
                    if fm and "links" in fm and isinstance(fm["links"], list):
                        if note_id in fm["links"]:
                            fm["links"] = [link for link in fm["links"] if link != note_id]
                            save_yaml_frontmatter(fpath, fm, body)
                except Exception as e:
                    print(f"Error updating links in {fpath}: {e}")
                    
    # 3. Clean from embeddings cache if present
    cache_path = os.path.join(base_dir, 'embeddings.pkl')
    if os.path.exists(cache_path):
        try:
            import pickle
            with open(cache_path, 'rb') as f:
                emb_cache = pickle.load(f)
            if note_id in emb_cache:
                del emb_cache[note_id]
                with open(cache_path, 'wb') as f:
                    pickle.dump(emb_cache, f)
        except Exception as e:
            print(f"Warning: Failed to update embeddings cache: {e}")
            
    # 4. Rebuild graph.json
    graph_path = os.path.join(base_dir, 'graph.json')
    try:
        import build_graph
        build_graph.build_graph_data(wiki_dir, graph_path)
    except Exception as e:
        print(f"Warning: Failed to rebuild graph after deletion: {e}")
        
    # 5. Sync deletion to GitHub
    sync_to_github(base_dir, commit_message=f"Delete note {note_id} via SecondSelf app")
    
    return True, f"Successfully deleted note {note_id}."

