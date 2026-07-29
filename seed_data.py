import os
import subprocess
import sys

def run_capture(args):
    cmd = [sys.executable, "capture.py"] + args
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    else:
        print(f"Output: {result.stdout.strip()}")

def main():
    print("Seeding test data into SecondSelf...")
    
    # 1. Capture notes
    run_capture(["note", "Idea: Build a browser extension for capturing bookmarks directly into SecondSelf API."])
    run_capture(["note", "Weekly shopping list: Organic milk, avocados, whole wheat bread, cold brew coffee, Greek yogurt."])
    run_capture(["note", "Project Alpha: Key contact is Sarah Connor (sarah@sky.net). Deadline for milestone 1 is next Friday."])
    run_capture(["note", "Learn: Local sentence-transformers embeddings are much faster than OpenAI API but require GPU memory for very large models."])
    run_capture(["note", "Workout plan: Mon/Wed/Fri - Strength training. Tue/Thu - Cardio & running 5k. Sat - Active recovery yoga."])
    run_capture(["note", "Financial Goals 2026: Save 30% of income. Maximize retirement contributions. Research index funds vs bonds."])
    run_capture(["note", "Recipe: Creamy Garlic Tuscan Chicken. Ingredients: chicken breast, heavy cream, chicken broth, garlic powder, Italian seasoning, spinach, sun-dried tomatoes."])
    run_capture(["note", "Archived Project: Legacy website redesign (Q4 2024). Completed launch in December, domain transferred."])
    run_capture(["note", "Project Alpha: Team alignment meeting notes. Sarah Connor to write technical spec. John Doe to set up repository."])
    
    # 2. Capture links
    run_capture(["link", "https://en.wikipedia.org/wiki/Force-directed_graph_drawing"])
    run_capture(["link", "https://python.org"])
    
    # 3. Capture file
    prob_stmt_path = os.path.abspath("../ProblemStatement.md")
    if os.path.exists(prob_stmt_path):
        run_capture(["file", prob_stmt_path])
    else:
        print(f"Warning: ProblemStatement.md not found at {prob_stmt_path}")

if __name__ == "__main__":
    main()
