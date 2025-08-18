import sys
import xml.etree.ElementTree as ET
from apted import APTED, Config

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

def pretty_tree(node, depth=0):
    """Return a pretty string representation of a Node tree with indentation."""
    indent = "  " * depth
    s = f"{indent}{node.name}\n"
    for child in node.get_children():
        s += pretty_tree(child, depth + 1)
    return s

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
    map_a = {}
    map_b = {}
    for nodeA, nodeB in mapping:
        if nodeA:
            map_a[nodeA] = nodeB
        if nodeB:
            map_b[nodeB] = nodeA

    def parse_node_name(name):
        """Returns tag, text for a node.name (e.g. 'p:hello' -> 'p', 'hello')"""
        if ':' in name:
            tag, text = name.split(':', 1)
        else:
            tag, text = name, ""
        return tag, text

    def walk(node_a, node_b):
        # Updated node: same mapped, but text differs
        if node_a and node_b and node_a.name != node_b.name:
            tag_a, text_a = parse_node_name(node_a.name)
            tag_b, text_b = parse_node_name(node_b.name)
            # Show update as modified content in the same tag, highlight changes
            children_a = node_a.get_children()
            children_b = node_b.get_children()
            # If leaf node (text node): show update inline
            if not children_a and not children_b:
                del_html = f"<del><{tag_a}>{text_a}</{tag_a}></del>"
                ins_html = f"<ins><{tag_b}>{text_b}</{tag_b}></ins>"
                return del_html + ins_html
            # Otherwise, show old subtree as deleted and new as inserted
            del_html = f"<del>" + walk(node_a, None) + "</del>"
            ins_html = f"<ins>" + walk(None, node_b) + "</ins>"
            return del_html + ins_html

        # Unchanged node (exact match)
        if node_a and node_b and node_a.name == node_b.name:
            tag, text = parse_node_name(node_a.name)
            children_a = node_a.get_children()
            if not children_a:
                return f"<{tag}>{text}</{tag}>"
            children_html = ''.join([walk(cA, map_a.get(cA)) for cA in children_a])
            return f"<{tag}>{children_html}</{tag}>"

        # Deletion (in A not in B)
        if node_a and not node_b:
            tag, text = parse_node_name(node_a.name)
            children_a = node_a.get_children()
            if not children_a:
                return f"<del class='diff-del'><{tag}>{text}</{tag}></del>"
            children_html = ''.join([walk(cA, None) for cA in children_a])
            return f"<del class='diff-del'><{tag}>{children_html}</{tag}></del>"

        # Insertion (in B not in A)
        if node_b and not node_a:
            tag, text = parse_node_name(node_b.name)
            children_b = node_b.get_children()
            if not children_b:
                return f"<ins class='diff-ins'><{tag}>{text}</{tag}></ins>"
            children_html = ''.join([walk(None, cB) for cB in children_b])
            return f"<ins class='diff-ins'><{tag}>{children_html}</{tag}></ins>"

        # Should not occur for well-formed trees/mapping
        return ""

    return walk(n1, n2)