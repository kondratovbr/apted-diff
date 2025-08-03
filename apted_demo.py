import sys
import xml.etree.ElementTree as ET
from apted import APTED, Config
from apted import APTED

class SimpleConfig(Config):
    def normalized_label(self, node):
        return node.name

    def rename(self, node1, node2):
        return 1 if node1.name != node2.name else 0

class Node:
    def __init__(self, name, children=None):
        self.name = name
        self.children = children if children is not None else []

    def get_children(self):
        return self.children

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

def diff_operations(n1, n2, mapping):
    """Return a list of diff operations as strings: Unchanged, Update, Delete, Insert."""
    ops = []
    for node1, node2 in mapping:
        if node1 and node2:
            if node1.name == node2.name:
                ops.append(f"Unchanged: {node1.name}")
            else:
                ops.append(f"Update: '{node1.name}' → '{node2.name}'")
        elif node1:
            ops.append(f"Delete: {node1.name}")
        elif node2:
            ops.append(f"Insert: {node2.name}")
    return ops

def pretty_tree(node, depth=0):
    """Return a pretty string representation of a Node tree with indentation."""
    indent = "  " * depth
    s = f"{indent}{node.name}\n"
    for child in node.get_children():
        s += pretty_tree(child, depth + 1)
    return s

def compute_diff(a, b):
    """
    Parse HTML/XML strings a, b to Node trees, compute tree edit distance and mapping.
    Returns (n1, n2, distance, mapping)
    """
    n1 = etree_to_node(parse_tree(a))
    n2 = etree_to_node(parse_tree(b))
    apted_instance = APTED(n1, n2, SimpleConfig())
    distance = apted_instance.compute_edit_distance()
    mapping = list(apted_instance.compute_edit_mapping())
    return n1, n2, distance, mapping

def build_diff_html(n1, n2, mapping):
    """Return an HTML string with <ins>, <del>, <span> for visualize-in-article diff."""

    # Build lookup for nodeA: nodeB, nodeB: nodeA
    map_A = {}
    map_B = {}
    for nodeA, nodeB in mapping:
        if nodeA:
            map_A[nodeA] = nodeB
        if nodeB:
            map_B[nodeB] = nodeA

    def parse_node_name(name):
        """Returns tag, text for a node.name (e.g. 'p:hello' -> 'p', 'hello')"""
        if ':' in name:
            tag, text = name.split(':', 1)
        else:
            tag, text = name, ""
        return tag, text

    def walk(nodeA, nodeB):
        # Updated node: same mapped, but text differs
        if nodeA and nodeB and nodeA.name != nodeB.name:
            tagA, textA = parse_node_name(nodeA.name)
            tagB, textB = parse_node_name(nodeB.name)
            # Show update as modified content in the same tag, highlight changes
            childrenA = nodeA.get_children()
            childrenB = nodeB.get_children()
            # If leaf node (text node): show update inline
            if not childrenA and not childrenB:
                # Show deleted and inserted values side by side
                del_html = f"<del class='diff-del'><{tagA}>{textA}</{tagA}></del>"
                ins_html = f"<ins class='diff-ins'><{tagB}>{textB}</{tagB}></ins>"
                return del_html + ins_html
            # Otherwise, show old subtree as deleted and new as inserted
            del_html = f"<del class='diff-del'>" + walk(nodeA, None) + "</del>"
            ins_html = f"<ins class='diff-ins'>" + walk(None, nodeB) + "</ins>"
            return del_html + ins_html

        # Unchanged node (exact match)
        if nodeA and nodeB and nodeA.name == nodeB.name:
            tag, text = parse_node_name(nodeA.name)
            childrenA = nodeA.get_children()
            if not childrenA:
                return f"<{tag}>{text}</{tag}>"
            children_html = ''.join([walk(cA, map_A.get(cA)) for cA in childrenA])
            return f"<{tag}>{children_html}</{tag}>"

        # Deletion (in A not in B)
        if nodeA and not nodeB:
            tag, text = parse_node_name(nodeA.name)
            childrenA = nodeA.get_children()
            if not childrenA:
                return f"<del class='diff-del'><{tag}>{text}</{tag}></del>"
            children_html = ''.join([walk(cA, None) for cA in childrenA])
            return f"<del class='diff-del'><{tag}>{children_html}</{tag}></del>"

        # Insertion (in B not in A)
        if nodeB and not nodeA:
            tag, text = parse_node_name(nodeB.name)
            childrenB = nodeB.get_children()
            if not childrenB:
                return f"<ins class='diff-ins'><{tag}>{text}</{tag}></ins>"
            children_html = ''.join([walk(None, cB) for cB in childrenB])
            return f"<ins class='diff-ins'><{tag}>{children_html}</{tag}></ins>"

        # Should not occur for well-formed trees/mapping
        return ""

    # Always show as rendered HTML, not text!
    return walk(n1, n2)