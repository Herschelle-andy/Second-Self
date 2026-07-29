import os
import json
import shutil
import unittest
import yaml
import build_graph

class TestPhase3Graph(unittest.TestCase):
    
    def setUp(self):
        """Set up dynamic wiki structures."""
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_wiki_dir = os.path.join(self.base_dir, 'test_wiki_p3')
        self.test_output_json = os.path.join(self.base_dir, 'test_graph_p3.json')
        os.makedirs(self.test_wiki_dir, exist_ok=True)

    def tearDown(self):
        """Clean up generated test artifacts."""
        if os.path.exists(self.test_wiki_dir):
            shutil.rmtree(self.test_wiki_dir)
        if os.path.exists(self.test_output_json):
            os.remove(self.test_output_json)

    def write_mock_note(self, note_id, title, category, links):
        cat_dir = os.path.join(self.test_wiki_dir, category)
        os.makedirs(cat_dir, exist_ok=True)
        
        frontmatter = {
            "id": note_id,
            "title": title,
            "category": category,
            "summary": f"Summary for {title}",
            "tags": ["test", category.lower()],
            "links": links
        }
        
        file_path = os.path.join(cat_dir, f"{note_id}.md")
        yaml_str = yaml.dump(frontmatter, sort_keys=False, allow_unicode=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"---\n{yaml_str}---\n\n# {title}\n\nBody content.")

    def test_graph_compilation_integrity(self):
        """Ensure correct node extraction, valid edges filtering, and unique mapping."""
        # 1. Create a circular relationship structure:
        # Note A (Projects) -> linked to B, C
        # Note B (Areas) -> linked to A
        # Note C (Resources) -> linked to A
        # Note D (Archives) -> linked to E (but E doesn't exist, so this should be filtered out!)
        self.write_mock_note("note_a", "Note A", "Projects", ["note_b", "note_c"])
        self.write_mock_note("note_b", "Note B", "Areas", ["note_a"])
        self.write_mock_note("note_c", "Note C", "Resources", ["note_a"])
        self.write_mock_note("note_d", "Note D", "Archives", ["note_non_existent"])
        
        # 2. Run graph builder function
        build_graph.build_graph_data(self.test_wiki_dir, self.test_output_json)
        
        # 3. Read and check output JSON
        self.assertTrue(os.path.exists(self.test_output_json), "graph.json was not created.")
        with open(self.test_output_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        
        # Check nodes
        self.assertEqual(len(nodes), 4, f"Expected 4 nodes, got {len(nodes)}.")
        node_ids = {node["id"] for node in nodes}
        self.assertEqual(node_ids, {"note_a", "note_b", "note_c", "note_d"})
        
        # Verify node categorization
        a_node = next(n for n in nodes if n["id"] == "note_a")
        self.assertEqual(a_node["label"], "Note A")
        self.assertEqual(a_node["category"], "Projects")
        
        # Check edges (should have exactly 2 undirected edges: A-B and A-C. A-D should not exist)
        # Verify non-existent note edge was ignored
        self.assertEqual(len(edges), 2, f"Expected 2 edges, got {len(edges)}.")
        
        # Check edge targets
        for edge in edges:
            self.assertIn(edge["from"], {"note_a", "note_b", "note_c"})
            self.assertIn(edge["to"], {"note_a", "note_b", "note_c"})
            self.assertNotEqual(edge["from"], edge["to"], "Self loop edge found.")
            
        print("[Test] Graph compilation verified. Edges properly validated and exported successfully!")

if __name__ == "__main__":
    print("==================================================")
    print("Running Automated Verification Suite for Phase 3...")
    print("==================================================")
    unittest.main()
