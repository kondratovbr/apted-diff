/**
 * Parse XML string into tree structure
 */
function parseXML(xmlString) {
    console.log('[ZSDiff] parseXML called with:', xmlString);
    const parser = new DOMParser();
    const doc = parser.parseFromString(xmlString, "application/xml");

    function buildTree(node) {
        if (node.nodeType === 3) { // Text node
            const text = node.nodeValue.trim();
            return text ? new TreeNode(`#text:${text}`) : null;
        }
        const label = node.tagName;
        const children = [];
        node.childNodes.forEach(child => {
            const childTree = buildTree(child);
            if (childTree) children.push(childTree);
        });
        return new TreeNode(label, children);
    }

    const tree = buildTree(doc.documentElement);
    console.log('[ZSDiff] Parsed tree:', tree);
    return tree;
}

/**
 * Tree Node
 */
class TreeNode {
    constructor(label, children = []) {
        this.label = label;
        this.children = children;
    }
}

/**
 * Postorder traversal
 */
function postorderTraversal(node, result = []) {
    // Logs every traversal call for deep trees. To avoid flooding, only log top
    if (result.length === 0) {
        console.log('[ZSDiff] postorderTraversal START for:', node.label);
    }
    if (!node) return result;
    for (let child of node.children) {
        postorderTraversal(child, result);
    }
    result.push(node);
    if (result.length === 1) {
        console.log('[ZSDiff] postorderTraversal END. Result:', result.map(n => n.label));
    }
    return result;
}

/**
 * Leftmost and Keyroots helpers
 */
function computeLeftmost(nodes) {
    console.log('[ZSDiff] computeLeftmost on', nodes.map(n => n.label));
    const leftmost = new Array(nodes.length);
    for (let i = 0; i < nodes.length; i++) {
        if (nodes[i].children.length === 0) {
            leftmost[i] = i;
        } else {
            leftmost[i] = leftmost[i - nodes[i].children.length];
        }
    }
    console.log('[ZSDiff] leftmost:', leftmost);
    return leftmost;
}

function computeKeyroots(leftmost) {
    console.log('[ZSDiff] computeKeyroots, leftmost:', leftmost);
    const seen = new Set();
    const keyroots = [];
    for (let i = 0; i < leftmost.length; i++) {
        seen.add(leftmost[i]);
    }
    for (let i = 0; i < leftmost.length; i++) {
        if (!seen.has(i)) {
            keyroots.push(i);
        }
    }
    keyroots.push(leftmost.length - 1);
    const sortedKeyroots = keyroots.sort((a, b) => a - b);
    console.log('[ZSDiff] keyroots:', sortedKeyroots);
    return sortedKeyroots;
}

/**
 * Tree Edit Distance with Diff
 */
function treeEditDistanceWithDiff(tree1, tree2) {
    console.log('[ZSDiff] treeEditDistanceWithDiff called');
    const T1 = postorderTraversal(tree1);
    const T2 = postorderTraversal(tree2);
    console.log('[ZSDiff] Postorder T1:', T1.map(n => n.label));
    console.log('[ZSDiff] Postorder T2:', T2.map(n => n.label));

    const l1 = computeLeftmost(T1);
    const l2 = computeLeftmost(T2);

    const keyroots1 = computeKeyroots(l1);
    const keyroots2 = computeKeyroots(l2);

    const treedist = Array.from({ length: T1.length + 1 }, () => Array(T2.length + 1).fill(0));
    const operations = Array.from({ length: T1.length + 1 }, () => Array(T2.length + 1).fill(null));

    const costInsert = 1;
    const costDelete = 1;
    const costReplace = (a, b) => (a === b ? 0 : 1);

    function forestDist(i, j) {
        console.log(`[ZSDiff] forestDist: i=${i}, j=${j}`);
        const m = i - l1[i] + 2;
        const n = j - l2[j] + 2;

        const fd = Array.from({ length: m }, () => Array(n).fill(0));
        const op = Array.from({ length: m }, () => Array(n).fill(null));

        for (let x = 1; x < m; x++) {
            fd[x][0] = fd[x - 1][0] + costDelete;
            op[x][0] = { op: 'delete', node: T1[l1[i] + x - 1].label };
        }
        for (let y = 1; y < n; y++) {
            fd[0][y] = fd[0][y - 1] + costInsert;
            op[0][y] = { op: 'insert', node: T2[l2[j] + y - 1].label };
        }

        for (let x = 1; x < m; x++) {
            for (let y = 1; y < n; y++) {
                const iIndex = l1[i] + x - 1;
                const jIndex = l2[j] + y - 1;

                if (l1[iIndex] === l1[i] && l2[jIndex] === l2[j]) {
                    const delCost = fd[x - 1][y] + costDelete;
                    const insCost = fd[x][y - 1] + costInsert;
                    const repCost = fd[x - 1][y - 1] + costReplace(T1[iIndex].label, T2[jIndex].label);

                    if (repCost <= delCost && repCost <= insCost) {
                        fd[x][y] = repCost;
                        op[x][y] = (costReplace(T1[iIndex].label, T2[jIndex].label) === 0)
                            ? { op: 'match', from: T1[iIndex].label }
                            : { op: 'rename', from: T1[iIndex].label, to: T2[jIndex].label };
                    } else if (delCost <= insCost) {
                        fd[x][y] = delCost;
                        op[x][y] = { op: 'delete', node: T1[iIndex].label };
                    } else {
                        fd[x][y] = insCost;
                        op[x][y] = { op: 'insert', node: T2[jIndex].label };
                    }

                    treedist[iIndex][jIndex] = fd[x][y];
                    operations[iIndex][jIndex] = op[x][y];
                } else {
                    const delCost = fd[x - 1][y] + costDelete;
                    const insCost = fd[x][y - 1] + costInsert;
                    const matchCost = fd[x - 1][y - 1] + treedist[iIndex][jIndex];

                    if (matchCost <= delCost && matchCost <= insCost) {
                        fd[x][y] = matchCost;
                        op[x][y] = operations[iIndex][jIndex];
                    } else if (delCost <= insCost) {
                        fd[x][y] = delCost;
                        op[x][y] = { op: 'delete', node: T1[iIndex].label };
                    } else {
                        fd[x][y] = insCost;
                        op[x][y] = { op: 'insert', node: T2[jIndex].label };
                    }
                }
            }
        }
        // Print sample of op and fd matrixes for diagnostics, not full (could be huge).
        console.log('[ZSDiff] forestDist op sample:', op[Math.min(1, op.length-1)]);
        console.log('[ZSDiff] forestDist fd sample:', fd[Math.min(1, fd.length-1)]);
        return { cost: fd[m - 1][n - 1], ops: backtrack(op, m - 1, n - 1) };
    }

    function backtrack(op, i, j) {
        const result = [];
        while (i > 0 || j > 0) {
            result.unshift(op[i][j]);
            if (op[i][j] && op[i][j].op === 'delete') {
                i--;
            } else if (op[i][j] && op[i][j].op === 'insert') {
                j--;
            } else {
                i--;
                j--;
            }
        }
        console.log('[ZSDiff] Final diff ops:', result.filter(Boolean));
        return result.filter(Boolean);
    }

    let diffOps = [];
    for (let i of keyroots1) {
        for (let j of keyroots2) {
            const { ops } = forestDist(i, j);
            diffOps = ops;
        }
    }

    const result = { distance: treedist[T1.length - 1][T2.length - 1], diff: diffOps };
    console.log('[ZSDiff] treeEditDistanceWithDiff RESULT:', result);
    return result;
}
