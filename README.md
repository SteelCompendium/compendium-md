# Draw Steel Compendium

Draw Steel Compendium is an independent product published under the DRAW STEEL Creator [[LICENSE|License]] and is not affiliated with MCDM Productions, LLC. DRAW STEEL © 2024 MCDM Productions, LLC. 

## Disclaimer

- To be clear, I don't dont own any of this. I just converted the docs over to markdown
- The conversion process is not perfect and there are a lot of mistakes. In particular, the headers are a big challenge that needs fixing and page breaks caused issues.
	- I will continue to update the repo as I go through it and continue to clean it up
- Diagrams are not included since Im assuming that is considered MCDM art.  I'll eventually recreate the diagrams myself in an ugly format.

## TODO

### Bugfixes

- Auto-links dont work with punctuation
  - See fury index page

### Features

- Keywords tables in "linked" rules doc
- [[Hide|hide]] and sneak, cover, concealment
- adventuring - falling, suffocating
- statblocks
- abilities in markdown and json form
  - List them flat in directory/json
  - "tag" them for sorting/filtering (`["Shadow", "1st-level", "College of Black Ash"]`)
- Make Classes directory
  - Abilities in here should just reference the `Abilities/*` files they need
    - This isnt generic markdown, obsidian-only
- Looks into mdformat plugins to see if anything is useful (https://github.com/executablebooks/mdformat)