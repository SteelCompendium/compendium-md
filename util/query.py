#!/usr/bin/env python3

import os
import argparse
from lxml import etree, html

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Extract sections and save as HTML or Markdown.")
    parser.add_argument("xpath", help="XPath to extract from the html")
    parser.add_argument("html_path", help="Path to the input HTML file")
    parser.add_argument("output_dir", help="Directory to save the output files")
    args = parser.parse_args()

    # Create the output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Parse the HTML file
    with open(args.html_path, 'r', encoding='utf-8') as f:
        tree = html.parse(f)

    # XPath expression to find all the level5 sections under triggered-action
    xpath_expr = args.xpath

    # Find all matching sections
    sections = tree.xpath(xpath_expr)

    # Iterate over the sections and save each one
    for section in sections:
        # Extract the first header (h1 to h6) and clean it for the filename
        header = section.xpath('.//*[self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6]/text()')[0]
        filename = os.path.join(args.output_dir, f'{header.replace(" ", "_")}')

        # Get the section content as HTML
        section_content = etree.tostring(section, pretty_print=True, method="html").decode('utf-8')

        # Save as HTML
        filename += ".html"
        with open(filename, 'w', encoding='utf-8') as f_out:
            f_out.write(section_content)

    print(f'Extracted {len(sections)} sections.')

if __name__ == "__main__":
    main()
