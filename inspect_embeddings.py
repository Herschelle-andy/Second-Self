import os
import pickle

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pkl_path = os.path.join(base_dir, 'embeddings.pkl')
    
    if not os.path.exists(pkl_path):
        print(f"Error: embeddings.pkl not found at {pkl_path}")
        return
        
    try:
        with open(pkl_path, 'rb') as f:
            data = pickle.load(f)
            
        print("==================================================")
        print("        embeddings.pkl Inspection Results        ")
        print("==================================================")
        print(f"Total Notes Cached: {len(data)}")
        print(f"File Size: {os.path.getsize(pkl_path) / 1024:.2f} KB\n")
        
        # Display details for the first few notes
        for idx, (note_id, info) in enumerate(list(data.items())[:5]):
            print(f"{idx+1}. Note ID: {note_id}")
            print(f"   - File MTime: {info.get('mtime')}")
            emb = info.get('embedding')
            if emb is not None:
                print(f"   - Vector Shape: {emb.shape}")
                print(f"   - Vector Snippet (First 5 dimensions):")
                print(f"     {emb[:5]}")
            else:
                print("   - Warning: No embedding array found!")
            print("-" * 50)
            
        if len(data) > 5:
            print(f"... and {len(data) - 5} more notes in cache.")
            
    except Exception as e:
        print(f"Error reading embeddings.pkl: {e}")

if __name__ == "__main__":
    main()
