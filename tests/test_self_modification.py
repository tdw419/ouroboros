"""
Tests for the Self-Modification Protocol.

Tests validate the 7-step modification cycle:
ASSESS → IDENTIFY → HYPOTHESIZE → VALIDATE → APPLY → VERIFY → COMMIT/ROLLBACK
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from src.ouroboros.protocols.self_modification import (
    ModificationType,
    RiskLevel,
    PerformanceMetrics,
    ImprovementHypothesis,
    ModificationResult,
    SelfModificationProtocol,
)


@pytest.fixture
def state_dir(tmp_path):
    """Create a temporary state directory."""
    state_dir = tmp_path / ".ouroboros" / "self_mod"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


@pytest.fixture
def protocol(state_dir):
    """Create a SelfModificationProtocol for testing."""
    return SelfModificationProtocol(state_dir)


@pytest.fixture
def sample_metrics():
    """Create sample performance metrics."""
    return PerformanceMetrics(
        accuracy=0.7,
        efficiency=0.6,
        novelty=0.5,
        stability=0.8,
        coverage=0.4,
    )


@pytest.fixture
def sample_hypothesis():
    """Create a sample improvement hypothesis."""
    return ImprovementHypothesis.create(
        description="Add caching for performance",
        bottleneck="efficiency",
        changes="cache.py",
    )


class TestModificationType:
    """Test ModificationType enum."""

    def test_modification_types(self):
        """ModificationType should have expected values."""
        assert ModificationType.CODE_CHANGE.value == "code_change"
        assert ModificationType.CONFIG_UPDATE.value == "config_update"
        assert ModificationType.PROMPT_REWRITE.value == "prompt_rewrite"
        assert ModificationType.ARCHITECTURE.value == "architecture"


class TestRiskLevel:
    """Test RiskLevel enum."""

    def test_risk_levels(self):
        """RiskLevel should have expected values."""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"


class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""

    def test_default_metrics(self):
        """Default metrics should have expected values."""
        metrics = PerformanceMetrics()
        assert metrics.accuracy == 0.0
        assert metrics.stability == 1.0

    def test_overall_score(self, sample_metrics):
        """overall_score should be weighted composite."""
        score = sample_metrics.overall_score()
        assert 0 <= score <= 1
        # Verify it's a weighted average
        expected = (
            sample_metrics.accuracy * 0.35 +
            sample_metrics.efficiency * 0.20 +
            sample_metrics.novelty * 0.15 +
            sample_metrics.stability * 0.20 +
            sample_metrics.coverage * 0.10
        )
        assert abs(score - expected) < 0.001

    def test_bottleneck_returns_lowest(self, sample_metrics):
        """bottleneck should return the weakest metric."""
        # coverage is 0.4, the lowest
        bottleneck = sample_metrics.bottleneck()
        assert bottleneck == "coverage"

    def test_bottleneck_with_tie(self):
        """bottleneck should handle ties."""
        metrics = PerformanceMetrics(
            accuracy=0.5,
            efficiency=0.5,
            novelty=0.5,
            stability=0.5,
            coverage=0.5,
        )
        bottleneck = metrics.bottleneck()
        assert bottleneck in ["accuracy", "efficiency", "novelty", "stability", "coverage"]


class TestImprovementHypothesis:
    """Test ImprovementHypothesis dataclass."""

    def test_hypothesis_creation(self):
        """Hypothesis should be created with required fields."""
        hypothesis = ImprovementHypothesis(
            id="HYP-001",
            description="Test hypothesis",
            target_bottleneck="accuracy",
            modification_type=ModificationType.CODE_CHANGE,
            risk_level=RiskLevel.MEDIUM,
        )
        assert hypothesis.id == "HYP-001"
        assert hypothesis.description == "Test hypothesis"
        assert hypothesis.target_bottleneck == "accuracy"

    def test_create_factory_method(self):
        """create factory method should generate ID."""
        hypothesis = ImprovementHypothesis.create(
            description="Test hypothesis",
            bottleneck="efficiency",
            changes="code changes",
        )
        assert hypothesis.id.startswith("HYP-")
        assert hypothesis.description == "Test hypothesis"
        assert hypothesis.code_changes == "code changes"

    def test_hypothesis_with_rollback_plan(self):
        """Hypothesis should accept rollback plan."""
        hypothesis = ImprovementHypothesis(
            id="HYP-002",
            description="Test",
            target_bottleneck="stability",
            modification_type=ModificationType.CODE_CHANGE,
            risk_level=RiskLevel.LOW,
            rollback_plan="git revert HEAD",
        )
        assert hypothesis.rollback_plan == "git revert HEAD"


class TestModificationResult:
    """Test ModificationResult dataclass."""

    def test_result_creation(self, sample_metrics):
        """Result should be created with required fields."""
        metrics_after = PerformanceMetrics(
            accuracy=0.75,
            efficiency=0.65,
            novelty=0.55,
            stability=0.85,
            coverage=0.45,
        )
        result = ModificationResult(
            hypothesis_id="HYP-001",
            metrics_before=sample_metrics,
            metrics_after=metrics_after,
            success=True,
            insight="Improved efficiency",
        )
        assert result.success is True
        assert result.insight == "Improved efficiency"

    def test_delta_positive(self, sample_metrics):
        """delta should be positive when metrics improve."""
        metrics_after = PerformanceMetrics(
            accuracy=0.8,  # Improved
            efficiency=0.7,  # Improved
            novelty=0.6,  # Improved
            stability=0.9,  # Improved
            coverage=0.5,  # Improved
        )
        result = ModificationResult(
            hypothesis_id="HYP-001",
            metrics_before=sample_metrics,
            metrics_after=metrics_after,
            success=True,
            insight="",
        )
        assert result.delta() > 0

    def test_delta_negative(self, sample_metrics):
        """delta should be negative when metrics degrade."""
        metrics_after = PerformanceMetrics(
            accuracy=0.6,  # Degraded
            efficiency=0.5,  # Degraded
            novelty=0.4,  # Degraded
            stability=0.7,  # Degraded
            coverage=0.3,  # Degraded
        )
        result = ModificationResult(
            hypothesis_id="HYP-001",
            metrics_before=sample_metrics,
            metrics_after=metrics_after,
            success=False,
            insight="",
        )
        assert result.delta() < 0


class TestSelfModificationProtocol:
    """Test SelfModificationProtocol class."""

    def test_initialization(self, protocol):
        """Protocol should initialize correctly."""
        assert protocol.history == []
        assert protocol.hypotheses == []
        assert protocol.current_metrics is not None

    # === STEP 1: ASSESS ===

    def test_assess_performance_default(self, protocol):
        """assess_performance should return default metrics if no state."""
        metrics = protocol.assess_performance()
        assert isinstance(metrics, PerformanceMetrics)

    def test_assess_performance_loads_state(self, protocol, state_dir):
        """assess_performance should load from state file."""
        # Write metrics file
        metrics_file = state_dir / "metrics.json"
        metrics_file.write_text(json.dumps({
            "accuracy": 0.8,
            "efficiency": 0.7,
            "novelty": 0.6,
            "stability": 0.9,
            "coverage": 0.5,
        }))

        metrics = protocol.assess_performance()
        assert metrics.accuracy == 0.8
        assert metrics.efficiency == 0.7

    # === STEP 2: IDENTIFY ===

    def test_identify_bottleneck(self, protocol, sample_metrics):
        """identify_bottleneck should return weakest metric."""
        bottleneck = protocol.identify_bottleneck(sample_metrics)
        assert bottleneck == "coverage"  # 0.4 is lowest

    def test_identify_architectural_limits(self, protocol):
        """identify_architectural_limits should return list of limits."""
        limits = protocol.identify_architectural_limits()
        assert isinstance(limits, list)
        assert len(limits) > 0

    # === STEP 3: HYPOTHESIZE ===

    def test_generate_hypotheses_for_accuracy(self, protocol):
        """generate_hypotheses should create accuracy hypotheses."""
        hypotheses = protocol.generate_hypotheses("accuracy")
        assert len(hypotheses) > 0
        assert all(h.target_bottleneck == "accuracy" for h in hypotheses)

    def test_generate_hypotheses_for_efficiency(self, protocol):
        """generate_hypotheses should create efficiency hypotheses."""
        hypotheses = protocol.generate_hypotheses("efficiency")
        assert len(hypotheses) > 0
        assert all(h.target_bottleneck == "efficiency" for h in hypotheses)

    def test_generate_hypotheses_stores(self, protocol):
        """generate_hypotheses should store hypotheses."""
        protocol.generate_hypotheses("accuracy")
        assert len(protocol.hypotheses) > 0

    # === STEP 4: VALIDATE ===

    def test_validate_safety_passes(self, protocol, sample_hypothesis):
        """validate_safety should pass safe hypotheses."""
        is_safe, reason = protocol.validate_safety(sample_hypothesis)
        assert is_safe is True
        assert "passed" in reason.lower()

    def test_validate_safety_blocks_protected_files(self, protocol):
        """validate_safety should block protected file modifications."""
        hypothesis = ImprovementHypothesis.create(
            description="Modify safety",
            bottleneck="accuracy",
            changes="import safety.py",
        )
        is_safe, reason = protocol.validate_safety(hypothesis)
        assert is_safe is False
        assert "protected" in reason.lower()

    def test_validate_safety_requires_rollback_plan(self, protocol):
        """validate_safety should require rollback plan."""
        hypothesis = ImprovementHypothesis(
            id="HYP-001",
            description="Test",
            target_bottleneck="accuracy",
            modification_type=ModificationType.CODE_CHANGE,
            risk_level=RiskLevel.MEDIUM,
            rollback_plan="",  # Empty
        )
        is_safe, reason = protocol.validate_safety(hypothesis)
        assert is_safe is False
        assert "rollback" in reason.lower()

    def test_validate_safety_blocks_critical_risk(self, protocol):
        """validate_safety should block critical risk."""
        hypothesis = ImprovementHypothesis(
            id="HYP-001",
            description="Critical change",
            target_bottleneck="accuracy",
            modification_type=ModificationType.CODE_CHANGE,
            risk_level=RiskLevel.CRITICAL,
            rollback_plan="git revert",
        )
        is_safe, reason = protocol.validate_safety(hypothesis)
        assert is_safe is False
        assert "critical" in reason.lower()

    # === STEP 5: APPLY ===

    def test_apply_modification(self, protocol, sample_hypothesis):
        """apply_modification should return True."""
        result = protocol.apply_modification(sample_hypothesis)
        assert result is True

    # === STEP 6: VERIFY ===

    def test_verify_improvement(self, protocol, sample_hypothesis):
        """verify_improvement should return ModificationResult."""
        result = protocol.verify_improvement(sample_hypothesis)
        assert isinstance(result, ModificationResult)
        assert result.hypothesis_id == sample_hypothesis.id

    def test_verify_records_history(self, protocol, sample_hypothesis):
        """verify_improvement should record in history."""
        protocol.verify_improvement(sample_hypothesis)
        assert len(protocol.history) == 1

    # === STEP 7: COMMIT OR ROLLBACK ===

    def test_commit_on_success(self, protocol, sample_metrics):
        """commit_or_rollback should commit on success."""
        result = ModificationResult(
            hypothesis_id="HYP-001",
            metrics_before=sample_metrics,
            metrics_after=PerformanceMetrics(accuracy=0.8, efficiency=0.7, novelty=0.6, stability=0.9, coverage=0.5),
            success=True,
            insight="Improved",
        )
        decision = protocol.commit_or_rollback(result)
        assert decision == "COMMITTED"

    def test_rollback_on_failure(self, protocol, sample_metrics):
        """commit_or_rollback should rollback on failure."""
        result = ModificationResult(
            hypothesis_id="HYP-001",
            metrics_before=sample_metrics,
            metrics_after=PerformanceMetrics(accuracy=0.6, efficiency=0.5, novelty=0.4, stability=0.7, coverage=0.3),
            success=False,
            insight="Degraded",
        )
        decision = protocol.commit_or_rollback(result)
        assert decision == "ROLLED_BACK"

    # === FULL CYCLE ===

    def test_run_cycle(self, protocol):
        """run_cycle should execute all steps."""
        result = protocol.run_cycle()
        assert isinstance(result, ModificationResult)
        assert result.hypothesis_id is not None

    def test_run_cycle_generates_hypotheses(self, protocol):
        """run_cycle should generate hypotheses."""
        protocol.run_cycle()
        assert len(protocol.hypotheses) > 0

    def test_run_cycle_records_history(self, protocol):
        """run_cycle should record result in history."""
        protocol.run_cycle()
        assert len(protocol.history) == 1


class TestProtectedPatterns:
    """Test protected pattern detection."""

    def test_protected_patterns_list(self, protocol):
        """Protocol should have protected patterns."""
        assert len(SelfModificationProtocol.PROTECTED_PATTERNS) > 0
        assert "safety.py" in SelfModificationProtocol.PROTECTED_PATTERNS
        assert "self_modification.py" in SelfModificationProtocol.PROTECTED_PATTERNS

    def test_cannot_modify_self(self, protocol):
        """Cannot modify the self_modification protocol itself."""
        hypothesis = ImprovementHypothesis.create(
            description="Modify self_modification.py",
            bottleneck="efficiency",
            changes="self_modification.py",
        )
        is_safe, _ = protocol.validate_safety(hypothesis)
        assert is_safe is False


class TestIntegration:
    """Integration tests for self-modification system."""

    def test_multiple_cycles(self, protocol):
        """Test running multiple modification cycles."""
        for i in range(3):
            result = protocol.run_cycle()
            assert result is not None

        assert len(protocol.history) == 3

    def test_hypothesis_accumulation(self, protocol):
        """Hypotheses should accumulate across cycles."""
        protocol.run_cycle()
        count1 = len(protocol.hypotheses)

        protocol.run_cycle()
        count2 = len(protocol.hypotheses)

        assert count2 >= count1

    def test_metrics_persistence(self, protocol, state_dir):
        """Metrics should persist after commit."""
        # Set initial metrics
        protocol.current_metrics = PerformanceMetrics(
            accuracy=0.8,
            efficiency=0.7,
            novelty=0.6,
            stability=0.9,
            coverage=0.5,
        )
        protocol._save_metrics()

        # Create new protocol and call assess_performance to load
        new_protocol = SelfModificationProtocol(state_dir)
        new_protocol.assess_performance()  # This loads from file
        assert new_protocol.current_metrics.accuracy == 0.8
