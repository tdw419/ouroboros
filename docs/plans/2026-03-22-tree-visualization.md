# Tree Visualization & Strategic Navigation Enhancement

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a `ouroboros tree` CLI command that visualizes the experiment flowchart and enhance the tree metadata to support strategic AI navigation.

**Architecture:** Extend the existing `ExperimentTree` and `ExperimentNode` classes with richer metadata (time spent, iterations at node, convergence rate). Add a new CLI command that renders the tree as an ASCII flowchart with Rich formatting, and update the status command to show tree summary.

**Tech Stack:** Python 3.10+, Typer, Rich, PyYAML

---

## Task 1: Add Enhanced Metadata to ExperimentNode

**Files:**
- Modify: `src/ouroboros/core/tree.py:16-59`
- Test: `tests/test_tree.py`

**Step 1: Write the failing test for new metadata fields**

```python
# tests/test_tree.py
from ouroboros.core.tree import ExperimentNode

def test_node_has_timing_metadata():
    """Node should track time spent and iterations."""
    node = ExperimentNode(
        id="test_node",
        commit_hash="abc123",
        metric=0.5,
        hypothesis="Test hypothesis",
        time_spent_seconds=120.0,
        iterations_at_node=3,
        convergence_rate=-0.1  # Negative = improving
    )
    assert node.time_spent_seconds == 120.0
    assert node.iterations_at_node == 3
    assert node.convergence_rate == -0.1
```

**Step 2: Run test to verify it fails**

Run: `cd /home/jericho/zion/projects/ouroboros/ouroboros && python -m pytest tests/test_tree.py::test_node_has_timing_metadata -v`
Expected: FAIL with "unexpected keyword argument" or similar

**Step 3: Add metadata fields to ExperimentNode dataclass**

```python
# src/ouroboros/core/tree.py
# Add to ExperimentNode dataclass fields:
    time_spent_seconds: float = 0.0
    iterations_at_node: int = 0
    convergence_rate: Optional[float] = None  # Negative = improving
```

**Step 4: Update to_dict and from_dict methods**

```python
# In to_dict method, add:
    "time_spent_seconds": self.time_spent_seconds,
    "iterations_at_node": self.iterations_at_node,
    "convergence_rate": self.convergence_rate,

# In from_dict method, add:
    time_spent_seconds=data.get("time_spent_seconds", 0.0),
    iterations_at_node=data.get("iterations_at_node", 0),
    convergence_rate=data.get("convergence_rate"),
```

**Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_tree.py::test_node_has_timing_metadata -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/ouroboros/core/tree.py tests/test_tree.py
git commit -m "feat(tree): add timing and convergence metadata to ExperimentNode"
```

---

## Task 2: Add Tree Statistics Method

**Files:**
- Modify: `src/ouroboros/core/tree.py:62-149`
- Test: `tests/test_tree.py`

**Step 1: Write the failing test for tree statistics**

```python
# tests/test_tree.py
from ouroboros.core.tree import ExperimentTree, ExperimentNode

def test_tree_statistics():
    """Tree should provide summary statistics."""
    tree = ExperimentTree()
    tree.add_node(ExperimentNode(id="root", commit_hash="a1", metric=None, hypothesis="Start", parent_id=None))
    tree.add_node(ExperimentNode(id="n1", commit_hash="b2", metric=0.5, hypothesis="Path A", parent_id="root", status="exhausted"))
    tree.add_node(ExperimentNode(id="n2", commit_hash="c3", metric=0.3, hypothesis="Path B", parent_id="root", status="active"))

    stats = tree.get_statistics()
    assert stats["total_nodes"] == 3
    assert stats["active_nodes"] == 1
    assert stats["exhausted_nodes"] == 1
    assert stats["max_depth"] == 1
    assert stats["best_metric"] == 0.3
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_tree.py::test_tree_statistics -v`
Expected: FAIL with "ExperimentTree has no attribute 'get_statistics'"

**Step 3: Implement get_statistics method**

```python
# src/ouroboros/core/tree.py - add to ExperimentTree class
    def get_statistics(self) -> Dict[str, Any]:
        """Return summary statistics about the tree."""
        active = [n for n in self.nodes.values() if n.status == "active"]
        exhausted = [n for n in self.nodes.values() if n.status == "exhausted"]
        achieved = [n for n in self.nodes.values() if n.status == "achieved"]

        depths = [n.depth for n in self.nodes.values()]
        best = self.get_best_node(lower_is_better=True)

        return {
            "total_nodes": len(self.nodes),
            "active_nodes": len(active),
            "exhausted_nodes": len(exhausted),
            "achieved_nodes": len(achieved),
            "max_depth": max(depths) if depths else 0,
            "best_metric": best.metric if best else None,
            "best_node_id": best.id if best else None,
        }
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_tree.py::test_tree_statistics -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/ouroboros/core/tree.py tests/test_tree.py
git commit -m "feat(tree): add get_statistics method for tree summary"
```

---

## Task 3: Enhance ASCII Flowchart with Rich Formatting

**Files:**
- Modify: `src/ouroboros/core/tree.py:127-148`
- Test: `tests/test_tree.py`

**Step 1: Write the failing test for enhanced flowchart**

```python
# tests/test_tree.py
def test_flowchart_includes_metadata():
    """Flowchart should show convergence and timing info."""
    tree = ExperimentTree()
    tree.add_node(ExperimentNode(
        id="root", commit_hash="a1", metric=None, hypothesis="Start",
        parent_id=None, time_spent_seconds=10.0
    ))
    tree.add_node(ExperimentNode(
        id="n1", commit_hash="b2", metric=0.5, hypothesis="Path A",
        parent_id="root", status="exhausted", convergence_rate=-0.05,
        time_spent_seconds=60.0
    ))

    flowchart = tree.generate_ascii_flowchart()
    assert "Path A" in flowchart
    assert "[EXHAUSTED]" in flowchart
    assert "60.0s" in flowchart or "1.0m" in flowchart
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_tree.py::test_flowchart_includes_metadata -v`
Expected: FAIL - timing info not in output

**Step 3: Enhance generate_ascii_flowchart method**

```python
# src/ouroboros/core/tree.py - replace generate_ascii_flowchart method
    def generate_ascii_flowchart(self) -> str:
        """Generate a visual representation of the experiment tree."""
        if not self.root_id:
            return "Empty Tree"

        lines = ["EXPERIMENT FLOWCHART", "===================="]

        def format_time(seconds: float) -> str:
            if seconds < 60:
                return f"{seconds:.0f}s"
            elif seconds < 3600:
                return f"{seconds/60:.1f}m"
            else:
                return f"{seconds/3600:.1f}h"

        def render_node(node_id: str, prefix: str = "", is_last: bool = True):
            node = self.nodes[node_id]
            connector = "└── " if is_last else "├── "

            # Build status tag
            status_tag = f" [{node.status.upper()}]" if node.status != "active" else ""

            # Build metric string
            metric_str = f" (M: {node.metric:.6f})" if node.metric is not None else ""

            # Build timing string
            time_str = ""
            if node.time_spent_seconds > 0:
                time_str = f" ⏱{format_time(node.time_spent_seconds)}"

            # Build convergence indicator
            conv_str = ""
            if node.convergence_rate is not None:
                if node.convergence_rate < 0:
                    conv_str = f" 📉{node.convergence_rate:.3f}"
                elif node.convergence_rate > 0:
                    conv_str = f" 📈+{node.convergence_rate:.3f}"

            hypothesis_short = node.hypothesis[:40] + ("..." if len(node.hypothesis) > 40 else "")
            lines.append(f"{prefix}{connector}{node.id}: {hypothesis_short}{metric_str}{time_str}{conv_str}{status_tag}")

            new_prefix = prefix + ("    " if is_last else "│   ")
            child_count = len(node.children)
            for i, child_id in enumerate(node.children):
                render_node(child_id, new_prefix, i == child_count - 1)

        render_node(self.root_id)
        return "\n".join(lines)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_tree.py::test_flowchart_includes_metadata -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/ouroboros/core/tree.py tests/test_tree.py
git commit -m "feat(tree): enhance flowchart with timing and convergence info"
```

---

## Task 4: Add `ouroboros tree` CLI Command

**Files:**
- Modify: `src/ouroboros/cli.py:154-209`
- Test: Manual CLI test

**Step 1: Add the tree command to CLI**

```python
# src/ouroboros/cli.py - add new command after status command
@app.command()
def tree(
    workspace: Path = typer.Option(
        Path("."), "--workspace", "-w", help="Workspace directory"
    ),
    stats: bool = typer.Option(False, "--stats", "-s", help="Show tree statistics"),
):
    """Visualize the experiment tree/flowchart."""
    from .core.tree import ExperimentTree

    workspace = workspace.resolve()
    ouroboros_dir = workspace / ".ouroboros"

    if not ouroboros_dir.exists():
        console.print("❌ Not initialized. Run 'ouroboros init' first.")
        raise typer.Exit(1)

    tree_file = ouroboros_dir / "tree.yaml"
    if not tree_file.exists():
        console.print("❌ No tree file found. Run 'ouroboros run' first.")
        raise typer.Exit(1)

    exp_tree = ExperimentTree.load(tree_file)

    if stats:
        # Show statistics
        tree_stats = exp_tree.get_statistics()
        stats_table = Table(title="Experiment Tree Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")

        stats_table.add_row("Total Nodes", str(tree_stats["total_nodes"]))
        stats_table.add_row("Active Nodes", str(tree_stats["active_nodes"]))
        stats_table.add_row("Exhausted Nodes", str(tree_stats["exhausted_nodes"]))
        stats_table.add_row("Achieved Nodes", str(tree_stats["achieved_nodes"]))
        stats_table.add_row("Max Depth", str(tree_stats["max_depth"]))
        stats_table.add_row("Best Metric", str(tree_stats["best_metric"] or "N/A"))
        stats_table.add_row("Best Node", str(tree_stats["best_node_id"] or "N/A"))

        console.print(stats_table)
        console.print()

    # Show flowchart
    console.print("[bold]Experiment Flowchart:[/bold]")
    console.print()
    console.print(exp_tree.generate_ascii_flowchart())
```

**Step 2: Run manual CLI test**

Run: `cd demo_pi && ouroboros tree --stats`
Expected: Shows tree statistics table and ASCII flowchart

**Step 3: Verify command is registered**

Run: `ouroboros --help`
Expected: Shows `tree` command in list

**Step 4: Commit**

```bash
git add src/ouroboros/cli.py
git commit -m "feat(cli): add 'ouroboros tree' command for flowchart visualization"
```

---

## Task 5: Update Status Command to Show Tree Summary

**Files:**
- Modify: `src/ouroboros/cli.py:154-209`

**Step 1: Add tree summary to status command**

```python
# src/ouroboros/cli.py - add to status command, after results table
    # Show tree summary
    tree_file = ouroboros_dir / "tree.yaml"
    if tree_file.exists():
        from .core.tree import ExperimentTree
        exp_tree = ExperimentTree.load(tree_file)
        tree_stats = exp_tree.get_statistics()

        if tree_stats["total_nodes"] > 0:
            console.print()
            tree_summary = Table(title="Experiment Tree")
            tree_summary.add_column("Metric", style="cyan")
            tree_summary.add_column("Value", style="green")

            tree_summary.add_row("Nodes", f"{tree_stats['total_nodes']} (Active: {tree_stats['active_nodes']}, Exhausted: {tree_stats['exhausted_nodes']})")
            tree_summary.add_row("Max Depth", str(tree_stats["max_depth"]))
            tree_summary.add_row("Best Node", f"{tree_stats['best_node_id']} (Metric: {tree_stats['best_metric']})")

            console.print(tree_summary)
```

**Step 2: Run manual CLI test**

Run: `cd demo_pi && ouroboros status`
Expected: Shows tree summary table after results

**Step 3: Commit**

```bash
git add src/ouroboros/cli.py
git commit -m "feat(cli): add tree summary to status command"
```

---

## Task 6: Update Loop to Track Node Metadata

**Files:**
- Modify: `src/ouroboros/core/loop.py:186-206`

**Step 1: Update node creation to include timing**

```python
# src/ouroboros/core/loop.py - in the execution section where new_node is created
# Add timing tracking

# Before the execution loop section, add:
            start_time = time.time()

# In the node creation section, update:
                elapsed = time.time() - start_time
                new_node_id = f"node_{self.goal.iterations}"
                new_node = ExperimentNode(
                    id=new_node_id,
                    commit_hash=result.get("commit", self._get_current_commit()),
                    metric=result.get("metric"),
                    hypothesis=spec.hypothesis,
                    parent_id=self.current_node_id,
                    status="active" if result.get("status") == "keep" else "exhausted",
                    depth=self.tree.get_node(self.current_node_id).depth + 1,
                    time_spent_seconds=elapsed,
                    iterations_at_node=1,
                )
```

**Step 2: Run manual test with dry-run**

Run: `cd demo_pi && ouroboros run --dry-run --max-iter 2`
Expected: Runs without errors

**Step 3: Commit**

```bash
git add src/ouroboros/core/loop.py
git commit -m "feat(loop): track timing metadata in experiment nodes"
```

---

## Task 7: Add Convergence Rate Calculation

**Files:**
- Modify: `src/ouroboros/core/loop.py`
- Test: `tests/test_tree.py`

**Step 1: Write test for convergence rate**

```python
# tests/test_tree.py
def test_convergence_rate_calculation():
    """Convergence rate should be calculated from parent to child metric."""
    tree = ExperimentTree()
    root = ExperimentNode(id="root", commit_hash="a1", metric=0.5, hypothesis="Start")
    child = ExperimentNode(
        id="n1", commit_hash="b2", metric=0.3, hypothesis="Better",
        parent_id="root", convergence_rate=-0.4  # 40% improvement
    )
    tree.add_node(root)
    tree.add_node(child)

    assert child.convergence_rate == -0.4
```

**Step 2: Add convergence calculation to loop**

```python
# src/ouroboros/core/loop.py - in node creation section
# Calculate convergence rate from parent
                parent_node = self.tree.get_node(self.current_node_id)
                convergence_rate = None
                if parent_node and parent_node.metric is not None and result.get("metric") is not None:
                    if parent_node.metric != 0:
                        convergence_rate = (result["metric"] - parent_node.metric) / abs(parent_node.metric)

                new_node = ExperimentNode(
                    id=new_node_id,
                    commit_hash=result.get("commit", self._get_current_commit()),
                    metric=result.get("metric"),
                    hypothesis=spec.hypothesis,
                    parent_id=self.current_node_id,
                    status="active" if result.get("status") == "keep" else "exhausted",
                    depth=self.tree.get_node(self.current_node_id).depth + 1,
                    time_spent_seconds=elapsed,
                    iterations_at_node=1,
                    convergence_rate=convergence_rate,
                )
```

**Step 3: Run test**

Run: `python -m pytest tests/test_tree.py::test_convergence_rate_calculation -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/ouroboros/core/loop.py tests/test_tree.py
git commit -m "feat(loop): calculate and track convergence rate between nodes"
```

---

## Task 8: Create Test File Structure

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_tree.py`

**Step 1: Create tests directory and init file**

```bash
mkdir -p tests
touch tests/__init__.py
```

**Step 2: Create comprehensive test file**

```python
# tests/test_tree.py
"""
Tests for ExperimentTree and ExperimentNode classes.
"""
import pytest
from pathlib import Path
from ouroboros.core.tree import ExperimentNode, ExperimentTree


class TestExperimentNode:
    """Tests for ExperimentNode dataclass."""

    def test_node_creation_basic(self):
        """Create a basic node."""
        node = ExperimentNode(
            id="test",
            commit_hash="abc123",
            metric=0.5,
            hypothesis="Test hypothesis"
        )
        assert node.id == "test"
        assert node.commit_hash == "abc123"
        assert node.metric == 0.5
        assert node.status == "active"

    def test_node_has_timing_metadata(self):
        """Node should track time spent and iterations."""
        node = ExperimentNode(
            id="test_node",
            commit_hash="abc123",
            metric=0.5,
            hypothesis="Test hypothesis",
            time_spent_seconds=120.0,
            iterations_at_node=3,
            convergence_rate=-0.1
        )
        assert node.time_spent_seconds == 120.0
        assert node.iterations_at_node == 3
        assert node.convergence_rate == -0.1

    def test_node_serialization(self):
        """Node should serialize to dict and back."""
        node = ExperimentNode(
            id="test",
            commit_hash="abc",
            metric=0.5,
            hypothesis="Test",
            time_spent_seconds=60.0
        )
        data = node.to_dict()
        restored = ExperimentNode.from_dict(data)
        assert restored.id == node.id
        assert restored.time_spent_seconds == 60.0


class TestExperimentTree:
    """Tests for ExperimentTree class."""

    def test_empty_tree(self):
        """Create an empty tree."""
        tree = ExperimentTree()
        assert len(tree.nodes) == 0
        assert tree.root_id is None

    def test_add_root_node(self):
        """Add a root node."""
        tree = ExperimentTree()
        root = ExperimentNode(id="root", commit_hash="a1", metric=None, hypothesis="Start")
        tree.add_node(root)
        assert tree.root_id == "root"
        assert len(tree.nodes) == 1

    def test_add_child_node(self):
        """Add a child node."""
        tree = ExperimentTree()
        root = ExperimentNode(id="root", commit_hash="a1", metric=None, hypothesis="Start", parent_id=None)
        tree.add_node(root)
        child = ExperimentNode(id="child", commit_hash="b2", metric=0.5, hypothesis="Test", parent_id="root")
        tree.add_node(child)

        assert len(tree.nodes) == 2
        assert "child" in tree.nodes["root"].children
        assert tree.nodes["child"].parent_id == "root"

    def test_tree_statistics(self):
        """Tree should provide summary statistics."""
        tree = ExperimentTree()
        tree.add_node(ExperimentNode(id="root", commit_hash="a1", metric=None, hypothesis="Start", parent_id=None))
        tree.add_node(ExperimentNode(id="n1", commit_hash="b2", metric=0.5, hypothesis="Path A", parent_id="root", status="exhausted"))
        tree.add_node(ExperimentNode(id="n2", commit_hash="c3", metric=0.3, hypothesis="Path B", parent_id="root", status="active"))

        stats = tree.get_statistics()
        assert stats["total_nodes"] == 3
        assert stats["active_nodes"] == 1
        assert stats["exhausted_nodes"] == 1
        assert stats["max_depth"] == 1
        assert stats["best_metric"] == 0.3

    def test_flowchart_generation(self):
        """Tree should generate ASCII flowchart."""
        tree = ExperimentTree()
        tree.add_node(ExperimentNode(id="root", commit_hash="a1", metric=None, hypothesis="Start", parent_id=None))
        tree.add_node(ExperimentNode(id="n1", commit_hash="b2", metric=0.5, hypothesis="Path A", parent_id="root", status="exhausted"))

        flowchart = tree.generate_ascii_flowchart()
        assert "EXPERIMENT FLOWCHART" in flowchart
        assert "root" in flowchart
        assert "n1" in flowchart
        assert "[EXHAUSTED]" in flowchart

    def test_flowchart_includes_metadata(self):
        """Flowchart should show convergence and timing info."""
        tree = ExperimentTree()
        tree.add_node(ExperimentNode(
            id="root", commit_hash="a1", metric=None, hypothesis="Start",
            parent_id=None, time_spent_seconds=10.0
        ))
        tree.add_node(ExperimentNode(
            id="n1", commit_hash="b2", metric=0.5, hypothesis="Path A",
            parent_id="root", status="exhausted", convergence_rate=-0.05,
            time_spent_seconds=60.0
        ))

        flowchart = tree.generate_ascii_flowchart()
        assert "Path A" in flowchart
        assert "[EXHAUSTED]" in flowchart
        assert "60.0s" in flowchart or "1.0m" in flowchart

    def test_get_best_node(self):
        """Should find the node with best metric."""
        tree = ExperimentTree()
        tree.add_node(ExperimentNode(id="root", commit_hash="a1", metric=1.0, hypothesis="Start"))
        tree.add_node(ExperimentNode(id="n1", commit_hash="b2", metric=0.5, hypothesis="Better", parent_id="root"))
        tree.add_node(ExperimentNode(id="n2", commit_hash="c3", metric=0.3, hypothesis="Best", parent_id="root"))

        best = tree.get_best_node(lower_is_better=True)
        assert best.id == "n2"
        assert best.metric == 0.3

    def test_convergence_rate_calculation(self):
        """Convergence rate should be calculated from parent to child metric."""
        tree = ExperimentTree()
        root = ExperimentNode(id="root", commit_hash="a1", metric=0.5, hypothesis="Start")
        child = ExperimentNode(
            id="n1", commit_hash="b2", metric=0.3, hypothesis="Better",
            parent_id="root", convergence_rate=-0.4
        )
        tree.add_node(root)
        tree.add_node(child)

        assert child.convergence_rate == -0.4
```

**Step 3: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add tests/
git commit -m "test: add comprehensive tests for tree module"
```

---

## Task 9: Update README Documentation

**Files:**
- Modify: `README.md`

**Step 1: Add tree command documentation**

```markdown
# Add to README.md after the commands section

### Tree Visualization

View the experiment tree/flowchart:

```bash
# Show the experiment flowchart
ouroboros tree

# Show statistics about the tree
ouroboros tree --stats
```

The tree shows:
- **Nodes**: Each experiment attempt
- **Metrics**: The result metric (M: 0.000123)
- **Timing**: Time spent on each node (⏱30s)
- **Convergence**: Improvement direction (📉-0.1 = improving)
- **Status**: [ACTIVE], [EXHAUSTED], [ACHIEVED], [BASELINE]

Example output:
```
EXPERIMENT FLOWCHART
====================
└── root: Initial state [BASELINE]
    ├── node_1: Increase Leibniz iterations (M: 0.042310) ⏱45s [EXHAUSTED]
    └── node_2: Switch to Nilakantha series (M: 0.000006) ⏱32s 📉-0.999 [ACTIVE]
```

### Strategic Backtracking

The AI can decide to **PIVOT** to a previous node when a path is exhausted:

```
📍 Current Path: node_5
🔀 PIVOTING to node: node_2
```

This allows exploring alternative approaches without losing progress.
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add tree visualization documentation"
```

---

## Final Verification

**Step 1: Run all tests**

```bash
python -m pytest tests/ -v
```

**Step 2: Run full integration test**

```bash
cd demo_pi
ouroboros reset --yes
ouroboros run --dry-run --max-iter 3
ouroboros tree --stats
ouroboros status
```

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete tree visualization and strategic navigation system"
```
