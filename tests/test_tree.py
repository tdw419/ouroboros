"""Tests for the experiment tree module."""

from ouroboros.core.tree import ExperimentNode, ExperimentTree


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


def test_node_metadata_serialization():
    """Node metadata should serialize and deserialize correctly."""
    original = ExperimentNode(
        id="test_node",
        commit_hash="abc123",
        metric=0.5,
        hypothesis="Test hypothesis",
        time_spent_seconds=240.0,
        iterations_at_node=5,
        convergence_rate=-0.15,
    )

    # Convert to dict and back
    data = original.to_dict()
    restored = ExperimentNode.from_dict(data)

    assert restored.time_spent_seconds == 240.0
    assert restored.iterations_at_node == 5
    assert restored.convergence_rate == -0.15


def test_node_metadata_defaults():
    """Node metadata should have sensible defaults."""
    node = ExperimentNode(
        id="test_node",
        commit_hash="abc123",
        metric=0.5,
        hypothesis="Test hypothesis",
    )
    assert node.time_spent_seconds == 0.0
    assert node.iterations_at_node == 0
    assert node.convergence_rate is None


def test_convergence_rate_calculation():
    """Convergence rate should be calculated from parent to child metric."""
    tree = ExperimentTree()
    root = ExperimentNode(id="root", commit_hash="a1", metric=0.5, hypothesis="Start", status="baseline")
    child = ExperimentNode(
        id="n1", commit_hash="b2", metric=0.3, hypothesis="Better",
        parent_id="root", convergence_rate=-0.4  # 40% improvement
    )
    tree.add_node(root)
    tree.add_node(child)

    assert child.convergence_rate == -0.4


class TestExperimentTree:
    """Tests for the ExperimentTree class."""

    def test_tree_statistics(self):
        """Tree should provide summary statistics."""
        tree = ExperimentTree()
        tree.add_node(ExperimentNode(id="root", commit_hash="a1", metric=None, hypothesis="Start", parent_id=None, status="baseline"))
        tree.add_node(ExperimentNode(id="n1", commit_hash="b2", metric=0.5, hypothesis="Path A", parent_id="root", status="exhausted"))
        tree.add_node(ExperimentNode(id="n2", commit_hash="c3", metric=0.3, hypothesis="Path B", parent_id="root", status="active"))

        stats = tree.get_statistics()
        assert stats["total_nodes"] == 3
        assert stats["active_nodes"] == 1
        assert stats["exhausted_nodes"] == 1
        assert stats["max_depth"] == 1
        assert stats["best_metric"] == 0.3

    def test_flowchart_includes_metadata(self):
        """Flowchart should show convergence and timing info."""
        tree = ExperimentTree()
        tree.add_node(ExperimentNode(
            id="root", commit_hash="a1", metric=None, hypothesis="Start",
            parent_id=None, time_spent_seconds=10.0, status="baseline"
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
