import os
import json
import shutil
import unittest
import yaml
import classify
import link

class TestPhase2Organization(unittest.TestCase):
    
    def setUp(self):
        """Setup isolated raw and wiki folders for integration testing."""
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_raw_dir = os.path.join(self.base_dir, 'test_raw_p2')
        self.test_wiki_dir = os.path.join(self.base_dir, 'test_wiki_p2')
        os.makedirs(self.test_raw_dir, exist_ok=True)
        os.makedirs(self.test_wiki_dir, exist_ok=True)

    def tearDown(self):
        """Clean up test folders."""
        if os.path.exists(self.test_raw_dir):
            shutil.rmtree(self.test_raw_dir)
        if os.path.exists(self.test_wiki_dir):
            shutil.rmtree(self.test_wiki_dir)

    def create_mock_capture(self, note_id, note_type, content, title=None):
        data = {
            "id": note_id,
            "type": note_type,
            "timestamp": "2026-07-26T12:00:00Z",
            "content": content,
            "metadata": {"title": title} if title else {}
        }
        file_path = os.path.join(self.test_raw_dir, f"{note_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def test_end_to_end_classification_and_linking(self):
        """Verify sorting, tagging, structure, and semantic link updates."""
        # 1. Create three raw staging files
        # Note 1 & Note 3 are highly related (Project Alpha Spec)
        # Note 2 is unrelated (Workout routine)
        self.create_mock_capture("test_note_01", "note", "Project Alpha: Key specifications and target milestones for deployment.")
        self.create_mock_capture("test_note_02", "note", "Strength training workout routines and weekly fitness schedules.")
        self.create_mock_capture("test_note_03", "note", "Technical specifications for Project Alpha team deployment milestones.")
        
        # Override paths in classify and run it
        # We temporarily point the functions to our test directories
        print("\n[Test] Running rule-based classification fallback...")
        
        # We temporarily mock the directories in classify.py for process_raw_captures
        # We can implement a tiny inline run to isolate directories safely
        client = classify.get_groq_client()
        for filename in os.listdir(self.test_raw_dir):
            note_id = os.path.splitext(filename)[0]
            with open(os.path.join(self.test_raw_dir, filename), 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                
            content = raw_data["content"]
            metadata = raw_data["metadata"]
            
            if client is not None:
                res = classify.classify_content(client, "note", content, metadata)
            else:
                res = classify.mock_classify_content("note", content, metadata)
                
            category = res["category"]
            self.assertIn(category, ['Projects', 'Areas', 'Resources', 'Archives'])
            
            # Save notes to test_wiki
            cat_dir = os.path.join(self.test_wiki_dir, category)
            os.makedirs(cat_dir, exist_ok=True)
            target_path = os.path.join(cat_dir, f"{note_id}.md")
            
            frontmatter = {
                "id": note_id,
                "title": res["title"],
                "captured_at": raw_data["timestamp"],
                "category": category,
                "tags": res["tags"],
                "summary": res["summary"],
                "links": []
            }
            yaml_str = yaml.dump(frontmatter, sort_keys=False, allow_unicode=True)
            with open(target_path, 'w', encoding='utf-8') as out_f:
                out_f.write(f"---\n{yaml_str}---\n\n# {res['title']}\n\n{content}")

        # Verify correct category placement
        # Projects should contain test_note_01 and test_note_03
        # Areas should contain test_note_02
        self.assertTrue(os.path.exists(os.path.join(self.test_wiki_dir, "Projects", "test_note_01.md")))
        self.assertTrue(os.path.exists(os.path.join(self.test_wiki_dir, "Areas", "test_note_02.md")))
        self.assertTrue(os.path.exists(os.path.join(self.test_wiki_dir, "Projects", "test_note_03.md")))
        
        # 2. Run semantic linking
        print("[Test] Running semantic embeddings auto-linking...")
        link.link_notes(self.test_wiki_dir, similarity_threshold=0.5)
        
        # Verify linking results
        # test_note_01 and test_note_03 should be bidirectionally linked
        # test_note_02 should have no links
        with open(os.path.join(self.test_wiki_dir, "Projects", "test_note_01.md"), 'r', encoding='utf-8') as f:
            n1_content = f.read()
        with open(os.path.join(self.test_wiki_dir, "Areas", "test_note_02.md"), 'r', encoding='utf-8') as f:
            n2_content = f.read()
        with open(os.path.join(self.test_wiki_dir, "Projects", "test_note_03.md"), 'r', encoding='utf-8') as f:
            n3_content = f.read()
            
        n1_fm = yaml.safe_load(n1_content.split('---')[1])
        n2_fm = yaml.safe_load(n2_content.split('---')[1])
        n3_fm = yaml.safe_load(n3_content.split('---')[1])
        
        self.assertIn("test_note_03", n1_fm["links"], "test_note_01 is missing link to test_note_03.")
        self.assertIn("test_note_01", n3_fm["links"], "test_note_03 is missing link to test_note_01.")
        self.assertEqual(len(n2_fm["links"]), 0, "test_note_02 (workout) should not be linked to project specs.")
        print("[Test] Verification complete: Bidirectional links populated correctly!")

if __name__ == "__main__":
    print("==================================================")
    print("Running Automated Verification Suite for Phase 2...")
    print("==================================================")
    unittest.main()
