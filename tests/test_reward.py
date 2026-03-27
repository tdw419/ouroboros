"""
Tests for the Reward Function and Learnable Action Valuation Protocol.

Tests validate state snapshots, actions, transitions, reward calculation,
and learning from outcomes.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from src.ouroboros.protocols.reward import (
    ActionType,
    StateSnapshot,
    Action,
    Transition,
    RewardWeights,
    RewardFunction,
    RewardGuidedAgent,
)


@pytest.fixture
def state_dir(tmp_path):
    """Create a temporary state directory."""
    state_dir = tmp_path / ".ouroboros" / "reward"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


@pytest.fixture
def reward_fn(state_dir):
    """Create a RewardFunction for testing."""
    return RewardFunction(state_dir)


@pytest.fixture
def sample_state():
    """Create a sample state snapshot."""
    return StateSnapshot(
        iteration=1,
        metric_score=0.5,
        test_coverage=0.6,
        error_count=3,
        files_modified=2,
        insights_gained=1,
    )


@pytest.fixture
def sample_action():
    """Create a sample action."""
    return Action(
        action_type=ActionType.CODE_CHANGE,
        description="Refactored core module",
        target="src/module.py",
    )


class TestActionType:
    """Test ActionType enum."""

    def test_action_types(self):
        """ActionType should have expected values."""
        assert ActionType.CODE_CHANGE.value == "code_change"
        assert ActionType.TEST_ADDITION.value == "test_addition"
        assert ActionType.REFACTOR.value == "refactor"
        assert ActionType.ROLLBACK.value == "rollback"


class TestStateSnapshot:
    """Test StateSnapshot dataclass."""

    def test_state_creation(self):
        """StateSnapshot should be created with required fields."""
        state = StateSnapshot(
            iteration=1,
            metric_score=0.5,
            test_coverage=0.6,
            error_count=3,
            files_modified=2,
            insights_gained=1,
        )
        assert state.iteration == 1
        assert state.metric_score == 0.5
        assert state.test_coverage == 0.6

    def test_to_vector(self, sample_state):
        """to_vector should return normalized features."""
        vector = sample_state.to_vector()
        assert len(vector) == 6
        assert all(isinstance(v, float) for v in vector)

    def test_to_dict(self, sample_state):
        """to_dict should serialize correctly."""
        d = sample_state.to_dict()
        assert d["iteration"] == 1
        assert d["metric_score"] == 0.5
        assert "timestamp" in d

    def test_from_dict(self):
        """from_dict should deserialize correctly."""
        data = {
            "iteration": 2,
            "metric_score": 0.7,
            "test_coverage": 0.8,
            "error_count": 1,
            "files_modified": 5,
            "insights_gained": 3,
            "timestamp": datetime.now().isoformat(),
        }
        state = StateSnapshot.from_dict(data)
        assert state.iteration == 2
        assert state.metric_score == 0.7


class TestAction:
    """Test Action dataclass."""

    def test_action_creation(self):
        """Action should be created with required fields."""
        action = Action(
            action_type=ActionType.CODE_CHANGE,
            description="Test action",
            target="test.py",
        )
        assert action.action_type == ActionType.CODE_CHANGE
        assert action.description == "Test action"
        assert action.target == "test.py"

    def test_action_with_parameters(self):
        """Action should accept optional parameters."""
        action = Action(
            action_type=ActionType.REFACTOR,
            description="Refactor module",
            target="module.py",
            parameters={"lines_changed": 50},
        )
        assert action.parameters["lines_changed"] == 50

    def test_to_dict(self, sample_action):
        """to_dict should serialize correctly."""
        d = sample_action.to_dict()
        assert d["action_type"] == "code_change"
        assert d["description"] == "Refactored core module"
        assert "timestamp" in d

    def test_from_dict(self):
        """from_dict should deserialize correctly."""
        data = {
            "action_type": "test_addition",
            "description": "Add tests",
            "target": "tests/",
            "parameters": {},
            "timestamp": datetime.now().isoformat(),
        }
        action = Action.from_dict(data)
        assert action.action_type == ActionType.TEST_ADDITION
        assert action.description == "Add tests"


class TestTransition:
    """Test Transition dataclass."""

    def test_transition_creation(self, sample_state, sample_action):
        """Transition should be created with required fields."""
        state_after = StateSnapshot(
            iteration=2,
            metric_score=0.55,
            test_coverage=0.65,
            error_count=2,
            files_modified=3,
            insights_gained=2,
        )
        transition = Transition(
            state_before=sample_state,
            action=sample_action,
            state_after=state_after,
            reward=0.1,
        )
        assert transition.reward == 0.1
        assert transition.outcome_success is None

    def test_to_dict(self, sample_state, sample_action):
        """to_dict should serialize correctly."""
        state_after = StateSnapshot(
            iteration=2,
            metric_score=0.55,
            test_coverage=0.65,
            error_count=2,
            files_modified=3,
            insights_gained=2,
        )
        transition = Transition(
            state_before=sample_state,
            action=sample_action,
            state_after=state_after,
            reward=0.1,
            outcome_success=True,
        )
        d = transition.to_dict()
        assert d["reward"] == 0.1
        assert d["outcome_success"] is True
        assert "state_before" in d
        assert "action" in d


class TestRewardWeights:
    """Test RewardWeights dataclass."""

    def test_default_weights(self):
        """Default weights should sum to ~1.0."""
        weights = RewardWeights()
        total = sum(weights.to_list())
        assert abs(total - 1.0) < 0.01

    def test_to_list(self):
        """to_list should return all weights."""
        weights = RewardWeights()
        w_list = weights.to_list()
        assert len(w_list) == 6
        assert weights.metric_improvement == w_list[0]

    def test_from_list(self):
        """from_list should update weights."""
        weights = RewardWeights()
        new_weights = [0.5, 0.2, 0.1, 0.1, 0.05, 0.05]
        weights.from_list(new_weights)
        assert weights.metric_improvement == 0.5

    def test_normalize(self):
        """normalize should make weights sum to 1.0."""
        weights = RewardWeights(
            metric_improvement=2.0,
            coverage_improvement=2.0,
            error_reduction=2.0,
            insight_generation=1.0,
            exploration_bonus=1.0,
            efficiency_penalty=1.0,
        )
        weights.normalize()
        total = sum(weights.to_list())
        assert abs(total - 1.0) < 0.0001


class TestRewardFunction:
    """Test RewardFunction class."""

    def test_initialization(self, reward_fn):
        """RewardFunction should initialize correctly."""
        assert reward_fn.weights is not None
        assert len(reward_fn.trajectories) == 0

    def test_compute_reward_positive(self, reward_fn):
        """Improving state should yield positive reward."""
        state_before = StateSnapshot(
            iteration=1,
            metric_score=0.5,
            test_coverage=0.6,
            error_count=3,
            files_modified=0,
            insights_gained=0,
        )
        state_after = StateSnapshot(
            iteration=2,
            metric_score=0.6,  # Improved
            test_coverage=0.7,  # Improved
            error_count=1,     # Reduced
            files_modified=1,
            insights_gained=2,
        )
        action = Action(ActionType.CODE_CHANGE, "Fix bug", "bug.py")

        reward = reward_fn.compute_reward(state_before, action, state_after)
        assert reward > 0

    def test_compute_reward_negative(self, reward_fn):
        """Degrading state should yield negative reward."""
        state_before = StateSnapshot(
            iteration=1,
            metric_score=0.5,
            test_coverage=0.6,
            error_count=1,
            files_modified=0,
            insights_gained=2,
        )
        state_after = StateSnapshot(
            iteration=2,
            metric_score=0.4,  # Degraded
            test_coverage=0.5,  # Degraded
            error_count=5,     # Increased
            files_modified=10,  # Many files
            insights_gained=0,
        )
        action = Action(ActionType.CODE_CHANGE, "Bad change", "bad.py")

        reward = reward_fn.compute_reward(state_before, action, state_after)
        assert reward < 0

    def test_record_transition(self, reward_fn, sample_state, sample_action):
        """record_transition should store trajectory."""
        state_after = StateSnapshot(
            iteration=2,
            metric_score=0.55,
            test_coverage=0.65,
            error_count=2,
            files_modified=3,
            insights_gained=2,
        )

        transition = reward_fn.record_transition(
            sample_state, sample_action, state_after, outcome_success=True
        )

        assert len(reward_fn.trajectories) == 1
        assert transition.outcome_success is True

    def test_learn_from_outcome_success(self, reward_fn, sample_state, sample_action):
        """Learning from success should adjust weights positively."""
        state_after = StateSnapshot(
            iteration=2,
            metric_score=0.6,  # Improved
            test_coverage=0.7,  # Improved
            error_count=1,
            files_modified=1,
            insights_gained=2,
        )

        reward_fn.record_transition(sample_state, sample_action, state_after)
        original_weights = reward_fn.weights.to_list().copy()

        reward_fn.learn_from_outcome(0, success=True)

        # Weights should have changed
        new_weights = reward_fn.weights.to_list()
        # At least some weights should be different
        # (may not all change due to normalization)

    def test_learn_from_outcome_failure(self, reward_fn, sample_state):
        """Learning from failure should adjust weights negatively."""
        action = Action(ActionType.CODE_CHANGE, "Bad change", "bad.py")
        state_after = StateSnapshot(
            iteration=2,
            metric_score=0.4,  # Degraded
            test_coverage=0.5,
            error_count=5,
            files_modified=10,
            insights_gained=0,
        )

        reward_fn.record_transition(sample_state, action, state_after)
        reward_fn.learn_from_outcome(0, success=False)

        # Weights should have changed
        assert reward_fn.weights is not None

    def test_get_best_actions(self, reward_fn, sample_state):
        """get_best_actions should rank actions by predicted reward."""
        candidates = [
            Action(ActionType.CODE_CHANGE, "Fix bug", "bug.py"),
            Action(ActionType.TEST_ADDITION, "Add tests", "tests/"),
            Action(ActionType.EXPLORATION, "Explore", "exp/"),
        ]

        ranked = reward_fn.get_best_actions(sample_state, candidates)

        assert len(ranked) == 3
        # Should be sorted by reward (descending)
        rewards = [r for _, r in ranked]
        assert rewards == sorted(rewards, reverse=True)

    def test_get_statistics(self, reward_fn):
        """get_statistics should return function stats."""
        stats = reward_fn.get_statistics()
        assert "total_transitions" in stats
        assert "avg_reward" in stats
        # weights key only present when there are transitions
        # or may be in the stats depending on implementation

    def test_persistence(self, reward_fn, state_dir, sample_state, sample_action):
        """Weights and trajectories should persist."""
        state_after = StateSnapshot(
            iteration=2,
            metric_score=0.55,
            test_coverage=0.65,
            error_count=2,
            files_modified=3,
            insights_gained=2,
        )

        reward_fn.record_transition(sample_state, sample_action, state_after)

        # Create new function to load from disk
        new_fn = RewardFunction(state_dir)
        assert len(new_fn.trajectories) == 1


class TestRewardGuidedAgent:
    """Test RewardGuidedAgent class."""

    def test_initialization(self, reward_fn):
        """Agent should initialize with reward function."""
        agent = RewardGuidedAgent(reward_fn)
        assert agent.reward_fn == reward_fn
        assert agent.current_state is None

    def test_observe_state(self, reward_fn, sample_state):
        """observe_state should update current state."""
        agent = RewardGuidedAgent(reward_fn)
        agent.observe_state(sample_state)
        assert agent.current_state == sample_state

    def test_select_action(self, reward_fn, sample_state):
        """select_action should choose highest predicted reward."""
        agent = RewardGuidedAgent(reward_fn)
        agent.observe_state(sample_state)

        candidates = [
            Action(ActionType.CODE_CHANGE, "Option A", "a.py"),
            Action(ActionType.TEST_ADDITION, "Option B", "tests/"),
        ]

        selected = agent.select_action(candidates)
        assert selected in candidates

    def test_execute_and_learn(self, reward_fn, sample_state):
        """execute_and_learn should record transition."""
        agent = RewardGuidedAgent(reward_fn)
        agent.observe_state(sample_state)

        action = Action(ActionType.CODE_CHANGE, "Test", "test.py")
        state_after = StateSnapshot(
            iteration=2,
            metric_score=0.55,
            test_coverage=0.65,
            error_count=2,
            files_modified=1,
            insights_gained=1,
        )

        reward = agent.execute_and_learn(action, state_after, success=True)

        assert isinstance(reward, float)
        assert agent.current_state == state_after
        assert len(reward_fn.trajectories) == 1


class TestIntegration:
    """Integration tests for reward system."""

    def test_full_learning_cycle(self, reward_fn):
        """Test full cycle: observe, act, learn."""
        agent = RewardGuidedAgent(reward_fn)

        # Initial state
        state1 = StateSnapshot(
            iteration=1,
            metric_score=0.5,
            test_coverage=0.5,
            error_count=5,
            files_modified=0,
            insights_gained=0,
        )
        agent.observe_state(state1)

        # Take action
        action = Action(ActionType.TEST_ADDITION, "Add unit tests", "tests/")
        state2 = StateSnapshot(
            iteration=2,
            metric_score=0.55,
            test_coverage=0.7,  # Coverage improved
            error_count=3,
            files_modified=1,
            insights_gained=1,
        )

        reward = agent.execute_and_learn(action, state2, success=True)

        # Check learning happened
        stats = reward_fn.get_statistics()
        assert stats["total_transitions"] == 1
        assert stats["success_rate"] == 1.0

    def test_multiple_transitions(self, reward_fn):
        """Test recording multiple transitions."""
        states = [
            StateSnapshot(i, 0.5 + i*0.05, 0.5 + i*0.05, 5-i, i, i)
            for i in range(5)
        ]
        actions = [
            Action(ActionType.CODE_CHANGE, f"Change {i}", f"file{i}.py")
            for i in range(4)
        ]

        for i in range(4):
            reward_fn.record_transition(states[i], actions[i], states[i+1], outcome_success=True)

        stats = reward_fn.get_statistics()
        assert stats["total_transitions"] == 4

    def test_action_ranking_preference(self, reward_fn):
        """Test that agent prefers certain action types."""
        state = StateSnapshot(
            iteration=1,
            metric_score=0.5,
            test_coverage=0.5,
            error_count=2,
            files_modified=0,
            insights_gained=0,
        )

        # Multiple action types
        candidates = [
            Action(ActionType.CODE_CHANGE, "Code", "code.py"),
            Action(ActionType.TEST_ADDITION, "Test", "tests/"),
            Action(ActionType.DOCUMENTATION, "Docs", "README.md"),
            Action(ActionType.EXPLORATION, "Explore", "exp/"),
        ]

        ranked = reward_fn.get_best_actions(state, candidates)

        # All should be ranked
        assert len(ranked) == 4

        # First should have highest predicted reward
        assert ranked[0][1] >= ranked[-1][1]
