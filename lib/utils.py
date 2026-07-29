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

def get_env_key(key_name, default=None):
    """Retrieve environment variable key safely."""
    return os.environ.get(key_name, default)

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

