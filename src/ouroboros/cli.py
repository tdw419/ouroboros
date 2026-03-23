"""
CLI for Ouroboros - Recursive Self-Prompting Loop
"""

import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from typing import List, Optional

from .core.goal import GoalState
from .core.loop import OuroborosLoop, LoopConfig
from .core.safety import SafetyConfig, SafetyManager

app = typer.Typer(help="Ouroboros - Recursive Self-Prompting AI Loop")
console = Console()


@app.command()
def init(
    objective: str = typer.Option(..., "--objective", "-o", help="The goal to achieve"),
    criteria: str = typer.Option(
        ..., "--criteria", "-c", help="Success criteria (e.g., 'accuracy >= 0.95')"
    ),
    workspace: Path = typer.Option(
        Path("."), "--workspace", "-w", help="Workspace directory"
    ),
    max_iterations: int = typer.Option(100, "--max-iter", "-n", help="Maximum iterations"),
    max_hours: float = typer.Option(24.0, "--max-hours", "-t", help="Maximum hours"),
    protect: Optional[List[str]] = typer.Option(
        None, "--protect", "-p", help="Files to protect (cannot be modified by AI)"
    ),
    allow: Optional[List[str]] = typer.Option(
        None, "--allow", "-a", help="Files the AI can modify (default: all non-protected)"
    ),
):
    """Initialize a new Ouroboros loop with a goal."""
    workspace = workspace.resolve()

    # Create .ouroboros directory
    ouroboros_dir = workspace / ".ouroboros"
    ouroboros_dir.mkdir(exist_ok=True)

    goal_file = ouroboros_dir / "goal.yaml"
    results_file = ouroboros_dir / "results.tsv"
    safety_file = ouroboros_dir / "safety.yaml"
    tree_file = ouroboros_dir / "tree.yaml"

    # Create goal state
    goal = GoalState(
        objective=objective,
        success_criteria=criteria,
        max_iterations=max_iterations,
        max_time_hours=max_hours,
    )
    goal.save(goal_file)

    # Create empty results file
    if not results_file.exists():
        with open(results_file, "w") as f:
            f.write("timestamp\thypothesis\ttarget\tstatus\tmetric\n")

    # Create empty tree
    if not tree_file.exists():
        with open(tree_file, "w") as f:
            f.write("{}")

    # Create safety config
    import yaml
    safety_config = {
        "protected_files": protect or [],
        "allowed_targets": allow or [],
        "create_backup": True,
        "max_file_size": 100000,
    }
    with open(safety_file, "w") as f:
        yaml.dump(safety_config, f)

    console.print(f"✅ Initialized Ouroboros loop in {ouroboros_dir}")
    console.print(f"🎯 Objective: {objective}")
    console.print(f"📊 Criteria: {criteria}")

    if protect:
        console.print(f"🔒 Protected files: {', '.join(protect)}")
    if allow:
        console.print(f"✏️ Allowed targets: {', '.join(allow)}")

    console.print()
    console.print("Run with: ouroboros run")
    console.print("Dry run: ouroboros run --dry-run")


@app.command()
def run(
    workspace: Path = typer.Option(
        Path("."), "--workspace", "-w", help="Workspace directory"
    ),
    model: str = typer.Option(
        "claude-sonnet-4-6-20250514", "--model", "-m", help="Model to use"
    ),
    delay: float = typer.Option(5.0, "--delay", "-d", help="Delay between iterations (seconds)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Generate prompts but don't execute"),
    max_iterations: int = typer.Option(100, "--max-iter", "-n", help="Override max iterations"),
    verify_safety: bool = typer.Option(True, "--verify-safety/--no-verify-safety", help="Enable safety verification"),
):
    """Run the Ouroboros loop."""
    workspace = workspace.resolve()
    ouroboros_dir = workspace / ".ouroboros"

    if not ouroboros_dir.exists():
        console.print("❌ Not initialized. Run 'ouroboros init' first.")
        raise typer.Exit(1)

    # Load safety config
    safety_file = ouroboros_dir / "safety.yaml"
    safety_manager = None
    if verify_safety and safety_file.exists():
        import yaml
        with open(safety_file) as f:
            safety_config_dict = yaml.safe_load(f)
        safety_config = SafetyConfig(
            protected_files=safety_config_dict.get("protected_files", []),
            allowed_targets=safety_config_dict.get("allowed_targets", []),
            create_backup=safety_config_dict.get("create_backup", True),
        )
        safety_manager = SafetyManager(safety_config, workspace)
        safety_manager.lock()

    config = LoopConfig(
        workspace_path=workspace,
        goal_file=ouroboros_dir / "goal.yaml",
        results_file=ouroboros_dir / "results.tsv",
        tree_file=ouroboros_dir / "tree.yaml",
        iteration_delay_seconds=delay,
        model=model,
        dry_run=dry_run,
        max_iterations=max_iterations,
        safety_manager=safety_manager,
    )

    loop = OuroborosLoop(config)
    loop.run()

    # Final safety verification
    if safety_manager and not dry_run:
        if not safety_manager.verify():
            violations = safety_manager.get_violations()
            console.print(f"\n⚠️ WARNING: Trust boundary violations detected!")
            for v in violations:
                console.print(f"  - {v}")
            console.print("The AI may have attempted to modify protected files.")


@app.command()
def status(
    workspace: Path = typer.Option(
        Path("."), "--workspace", "-w", help="Workspace directory"
    ),
):
    """Show current loop status."""
    workspace = workspace.resolve()
    ouroboros_dir = workspace / ".ouroboros"

    if not ouroboros_dir.exists():
        console.print("❌ Not initialized. Run 'ouroboros init' first.")
        raise typer.Exit(1)

    goal = GoalState.load(ouroboros_dir / "goal.yaml")

    table = Table(title="Ouroboros Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Objective", goal.objective)
    table.add_row("Success Criteria", goal.success_criteria)
    table.add_row("Current State", goal.current_state)
    table.add_row("Iterations", str(goal.iterations))
    table.add_row("Best Metric", str(goal.best_metric or "N/A"))
    table.add_row("Max Iterations", str(goal.max_iterations))
    table.add_row("Created", goal.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    table.add_row("Updated", goal.updated_at.strftime("%Y-%m-%d %H:%M:%S"))

    console.print(table)

    # Show recent results
    results_file = ouroboros_dir / "results.tsv"
    if results_file.exists():
        with open(results_file) as f:
            lines = f.readlines()

        if len(lines) > 1:
            console.print()
            results_table = Table(title="Recent Results")
            results_table.add_column("Time", style="dim")
            results_table.add_column("Hypothesis", style="cyan")
            results_table.add_column("Status")
            results_table.add_column("Metric")

            for line in lines[-5:]:  # Last 5 results
                parts = line.strip().split("\t")
                if len(parts) >= 5:
                    results_table.add_row(
                        parts[0][:19],  # timestamp
                        parts[1][:40] + "...",  # hypothesis
                        parts[3],  # status
                        parts[4],  # metric
                    )

            console.print(results_table)

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


@app.command()
def reset(
    workspace: Path = typer.Option(
        Path("."), "--workspace", "-w", help="Workspace directory"
    ),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Reset the loop state (keeps goal, clears results)."""
    workspace = workspace.resolve()
    ouroboros_dir = workspace / ".ouroboros"

    if not ouroboros_dir.exists():
        console.print("❌ Not initialized.")
        raise typer.Exit(1)

    if not confirm:
        if not typer.confirm("This will clear results. Continue?"):
            raise typer.Abort()

    # Reset results
    results_file = ouroboros_dir / "results.tsv"
    with open(results_file, "w") as f:
        f.write("timestamp\thypothesis\ttarget\tstatus\tmetric\n")

    # Reset tree
    tree_file = ouroboros_dir / "tree.yaml"
    with open(tree_file, "w") as f:
        f.write("{}")

    # Reset goal iterations
    goal = GoalState.load(ouroboros_dir / "goal.yaml")
    goal.iterations = 0
    goal.best_metric = None
    goal.current_state = "initialized"
    goal.save(ouroboros_dir / "goal.yaml")

    console.print("✅ Loop reset. Run 'ouroboros run' to start fresh.")


if __name__ == "__main__":
    app()
