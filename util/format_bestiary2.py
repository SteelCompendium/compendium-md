import re
import json

def parse_statblock(statblock_lines):
    """
    Parses a statblock and returns a dictionary of its fields.
    """
    fields = {}
    attributes = {}
    abilities = []
    current_ability = None

    # Extract name from heading
    heading_line = statblock_lines[0]
    name_match = re.match(r'#+\s+(.*)', heading_line)
    if name_match:
        fields['Name'] = name_match.group(1).strip()
    else:
        fields['Name'] = 'Unnamed Creature'

    # Iterate over the lines
    i = 1  # Start from the line after the heading
    while i < len(statblock_lines):
        line = statblock_lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Check for Level and Type
        level_type_match = re.match(r'\*\*(Level\s+\d+.*?)\*\*\s*(.*)', line)
        if level_type_match:
            level_info = level_type_match.group(1).replace('Level', '').strip()
            fields['Level'] = level_info
            if level_type_match.group(2):
                fields['Type'] = level_type_match.group(2).strip()
            i += 1
            continue

        # Check for EV
        ev_match = re.match(r'\*\*EV\s*(\d+)\*\*', line)
        if ev_match:
            fields['EV'] = ev_match.group(1)
            i += 1
            continue

        # Check for other fields
        field_match = re.match(r'\*\*(.*?)\*\*:\s*(.*)', line)
        if field_match:
            field_name = field_match.group(1).strip()
            field_value = field_match.group(2).strip()
            fields[field_name] = field_value
            i += 1
            continue

        # Check for attributes
        attr_match = re.match(r'-\s*\*\*(.*?)\*\*[:：]?\s*([\+\-]?\d+)', line)
        if attr_match:
            attr_name = attr_match.group(1).strip()
            attr_value = attr_match.group(2).strip()
            attributes[attr_name] = attr_value
            i += 1
            continue

        # Check for abilities
        ability_name_match = re.match(r'\*\*(.*?)\*\*', line)
        if ability_name_match:
            # If we were parsing an ability, save it
            if current_ability:
                abilities.append(current_ability)
            # Start a new ability
            ability_name = ability_name_match.group(1).strip()
            # Skip if this is a field we've already captured
            if ability_name not in ['Level', 'EV', 'Stamina', 'Immunity', 'Weakness', 'Speed', 'Size', 'Free Strike']:
                current_ability = {'Name': ability_name, 'Details': line}
                i += 1
                # Collect the rest of the ability details
                while i < len(statblock_lines):
                    next_line = statblock_lines[i].strip()
                    # Check if the next line is a new ability or a field
                    next_ability_match = re.match(r'\*\*(.*?)\*\*', next_line)
                    if next_ability_match:
                        next_ability_name = next_ability_match.group(1).strip()
                        if next_ability_name not in ['Level', 'EV', 'Stamina', 'Immunity', 'Weakness', 'Speed', 'Size', 'Free Strike']:
                            break
                    # Append to ability details
                    current_ability['Details'] += '\n' + next_line
                    i += 1
                continue
            else:
                i += 1
                continue

        # Increment the index if no patterns matched
        i += 1

    # After loop, add the last ability
    if current_ability:
        abilities.append(current_ability)

    if attributes:
        fields['Attributes'] = attributes
    if abilities:
        fields['Abilities'] = abilities

    return fields

def format_statblock(fields):
    """
    Formats a statblock dictionary into a markdown string.
    """
    lines = []
    lines.append(f"### {fields.get('Name', 'Unnamed Creature')}\n")

    # Level and Type
    level = fields.get('Level', '')
    type_ = fields.get('Type', '')
    if level or type_:
        lines.append(f"**Level {level}** {type_}\n")

    # EV (if present)
    if 'EV' in fields:
        lines.append(f"**EV**: {fields['EV']}")

    # Other fields
    for key in ['Stamina', 'Immunity', 'Weakness', 'Speed', 'Size', 'Free Strike']:
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
        if line.startswith('###'):
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
