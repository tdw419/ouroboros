"""
Tests for the Watchdog Self-Healing Protocol.

Tests validate the dependency manager, watchdog agent, and
self-healing loop functionality.
"""

import pytest
import json
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.ouroboros.protocols.watchdog import (
    HealthStatus,
    RecoveryAction,
    HealthCheck,
    ModificationRecord,
    WatchdogConfig,
    DependencyManager,
    WatchdogAgent,
    SelfHealingLoop,
)


@pytest.fixture
def workspace(tmp_path):
    """Create a temporary workspace directory."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def state_dir(workspace):
    """Create a temporary state directory."""
    state_dir = workspace / ".ouroboros"
    state_dir.mkdir()
    return state_dir


@pytest.fixture
def config():
    """Create a test watchdog configuration."""
    return WatchdogConfig(
        check_interval_seconds=0.1,
        hang_timeout_seconds=0.5,
        max_consecutive_failures=2,
        rollback_on_unhealthy=True,
        restart_on_hang=True,
    )


@pytest.fixture
def dependency_manager(workspace, state_dir):
    """Create a DependencyManager for testing."""
    return DependencyManager(workspace, state_dir)


@pytest.fixture
def watchdog_agent(config, dependency_manager):
    """Create a WatchdogAgent for testing."""
    return WatchdogAgent(config, dependency_manager)


class TestHealthStatus:
    """Test HealthStatus enum."""

    def test_health_status_values(self):
        """HealthStatus should have expected values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.CRITICAL.value == "critical"


class TestRecoveryAction:
    """Test RecoveryAction enum."""

    def test_recovery_action_values(self):
        """RecoveryAction should have expected values."""
        assert RecoveryAction.NONE.value == "none"
        assert RecoveryAction.ROLLBACK.value == "rollback"
        assert RecoveryAction.RESTART.value == "restart"


class TestHealthCheck:
    """Test HealthCheck dataclass."""

    def test_health_check_creation(self):
        """HealthCheck should be created with required fields."""
        check = HealthCheck(
            status=HealthStatus.HEALTHY,
            message="All checks passed",
        )
        assert check.status == HealthStatus.HEALTHY
        assert check.message == "All checks passed"
        assert check.timestamp is not None

    def test_health_check_with_details(self):
        """HealthCheck should accept optional details."""
        check = HealthCheck(
            status=HealthStatus.DEGRADED,
            message="Partial failure",
            details={"disk": "low", "memory": "ok"},
        )
        assert check.details["disk"] == "low"


class TestModificationRecord:
    """Test ModificationRecord dataclass."""

    def test_modification_record_creation(self):
        """ModificationRecord should track all fields."""
        record = ModificationRecord(
            id="MOD-001",
            timestamp=datetime.now(),
            files_changed=["test.py", "main.py"],
            diff="--- test.py\n+++ test.py\n@@ -1 +1 @@\n-old\n+new",
        )
        assert record.id == "MOD-001"
        assert len(record.files_changed) == 2
        assert record.rolled_back is False
        assert record.commit_sha is None

    def test_modification_record_with_commit(self):
        """ModificationRecord should track commit SHA."""
        record = ModificationRecord(
            id="MOD-002",
            timestamp=datetime.now(),
            files_changed=["test.py"],
            diff="changes",
            commit_sha="abc123",
        )
        assert record.commit_sha == "abc123"


class TestWatchdogConfig:
    """Test WatchdogConfig dataclass."""

    def test_default_config(self):
        """Default config should have sensible values."""
        config = WatchdogConfig()
        assert config.check_interval_seconds == 5.0
        assert config.hang_timeout_seconds == 60.0
        assert config.max_consecutive_failures == 3
        assert config.rollback_on_unhealthy is True

    def test_custom_config(self):
        """Custom config should override defaults."""
        config = WatchdogConfig(
            check_interval_seconds=1.0,
            max_consecutive_failures=5,
        )
        assert config.check_interval_seconds == 1.0
        assert config.max_consecutive_failures == 5


class TestDependencyManager:
    """Test DependencyManager class."""

    def test_initialization(self, dependency_manager):
        """DependencyManager should initialize empty."""
        assert len(dependency_manager.modifications) == 0

    def test_record_modification(self, dependency_manager):
        """Recording a modification should add to history."""
        record = dependency_manager.record_modification(
            files_changed=["test.py"],
            diff="test diff",
        )
        assert len(dependency_manager.modifications) == 1
        assert record.id.startswith("MOD-")
        assert record.files_changed == ["test.py"]
        assert record.diff == "test diff"

    def test_record_modification_persists(self, dependency_manager, state_dir):
        """Modifications should persist to disk."""
        dependency_manager.record_modification(
            files_changed=["test.py"],
            diff="test diff",
        )

        # Create new manager to load from disk
        new_manager = DependencyManager(dependency_manager.workspace, state_dir)
        assert len(new_manager.modifications) == 1

    def test_get_last_modification(self, dependency_manager):
        """get_last_modification should return most recent non-rolled-back."""
        dependency_manager.record_modification(["a.py"], "diff1")
        dependency_manager.record_modification(["b.py"], "diff2")

        last = dependency_manager.get_last_modification()
        assert last.files_changed == ["b.py"]

    def test_get_last_modification_ignores_rolled_back(self, dependency_manager):
        """Should skip rolled-back modifications."""
        r1 = dependency_manager.record_modification(["a.py"], "diff1")
        dependency_manager.record_modification(["b.py"], "diff2")

        # Roll back the second one
        dependency_manager.modifications[-1].rolled_back = True

        last = dependency_manager.get_last_modification()
        assert last.id == r1.id

    def test_get_last_modification_returns_none_when_empty(self, dependency_manager):
        """Should return None when no modifications exist."""
        assert dependency_manager.get_last_modification() is None

    def test_update_health_after(self, dependency_manager):
        """Should update health status after modification."""
        record = dependency_manager.record_modification(["test.py"], "diff")
        assert record.health_after is None

        dependency_manager.update_health_after(record.id, HealthStatus.HEALTHY)
        updated = dependency_manager.modifications[0]
        assert updated.health_after == HealthStatus.HEALTHY

    def test_rollback_no_modifications(self, dependency_manager):
        """Rollback should fail when no modifications exist."""
        success, msg = dependency_manager.rollback_last()
        assert success is False
        assert "No modifications" in msg


class TestWatchdogAgent:
    """Test WatchdogAgent class."""

    def test_initialization(self, watchdog_agent):
        """WatchdogAgent should initialize with correct state."""
        assert watchdog_agent._running is False
        assert watchdog_agent._consecutive_failures == 0
        assert watchdog_agent._health_status == HealthStatus.HEALTHY

    def test_start_and_stop(self, watchdog_agent):
        """WatchdogAgent should start and stop cleanly."""
        watchdog_agent.start()
        assert watchdog_agent._running is True
        time.sleep(0.2)  # Let it run a bit
        watchdog_agent.stop()
        assert watchdog_agent._running is False

    def test_heartbeat(self, watchdog_agent):
        """Heartbeat should update last_heartbeat time."""
        watchdog_agent._last_heartbeat = None
        watchdog_agent.heartbeat()
        assert watchdog_agent._last_heartbeat is not None

    def test_heartbeat_resets_failures(self, watchdog_agent):
        """Heartbeat should reset consecutive failures."""
        watchdog_agent._consecutive_failures = 5
        watchdog_agent.heartbeat()
        assert watchdog_agent._consecutive_failures == 0

    def test_run_health_check_healthy(self, watchdog_agent):
        """Health check should return healthy for valid workspace."""
        health = watchdog_agent._run_health_check()
        assert health.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)

    def test_get_status(self, watchdog_agent):
        """get_status should return current state."""
        status = watchdog_agent.get_status()
        assert "running" in status
        assert "health_status" in status
        assert "consecutive_failures" in status

    def test_on_unhealthy_callback(self, watchdog_agent, config):
        """on_unhealthy callback should be called on unhealthy state."""
        callback = Mock()
        watchdog_agent.on_unhealthy = callback

        # Trigger unhealthy handling
        health = HealthCheck(
            status=HealthStatus.UNHEALTHY,
            message="Test unhealthy",
        )
        watchdog_agent._handle_unhealthy(health)

        callback.assert_called_once_with(health)

    def test_max_failures_triggers_rollback(self, watchdog_agent, dependency_manager):
        """Max consecutive failures should trigger rollback."""
        # Record a modification that can be rolled back
        dependency_manager.record_modification(["test.py"], "diff")

        # Set up to trigger rollback
        watchdog_agent._consecutive_failures = watchdog_agent.config.max_consecutive_failures

        health = HealthCheck(
            status=HealthStatus.UNHEALTHY,
            message="Test unhealthy",
        )
        watchdog_agent._handle_unhealthy(health)

        # Should have reset failures after rollback attempt
        assert watchdog_agent._consecutive_failures == 0


class TestSelfHealingLoop:
    """Test SelfHealingLoop class."""

    def test_initialization(self, workspace):
        """SelfHealingLoop should initialize correctly."""
        loop = SelfHealingLoop(workspace)
        assert loop.dependency_manager is not None
        assert loop.watchdog is not None

    def test_start_and_stop(self, workspace, config):
        """SelfHealingLoop should start and stop cleanly."""
        # Use fast check interval for quick test execution
        loop = SelfHealingLoop(workspace, config)
        loop.start()
        time.sleep(0.1)  # Just enough to let thread start
        loop.stop()

    def test_checkpoint(self, workspace):
        """Checkpoint should send heartbeat."""
        loop = SelfHealingLoop(workspace)
        loop.checkpoint()
        assert loop.watchdog._last_heartbeat is not None

    def test_is_healthy(self, workspace):
        """is_healthy should reflect health status."""
        loop = SelfHealingLoop(workspace)
        assert loop.is_healthy() is True  # Starts healthy

        loop.watchdog._health_status = HealthStatus.UNHEALTHY
        assert loop.is_healthy() is False

    def test_record_modification(self, workspace):
        """record_modification should track changes."""
        loop = SelfHealingLoop(workspace)
        mod_id = loop.record_modification(["test.py"], "diff")
        assert mod_id.startswith("MOD-")
        assert loop._last_modification_id == mod_id

    def test_confirm_modification_healthy(self, workspace):
        """confirm_modification_healthy should update status."""
        loop = SelfHealingLoop(workspace)
        mod_id = loop.record_modification(["test.py"], "diff")
        loop.confirm_modification_healthy()

        # Check the modification was updated
        mod = loop.dependency_manager.get_last_modification()
        assert mod.health_after == HealthStatus.HEALTHY

    def test_get_status(self, workspace):
        """get_status should return comprehensive status."""
        loop = SelfHealingLoop(workspace)
        status = loop.get_status()

        assert "watchdog" in status
        assert "workspace" in status
        assert status["workspace"] == str(workspace)


class TestIntegration:
    """Integration tests for watchdog system."""

    def test_full_cycle(self, workspace, config):
        """Test full cycle: start, modify, checkpoint, stop."""
        loop = SelfHealingLoop(workspace, config)
        loop.start()

        try:
            # Simulate work with checkpoints
            for i in range(3):
                loop.checkpoint()
                assert loop.is_healthy()
                time.sleep(0.05)

            # Record a modification
            mod_id = loop.record_modification(
                ["example.py"],
                "--- example.py\n+++ example.py\n@@\n-old\n+new",
            )
            assert mod_id is not None

            # Confirm healthy
            loop.confirm_modification_healthy()

            # Continue work
            for i in range(3):
                loop.checkpoint()
                time.sleep(0.05)

        finally:
            loop.stop()

        # Verify state
        status = loop.get_status()
        assert status["watchdog"]["modifications_tracked"] == 1

    def test_multiple_modifications(self, workspace):
        """Test tracking multiple modifications."""
        loop = SelfHealingLoop(workspace)

        # Record several modifications
        for i in range(5):
            loop.record_modification([f"file{i}.py"], f"diff{i}")

        # Check all are tracked
        assert len(loop.dependency_manager.modifications) == 5

        # Get last should return the most recent
        last = loop.dependency_manager.get_last_modification()
        assert last.files_changed == ["file4.py"]
