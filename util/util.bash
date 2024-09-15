# Source: https://stackoverflow.com/a/76503202
title_case() {
   ((CHR_PTR=0))
   set ${*,,}
   for f in ${*} ; do
      case $f in
         ebay) c+="eBay " ;;
         mcdonalds|"mcdonald's") c+="McDonald's " ;;
         vs) c+="vs. " ;;
         a|about|and|but|by|for|in|is|of|or|the|to) \
             [ "$CHR_PTR" -eq "0" ] && {
                c+="${f^} "
             } || {
                c+="$f "
             } ;;
         bbq|diy|hdtv|hf|kfc|mdf|sdtv|shf|tv|uhf|vlf|vhf) c+="${f^^} " ;;
         *) c+="${f^} " ;;
      esac
      ((CHR_PTR++))
   done
   x=${c## } ; c=${x%% }
   echo "$c"
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
    markdown_filename="$(title_case "$h_filename" | sed -e 's/html/md/' -e 's/_/ /g' -e "s/’//g" -e "s/'//g")"

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