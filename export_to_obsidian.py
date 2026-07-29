import os
import re
import yaml
from lib.utils import load_yaml_frontmatter, save_yaml_frontmatter

def export_for_obsidian(wiki_dir):
    """Update all markdown files in the wiki to include native Obsidian Wikilinks in their body."""
    if not os.path.exists(wiki_dir):
        print(f"Error: wiki/ directory does not exist at {wiki_dir}")
        return
        
    print("Scanning wiki directory for notes...")
    notes_processed = 0
    
    # Walk through the wiki folder recursively
    for root, dirs, files in os.walk(wiki_dir):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                try:
                    # 1. Parse note
                    frontmatter, body = load_yaml_frontmatter(file_path)
                    if not frontmatter:
                        continue
                        
                    links = frontmatter.get("links", [])
                    if not isinstance(links, list):
                        links = []
                        
                    # 2. Clean previous 'Related Notes' section from the body
                    # Use a regex that matches ## Related Notes or ## Related and everything below it
                    cleaned_body = re.split(r'\n## Related Notes', body)[0].strip()
                    
                    # 3. If there are links, append Obsidian-compatible Wikilinks at the bottom
                    if links:
                        wikilinks_section = "\n\n## Related Notes\n"
                        for target_id in links:
                            wikilinks_section += f"- [[{target_id}]]\n"
                        new_body = cleaned_body + wikilinks_section
                    else:
                        new_body = cleaned_body
                        
                    # 4. Save note back
                    save_yaml_frontmatter(file_path, frontmatter, new_body)
                    notes_processed += 1
                except Exception as e:
                    print(f"Error updating note {file_path}: {e}")
                    
    print(f"\nObsidian export completed! Processed {notes_processed} notes.")
    print("You can now open the 'wiki/' folder directly in Obsidian as a vault.")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    wiki_directory = os.path.join(base_dir, 'wiki')
    export_for_obsidian(wiki_directory)
