from flask import send_file, send_from_directory
import os
from flask import Flask, render_template_string, request
from apted_demo import compute_diff, pretty_tree, diff_operations

app = Flask(__name__)

@app.route('/zs-demo')
def zs_demo():
    # Serve the demo HTML file from the js/ directory
    return send_file(os.path.join('js', 'demo.html'))

@app.route('/js/<path:filename>')
def js_static(filename):
    # Serve JS files from the js/ directory
    return send_from_directory('js', filename)

EXAMPLE_A = """<article>
  <h2>Welcome to PearAI Demo</h2>
  <p>
    This is a <b>simple example article</b> to demonstrate <i>HTML/XML Tree Diff</i>.<br/>
    Compare this text to see how <b>small edits</b> are detected and rendered.
  </p>
  <ul>
    <li>First item</li>
    <li>Second item</li>
    <li>Third item</li>
  </ul>
  <p>End of article.</p>
</article>"""

EXAMPLE_B = """<article>
  <h2>Welcome to the PearAI Demo!</h2>
  <p>
    This is a <b>simple article</b> showing <i>HTML/XML Tree Diff</i>.<br/>
    Try comparing it and see how <b>changes</b> are detected and visualized.
  </p>
  <ul>
    <li>First item</li>
    <li>Second entry</li>
    <li>Fourth item</li>
  </ul>
  <p>The end of this article.</p>
</article>"""

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>HTML/XML Tree Diff Demo</title>
    <style>
        body { font-family: system-ui, sans-serif; margin: 2rem; }
        textarea { width: 45vw; height: 18vh; font-family: monospace; }
        .diff-op-unchanged { color: #888; }
        .diff-op-update { color: #e2a200; }
        .diff-op-insert { color: #29862d; }
        .diff-op-delete { color: #c62828; }
        pre { background: #fafcff; padding: 0.8em; border-radius: 6px; font-size: 1em; }
    </style>
</head>
<body>
    <h1>HTML/XML Tree Diff Demo (APTED)</h1>
    <form method="post">
        <div>
            <label>Text A:</label><br>
            <textarea name="a">{{example_a}}</textarea>
        </div>
        <div>
            <label>Text B:</label><br>
            <textarea name="b">{{example_b}}</textarea>
        </div>
        <div style="margin: 1em 0;">
            <button type="submit">Diff!</button>
        </div>
    </form>
    {% if tree_a and tree_b %}
    <div style="display:flex; gap:3rem; align-items:flex-start; margin-bottom: 2em;">
      <div>
        <h2>Text A (Rendered):</h2>
        <div style="border:1px solid #eee; border-radius:7px; padding:0.7em; background:#fffef3; min-width:250px;">
          {{ example_a | safe }}
        </div>
      </div>
      <div>
        <h2>Text B (Rendered):</h2>
        <div style="border:1px solid #eee; border-radius:7px; padding:0.7em; background:#f7fff7; min-width:250px;">
          {{ example_b | safe }}
        </div>
      </div>
    </div>
    <h2>Input A (Parsed Tree):</h2>
    <pre>{{ tree_a }}</pre>
    <h2>Input B (Parsed Tree):</h2>
    <pre>{{ tree_b }}</pre>
    <h2>APTED Distance: {{distance}}</h2>
    {% if mapping %}
    <h3>Raw Mapping:</h3>
    <pre style="font-size:1em;">
{% for pair in mapping %}
  {{ pair[0].name if pair[0] else 'None' }} → {{ pair[1].name if pair[1] else 'None' }}
{% endfor %}
    </pre>
    {% endif %}
    {% if diff_html %}
    <h2>Rendered Diff (in-article):</h2>
    <div style="border:1px solid #dde5e9; background:#f9fafd; border-radius:8px; padding:1.3em; margin-bottom:1em; font-size:1.05em; max-width:900px;">
      <style>
        .diff-del { background: #ffecec; color:#c62828; text-decoration: line-through; padding: 0 .2em; border-radius:3px; }
        .diff-ins { background: #e6ffed; color:#1b4b1a; padding: 0 .2em; border-radius:3px; }
        .diff-upd { background: #fffbe8; color:#876700; padding: 0 .2em; border-radius:3px;}
      </style>
      {{ diff_html | safe }}
    </div>
    {% endif %}
    {% endif %}
    <hr>
    <div style="font-size:0.9em;">Powered by <a href="https://github.com/JoaoFelipe/apted" target="_blank">APTED</a>. Quick demo by PearAI.</div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    a = EXAMPLE_A
    b = EXAMPLE_B
    tree_a = tree_b = distance = diff_ops = None
    from apted_demo import build_diff_html
    diff_html = None
    mapping = []
    if request.method == "POST":
        a = request.form.get("a", a)
        b = request.form.get("b", b)
        try:
            n1, n2, distance, mapping = compute_diff(a, b)
            tree_a = pretty_tree(n1)
            tree_b = pretty_tree(n2)
            diff_ops = diff_operations(n1, n2, mapping)
            diff_html = build_diff_html(n1, n2, mapping)
        except Exception as e:
            tree_a = f"Error: {e}"
            tree_b = ""
            distance = ""
            diff_ops = []
            diff_html = None
    return render_template_string(
        TEMPLATE,
        example_a=a,
        example_b=b,
        tree_a=tree_a,
        tree_b=tree_b,
        distance=distance,
        diff_ops=diff_ops or [],
        diff_html=diff_html,
        mapping=mapping or []
    )

if __name__ == "__main__":
    app.run(debug=True)