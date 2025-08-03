# HTML/XML APTED Diff

A minimal Python CLI tool to compute the APTED (All Path Tree Edit Distance) between two HTML/XML strings.

## Requirements

- Python 3.8+
- APTED (`pip install apted` or via pyproject.toml)

## Install dependencies

```sh
pip install .
```
or directly:
```sh
pip install apted
```

## Usage

Run from the command line:

```sh
python main.py --a "<root><a>hi</a></root>" --b "<root><a>hello</a></root>"
```

This will print an integer representing the tree edit distance.

- If your XML/HTML is large or contains quotes, it is best to use single quotes for the outer string, or read the strings from files and pass them to the CLI.
- Returns error on invalid XML/HTML.

## Notes

- Only computes the distance (not the exact edit script/diff steps).
- For HTML, only well-formed (XML-compatible) HTML will work (“XHTML”).