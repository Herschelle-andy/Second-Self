import os
import json
from lib.utils import load_yaml_frontmatter

def build_graph_data(wiki_dir, output_path):
    """Scan the wiki directory, read YAML frontmatters, and compile nodes and edges."""
    if not os.path.exists(wiki_dir):
        print(f"Wiki directory does not exist: {wiki_dir}")
        return
        
    nodes = []
    edges_set = set() # To store unique undirected links
    valid_ids = set() # To ensure we only create edges to notes that exist
    note_details = {} # Map ID to frontmatter details
    
    # First pass: Gather all existing notes and their IDs
    for root, dirs, files in os.walk(wiki_dir):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                try:
                    frontmatter, _ = load_yaml_frontmatter(file_path)
                    if frontmatter:
                        note_id = frontmatter.get("id")
                        if note_id:
                            valid_ids.add(note_id)
                            note_details[note_id] = frontmatter
                except Exception as e:
                    print(f"Error parsing note {file_path} for graph: {e}")
                    
    # Second pass: Build node and edge models
    for note_id, fm in note_details.items():
        title = fm.get("title", "Untitled Note")
        category = fm.get("category", "Resources")
        summary = fm.get("summary", "")
        tags = fm.get("tags", [])
        
        # Define node
        nodes.append({
            "id": note_id,
            "label": title,
            "category": category,
            "summary": summary,
            "tags": tags
        })
        
        # Retrieve links
        links = fm.get("links", [])
        if isinstance(links, list):
            for target_id in links:
                if target_id in valid_ids:
                    # Represent edge uniquely as sorted tuple of IDs
                    edge_tuple = tuple(sorted([note_id, target_id]))
                    edges_set.add(edge_tuple)
                    
    # Format edges for vis-network / Cytoscape
    edges = [{"from": edge[0], "to": edge[1]} for edge in edges_set]
    
    graph_data = {
        "nodes": nodes,
        "edges": edges
    }
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
        print(f"Graph construction complete. Saved {len(nodes)} nodes and {len(edges)} edges to {output_path}")
    except Exception as e:
        print(f"Error saving graph JSON: {e}")

if __name__ == "__main__":
    base_directory = os.path.dirname(os.path.abspath(__file__))
    wiki_directory = os.path.join(base_directory, 'wiki')
    output_json_path = os.path.join(base_directory, 'graph.json')
    
    build_graph_data(wiki_directory, output_json_path)
