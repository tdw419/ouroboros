# tests/test_researcher.py
"""Tests for Autonomous Research Engine."""

import pytest
import json
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ouroboros.v2.researcher import ResearchEngine

class TestResearchEngine:
    """Test the ResearchEngine class."""

    def test_init_creates_results_file(self, tmp_path: Path):
        """Initialization should create results directory."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        autoresearch = tmp_path / "autoresearch"
        autoresearch.mkdir()

        engine = ResearchEngine(workspace, autoresearch)
        assert engine.results_file.parent.exists()

    def test_get_best_metric_empty(self, tmp_path: Path):
        """get_best_metric should return None when no results exist."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        autoresearch = tmp_path / "autoresearch"
        autoresearch.mkdir()

        engine = ResearchEngine(workspace, autoresearch)
        result = engine.get_best_metric("val_bpb")
        assert result is None

    def test_get_best_metric_with_data(self, tmp_path: Path):
        """get_best_metric should return the minimum for val_bpb."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        autoresearch = tmp_path / "autoresearch"
        autoresearch.mkdir()

        engine = ResearchEngine(workspace, autoresearch)

        # Manually populate results
        engine._save_result({"success": True, "val_bpb": 2.5})
        engine._save_result({"success": True, "val_bpb": 2.1})
        engine._save_result({"success": True, "val_bpb": 2.3})

        best = engine.get_best_metric("val_bpb", minimize=True)
        assert best == 2.1

    def test_get_best_metric_maximize(self, tmp_path: Path):
        """get_best_metric should return the maximum when minimize=False."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        autoresearch = tmp_path / "autoresearch"
        autoresearch.mkdir()

        engine = ResearchEngine(workspace, autoresearch)

        engine._save_result({"success": True, "mfu_percent": 45.0})
        engine._save_result({"success": True, "mfu_percent": 52.0})

        best = engine.get_best_metric("mfu_percent", minimize=False)
        assert best == 52.0

    def test_parse_output_extracts_metrics(self, tmp_path: Path):
        """_parse_output should extract metrics from training output."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        autoresearch = tmp_path / "autoresearch"
        autoresearch.mkdir()

        engine = ResearchEngine(workspace, autoresearch)

        output = """
Training complete!
val_bpb: 2.34
peak_vram_mb: 1024.5
mfu_percent: 48.2
num_params_M: 125.6
depth: 12
"""
        metrics = engine._parse_output(output)

        assert metrics["val_bpb"] == 2.34
        assert metrics["peak_vram_mb"] == 1024.5
        assert metrics["mfu_percent"] == 48.2
        assert metrics["num_params_M"] == 125.6
        assert metrics["depth"] == 12
