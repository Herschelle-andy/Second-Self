import os
import sys
import json
import yaml
from groq import Groq

# Load local environment files
from lib.utils import load_env
load_env(os.path.dirname(os.path.abspath(__file__)))

def get_groq_client():
    """Retrieve Groq API key and instantiate Groq client."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)

def is_already_classified(base_dir, note_id):
    """Check if the note is already present in any of the wiki folders."""
    wiki_dir = os.path.join(base_dir, 'wiki')
    categories = ['Projects', 'Areas', 'Resources', 'Archives']
    for cat in categories:
        target_path = os.path.join(wiki_dir, cat, f"{note_id}.md")
        if os.path.exists(target_path):
            return True
    return False

def mock_classify_content(content_type, content, original_metadata):
    """Fallback rule-based classification if GROQ_API_KEY is not set."""
    content_lower = content.lower()
    
    # Heuristics for categories
    if any(k in content_lower for k in ["project", "milestone", "deadline", "todo", "meeting"]):
        category = "Projects"
    elif any(k in content_lower for k in ["workout", "exercise", "shopping", "health", "finance", "goals", "budget"]):
        category = "Areas"
    elif any(k in content_lower for k in ["archive", "legacy", "old", "completed", "retired"]):
        category = "Archives"
    else:
        category = "Resources"
        
    # Heuristics for Title
    title = original_metadata.get('title') or original_metadata.get('original_filename')
    if not title:
        # Generate from first line of text or content snippet
        first_line = content.split('\n')[0].strip()
        if len(first_line) > 5 and len(first_line) < 50:
            title = first_line
        else:
            title = f"Captured {category[:-1]} Note"
            
    # Clean up markdown formatting in title if any
    title = title.replace("#", "").strip()

    # Heuristics for tags
    tags = []
    if content_type == "link":
        tags.append("bookmark")
    elif content_type == "file":
        tags.append("file")
    else:
        tags.append("note")
        
    for kw in ["alpha", "python", "graph", "recipe", "learn", "shopping", "workout", "finance"]:
        if kw in content_lower:
            tags.append(kw)
            
    # Summary
    summary = content.split('\n')[0].strip()
    if len(summary) > 100:
        summary = summary[:97] + "..."
    elif not summary:
        summary = f"Automatically captured {content_type}."
        
    return {
        "title": title,
        "category": category,
        "tags": list(set(tags))[:4],
        "summary": summary
    }

def classify_content(client, content_type, content, original_metadata):
    """Send raw content to Llama-3 on Groq to get PARA category, tags, title, and summary."""
    prompt = f"""
You are "The Librarian", an AI assistant specialized in organizing raw captures into a personal Second Brain using the PARA Method.
The PARA framework consists of:
- Projects: Things you are actively working on with a specific deadline/goal.
- Areas: Ongoing responsibilities that require standard maintenance (health, finances, writing, coding skill, etc.).
- Resources: Topics of interest, references, guides, tools, bookmarks that don't belong to a specific project or area.
- Archives: Inactive items from the other three categories (completed projects, old responsibilities, etc.).

Analyze the captured item below:
---
Type: {content_type}
Original Title/Filename: {original_metadata.get('title') or original_metadata.get('original_filename') or 'None'}
Raw Content:
{content}
---

Your response MUST be a JSON object with the following fields:
- "title": A short, clean, descriptive title for the note (generate one if not present, do not include timestamps in title).
- "category": The exact category string: "Projects", "Areas", "Resources", or "Archives".
- "tags": A list of 2-5 relevant, lowercase tags/keywords.
- "summary": A one-line summary of the content (maximum 150 characters).

Generate the response in valid JSON format.
"""
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", # Groq's high capability model
            messages=[
                {"role": "system", "content": "You output JSON matching the requested schema."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=500
        )
        
        response_text = completion.choices[0].message.content
        return json.loads(response_text)
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        # Try fallback to llama-3.1-8b-instant if the 70b model fails or is rate limited
        try:
            print("Trying fallback model llama-3.1-8b-instant...")
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You output JSON matching the requested schema."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=500
            )
            response_text = completion.choices[0].message.content
            return json.loads(response_text)
        except Exception as fallback_err:
            print(f"Fallback model also failed: {fallback_err}")
            return None

def process_raw_captures(base_dir):
    """Iterate over all raw files and run the classification pipeline."""
    raw_dir = os.path.join(base_dir, 'raw')
    wiki_dir = os.path.join(base_dir, 'wiki')
    
    if not os.path.exists(raw_dir):
        print(f"Error: raw/ folder does not exist at {raw_dir}")
        return
        
    client = get_groq_client()
    if client is None:
        print("WARNING: GROQ_API_KEY is not set. Using rule-based fallback local classifier.")
    
    # List all raw JSON files
    raw_files = [f for f in os.listdir(raw_dir) if f.endswith('.json')]
    
    if not raw_files:
        print("No raw capture JSON files found to classify.")
        return
        
    classified_count = 0
    for filename in raw_files:
        note_id = os.path.splitext(filename)[0]
        
        if is_already_classified(base_dir, note_id):
            continue
            
        json_path = os.path.join(raw_dir, filename)
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except Exception as e:
            print(f"Error reading raw capture {filename}: {e}")
            continue
            
        content_type = raw_data.get("type", "note")
        content = raw_data.get("content", "")
        timestamp = raw_data.get("timestamp", "")
        metadata = raw_data.get("metadata", {})
        
        # Limit content text passed to LLM for classification safety
        content_snippet = content[:8000] if content else ""
        
        print(f"Classifying raw capture: {note_id} ({content_type}) ...")
        if client is not None:
            classification = classify_content(client, content_type, content_snippet, metadata)
            if not classification:
                print(f"Warning: Groq LLM classification failed for {note_id}. Falling back to local heuristic classifier.")
                classification = mock_classify_content(content_type, content_snippet, metadata)
        else:
            classification = mock_classify_content(content_type, content_snippet, metadata)
        
        if not classification:
            print(f"Error: Failed to classify {note_id} even with fallback. Skipping.")
            continue
            
        # Parse out classifications
        title = classification.get("title", "Untitled Note")
        category = classification.get("category", "Resources")
        # Ensure category is standard
        if category not in ['Projects', 'Areas', 'Resources', 'Archives']:
            category = 'Resources'
            
        tags = classification.get("tags", [])
        summary = classification.get("summary", "No summary generated.")
        
        # Construct target path
        cat_dir = os.path.join(wiki_dir, category)
        os.makedirs(cat_dir, exist_ok=True)
        target_path = os.path.join(cat_dir, f"{note_id}.md")
        
        # Prepare frontmatter
        frontmatter = {
            "id": note_id,
            "title": title,
            "captured_at": timestamp,
            "category": category,
            "tags": tags,
            "summary": summary,
            "links": [] # Will be updated by link.py
        }
        
        # Format the markdown note
        yaml_str = yaml.dump(frontmatter, sort_keys=False, allow_unicode=True)
        markdown_content = f"---\n{yaml_str}---\n\n# {title}\n\n"
        
        if content_type == "link":
            url = metadata.get("url", "")
            markdown_content += f"*Source URL: [{url}]({url})*\n\n"
            markdown_content += f"## Web Page Content\n\n{content}\n"
        elif content_type == "file":
            stored_name = metadata.get("stored_filename", "")
            orig_name = metadata.get("original_filename", "")
            markdown_content += f"*Source File: `{orig_name}` (stored as `raw/{stored_name}`)*\n\n"
            markdown_content += f"## File Content\n\n{content}\n"
        else:
            markdown_content += f"{content}\n"
            
        try:
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"Saved note to wiki: wiki/{category}/{note_id}.md")
            classified_count += 1
        except Exception as e:
            print(f"Error saving classified note {note_id}: {e}")
            
    print(f"\nClassification run complete. Processed {classified_count} new notes.")

if __name__ == "__main__":
    base_directory = os.path.dirname(os.path.abspath(__file__))
    process_raw_captures(base_directory)
