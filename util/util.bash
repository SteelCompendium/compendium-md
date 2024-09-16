# Source: https://stackoverflow.com/a/42943426
# I dont understand why this works, but it works
title_case() {
    set ${*,,}
    echo ${*^}
}

# converts all files in the folder from html to md
html_folder_to_md() {
    local html_folder="${1:-}"

    for html_file in $(ls "$html_folder"); do
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

    # Delete html file
    rm "$html_file_path"
}

reduce_headers_in_md() {
    local md_file_path="${1:-}"

    # Find the extra levels of the first header (number of # symbols - 1); then remove them
    headers_to_remove=$(grep --color=never -m 1 "^#" "$md_file_path" | sed -E 's/(\#+)\#.*/\1/g')
    sed -i "s/$headers_to_remove//g" "$md_file_path"
}

title_case_headers_in_md() {
    local md_file_path="${1:-}"
    sed -E '/^#+ /{s/(#+)\s*(.*)/\1 \L\2/g; s/(#+\s*)([a-z])/\1\u\2/g; s/\s([a-z])/ \u\1/g}' "$md_file_path" > .tmp
    mv .tmp "$md_file_path"
}