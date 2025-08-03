from flask import Flask, request
from apted_demo import compute_diff, pretty_tree, diff_operations, build_diff_html

app = Flask(__name__)

@app.route("/", methods=["POST"])
def diff():
    """Generate a diff using APTED algorithm"""
    tree_a = tree_b = distance = diff_ops = None
    diff_html = None
    mapping = []
    if request.method == "POST":
        a = request.json.get("a", '')
        b = request.json.get("b", '')
        print('a:')
        print(a)
        print('b:')
        print(b)
        try:
            n1, n2, distance, mapping = compute_diff(a, b)
            tree_a = pretty_tree(n1)
            tree_b = pretty_tree(n2)
            diff_ops = diff_operations(n1, n2, mapping)
            diff_html = build_diff_html(n1, n2, mapping)

            print(diff_ops)
            print(diff_html)
        except Exception as e:
            tree_a = f"Error: {e}"
            tree_b = ""
            distance = ""
            diff_ops = []
            diff_html = None
    return {
        "diff_html": diff_html,
    }

if __name__ == "__main__":
    app.run(debug=True)