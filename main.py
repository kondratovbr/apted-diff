import argparse
import sys
import xml.etree.ElementTree as ET
from apted import APTED, Config

class Node:
    def __init__(self, name, children=None):
        self.name = name
        self.children = children if children is not None else []

    def get_children(self):
        return self.children

class SimpleConfig(Config):
    def normalized_label(self, node):
        return node.name

    def rename(self, node1, node2):
        return 1 if node1.name != node2.name else 0

def parse_tree(xml_string):
    try:
        root = ET.fromstring(xml_string)
        return root
    except ET.ParseError as e:
        print(f"Error parsing XML/HTML: {e}", file=sys.stderr)
        sys.exit(1)

def etree_to_node(node):
    """Convert ElementTree node to apted Node, with tag content included in label."""
    label = node.tag
    # Include text content in the label if present
    if node.text and node.text.strip():
        label += f":{node.text.strip()}"
    return Node(label, [etree_to_node(child) for child in node])

def print_tree(node, depth=0):
    """Recursively print an apted.Node tree with indentation."""
    indent = "  " * depth
    print(f"{indent}{node.name}")
    for child in node.get_children():
        print_tree(child, depth + 1)

def show_diff(n1, n2):
    apted_instance = APTED(n1, n2, SimpleConfig())
    mapping = list(apted_instance.compute_edit_mapping())
    print("\nRaw node mapping (A->B):")
    for i, (node1, node2) in enumerate(mapping):
        label1 = node1.name if node1 else None
        label2 = node2.name if node2 else None
        print(f"  Mapping {i+1}: {label1} -> {label2}")
    matched_a = set()
    matched_b = set()
    changes = []
    for node1, node2 in mapping:
        if node1 and node2:
            if node1.name == node2.name:
                changes.append(f"Unchanged: {node1.name}")
            else:
                changes.append(f"Update: '{node1.name}' -> '{node2.name}'")
            matched_a.add(node1)
            matched_b.add(node2)
        elif node1:
            changes.append(f"Delete: {node1.name}")
            matched_a.add(node1)
        elif node2:
            changes.append(f"Insert: {node2.name}")
            matched_b.add(node2)
    print("\nTree Diff Operations:")
    for change in changes:
        print("  -", change)
        
def main():
    parser = argparse.ArgumentParser(
        description="Compute the APTED tree edit distance between two HTML/XML strings."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--demo", action="store_true", help="Run demo with example HTML strings")

    # Demo illustrating node movement: <footer> moves inside body
    example_a = (
        "<html>"
        "<body>"
        "<header><h1>My Site</h1></header>"
        "<main>"
        "<section>Section 1</section>"
        "<section>Section 2</section>"
        "</main>"
        "<footer>Copyright 2025</footer>"
        "</body>"
        "</html>"
    )
    example_b = (
        "<html>"
        "<body>"
        "<header><h1>My Site</h1></header>"
        "<footer>Copyright 2025</footer>"
        "<main>"
        "<section>Section 1</section>"
        "<section>Section 2</section>"
        "</main>"
        "</body>"
        "</html>"
    )
    print("Example A:\n", example_a)
    print("Example B:\n", example_b)
    tree_a = parse_tree(example_a)
    tree_b = parse_tree(example_b)
    print("\nParsed Tree for A:")
    n1 = etree_to_node(tree_a)
    print_tree(n1)
    print("\nParsed Tree for B:")
    n2 = etree_to_node(tree_b)
    print_tree(n2)
    distance = APTED(n1, n2, SimpleConfig()).compute_edit_distance()
    show_diff(n1, n2)
    print("\nAPTED distance:", distance)

if __name__ == "__main__":
    main()
