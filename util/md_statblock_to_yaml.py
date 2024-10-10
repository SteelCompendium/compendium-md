import re
import yaml

# General purpose of this file is to pass a markdown string containing a statblock and it returns the parsed
# yaml of the statblock data.
############################################################################################################

def parse_header(markdown_text):
    """
    Extracts the name of the statblock from the header.
    """
    lines = markdown_text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if re.match(r'^#{2,6}', line):
            name = line.lstrip('#').strip()
            return name.title()
    return None

def parse_basic_stats(section_text):
    data = {}

    lines = section_text.strip().split('\n')

    # Initialize variables
    data['ancestry'] = []
    data['roles'] = []

    for line in lines:
        line = line.strip()
        if line.startswith('**') and line.endswith('**'):
            # It's a bolded line without colon
            # Check if it's 'Level X Role'
            match = re.match(r'\*\*Level (\d+) (.+)\*\*', line)
            if match:
                level = int(match.group(1))
                roles = match.group(2).split(' ')
                roles = [role.strip() for role in roles]
                data['level'] = level
                data['roles'] = roles
            elif line.startswith('**EV'):
                # Parse EV
                match = re.match(r'\*\*EV (\d+)\*\*', line)
                if match:
                    ev = int(match.group(1))
                    data['ev'] = ev
            else:
                # Maybe it's a trait or ability
                # For now, ignore
                pass
        elif line.startswith('*') and line.endswith('*'):
            # Ancestry
            ancestry = line.strip('*').split(',')
            ancestry = [a.strip() for a in ancestry]
            data['ancestry'] = ancestry
        elif line.startswith('**') and '**' in line[2:]:
            # It's a bolded keyword with a colon
            # For example, '**Stamina**: 120'
            match = re.match(r'\*\*(.+?)\*\*:\s*(.+)', line)
            if match:
                key = match.group(1).strip().lower().replace(' ', '_')
                value = match.group(2).strip()
                if key in ['stamina', 'free_strike']:
                    data[key] = int(value)
                elif key == 'immunity' or key == 'immunities':
                    immunities = [s.strip() for s in value.split(',')]
                    data['immunities'] = immunities
                elif key == 'size':
                    # Parse size and stability
                    if '/' in value:
                        size_part, stability_part = value.split('/')
                        size = size_part.strip()
                        stability = stability_part.strip()
                        if 'Stability' in stability:
                            stability = stability.replace('Stability', '').strip()
                        data['size'] = size
                        data['stability'] = int(stability)
                    else:
                        data['size'] = value
                else:
                    data[key] = value
        else:
            # Maybe other lines
            pass

    return data

def parse_characteristics(section_text):
    data = {}

    lines = section_text.strip().split('\n')

    for line in lines:
        line = line.strip()
        if line.startswith('- **') and '**' in line[3:]:
            # Parse characteristic
            match = re.match(r'- \*\*(.+?)\*\* ([+-]?\d+)', line)
            if match:
                key = match.group(1).strip().lower()
                value = int(match.group(2))
                data[key] = value
    return data

def parse_ability(section_text):
    ability = {}

    lines = section_text.strip().split('\n')

    # First line is ability name and other info
    first_line = lines[0].strip()

    # Extract name, type, roll, cost
    # Try to match different patterns
    # Pattern 1: **Name (Type)** ◆ Roll ◆ Cost
    pattern1 = r'\*\*(.+?)\s*\((.+?)\)\*\*\s*◆\s*(.+?)\s*◆\s*(.+)'
    # Pattern 2: **Name (Type)** ◆ Roll
    pattern2 = r'\*\*(.+?)\s*\((.+?)\)\*\*\s*◆\s*(.+)'
    # Pattern 3: **Name (Type)**
    pattern3 = r'\*\*(.+?)\s*\((.+?)\)\*\*'
    # Pattern 4: **Name** ◆ Roll ◆ Cost
    pattern4 = r'\*\*(.+?)\*\*\s*◆\s*(.+?)\s*◆\s*(.+)'
    # Pattern 5: **Name** ◆ Roll
    pattern5 = r'\*\*(.+?)\*\*\s*◆\s*(.+)'
    # Pattern 6: **Name**
    pattern6 = r'\*\*(.+?)\*\*'

    match = re.match(pattern1, first_line)
    if match:
        ability['name'] = match.group(1).strip()
        ability['type'] = match.group(2).strip()
        ability['roll'] = match.group(3).strip()
        ability['cost'] = match.group(4).strip()
    else:
        match = re.match(pattern2, first_line)
        if match:
            ability['name'] = match.group(1).strip()
            ability['type'] = match.group(2).strip()
            ability['roll'] = match.group(3).strip()
        else:
            match = re.match(pattern3, first_line)
            if match:
                ability['name'] = match.group(1).strip()
                ability['type'] = match.group(2).strip()
            else:
                match = re.match(pattern4, first_line)
                if match:
                    ability['name'] = match.group(1).strip()
                    ability['roll'] = match.group(2).strip()
                    ability['cost'] = match.group(3).strip()
                else:
                    match = re.match(pattern5, first_line)
                    if match:
                        ability['name'] = match.group(1).strip()
                        ability['roll'] = match.group(2).strip()
                    else:
                        match = re.match(pattern6, first_line)
                        if match:
                            ability['name'] = match.group(1).strip()

    # After setting 'type', check for 'Villain Action N'
    if 'type' in ability:
        type_str = ability['type']
        villain_action_match = re.match(r'Villain Action\s*(\d+)', type_str)
        if villain_action_match:
            n = int(villain_action_match.group(1))
            ability['type'] = 'Villain Action'  # Normalize type
            ability['cost'] = f'{n} VP'

    # Now process the rest of the lines
    i = 1
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('Keywords:'):
            keywords_line = line[len('Keywords:'):].strip()
            keywords = [k.strip() for k in keywords_line.split(',')]
            ability['keywords'] = keywords
        elif line.startswith('Distance:'):
            distance = line[len('Distance:'):].strip()
            ability['distance'] = distance
        elif line.startswith('Target:'):
            target = line[len('Target:'):].strip()
            ability['target'] = target
        elif line.startswith('Trigger:'):
            trigger = line[len('Trigger:'):].strip()
            ability['trigger'] = trigger
        elif line.startswith('Effect:'):
            effect_line = line[len('Effect:'):].strip()
            effect = effect_line
            # Check if next lines are continuation of effect
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('-'):
                effect += ' ' + lines[i].strip()
                i += 1
            ability['effect'] = effect
            continue  # We've already incremented i
        elif line.startswith('-'):
            # Tiers or additional effects
            if line.startswith('- **'):
                # Additional effect with cost
                match = re.match(r'- \*\*(.+?)\*\*:\s*(.+)', line)
                if match:
                    cost = match.group(1).strip()
                    additional_effect = match.group(2).strip()
                    # Check if next lines are continuation
                    i += 1
                    while i < len(lines) and not lines[i].strip().startswith('-'):
                        additional_effect += ' ' + lines[i].strip()
                        i += 1
                    if 'additional_effects' not in ability:
                        ability['additional_effects'] = []
                    ability['additional_effects'].append({'cost': cost, 'effect': additional_effect})
                    continue  # Already incremented i
            else:
                # Tier lines may start with '- ✦', '- ★', '- ✸', or '- ≤11:'
                # Match lines like '- ✦ ≤11: description' or '- ≤11: description'
                match = re.match(r'-\s*([✦★✸])?\s*(.+?):\s*(.+)', line)
                if match:
                    symbol = match.group(1)
                    threshold = match.group(2).strip()
                    description = match.group(3).strip()
                    # Process description continuation
                    i += 1
                    while i < len(lines) and not lines[i].strip().startswith('-'):
                        description += ' ' + lines[i].strip()
                        i += 1
                    # Map threshold to tier
                    if symbol == '✦' or '≤11' in threshold or '≤ 11' in threshold:
                        ability['t1'] = description
                    elif symbol == '★' or '12–16' in threshold or '12-16' in threshold:
                        ability['t2'] = description
                    elif symbol == '✸' or '17+' in threshold:
                        ability['t3'] = description
                    else:
                        # Store threshold and description as is
                        if 'tiers' not in ability:
                            ability['tiers'] = []
                        ability['tiers'].append({'threshold': f"{threshold}", 'description': description})
                    continue  # Already incremented i
                else:
                    # Maybe it's an additional effect without cost
                    pass
        else:
            # Other lines, maybe continuation of previous
            i += 1
            continue
        i += 1

    return ability

def parse_markdown_statblock(markdown_text):
    # Initialize the data dictionary
    data = {}

    # Extract the name from the header
    name = parse_header(markdown_text)
    if name:
        data['name'] = name

    # Remove the header line from the markdown_text
    markdown_text = '\n'.join(markdown_text.strip().split('\n')[1:])

    # Split the markdown into sections separated by blank lines
    sections = re.split(r'\n\s*\n', markdown_text.strip())

    # The first section is basic stats
    basic_stats_section = sections[0]

    # Parse basic stats
    data.update(parse_basic_stats(basic_stats_section))

    # The next section(s) may be characteristics or abilities
    abilities = []
    for section in sections[1:]:
        section = section.strip()
        if not section:
            continue
        if section.startswith('- **'):
            # This is characteristics section
            data.update(parse_characteristics(section))
        elif section.startswith('**'):
            # This is an ability or trait
            # Check if it's a trait (no parentheses in the title)
            first_line = section.split('\n')[0]
            if '(' in first_line and ')' in first_line:
                # It's an ability
                ability = parse_ability(section)
                abilities.append(ability)
            else:
                # It's a trait
                lines = section.strip().split('\n')
                trait_name = lines[0].strip('*').strip()
                trait_effect = ' '.join(lines[1:]).strip()
                if 'traits' not in data:
                    data['traits'] = []
                data['traits'].append({'name': trait_name, 'effect': trait_effect})
        else:
            # Unknown section
            pass

    if abilities:
        data['abilities'] = abilities

    return data

def process_markdown(markdown_text):
    """
    Processes the markdown statblock and returns a YAML string.

    Args:
        markdown_text (str): The markdown text of the statblock.

    Returns:
        str: The YAML representation of the statblock.
    """
    data = parse_markdown_statblock(markdown_text)
    yaml_string = yaml.dump(data, sort_keys=False, allow_unicode=True)
    return yaml_string
