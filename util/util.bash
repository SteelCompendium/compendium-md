# Source: https://stackoverflow.com/a/42943426
# I dont understand why this works, but it works
title_case() {
    set ${*,,}
    echo ${*^}
}

# converts all files in the folder from html to md
html_folder_to_md() {
    local html_folder="${1:-}"

    for html_file in $(ls "$html_folder" | grep ".html"); do
        html_to_md "${html_folder}/${html_file}"
    done
}

# converts file from html to md
html_to_md() {
    local html_file_path="${1:-}"

    h_path="$(realpath "$html_file_path")"
    h_folder_path="$(dirname "$h_path")"
    h_filename="$(basename "$h_path")"

    # build the md filename, formatted
    markdown_filename=$(echo "$h_filename" | sed -e 's/html/md/' -e 's/_/ /g' -e "s/’//g" -e "s/'//g")
    markdown_filename="$(title_case "$markdown_filename")"

    # convert html to markdown
    pandoc --wrap=none --standalone \
        --from=html \
        --to=markdown_strict+pipe_tables \
        -o "${h_folder_path}/${markdown_filename}" \
        "${h_folder_path}/${h_filename}"

    # Cleanup the markdown files
    reduce_headers_in_md "${h_folder_path}/${markdown_filename}"
    title_case_headers_in_md "${h_folder_path}/${markdown_filename}"
    # TODO - the format_ability_tables should probably go here?
    build_and_apply_frontmatter "${h_folder_path}/${markdown_filename}"

    # Delete html file
    rm "$html_file_path"
}

reduce_headers_in_md() {
    local md_file_path="${1:-}"

    # Find the first header and count the number of # symbols
    first_header=$(grep --color=never -m 1 "^#" "$md_file_path" | sed -E 's/(#+).*/\1/')
    first_header_length=${#first_header}  # Get the length of the header (i.e., number of # symbols)

    if [[ $first_header_length -gt 1 ]]; then
        # Reduce the number of # symbols in all headers by the first header length minus one
        sed -i -E "s/^#{$first_header_length}/#/" "$md_file_path"
    fi
}

title_case_headers_in_md() {
    local md_file_path="${1:-}"
    sed -E '/^#+ /{s/(#+)\s*(.*)/\1 \L\2/g; s/(#+\s*)([a-z])/\1\u\2/g; s/\s([a-z])/ \u\1/g}' "$md_file_path" > .tmp
    mv .tmp "$md_file_path"
}

build_and_apply_frontmatter() {
    local md_file_path="${1:-}"

    local title
    title="$(sed -nE "s/^#\s+(.*)/\1/p" "$md_file_path" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
    local name
    name="$(echo "$title" | sed -E 's/([^\(]+).*/\1/g' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
    local cost
    cost="$(echo "$title" | sed -E 's/[^\(]+\(([^\)]+)\)/\1/g' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
    if [ "$cost" == "$title" ]; then
        cost=""
    fi

    # Figure out the directory this is in (relative to project root)
    local root_dir=$(git rev-parse --show-toplevel)
    local relative_path="$(realpath -s --relative-to="$root_dir" "$md_file_path")"

    # type is the first directory under the root
    local type_raw
    type_raw=$(echo "$relative_path" | awk -F'/' '{ print $1 }' )
    local type
    type="$(echo "$type_raw" | sed -E 's/([A-Z])/\L\1/g' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"

    # subtype is the second directory under the root (if applicable)
    local subtype_raw
    subtype_raw="$(realpath -s --relative-to="$root_dir/$type_raw" "$md_file_path" | awk -F'/' '{ print $1 }')"
    local subtype
    subtype="$(echo "$subtype_raw" | sed -E 's/([A-Z])/\L\1/g' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
    if [ "$subtype_raw" == "$(basename "$md_file_path")" ]; then
        subtype=""
    fi

    # this is temporary - similar regex is used in format_ability_tables. It is VERY slow
    local ability_kv_pairs
    ability_kv_pairs="$(sed -nE "s/^\-?\s*\*\*([^:\*]+?)\**:\**\s*(\S.*)?\s*$/\1: \2/p" "$md_file_path")"
    if [ -n "${ability_kv_pairs:-}" ]; then
        local keywords
        keywords="$(echo "$ability_kv_pairs" | awk -F: '/^Keywords:/ { print $2 }' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
        local ability_type
        ability_type="$(echo "$ability_kv_pairs" | awk -F: '/^Type:/ { print $2 }' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
        local distance
        distance="$(echo "$ability_kv_pairs" | awk -F: '/^Distance:/ { print $2 }' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
        local target
        target="$(echo "$ability_kv_pairs" | awk -F: '/^Target:/ { print $2 }' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
        local trigger
        trigger="$(echo "$ability_kv_pairs" | awk -F: '/^Trigger:/ { print $2 }' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
    fi

    frontmatter_path="$(mktemp)"
    echo "---
title: \"${title:-}\"
name: \"${name:-}\"
type: \"${type:-}\"" >> "$frontmatter_path"
    if [ -n "${cost:-}" ]; then
        echo "cost: \"${cost}\"" >> "$frontmatter_path"
    fi
    if [ -n "${subtype:-}" ]; then
        echo "subtype: \"${subtype}\"" >> "$frontmatter_path"
    fi
    if [ -n "${keywords:-}" ]; then
        echo "keywords: \"${keywords}\"" >> "$frontmatter_path"
        echo "keyword_list: [${keywords}]" >> "$frontmatter_path"
    fi
    if [ -n "${ability_type:-}" ]; then
        echo "ability_type: \"${ability_type}\"" >> "$frontmatter_path"
    fi
    if [ -n "${distance:-}" ]; then
        echo "distance: \"${distance}\"" >> "$frontmatter_path"
    fi
    if [ -n "${target:-}" ]; then
        echo "target: \"${target}\"" >> "$frontmatter_path"
    fi
    if [ -n "${trigger:-}" ]; then
        echo "trigger: \"${trigger}\"" >> "$frontmatter_path"
    fi
    echo "---" >> "$frontmatter_path"

    cat "$frontmatter_path" | cat - "$md_file_path" > temp && mv temp "$md_file_path"
}