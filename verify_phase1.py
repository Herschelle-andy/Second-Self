import os
import json
import shutil
import unittest
from datetime import datetime
import capture

class TestPhase1Capture(unittest.TestCase):
    
    def setUp(self):
        """Set up temporary raw and wiki directories."""
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_raw_dir = os.path.join(self.base_dir, 'test_raw')
        self.test_wiki_dir = os.path.join(self.base_dir, 'test_wiki')
        os.makedirs(self.test_raw_dir, exist_ok=True)
        os.makedirs(self.test_wiki_dir, exist_ok=True)

    def tearDown(self):
        """Clean up temporary test directories."""
        if os.path.exists(self.test_raw_dir):
            shutil.rmtree(self.test_raw_dir)
        if os.path.exists(self.test_wiki_dir):
            shutil.rmtree(self.test_wiki_dir)

    def test_capture_note(self):
        """Test note capturing produces valid JSON and correct schema."""
        test_content = "This is a unit test note content."
        note_id = capture.capture_note(self.test_raw_dir, test_content)
        
        # Verify file exists
        expected_file = os.path.join(self.test_raw_dir, f"{note_id}.json")
        self.assertTrue(os.path.exists(expected_file), "Capture file was not created.")
        
        # Validate schema
        with open(expected_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.assertEqual(data["id"], note_id)
        self.assertEqual(data["type"], "note")
        self.assertEqual(data["content"], test_content)
        self.assertTrue("timestamp" in data)
        self.assertEqual(data["metadata"], {})
        
        # Check timestamp format (ISO 8601 UTC ending with Z)
        self.assertTrue(data["timestamp"].endswith("Z"))
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

    def test_capture_link(self):
        """Test url capture and basic HTML cleaning."""
        # We'll test with python.org which is highly reliable
        url = "https://python.org"
        link_id = capture.capture_link(self.test_raw_dir, url)
        
        expected_file = os.path.join(self.test_raw_dir, f"{link_id}.json")
        self.assertTrue(os.path.exists(expected_file), "Link capture file was not created.")
        
        with open(expected_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.assertEqual(data["id"], link_id)
        self.assertEqual(data["type"], "link")
        self.assertEqual(data["metadata"]["url"], url)
        self.assertTrue(len(data["metadata"]["title"]) > 0)
        self.assertTrue(len(data["content"]) > 0)
        
        # Ensure scripts are decompiled / not present in scraped body content
        self.assertNotIn("<script>", data["content"])
        self.assertNotIn("</script>", data["content"])

    def test_capture_file(self):
        """Test copy and reading of local text files."""
        # Create a mock text file
        dummy_file_path = os.path.join(self.base_dir, "dummy_test_file.txt")
        dummy_content = "Mock file content for verification."
        with open(dummy_file_path, 'w', encoding='utf-8') as f:
            f.write(dummy_content)
            
        try:
            file_id = capture.capture_file(self.test_raw_dir, dummy_file_path)
            
            expected_json = os.path.join(self.test_raw_dir, f"{file_id}.json")
            self.assertTrue(os.path.exists(expected_json), "Metadata JSON was not created.")
            
            with open(expected_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.assertEqual(data["id"], file_id)
            self.assertEqual(data["type"], "file")
            self.assertEqual(data["content"], dummy_content)
            self.assertEqual(data["metadata"]["original_filename"], "dummy_test_file.txt")
            
            # Verify file was copied to raw folder
            expected_copied_file = os.path.join(self.test_raw_dir, data["metadata"]["stored_filename"])
            self.assertTrue(os.path.exists(expected_copied_file), "Copied source file not found in raw/ folder.")
        finally:
            if os.path.exists(dummy_file_path):
                os.remove(dummy_file_path)

if __name__ == "__main__":
    print("==================================================")
    print("Running Automated Verification Suite for Phase 1...")
    print("==================================================")
    unittest.main()
