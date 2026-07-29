import os
import pickle

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pkl_path = os.path.join(base_dir, 'embeddings.pkl')
    report_path = os.path.join(base_dir, 'embeddings_report.txt')
    
    if not os.path.exists(pkl_path):
        print(f"Error: embeddings.pkl not found at {pkl_path}")
        print("Please run 'python link.py' first to generate the embeddings.")
        return
        
    try:
        # Load the binary pickle file
        with open(pkl_path, 'rb') as f:
            data = pickle.load(f)
            
        print(f"Loading {len(data)} embeddings from {pkl_path}...")
        
        # Write the human-readable embeddings to a text file
        with open(report_path, 'w', encoding='utf-8') as out:
            out.write("==================================================\n")
            out.write("       SecondSelf Embeddings Report (Full Vectors) \n")
            out.write("==================================================\n\n")
            out.write(f"Total Notes Cached: {len(data)}\n")
            out.write(f"Vector Dimensions: 384 (all-MiniLM-L6-v2)\n\n")
            
            for idx, (note_id, info) in enumerate(data.items()):
                out.write(f"--- Note #{idx+1} ---\n")
                out.write(f"ID: {note_id}\n")
                out.write(f"Timestamp/MTime: {info.get('mtime')}\n")
                
                emb = info.get('embedding')
                if emb is not None:
                    out.write(f"Embedding Vector (384 dimensions):\n")
                    # Format vector elements for readability (8 per line)
                    elements = [f"{x:.6f}" for x in emb]
                    chunked_elements = [elements[i:i+8] for i in range(0, len(elements), 8)]
                    for chunk in chunked_elements:
                        out.write(f"  [{', '.join(chunk)}]\n")
                else:
                    out.write("No embedding vector found.\n")
                out.write("\n" + "="*50 + "\n\n")
                
        print(f"Success! Human-readable report written to: {report_path}")
        print("You can open this file in your editor to view the full embedding vectors.")
        
    except Exception as e:
        print(f"Error processing embeddings: {e}")

if __name__ == "__main__":
    main()
