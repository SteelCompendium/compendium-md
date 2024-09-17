import os
import re
import sys

def find_markdown_files(directory):
    """Find all markdown files in a given directory."""
    markdown_files = []
    for root, a, files in os.walk(directory):
        # TODO - these should be taken in as script args
        if "../Rules" in root:
            continue
        for file in files:
            if file.endswith(".md"):
                markdown_files.append(os.path.join(root, file))
    return markdown_files

def read_file_with_encoding_fallback(file_path):
    """Read file with a fallback for encoding issues."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='ISO-8859-1') as file:
            return file.read()

def update_ability_tables(file_path):
    """Update ability tables in a markdown file."""
    try:
        content = read_file_with_encoding_fallback(file_path)
        original_content = content

        # Define the keys of interest
        keys_of_interest = ['Keywords', 'Type', 'Distance', 'Target']
        key_values = {}
        positions_to_remove = []

        # Define the pattern to match key-value pairs at the start of a line
        pattern = r'^\*\*(.+?)\**:\**\s*(.+)$'

        # Find all matches
        for match in re.finditer(pattern, content, flags=re.MULTILINE):
            key = match.group(1).strip()
            value = match.group(2).strip()
            if key in keys_of_interest:
                key_values[key] = value
                positions_to_remove.append((match.start(), match.end()))

        if not positions_to_remove:
            # No keys found; no modification needed
            return

        # Remove the key-value pairs from the content
        positions_to_remove.sort(reverse=True)
        for start, end in positions_to_remove:
            content = content[:start] + content[end:]

        # Find the earliest position to insert the table
        insert_position = min(start for start, _ in positions_to_remove)

        # Create the markdown table
        keywords = key_values.get('Keywords', '')
        type_ = key_values.get('Type', '')
        distance = key_values.get('Distance', '')
        target = key_values.get('Target', '')

        table = (
            f'| **Keywords:** {keywords} | **Type:** {type_} |\n'
            f'| {"-" * max(len(keywords) + 18, 35)} | {"-" * max(len(type_) + 14, 32)} |\n'
            f'| **Distance:** {distance} | **Target:** {target} |'
        )

        # Insert the table into the content
        content = content[:insert_position] + table + '\n' + content[insert_position:]

        # Only write changes if there are any updates
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"Updated ability tables in file: {file_path}")
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

def update_all_notes(directory):
    """Update all notes in the Obsidian vault directory."""
    markdown_files = find_markdown_files(directory)

    for file_path in markdown_files:
        update_ability_tables(file_path)
    print(f"Abilitiy Tables formatted successfully in directory: {directory}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python format_ability_tables.py <directory_path>")
        sys.exit(1)

    vault_directory = sys.argv[1]

    if not os.path.isdir(vault_directory):
        print(f"Error: The directory {vault_directory} does not exist.")
        sys.exit(1)

    update_all_notes(vault_directory)
