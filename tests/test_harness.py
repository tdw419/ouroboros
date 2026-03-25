"""Tests for Ouroboros V2 Protocol Harness."""

import os
import subprocess
import json
import pytest
from pathlib import Path


# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


class TestAlignmentValidation:
    """Test the validate-alignment CLI command."""

    def test_validate_alignment_safe_code(self):
        """Safe code should pass validation."""
        code = "def add(a, b): return a + b"
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT)
        result = subprocess.run(
            ["python3", "src/ouroboros/v2/harness.py", "validate-alignment", code],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            env=env
        )
        assert result.returncode == 0
        decision = json.loads(result.stdout)
        assert decision["approved"] is True

    def test_validate_alignment_dangerous_eval(self):
        """Code with eval() should be blocked."""
        code = "def run(code): return eval(code)"
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT)
        result = subprocess.run(
            ["python3", "src/ouroboros/v2/harness.py", "validate-alignment", code],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            env=env
        )
        decision = json.loads(result.stdout)
        assert decision["approved"] is False
        assert "PD-004" in decision.get("blocked_by", "")


class TestStatusCommand:
    """Test the status CLI command."""

    def test_status_returns_firewall_info(self):
        """Status should return firewall statistics."""
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT)
        result = subprocess.run(
            ["python3", "src/ouroboros/v2/harness.py", "status"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            env=env
        )
        assert result.returncode == 0
        status = json.loads(result.stdout)
        assert "firewall" in status
        assert "active" in status["firewall"]
        assert "directives_count" in status["firewall"]


class TestResearchCommands:
    """Test research-related CLI commands."""

    def test_get_best_metric_no_data(self):
        """get-best-metric should handle no data gracefully."""
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT)
        result = subprocess.run(
            ["python3", "src/ouroboros/v2/harness.py", "get-best-metric", "--metric", "val_bpb"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            env=env
        )
        # Should succeed even with no data
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "best_metric" in data
