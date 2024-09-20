import re
import json

def parse_statblock(statblock_lines):
    """
    Parses a statblock and returns a dictionary of its fields.
    """
    statblock_text = '\n'.join(statblock_lines)
    fields = {}

    # Extract name from heading
    heading_line = statblock_lines[0]
    name_match = re.match(r'#+\s+(.*)', heading_line)
    if name_match:
        fields['Name'] = name_match.group(1).strip()

    # Extract Level and Type (e.g., **Level 3 Boss**)
    level_type_pattern = re.compile(r'\*\*(Level.*?)\*\*\s*(.*)')
    level_type_match = level_type_pattern.search(statblock_text)
    if level_type_match:
        fields['Level'] = level_type_match.group(1).replace('Level', '').strip()
        if level_type_match.group(2):
            fields['Type'] = level_type_match.group(2).strip()

    # Extract EV if present
    ev_match = re.search(r'\*\*EV\s*(\d+)\*\*', statblock_text)
    if ev_match:
        fields['EV'] = ev_match.group(1)

    # Extract other fields (e.g., **Stamina**: 120)
    field_pattern = re.compile(r'\*\*(.*?)\**:\**\s*(.*)')
    fields_found = field_pattern.findall(statblock_text)
    for field_name, field_value in fields_found:
        field_name = field_name.strip()
        field_value = field_value.strip()
        # Skip attributes and abilities
        if field_name not in ['Might', 'Agility', 'Reason', 'Intuition', 'Presence']:
            fields[field_name] = field_value

    # Extract attributes
    attr_pattern = re.compile(r'-\s*\*\*(.*?)\**[:：]?\**\s*([\+\-]?\d+)')
    attrs_found = attr_pattern.findall(statblock_text)
    attributes = {}
    for attr_name, attr_value in attrs_found:
        attributes[attr_name.strip()] = attr_value.strip()
    if attributes:
        fields['Attributes'] = attributes

    # Extract Abilities
    ability_pattern = re.compile(r'\*\*(.*?)\**(?:\s*◆\s*(.*?)\s*◆\s*(.*?))(?:\n\n|\Z)', re.DOTALL)
    abilities_found = ability_pattern.finditer(statblock_text)
    abilities = []
    for match in abilities_found:
        ability_name = match.group(1).strip()
        ability_details = match.group(0).strip()
        abilities.append({
            'Name': ability_name,
            'Details': ability_details
        })
    if abilities:
        fields['Abilities'] = abilities

    return fields

def format_statblock(fields):
    """
    Formats a statblock dictionary into a markdown string.
    """
    lines = []
    lines.append(f"#### {fields.get('Name', 'Unnamed Creature')}\n")

    # Level and Type
    level = fields.get('Level', '')
    type_ = fields.get('Type', '')
    if level or type_:
        lines.append(f"**Level {level}** {type_}\n")

    # Other fields
    for key in ['EV', 'Stamina', 'Immunity', 'Weakness', 'Speed', 'Size', 'Free Strike']:
        if key in fields:
            lines.append(f"**{key}**: {fields[key]}")

    lines.append('')

    # Attributes
    if 'Attributes' in fields:
        for attr_name, attr_value in fields['Attributes'].items():
            lines.append(f"- **{attr_name}**: {attr_value}")
        lines.append('')

    # Abilities
    if 'Abilities' in fields:
        for ability in fields['Abilities']:
            lines.append(ability['Details'])
            lines.append('')

    return '\n'.join(lines)

def process_markdown(input_file, output_file):
    """
    Reads the input markdown file, processes statblocks, and writes to the output file.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    statblocks = []
    current_statblock = []
    for line in lines:
        if line.startswith('####'):
            if current_statblock:
                statblocks.append(current_statblock)
                current_statblock = []
        current_statblock.append(line.strip('\n'))
    if current_statblock:
        statblocks.append(current_statblock)

    formatted_statblocks = []
    for statblock_lines in statblocks:
        fields = parse_statblock(statblock_lines)

        if fields['Name']:
            with open(f'../Bestiary/{fields["Name"]}.json', 'w', encoding='utf-8') as f:
                json.dump(fields, f, indent=4)

        formatted_statblock = format_statblock(fields)
        formatted_statblocks.append(formatted_statblock)

    with open(output_file, 'w', encoding='utf-8') as f:
        for statblock in formatted_statblocks:
            f.write(statblock)
            f.write('\n\n')

# Example usage:
input_markdown_file = '../Rules/Draw Steel Bestiary.md'
output_markdown_file = '../Rules/Draw Steel Bestiary - Formatted.md'
process_markdown(input_markdown_file, output_markdown_file)
