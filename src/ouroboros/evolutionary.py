"""
Evolutionary Loop - Complete Integration

A unified loop that orchestrates all ouroboros components:
- Insights Database (learning from experience)
- Watchdog (health monitoring, auto-rollback)
- Reward Model (action valuation)
- Generator/Critic (iterative improvement)
- Sandbox (safe execution)
- Meta Prompt Engine (adaptive prompts)
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Any
from enum import Enum
import json
import traceback


class LoopPhase(Enum):
    INITIALIZING = "initializing"
    GENERATING = "generating"
    EXECUTING = "executing"
    EVALUATING = "evaluating"
    LEARNING = "learning"
    RESTING = "resting"
    RECOVERING = "recovering"
    STOPPED = "stopped"


class LoopState(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    RECOVERING = "recovering"
    STOPPED = "stopped"


@dataclass
class LoopMetrics:
    """Metrics tracked during loop execution."""
    total_iterations: int = 0
    successful_iterations: int = 0
    failed_iterations: int = 0
    rollbacks_triggered: int = 0
    insights_generated: int = 0
    avg_reward: float = 0.0
    uptime_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "total_iterations": self.total_iterations,
            "successful_iterations": self.successful_iterations,
            "failed_iterations": self.failed_iterations,
            "rollbacks_triggered": self.rollbacks_triggered,
            "insights_generated": self.insights_generated,
            "avg_reward": self.avg_reward,
            "uptime_seconds": self.uptime_seconds,
        }


@dataclass
class EvolutionaryConfig:
    """Configuration for the evolutionary loop."""
    # Iteration settings
    max_iterations: int = 100
    iteration_delay_seconds: float = 5.0
    rest_interval: int = 10  # Rest every N iterations
    rest_duration_seconds: float = 10.0

    # Safety settings
    enable_watchdog: bool = True
    enable_sandbox: bool = True
    enable_alignment_firewall: bool = True  # Prime Directive enforcement
    auto_rollback: bool = True
    max_consecutive_failures: int = 3

    # Learning settings
    enable_reward_learning: bool = True
    enable_meta_prompts: bool = True
    insights_window: int = 5  # Analyze last N insights

    # Generator/Critic settings
    max_revision_iterations: int = 3
    convergence_threshold: float = 0.7

    # Paths
    workspace: Optional[Path] = None
    state_dir: Optional[Path] = None


class EvolutionaryLoop:
    """
    The unified evolutionary loop that orchestrates all components.

    Flow:
    1. Initialize all components
    2. Receive/generate a prompt
    3. Generator produces solution
    4. Sandbox validates safety
    5. Execute if safe
    6. Critic evaluates result
    7. Record insight and update reward model
    8. Watchdog monitors health
    9. Meta engine updates prompts if needed
    10. Repeat
    """

    def __init__(self, config: EvolutionaryConfig):
        self.config = config
        self.workspace = config.workspace or Path(".")
        self.state_dir = config.state_dir or self.workspace / ".ouroboros"
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # State
        self.phase = LoopPhase.INITIALIZING
        self.state = LoopState.HEALTHY
        self.metrics = LoopMetrics()
        self.consecutive_failures = 0
        self.start_time: Optional[datetime] = None

        # Components (lazy loaded)
        self._insights_db = None
        self._watchdog = None
        self._reward_fn = None
        self._generator = None
        self._critic = None
        self._sandbox = None
        self._meta_engine = None
        self._dependency_mgr = None
        self._alignment_firewall = None  # Prime Directive enforcement

        # Callbacks
        self.on_iteration_start: Optional[Callable[[int], None]] = None
        self.on_iteration_complete: Optional[Callable[[int, bool], None]] = None
        self.on_rollback: Optional[Callable[[str], None]] = None
        self.on_insight: Optional[Callable[[str], None]] = None

        # Running flag
        self._running = False

    # === Component Accessors (Lazy Loading) ===

    @property
    def insights_db(self):
        """Get or create insights database."""
        if self._insights_db is None:
            from .protocols.insights import InsightsDatabase
            self._insights_db = InsightsDatabase(self.state_dir / "insights")
        return self._insights_db

    @property
    def watchdog(self):
        """Get or create watchdog agent."""
        if self._watchdog is None and self.config.enable_watchdog:
            from .protocols.watchdog import WatchdogAgent, WatchdogConfig, DependencyManager
            dm = DependencyManager(self.workspace, self.state_dir)
            self._dependency_mgr = dm
            wconfig = WatchdogConfig(
                rollback_on_unhealthy=self.config.auto_rollback,
            )
            self._watchdog = WatchdogAgent(wconfig, dm)
            self._watchdog.on_rollback = self._handle_rollback
        return self._watchdog

    @property
    def reward_fn(self):
        """Get or create reward function."""
        if self._reward_fn is None and self.config.enable_reward_learning:
            from .protocols.reward import RewardFunction
            self._reward_fn = RewardFunction(self.state_dir / "reward")
        return self._reward_fn

    @property
    def generator(self):
        """Get or create generator agent."""
        if self._generator is None:
            from .protocols.cognitive import GeneratorAgent
            self._generator = GeneratorAgent()
        return self._generator

    @property
    def critic(self):
        """Get or create critic agent."""
        if self._critic is None:
            from .protocols.cognitive import CriticAgent
            self._critic = CriticAgent(self.reward_fn)
        return self._critic

    @property
    def sandbox(self):
        """Get or create sandbox validator."""
        if self._sandbox is None and self.config.enable_sandbox:
            from .protocols.sandbox import SafetyValidator, SafetyConfig
            sconfig = SafetyConfig()
            self._sandbox = SafetyValidator(sconfig, self.workspace)
        return self._sandbox

    @property
    def alignment_firewall(self):
        """Get or create alignment firewall (Prime Directive enforcement)."""
        if self._alignment_firewall is None and self.config.enable_alignment_firewall:
            from .protocols.alignment import AlignmentFirewall
            self._alignment_firewall = AlignmentFirewall(self.state_dir / "alignment")
        return self._alignment_firewall

    @property
    def meta_engine(self):
        """Get or create meta prompt engine."""
        if self._meta_engine is None and self.config.enable_meta_prompts:
            from .protocols.meta_prompt import MetaPromptEngine
            self._meta_engine = MetaPromptEngine(self.state_dir / "meta")
        return self._meta_engine

    # === Main Loop ===

    def run(self, initial_prompt: Optional[str] = None):
        """
        Run the evolutionary loop.

        Args:
            initial_prompt: Optional starting prompt. If None, generates one.
        """
        self._running = True
        self.start_time = datetime.now()
        self.phase = LoopPhase.INITIALIZING

        print("=" * 60)
        print("🐍 OUROBOROS EVOLUTIONARY LOOP")
        print("=" * 60)
        print(f"Workspace: {self.workspace}")
        print(f"State dir: {self.state_dir}")
        print(f"Max iterations: {self.config.max_iterations}")
        print("=" * 60)

        # Start watchdog
        if self.watchdog:
            self.watchdog.start()
            print("✓ Watchdog started")

        try:
            current_prompt = initial_prompt

            while self._running and self.metrics.total_iterations < self.config.max_iterations:
                # Check state
                if self.state == LoopState.STOPPED:
                    break

                # Start iteration
                self.metrics.total_iterations += 1
                iteration = self.metrics.total_iterations
                self.phase = LoopPhase.GENERATING

                if self.on_iteration_start:
                    self.on_iteration_start(iteration)

                print(f"\n{'─' * 60}")
                print(f"📊 Iteration {iteration}")
                print(f"   Phase: {self.phase.value}")
                print(f"   State: {self.state.value}")

                try:
                    # Generate or use provided prompt
                    if current_prompt is None:
                        current_prompt = self._generate_next_prompt()

                    print(f"\n📝 Prompt: {current_prompt[:100]}...")

                    # Generator/Critic cycle
                    self.phase = LoopPhase.GENERATING
                    result = self._run_generator_critic_cycle(current_prompt)

                    # Safety check
                    if self.sandbox and result.get("code_changes"):
                        self.phase = LoopPhase.EXECUTING
                        safe = self._validate_safety(result["code_changes"])
                        if not safe:
                            print("   ⚠️ Safety validation failed, skipping execution")
                            result["success"] = False
                            result["insight"] = "Safety validation prevented unsafe modification"

                    # Record result
                    self.phase = LoopPhase.LEARNING
                    insight = self._record_iteration(result)
                    self.metrics.insights_generated += 1

                    if result.get("success"):
                        self.metrics.successful_iterations += 1
                        self.consecutive_failures = 0
                    else:
                        self.metrics.failed_iterations += 1
                        self.consecutive_failures += 1

                    # Check for too many failures
                    if self.consecutive_failures >= self.config.max_consecutive_failures:
                        self.state = LoopState.DEGRADED
                        print(f"   ⚠️ Degraded state: {self.consecutive_failures} consecutive failures")

                    # Update meta prompts periodically
                    if self.meta_engine and iteration % 5 == 0:
                        self._update_meta_prompts()

                    # Watchdog heartbeat
                    if self.watchdog:
                        self.watchdog.heartbeat()

                    # Rest periodically
                    if iteration % self.config.rest_interval == 0:
                        self._rest()

                    if self.on_iteration_complete:
                        self.on_iteration_complete(iteration, result.get("success", False))

                    # Generate next prompt
                    current_prompt = None

                except Exception as e:
                    print(f"   ❌ Iteration failed: {e}")
                    traceback.print_exc()
                    self.metrics.failed_iterations += 1
                    self.consecutive_failures += 1

                    # Record failure as insight
                    self._record_failure_insight(str(e))

        finally:
            # Stop watchdog
            if self.watchdog:
                self.watchdog.stop()

            self.phase = LoopPhase.STOPPED
            self._save_final_state()

        print("\n" + "=" * 60)
        print("🏁 EVOLUTIONARY LOOP COMPLETE")
        print("=" * 60)
        self._print_summary()

    def stop(self):
        """Stop the loop gracefully."""
        self._running = False
        self.state = LoopState.STOPPED

    # === Internal Methods ===

    def _generate_next_prompt(self) -> str:
        """Generate the next prompt to work on."""
        from .core.self_prompt_loop import SelfPrompter

        prompter = SelfPrompter(self.state_dir / "self_prompt_state.json")
        next_prompt = prompter.generate_next_prompt()

        # Update with meta prompt if available
        if self.meta_engine:
            system_prompt = self.meta_engine.get_current_prompt()
            # Could inject learned rules into prompt generation

        return next_prompt.get("prompt", "Continue improving the system")

    def _run_generator_critic_cycle(self, prompt: str) -> dict:
        """Run the Generator/Critic iterative improvement cycle."""
        from .protocols.cognitive import Task

        # Create task from prompt
        task = Task(
            id=f"task-{self.metrics.total_iterations}",
            description=prompt,
            target_file="src/ouroboros/",
            difficulty=0.5,
        )

        # Run cognitive simulation
        from .protocols.cognitive import CognitiveSimulation
        sim = CognitiveSimulation(self.state_dir / "simulations", self.reward_fn)

        # Override max iterations
        final_attempt = sim.run_task(task, max_iterations=self.config.max_revision_iterations)

        result = {
            "success": final_attempt.final_score >= self.config.convergence_threshold,
            "score": final_attempt.final_score,
            "iterations": final_attempt.iteration,
            "output": final_attempt.generator_output,
            "code_changes": final_attempt.generator_output if final_attempt.final_score >= 0.5 else None,
            "insight": f"Generator/Critic converged at score {final_attempt.final_score:.2f} after {final_attempt.iteration} iterations",
        }

        # Alignment Firewall: Validate BEFORE any execution
        if result.get("code_changes") and self.alignment_firewall:
            decision = self.alignment_firewall.validate(result["code_changes"])
            if not decision.approved:
                print(f"   🔥 ALIGNMENT FIREWALL BLOCKED: {decision.summary}")
                result["success"] = False
                result["blocked_by_firewall"] = True
                result["firewall_decision"] = decision.summary
                result["insight"] = f"Alignment violation: {decision.blocked_by}"
                # Handle halt-level violations
                if decision.halt_required:
                    self.state = LoopState.STOPPED
                    self._running = False

        return result

    def _validate_safety(self, code: str) -> bool:
        """Validate code changes in sandbox."""
        if not self.sandbox:
            return True

        result = self.sandbox.validate(code, self.workspace / "proposed_change.py")
        if not result.safe:
            print(f"   Sandbox violations: {len(result.violations)}")
            for v in result.violations[:3]:
                print(f"     - {v.message}")

        return result.safe

    def _record_iteration(self, result: dict) -> str:
        """Record iteration result and extract insight."""
        insight = result.get("insight", "No insight recorded")

        # Add to insights database
        if self.insights_db:
            recorded_insight, score = self.insights_db.add_insight(
                content=insight,
                tags=["evolutionary_loop", f"iteration_{self.metrics.total_iterations}"],
                source_iteration=self.metrics.total_iterations,
            )
            print(f"   💡 Insight: {insight[:80]}...")

            if self.on_insight:
                self.on_insight(insight)

        # Update reward model
        if self.reward_fn:
            from .protocols.reward import StateSnapshot, Action, ActionType

            state = StateSnapshot(
                iteration=self.metrics.total_iterations,
                metric_score=result.get("score", 0.5),
                test_coverage=0.0,  # Would need to measure
                error_count=self.consecutive_failures,
                files_modified=1 if result.get("code_changes") else 0,
                insights_gained=1,
            )

            action = Action(
                action_type=ActionType.CODE_CHANGE if result.get("code_changes") else ActionType.EXPLORATION,
                description=result.get("insight", "iteration"),
                target="ouroboros",
            )

            # Record transition
            self.reward_fn.record_transition(
                state, action, state,
                outcome_success=result.get("success", False)
            )

        return insight

    def _record_failure_insight(self, error: str):
        """Record a failure as an insight."""
        if self.insights_db:
            self.insights_db.add_insight(
                content=f"Failure pattern: {error[:200]}",
                tags=["failure", "error"],
                source_iteration=self.metrics.total_iterations,
            )

    def _update_meta_prompts(self):
        """Update meta prompts from recent insights."""
        if not self.meta_engine:
            return

        # Get recent insights
        recent_insights = [i.content for i in self.insights_db.get_all_insights()[-self.config.insights_window:]]

        if recent_insights:
            new_rules = self.meta_engine.update_from_insights(recent_insights)
            if new_rules:
                print(f"   📚 Added {len(new_rules)} new prompt rules")

    def _handle_rollback(self, success: bool, message: str):
        """Handle watchdog-triggered rollback."""
        self.metrics.rollbacks_triggered += 1
        print(f"   🔄 Rollback: {message}")

        if self.on_rollback:
            self.on_rollback(message)

    def _rest(self):
        """Rest period between batches of iterations."""
        import time

        self.phase = LoopPhase.RESTING
        print(f"\n😴 Resting for {self.config.rest_duration_seconds}s...")

        # Update metrics
        if self.start_time:
            self.metrics.uptime_seconds = (datetime.now() - self.start_time).total_seconds()

        # Calculate average reward
        if self.reward_fn:
            stats = self.reward_fn.get_statistics()
            self.metrics.avg_reward = stats.get("avg_reward", 0.0)

        time.sleep(self.config.rest_duration_seconds)

    def _save_final_state(self):
        """Save final state to disk."""
        state_file = self.state_dir / "evolutionary_state.json"
        data = {
            "metrics": self.metrics.to_dict(),
            "phase": self.phase.value,
            "state": self.state.value,
            "consecutive_failures": self.consecutive_failures,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": datetime.now().isoformat(),
        }

        with open(state_file, "w") as f:
            json.dump(data, f, indent=2)

    def _print_summary(self):
        """Print execution summary."""
        print(f"\nTotal iterations: {self.metrics.total_iterations}")
        print(f"Successful: {self.metrics.successful_iterations}")
        print(f"Failed: {self.metrics.failed_iterations}")
        print(f"Rollbacks: {self.metrics.rollbacks_triggered}")
        print(f"Insights generated: {self.metrics.insights_generated}")
        print(f"Average reward: {self.metrics.avg_reward:.3f}")

        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            print(f"Total runtime: {duration:.1f}s")

    def get_status(self) -> dict:
        """Get current loop status."""
        return {
            "phase": self.phase.value,
            "state": self.state.value,
            "running": self._running,
            "metrics": self.metrics.to_dict(),
            "consecutive_failures": self.consecutive_failures,
        }


# === Convenience Function ===

def run_evolutionary_loop(
    workspace: Path = None,
    max_iterations: int = 10,
    initial_prompt: str = None,
    **kwargs
) -> LoopMetrics:
    """
    Run the evolutionary loop with sensible defaults.

    Args:
        workspace: Working directory
        max_iterations: Maximum iterations to run
        initial_prompt: Starting prompt (optional)
        **kwargs: Additional config options

    Returns:
        Loop metrics
    """
    config = EvolutionaryConfig(
        workspace=workspace or Path("."),
        max_iterations=max_iterations,
        **kwargs
    )

    loop = EvolutionaryLoop(config)
    loop.run(initial_prompt)

    return loop.metrics


# === Usage Example ===

if __name__ == "__main__":
    from pathlib import Path

    workspace = Path(".")
    state_dir = workspace / ".ouroboros"
    state_dir.mkdir(exist_ok=True)

    config = EvolutionaryConfig(
        workspace=workspace,
        state_dir=state_dir,
        max_iterations=5,
        iteration_delay_seconds=2.0,
        enable_watchdog=True,
        enable_sandbox=True,
        enable_reward_learning=True,
        enable_meta_prompts=True,
    )

    loop = EvolutionaryLoop(config)

    # Set up callbacks
    def on_insight(insight):
        print(f"   🧠 Learned: {insight[:60]}...")

    loop.on_insight = on_insight

    # Run with initial prompt
    loop.run(
        initial_prompt="Improve the self-prompting loop by adding better reflection"
    )

    # Print final status
    print("\n" + "=" * 60)
    print("FINAL STATUS")
    print(json.dumps(loop.get_status(), indent=2))
