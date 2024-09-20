import re
import json

def clean_field(field_name):
    return field_name.lower().replace("*", "").strip()

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
        fields['name'] = name_match.group(1).strip()

    # Extract Level and Type (e.g., **Level 3 Boss**)
    level_type_pattern = re.compile(r'\*\*(Level\s+?)\*\*\s*(\d+)\s+(.*)')
    level_type_match = level_type_pattern.search(statblock_text)
    if level_type_match:
        fields['level'] = level_type_match.group(1).replace('Level', '').strip()
        if level_type_match.group(2):
            fields['type'] = level_type_match.group(2).strip()

    # Extract EV if present
    ev_match = re.search(r'\*\*EV\s*(\d+)\*\*', statblock_text)
    if ev_match:
        fields['encounter_value'] = ev_match.group(1)

    # Extract other fields (e.g., **Stamina**: 120)
    field_pattern = re.compile(r'\*\*(.*?)\**:\**\s*(.*)')
    fields_found = field_pattern.findall(statblock_text)
    for field_name, field_value in fields_found:
        field_name = clean_field(field_name)
        field_value = clean_field(field_value)
        # Skip attributes and abilities
        if field_name not in ['might', 'agility', 'reason', 'intuition', 'presence']:
            fields[field_name] = field_value

    # Extract characteristics
    char_pattern = re.compile(r'-\s*\*\*(.*?)\**[:：]?\**\s*([\+\-]?\d+)')
    chars_found = char_pattern.findall(statblock_text)
    characteristics = {}
    for char_name, char_value in chars_found:
        characteristics[clean_field(char_name)] = clean_field(char_value)
    if characteristics:
        fields['characteristics'] = characteristics

    # Extract Abilities
    #ability_pattern = re.compile(r'\*\*(.*?)\**(?:\s*◆\s*(.*?)\s*◆\s*(.*?))(?:\n\n|\Z)', re.DOTALL | re.MULTILINE)
    ability_pattern = re.compile(r'\*\*(.*)\*\*', re.DOTALL | re.MULTILINE)
    abilities_found = ability_pattern.finditer(statblock_text)
    abilities = []
    for match in abilities_found:
        ability_name = match.group(1).strip()
        ability_details = match.group(0).strip()
        abilities.append({
            'name': ability_name,
            'details': ability_details
        })
    if abilities:
        fields['abilities'] = abilities

    return fields

def format_statblock(fields):
    """
    Formats a statblock dictionary into a markdown string.
    """
    lines = []
    lines.append(f"#### {fields.get('name', 'Unnamed Creature')}\n")

    # Level and Type
    level = fields.get('level', '')
    type_ = fields.get('type', '')
    if level or type_:
        lines.append(f"**Level {level}** {type_}\n")

    # Other fields
    for key in ['encounter_value', 'stamina', 'immunity', 'weakness', 'speed', 'size', 'free_strike']:
        if key in fields:
            lines.append(f"**{key}**: {fields[key]}")

    lines.append('')

    # Attributes
    if 'attributes' in fields:
        for attr_name, attr_value in fields['attributes'].items():
            lines.append(f"- **{attr_name}**: {attr_value}")
        lines.append('')

    # Abilities
    if 'abilities' in fields:
        for ability in fields['abilities']:
            lines.append(ability['details'])
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

        if fields['name']:
            with open(f'../Bestiary/{fields["name"]}.json', 'w', encoding='utf-8') as f:
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
