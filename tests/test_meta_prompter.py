# tests/test_meta_prompter.py
"""Tests for Meta-Prompt Engine integration."""

import subprocess
import json
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class TestMetaPrompterCLI:
    """Test meta_prompter.py CLI commands."""

    def test_update_with_empty_insights(self, tmp_path: Path):
        """Update command should handle empty insights."""
        env = {"PYTHONPATH": str(PROJECT_ROOT)}
        result = subprocess.run(
            ["python3", "src/ouroboros/v2/meta_prompter.py", "update", "{}"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            env=env
        )
        # Should succeed or return valid JSON
        assert result.returncode == 0 or "new_rules" in result.stdout

    def test_get_current_returns_json(self):
        """get-current command should return JSON with rules."""
        env = {"PYTHONPATH": str(PROJECT_ROOT)}
        result = subprocess.run(
            ["python3", "src/ouroboros/v2/meta_prompter.py", "get-current"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            env=env
        )
        # Should return valid JSON
        data = json.loads(result.stdout)
        assert "rules" in data

    def test_update_with_failure_insights(self):
        """Update command should create rules from failure patterns."""
        env = {"PYTHONPATH": str(PROJECT_ROOT)}
        insights = json.dumps([
            "Test failed due to timeout error",
            "Build failed with compilation error",
            "Another timeout error occurred",
        ])
        result = subprocess.run(
            ["python3", "src/ouroboros/v2/meta_prompter.py", "update", insights],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            env=env
        )
        # Should return valid JSON with new_rules
        data = json.loads(result.stdout)
        assert "new_rules" in data

    def test_get_current_includes_statistics(self):
        """get-current command should include statistics."""
        env = {"PYTHONPATH": str(PROJECT_ROOT)}
        result = subprocess.run(
            ["python3", "src/ouroboros/v2/meta_prompter.py", "get-current"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            env=env
        )
        data = json.loads(result.stdout)
        assert "statistics" in data
        assert "prompt_length" in data
