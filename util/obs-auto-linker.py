import os
import re
import sys

def find_markdown_files(directory):
    """Find all markdown files in a given directory."""
    markdown_files = []
    for root, a, files in os.walk(directory):
        # TODO - these should be taken in as script args
        if "../Rules" in root or "../Cultures" in root or "../Skills" in root or "../util" in root:
            continue
        for file in files:
            if file.endswith(".md"):
                markdown_files.append(os.path.join(root, file))
    return markdown_files

def get_note_titles(markdown_files):
    """Extract note titles (without extension) from a list of markdown files."""
    note_titles = set()
    for file in markdown_files:
        title = os.path.basename(file).replace(".md", "")
        note_titles.add(title)
    return note_titles

def read_file_with_encoding_fallback(file_path):
    """Read file with a fallback for encoding issues."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='ISO-8859-1') as file:
            return file.read()

def update_unlinked_references_in_file(file_path, note_titles):
    """Update unlinked references in a markdown file by converting them to Obsidian links."""
    try:
        content = read_file_with_encoding_fallback(file_path)
        original_content = content

        # Search for potential note references (any of the note titles found in the directory)
        for title in note_titles:
            # Don't add links to self
            if title.lower() in os.path.splitext(os.path.basename(file_path))[0].lower():
                continue

            # This regex looks for the note title as a standalone word (case-insensitive, not in [[ ]] links)
            pattern = r'(?<!\[\[)\b({})\b(?!\]\])'.format(re.escape(title))

            # Define a replacement function to handle casing and create alias if needed
            def replace_with_link(match):
                found_text = match.group(0)
                if found_text != title:
                    # If the found text case doesn't match the title, create an alias
                    return f'[[{title}|{found_text}]]'
                return f'[[{title}]]'

            # Replace any found references with Obsidian-style links, handling case and alias
            content = re.sub(pattern, replace_with_link, content, flags=re.IGNORECASE)

        # Only write changes if there are any updates
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"Updated links in file: {file_path}")
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

def update_all_notes(directory):
    """Update all notes in the Obsidian vault directory."""
    markdown_files = find_markdown_files(directory)
    note_titles = get_note_titles(markdown_files)

    for file_path in markdown_files:
        update_unlinked_references_in_file(file_path, note_titles)
    print(f"Links updated successfully in directory: {directory}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python obs-auto-linker.py <directory_path>")
        sys.exit(1)

    vault_directory = sys.argv[1]

    if not os.path.isdir(vault_directory):
        print(f"Error: The directory {vault_directory} does not exist.")
        sys.exit(1)

    update_all_notes(vault_directory)
