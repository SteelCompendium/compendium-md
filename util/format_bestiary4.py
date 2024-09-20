import re
import json
import os

def to_lower_snake_case(s):
    s = s.strip()
    s = s.lower()
    s = s.replace(' ', '_')
    s = re.sub(r'\W+', '_', s)
    s = re.sub(r'_+', '_', s)
    return s.strip('_')

def parse_ability(details):
    """
    Parses the details of an ability and returns a dictionary with its subfields.
    """
    print("====================")
    print(details)
    ability = {}
    lines = details.strip().split('\n')
    if not lines:
        return ability
    header_line = lines[0].strip()

    # Parse the ability header
    # Pattern: **Ability Name (Cost)** ◆ Roll ◆ Type
    header_pattern = re.compile(r'\*\*(.*?)\s*(?:\((.*?)\))?\*\*\s*(?:◆\s*(.*?)\s*◆\s*(.*))?')
    header_match = header_pattern.match(header_line)
    if header_match:
        ability_name = header_match.group(1).strip()
        cost = header_match.group(2)
        roll = header_match.group(3)
        type_ = header_match.group(4)
        ability['name'] = ability_name
        if cost:
            ability['cost'] = cost.strip()
        if type_:
            ability['type'] = type_.strip()
        if roll:
            ability['power_roll'] = {'roll': roll.strip()}
        else:
            ability['power_roll'] = {}
    else:
        # If header doesn't match, set name as the whole line without ** **
        ability_name = header_line.strip('*')
        ability['name'] = ability_name

    # Now process the rest of the lines
    i = 1
    while i < len(lines):
        line = lines[i].strip()

        # Check for fields: **Field Name**: Value
        field_match = re.match(r'\*\*(.*?)\*\*:\s*(.*)', line)
        if field_match:
            field_name = to_lower_snake_case(field_match.group(1).strip())
            field_value = field_match.group(2).strip()
            ability[field_name] = field_value
            i += 1
            continue

        # Check for power roll tiers
        tier_match = re.match(r'-\s*(✦|★|✸)\s*(.*?):\s*(.*)', line)
        if tier_match:
            symbol = tier_match.group(1)
            tier_effect = tier_match.group(3).strip()
            # Map symbol to tier level
            symbol_to_tier = {'✦': 'tier_1', '★': 'tier_2', '✸': 'tier_3'}
            tier_key = symbol_to_tier.get(symbol, 'unknown_tier')
            ability['power_roll'][tier_key] = tier_effect
            i += 1
            continue

        # Check for 'Effect' line
        effect_match = re.match(r'\*\*Effect\*\*:\s*(.*)', line)
        if effect_match:
            effect_text = effect_match.group(1).strip()
            ability['effect'] = effect_text
            i += 1
            # Continue to collect any indented lines
            while i < len(lines) and (lines[i].startswith('  ') or lines[i].startswith('\t')):
                ability['effect'] += ' ' + lines[i].strip()
                i += 1
            continue

        # Handle other lines (could be description or continuation)
        if line.startswith('**'):
            # Possibly another field or heading we didn't catch
            i += 1
            continue

        # Append to description
        if 'description' in ability:
            ability['description'] += ' ' + line.strip()
        else:
            ability['description'] = line.strip()
        i += 1

    # Remove 'power_roll' if it's empty
    if 'power_roll' in ability and not ability['power_roll']:
        del ability['power_roll']

    return ability

def parse_statblock(statblock_lines):
    """
    Parses a statblock and returns a dictionary of its fields.
    """
    fields = {}
    characteristics = {}
    abilities = []
    current_ability_lines = None

    # Extract name from heading
    heading_line = statblock_lines[0]
    name_match = re.match(r'#+\s+(.*)', heading_line)
    if name_match:
        fields['name'] = name_match.group(1).strip()
    else:
        fields['name'] = 'Unnamed Creature'

    # Fields to skip when detecting abilities
    known_fields = set(['level', 'ev', 'stamina', 'immunity', 'weakness', 'speed', 'size', 'stability', 'free_strike'])

    # Iterate over the lines
    i = 1  # Start from the line after the heading
    while i < len(statblock_lines):
        line = statblock_lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Check for Level and Roles
        level_type_match = re.match(r'\*\*(Level\s+.*?)\*\*(.*)', line)
        if level_type_match:
            level_info = level_type_match.group(1).replace('Level', '').strip()
            # Extract level as an integer
            level_digits = re.findall(r'\d+', level_info)
            if level_digits:
                fields['level'] = int(level_digits[0])
            else:
                fields['level'] = None
            # Extract roles as a list of strings
            roles = re.findall(r'[^\d\s]+', level_info)
            if roles:
                fields['roles'] = roles
            else:
                fields['roles'] = []
            # Additional roles or types
            if level_type_match.group(2):
                extra_roles = level_type_match.group(2).strip()
                if extra_roles:
                    extra_roles_list = re.split(r',|;', extra_roles)
                    fields['roles'].extend([role.strip() for role in extra_roles_list if role.strip()])
            i += 1
            continue

        # Check for EV
        ev_match = re.match(r'\*\*EV\s*(\d+)\*\*', line)
        if ev_match:
            fields['ev'] = int(ev_match.group(1))
            i += 1
            continue

        # Check for other fields
        field_match = re.match(r'\*\*(.*?)\*\*:\s*(.*)', line)
        if field_match:
            field_name = field_match.group(1).strip()
            field_value = field_match.group(2).strip()
            # Adjust field names to lower_snake_case
            field_name_snake = to_lower_snake_case(field_name)
            if field_name_snake == 'size':
                # Split size and stability
                size_stability_match = re.match(r'(\S+)\s*/\s*Stability\s*(\d+)', field_value)
                if size_stability_match:
                    fields['size'] = size_stability_match.group(1).strip()
                    fields['stability'] = int(size_stability_match.group(2))
                else:
                    fields['size'] = field_value
            else:
                fields[field_name_snake] = field_value
            i += 1
            continue

        # Check for characteristics (was attributes)
        attr_match = re.match(r'-\s*\*\*(.*?)\*\*[:：]?\s*([\+\-]?\d+)', line)
        if attr_match:
            attr_name = attr_match.group(1).strip()
            attr_value = attr_match.group(2).strip()
            characteristics[attr_name] = attr_value
            i += 1
            continue

        # Check for abilities
        ability_name_match = re.match(r'\*\*(.*?)\*\*', line)
        if ability_name_match:
            ability_name = ability_name_match.group(1).strip()
            field_name_snake = to_lower_snake_case(ability_name)
            if field_name_snake not in known_fields:
                # If we were parsing an ability, save it
                if current_ability_lines:
                    current_ability_details = '\n'.join(current_ability_lines)
                    parsed_ability = parse_ability(current_ability_details)
                    abilities.append(parsed_ability)
                # Start a new ability
                current_ability_lines = [line]
                i += 1
                continue
            else:
                i += 1
                continue
        else:
            # Append line to current ability if we're parsing one
            if current_ability_lines is not None:
                current_ability_lines.append(line)
            i += 1

    # After loop, process the last ability
    if current_ability_lines:
        current_ability_details = '\n'.join(current_ability_lines)
        parsed_ability = parse_ability(current_ability_details)
        abilities.append(parsed_ability)

    if characteristics:
        fields['characteristics'] = characteristics
    if abilities:
        fields['abilities'] = abilities

    return fields

def format_statblock(fields):
    """
    Formats a statblock dictionary into a markdown string.
    """
    lines = []
    lines.append(f"### {fields.get('name', 'Unnamed Creature')}\n")

    # Level and Roles
    level = fields.get('level', '')
    roles = fields.get('roles', [])
    roles_str = ' '.join(roles)
    if level or roles:
        lines.append(f"**Level {level} {roles_str}**\n")

    # EV (if present)
    if 'ev' in fields:
        lines.append(f"**EV**: {fields['ev']}")

    # Other fields
    for key in ['stamina', 'immunity', 'weakness', 'speed', 'size', 'stability', 'free_strike']:
        if key in fields:
            lines.append(f"**{key.replace('_', ' ').title()}**: {fields[key]}")

    lines.append('')

    # Characteristics
    if 'characteristics' in fields:
        for attr_name, attr_value in fields['characteristics'].items():
            lines.append(f"- **{attr_name}**: {attr_value}")
        lines.append('')

    # Abilities
    if 'abilities' in fields:
        for ability in fields['abilities']:
            lines.append(ability.get('details', ''))
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

        if fields['name']:
            # Ensure the directory exists
            os.makedirs('../Bestiary', exist_ok=True)
            # Make a safe filename
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', fields["name"])
            with open(f'../Bestiary/{safe_name}.json', 'w', encoding='utf-8') as f:
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
