#!/usr/bin/env bash
set -euo pipefail

source ./util.bash

# For a given class, parses the rules json doc to extract abilities and create dedicated files for them
generate_abilities_for_class() {
    local class="${1:-}"

    local class_title
    class_title="$(title_case "$class")"
    local folder_path
    folder_path="../Abilities/${class_title}"
    mkdir -p "$folder_path"

    local links="$(mktemp)"

    # Add abilities
    abilities_types="$(jq -rc ".${class}[\"1ST-LEVEL FEATURES\"][\"${class} ABILITIES\"] | to_entries | .[]" '../Rules/Draw Steel Rules.json')"
    echo "$abilities_types" | while read -r ability_type; do
        local type_raw
        type_raw="$(jq -r '.key' <(echo "$ability_type"))"
        local abilities_raw
        abilities_raw="$(jq -r '.value' <(echo "$ability_type"))"

        local type
        type="$(title_case "$type_raw")"
        if [ "$type" != "Heroic Abilities" ] && [ "$type" != "Kit Signature Ability" ]; then
            abilities_json="$(echo "$abilities_raw" | jq -rc '. | to_entries | .[]')"
            echo "$abilities_json" | while read -r ability; do
                ability_entry_to_markdown "$ability" "$class" "$type" "$folder_path" "$links"
            done
        fi
    done

    # Add Triggered Actions
    triggered_actions="$(jq -rc ".${class}[\"1ST-LEVEL FEATURES\"] | to_entries[] | select(.key | contains(\"TRIGGERED ACTION\")) | .value | to_entries[]" '../Rules/Draw Steel Rules.json')"
    echo "$triggered_actions" | while read -r triggered_action; do
        ability_entry_to_markdown "$triggered_action" "$class" "Triggered Action" "$folder_path" "$links"
    done

    # Build index note for the class
    generate_ability_index_markdown "${class_title} Ability Index" "$(cat "$links")" > "$folder_path/_${class_title} Ability Index.md"
}

ability_entry_to_markdown() {
    # json of the ability, expected to have `key` and `value` fields
    local ability_kv="${1:-}"
    # Name of the source the grants the ability (class, kit,etc)
    local source_name="${2:-}"
    # Type of the ability (triggered action, etc)
    local ability_type="${3:-}"
    # path to the ability folder to dump the ability
    local ability_folder_path="${4:-}"
    # path the to links directory to add this ability filename to
    local links_path="${5:-}"

    name="$(jq -r '.key' <(echo "$ability_kv"))"
    value="$(jq -r '.value' <(echo "$ability_kv"))"

    # Some classes have a special subheadings, skip them
    if [[ "$name" =~ "TRIGGERED ACTION" ]]; then
        return
    fi

    local filename
    filename="$(title_case "$name" | sed 's/(.*)//g' | xargs)"
    local ability_path="${ability_folder_path}/${filename}.md"
    ability_to_markdown "$name" "$value" "$source_name" "$ability_type" > "$ability_path"
    echo "${filename}.md" >> "$links"
}

# Prints out markdown for an ability
ability_to_markdown() {
    # String of the ability name - expected to be all uppercase
    local name_raw="${1:-}"
    # String of the ability value - expected to be... a mess
    local value_raw="${2:-}"
    # String of how the ability is granted (class, kit, etc) - expected to be all uppercase
    local source_raw="${3:-}"
    # String of the ability type (triggered action, 3-rage, etc) - expected to be all uppercase
    local type_raw="${4:-}"

    # Cleanup input
    local name
    name="$(title_case "$name_raw")"
    local source
    source="$(title_case "$source_raw")"

    # Parse cost
    local cost
    cost="$(echo "$name_raw" | sed 's/.*(\(.*\)).*/\1/g')"
    if [ "$cost" == "$name_raw" ]; then
        cost=""
    fi

    # Format ability if json, otherwise just do your best
    if [[ "$value_raw" == *{* ]]; then
        content="$(ability_json_to_markdown "$value_raw")"
    else
        echo >&2 "[WARN] Parsing ability $name_raw content raw"
        content="$(ability_content_to_markdown "$value_raw")"
    fi

    # Build markdown
    markdown="---"
    markdown="${markdown}\nname: \"$name\""
    markdown="${markdown}\ntype: \"$type_raw\""
    markdown="${markdown}\nsource: \"$source\""
    markdown="${markdown}\ncost: \"$cost\""
    markdown="${markdown}\n---"
    markdown="${markdown}\n"
    markdown="${markdown}\n# $name"
    markdown="${markdown}\n"
    markdown="${markdown}\n$content"

    # TODO - format the markdown with a linter
    echo -e "$markdown"
}

# Converts an ability in json to markdown.  This is used when an ability was able to be converted to json
ability_json_to_markdown() {
    local value_raw="${1:-}"
    local content_path
    content_path="$(mktemp)"

    ability_field_to_markdown "*" "description" "*" "$value_raw" >> $content_path

    echo "" >> $content_path

    local keywords="$(ability_field_to_markdown "" "keywords" "" "$value_raw")"
    local type="$(ability_field_to_markdown "" "type" "" "$value_raw")"
    local distance="$(ability_field_to_markdown "" "distance" "" "$value_raw")"
    local target="$(ability_field_to_markdown "" "target" "" "$value_raw")"

    if [ -n "$keywords" ] || [ -n "$type" ] || [ -n "$distance" ] || [ -n "$target" ]; then
        echo "| **Keywords:** ${keywords} | **Type:** ${type} |" >> $content_path
        echo "| :-- | :-- |" >> $content_path
        echo "| **Distance:** ${distance} | **Target:** ${target} |" >> $content_path
    fi

    ability_field_to_markdown "\n**Trigger:** " "trigger" "" "$value_raw" >> $content_path

    ability_field_to_markdown "\n**" "roll" "**" "$value_raw" >> $content_path

    ability_field_to_markdown "\n- **11 or lower:** " "tier1" "" "$value_raw" >> $content_path
    ability_field_to_markdown "- **12-16:** " "tier2" "" "$value_raw" >> $content_path
    ability_field_to_markdown "- **17+:** " "tier3" "" "$value_raw" >> $content_path

    ability_field_to_markdown "\n**Effect:** " "effect" "" "$value_raw" >> $content_path

    # TODO - alt effects
    #    alt_effects="$(echo "$value_raw" | jq '.alternative_effects // empty | .[]')"
    #    if [ "$alt_effects" != "" ]; then
    #        echo >&2 "HEY"
    #        echo >&2 "$alt_effects"
    #        echo "$alt_effects" | while read -r alt_effect; do
    #            echo "\n**Alternative Effect:** $alt_effect" >> $content_path
    #        done
    #    fi

    local spend_cost
    spend_cost=$(ability_field_to_markdown " " "spend_cost" "" "$value_raw")
    ability_field_to_markdown "\n**Spend${spend_cost}:** " "spend_effect" "" "$value_raw" >> $content_path

    local persistent_cost
    persistent_cost=$(ability_field_to_markdown " " "persistent_cost" "" "$value_raw")
    ability_field_to_markdown "\n**Persistent${persistent_cost}:** " "persistent_effect" "" "$value_raw" >> $content_path

    cat "$content_path"
}

# Checks an ability json object for a key and if present will generate markdown for the value
ability_field_to_markdown() {
    local prefix="${1:-}"
    local key="${2:-}"
    local suffix="${3:-}"
    local json="${4:-}"
    value="$(echo "$json" | jq -r ".$key // empty")"
    if [ -n "$value" ]; then
        echo "${prefix}${value}${suffix}"
    fi
}

# Converts an ability in plaintext to markdown.  This is used when an ability was unable to be converted to json
ability_content_to_markdown() {
    local value_raw="${1:-}"

    local content_path
    content_path="$(mktemp)"
    echo "$value_raw" | while read -r val_line; do
        # Handle embedded json arrays (ability keywords, etc)
        if [[ "$val_line" =~ ^\[.*\]$ ]]; then
            echo "$val_line" | sed "s/'/\"/g" | jq -c '.[]' | while read item; do
                local item_val
                item_val="$(echo "$item" | sed -e 's/^"//' -e 's/"$//')"
                echo "\n- ${item_val}" >> "$content_path"
            done
        elif [[ "$val_line" =~ ^\-\s*\[.*\]$ ]]; then
            echo "$val_line" | sed "s/^-\s*//g" | sed "s/'/\"/g" | jq -c '.[]' | while read item; do
                local item_val
                item_val="$(echo "$item" | sed -e 's/^"//' -e 's/"$//')"
                echo "\n- ${item}" >> "$content_path"
            done
        else
            echo "${val_line}" >> "$content_path"
        fi
    done
    cat "$content_path"
}

# Prints out markdown for an "index" note of abilities
generate_ability_index_markdown() {
    # String for the title
    local title="${1:-}"
    # newline-separated list of string urls of links to include
    local links="${2:-}"
    local markdown_path
    markdown_path="$(mktemp)"
    echo "# $title" >> "$markdown_path"
    echo "" >> "$markdown_path"

    echo -e "$links" | while read -r link; do
        local name
        name="$(echo "$link" | sed 's/.md//g')"
        echo "- [$name]($link)" >> "$markdown_path"
    done

    cat "$markdown_path"
}
