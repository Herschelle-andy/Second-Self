import os
import shutil
import unittest
import yaml
import ask

class TestPhase4Oracle(unittest.TestCase):
    
    def setUp(self):
        """Setup isolated wiki folder for testing RAG querying."""
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_wiki_dir = os.path.join(self.base_dir, 'test_wiki_p4')
        os.makedirs(self.test_wiki_dir, exist_ok=True)

    def tearDown(self):
        """Clean up test folders."""
        if os.path.exists(self.test_wiki_dir):
            shutil.rmtree(self.test_wiki_dir)

    def write_mock_note(self, note_id, title, category, content):
        cat_dir = os.path.join(self.test_wiki_dir, category)
        os.makedirs(cat_dir, exist_ok=True)
        
        frontmatter = {
            "id": note_id,
            "title": title,
            "category": category,
            "summary": f"Summary details of {title}",
            "tags": ["test"],
            "links": []
        }
        
        file_path = os.path.join(cat_dir, f"{note_id}.md")
        yaml_str = yaml.dump(frontmatter, sort_keys=False, allow_unicode=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"---\n{yaml_str}---\n\n# {title}\n\n{content}")

    def test_rag_query_retrieval_and_synthesis(self):
        """Verify embeddings search selects correct note and Groq synthesizes response."""
        # Check API key first
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            print("[Test] Skipping RAG verification: GROQ_API_KEY is not configured.")
            return

        # 1. Create a note with a highly specific piece of fact/content
        fact_note_id = "fact_note_101"
        fact_title = "Secret Vault Protocols"
        fact_content = "The passcode to open the main server vault door is 554433. Do not share this sequence."
        self.write_mock_note(fact_note_id, fact_title, "Projects", fact_content)
        
        # 2. Add an irrelevant note
        self.write_mock_note("unrelated_102", "Grocery Purchases", "Resources", "Buy apples, milk, and bread.")

        # 3. Query RAG engine
        print("\n[Test] Running RAG vector retrieval & Llama-3 synthesis...")
        query = "What is the passcode to open the vault door?"
        answer, sources = ask.ask_brain(query, self.test_wiki_dir, top_k=2)
        
        print(f"Query: '{query}'")
        print(f"Answer: '{answer}'")
        print("Sources:")
        for src in sources:
            print(f"- {src['title']} (Score: {src['score']:.3f})")
            
        # 4. Assertions
        # Verify the fact note was retrieved as a source
        source_ids = {src["id"] for src in sources}
        self.assertIn(fact_note_id, source_ids, "Fact note was not retrieved by cosine similarity search.")
        
        # Verify the answer contains the passcode
        self.assertIn("554433", answer, "Answer synthesized by Groq failed to state the passcode.")
        print("[Test] Verification complete: RAG answers synthesized correctly with citations!")

if __name__ == "__main__":
    print("==================================================")
    print("Running Automated Verification Suite for Phase 4...")
    print("==================================================")
    unittest.main()
