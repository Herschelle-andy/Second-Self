import os
import sys
import json
import time
import shutil
import argparse
from datetime import datetime, timezone
import urllib.parse
import requests
from bs4 import BeautifulSoup

def setup_directories(base_dir):
    """Ensure raw/ and wiki/ directories exist."""
    raw_dir = os.path.join(base_dir, 'raw')
    wiki_dir = os.path.join(base_dir, 'wiki')
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(wiki_dir, exist_ok=True)
    return raw_dir, wiki_dir

def generate_id(prefix):
    """Generate a unique ID based on current timestamp and fractional seconds."""
    timestamp = int(time.time() * 1000)
    return f"{prefix}_{timestamp}"

def capture_note(raw_dir, content):
    """Capture a plain text note and save to raw/."""
    note_id = generate_id("note")
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    data = {
        "id": note_id,
        "type": "note",
        "timestamp": timestamp,
        "content": content,
        "metadata": {}
    }
    
    file_path = os.path.join(raw_dir, f"{note_id}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully captured note: {note_id}")
    return note_id

def capture_link(raw_dir, url):
    """Capture a URL, fetch its title/content, and save to raw/."""
    # Validate/Format URL
    parsed_url = urllib.parse.urlparse(url)
    if not parsed_url.scheme:
        url = "https://" + url
        parsed_url = urllib.parse.urlparse(url)
    
    link_id = generate_id("link")
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    print(f"Fetching URL: {url} ...")
    content = ""
    title = url
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        # Get text
        text = soup.get_text()
        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        content = "\n".join(chunk for chunk in chunks if chunk)
    except Exception as e:
        print(f"Warning: Failed to fetch full page content: {e}. Storing URL link only.")
        content = f"Link to: {url}. (Fetch failed)"
        title = url
        
    data = {
        "id": link_id,
        "type": "link",
        "timestamp": timestamp,
        "content": content,
        "metadata": {
            "url": url,
            "title": title
        }
    }
    
    file_path = os.path.join(raw_dir, f"{link_id}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully captured link: {link_id} - Title: {title}")
    return link_id

def capture_file(raw_dir, source_file_path):
    """Capture a file by copying it to raw/ and saving a metadata entry."""
    if not os.path.exists(source_file_path):
        print(f"Error: File '{source_file_path}' does not exist.")
        sys.exit(1)
        
    file_id = generate_id("file")
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    original_filename = os.path.basename(source_file_path)
    # Target filename in raw/ starts with unique file_id to avoid collision
    target_filename = f"{file_id}_{original_filename}"
    target_file_path = os.path.join(raw_dir, target_filename)
    
    print(f"Copying file to: {target_file_path} ...")
    shutil.copy2(source_file_path, target_file_path)
    
    # Check if we can extract text content if it's text-based
    content = ""
    # Check extension
    _, ext = os.path.splitext(original_filename.lower())
    if ext in ['.txt', '.md', '.json', '.html', '.csv']:
        try:
            with open(source_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            content = f"Error reading text content: {e}"
    else:
        # Non-text file (PDF, Docx, Image)
        # Note: Week 2 classifer or helper scripts can extract text using specialized libraries
        content = f"Binary/Document file: {original_filename}. Raw file path: {target_filename}"
        
    data = {
        "id": file_id,
        "type": "file",
        "timestamp": timestamp,
        "content": content,
        "metadata": {
            "original_path": os.path.abspath(source_file_path),
            "original_filename": original_filename,
            "stored_filename": target_filename,
            "extension": ext
        }
    }
    
    file_path = os.path.join(raw_dir, f"{file_id}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully captured file: {file_id} - {original_filename}")
    return file_id

def main():
    parser = argparse.ArgumentParser(description="SecondSelf Capture Pipeline: Capture notes, links, and files.")
    parser.add_argument("type", choices=["note", "link", "file"], help="Type of content to capture")
    parser.add_argument("content", help="The note text, URL to capture, or path to the file")
    
    args = parser.parse_args()
    
    # Determine base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir, _ = setup_directories(base_dir)
    
    if args.type == "note":
        capture_note(raw_dir, args.content)
    elif args.type == "link":
        capture_link(raw_dir, args.content)
    elif args.type == "file":
        capture_file(raw_dir, args.content)

if __name__ == "__main__":
    main()
