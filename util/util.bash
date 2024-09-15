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
    markdown_filename="$(title_case "$h_filename" | sed -e 's/html/md/' -e 's/_/ /g')"

    # convert html to markdown
    pandoc --wrap=none -f html -t markdown_strict -o "${h_folder_path}/${markdown_filename}" "${h_folder_path}/${h_filename}"

    # Reduce the nested headers
    reduce_headers_in_md "${h_folder_path}/${markdown_filename}"

    # Delete html file
    rm "$html_file_path"
}

reduce_headers_in_md() {
    local md_file_path="${1:-}"

    # Find the level of the first header (number of # symbols)
    first_header_level=$(grep -m 1 "^#" "$md_file_path" | grep -o '^#*' | wc -c)

    # Subtract 1 to get the level shift needed
    # TODO - this should be `-1` NOT `-2` - there is something wrong...
    header_shift=$((first_header_level - 2))
    headers_to_remove=$(printf '#%.0s' $(seq 1 $header_shift))

    sed -i "s/$headers_to_remove//g" "$md_file_path"
}