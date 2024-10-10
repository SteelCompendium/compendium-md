import os
import re
import sys
from md_statblock_to_yaml import process_markdown
import yaml

def has_statblock_stuff(markdown_line):
    return any(word in markdown_line for word in ["Speed", "Level", "EV", "Size", "Free Strike"])

def extract_statblocks(markdown_text):
    """
    Extracts statblocks from a markdown document.

    Args:
        markdown_text (str): The markdown document as a string.

    Returns:
        List[str]: A list of statblock texts.
    """
    # Split the document into lines
    lines = markdown_text.split('\n')
    statblocks = []
    current_statblock = []
    current_statblock_confidence = 0
    inside_statblock = False


    # Define a regex pattern to match headers of various levels
    header_pattern = re.compile(r'^(#{1,6})\s*(.+)$')

    # The header level that indicates the start of a statblock
    statblock_header_level = 4

    # number of "statblock stuff" is required to count the markdown section as a statblock (see has_statblock_stuff)
    required_statblock_confidence = 5

    # Iterate over each line
    for i, line in enumerate(lines):
        stripped_line = line.strip()

        # Check if the line is a header
        header_match = header_pattern.match(stripped_line)
        if header_match:
            header_level = len(header_match.group(1))
            header_text = header_match.group(2).strip()

            # If the header is at the statblock level, it indicates the start of a statblock
            if header_level == statblock_header_level:
                # If we were inside a statblock, save it before starting a new one
                if inside_statblock and current_statblock:
                    if current_statblock_confidence >= required_statblock_confidence:
                        statblocks.append('\n'.join(current_statblock))
                    current_statblock = []
                    current_statblock_confidence = 0

                # Start a new statblock
                inside_statblock = True
                current_statblock.append(line)
                if has_statblock_stuff(line):
                    current_statblock_confidence += 1
            else:
                # If we encounter a header of any other level while inside a statblock,
                # we continue collecting lines as part of the statblock
                if inside_statblock:
                    current_statblock.append(line)
                    if has_statblock_stuff(line):
                        current_statblock_confidence += 1
                else:
                    # Not inside a statblock, skip
                    continue
        else:
            if inside_statblock:
                current_statblock.append(line)
                if has_statblock_stuff(line):
                    current_statblock_confidence += 1

    # Add the last statblock if the document ends without a new header
    if inside_statblock and current_statblock:
        if current_statblock_confidence >= required_statblock_confidence:
            statblocks.append('\n'.join(current_statblock))

    return statblocks

def get_statblock_name(statblock_text):
    """
    Extracts the name of the statblock from the header line.

    Args:
        statblock_text (str): The markdown text of the statblock.

    Returns:
        str: The name of the statblock.
    """
    lines = statblock_text.strip().split('\n')
    for line in lines:
        line = line.strip()
        header_match = re.match(r'^#{4}\s*(.+)$', line)
        if header_match:
            name = header_match.group(1).strip()
            # Remove any characters that are invalid in filenames
            name = re.sub(r'[\\/:"*?<>|]+', '', name)
            return name
    return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python extract_statblocks.py <input_markdown_file>")
        sys.exit(1)

    input_markdown_file = sys.argv[1]

    # Read the input markdown file
    with open(input_markdown_file, 'r', encoding='utf-8') as f:
        markdown_text = f.read()

    # Extract statblocks
    statblocks = extract_statblocks(markdown_text)

    # Ensure output directories exist
    markdown_output_dir = os.path.join('..', 'bestiary', 'markdown')
    yaml_output_dir = os.path.join('..', 'bestiary', 'yaml')
    os.makedirs(markdown_output_dir, exist_ok=True)
    os.makedirs(yaml_output_dir, exist_ok=True)

    for statblock_text in statblocks:
        # Get the statblock name
        name = get_statblock_name(statblock_text)
        if not name:
            print("Skipping statblock with no name")
            continue

        # Process the markdown to get YAML
        try:
            yaml_string = process_markdown(statblock_text)
            data = yaml.safe_load(yaml_string)
            if not data.get('name'):
                print(f"Skipping statblock: {name} (parsing failed or no name)")
                continue
            name = data.get('name')
        except Exception as e:
            print(f"Error parsing statblock: {name}, {e}")
            continue

        print(f"Processing statblock: {name}")

        # Write the markdown to file
        markdown_filename = f"{name}.md"
        markdown_filepath = os.path.join(markdown_output_dir, markdown_filename)
        with open(markdown_filepath, 'w', encoding='utf-8') as md_file:
            md_file.write(statblock_text)

        # Write the YAML to file
        yaml_filename = f"{name}.yaml"
        yaml_filepath = os.path.join(yaml_output_dir, yaml_filename)
        with open(yaml_filepath, 'w', encoding='utf-8') as yaml_file:
            yaml_file.write(yaml_string)

if __name__ == "__main__":
    main()
