"""Core module for Ouroboros loop components."""

from .goal import GoalState
from .loop import OuroborosLoop, LoopConfig
from .prompt_generator import SelfPromptGenerator, ExperimentSpec

__all__ = [
    "GoalState",
    "OuroborosLoop",
    "LoopConfig",
    "SelfPromptGenerator",
    "ExperimentSpec",
]
