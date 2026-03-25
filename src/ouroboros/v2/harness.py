import click
import json
from pathlib import Path
from src.ouroboros.protocols.alignment import AlignmentFirewall
from src.ouroboros.protocols.watchdog import SelfHealingLoop, WatchdogConfig
from src.ouroboros.v2.researcher import ResearchEngine

AUTORESEARCH_PATH = Path("/home/jericho/zion/apps/autoresearch")

@click.group()
def cli():
    """Ouroboros Protocol Harness - Agent-Native CLI for Python Protocols."""
    pass

@cli.command()
@click.argument('code')
def validate_alignment(code):
    """Validate code against the Alignment Firewall."""
    state_dir = Path(".ouroboros/v2/alignment")
    firewall = AlignmentFirewall(state_dir)
    decision = firewall.validate(code)
    # Output only the JSON decision for agentic workers
    click.echo(json.dumps(decision.to_dict(), indent=2))

@cli.command()
def check_health():
    """Run health checks and return the current health status."""
    workspace = Path(".")
    loop = SelfHealingLoop(workspace)
    health = loop.watchdog._run_health_check()
    result = {
        "status": health.status.value,
        "message": health.message,
        "timestamp": health.timestamp.isoformat(),
        "details": health.details
    }
    click.echo(json.dumps(result, indent=2))

@cli.command()
def rollback():
    """Rollback the last modification."""
    workspace = Path(".")
    loop = SelfHealingLoop(workspace)
    success, message = loop.dependency_manager.rollback_last()
    result = {
        "success": success,
        "message": message
    }
    click.echo(json.dumps(result, indent=2))

@cli.command()
@click.option('--files', '-f', multiple=True, help='Files changed')
@click.option('--diff', '-d', help='The diff content')
@click.option('--sha', '-s', help='The commit SHA (if any)')
def record_modification(files, diff, sha):
    """Record a modification for potential rollback."""
    workspace = Path(".")
    loop = SelfHealingLoop(workspace)
    mod_id = loop.record_modification(list(files), diff, sha)
    result = {
        "mod_id": mod_id,
        "timestamp": Path(".ouroboros/v2/modifications.json").stat().st_mtime if Path(".ouroboros/v2/modifications.json").exists() else None
    }
    click.echo(json.dumps(result, indent=2))

@cli.command()
@click.argument('script_path')
@click.option('--timeout', default=400, help='Experiment timeout in seconds')
def run_experiment(script_path, timeout):
    """Run a single training experiment and extract metrics."""
    engine = ResearchEngine(Path("."), AUTORESEARCH_PATH)
    result = engine.run_experiment(Path(script_path), timeout_seconds=timeout)
    click.echo(json.dumps(result, indent=2))

@cli.command()
@click.option('--metric', default="val_bpb", help='Metric name to optimize')
@click.option('--maximize', is_flag=True, help='Whether to maximize the metric')
def get_best_metric(metric, maximize):
    """Get the best recorded metric value."""
    engine = ResearchEngine(Path("."), AUTORESEARCH_PATH)
    best = engine.get_best_metric(metric, minimize=not maximize)
    click.echo(json.dumps({"best_metric": best}))

@cli.command()
def status():
    """Get status of the Alignment Firewall and Watchdog."""
    state_dir = Path(".ouroboros/v2/alignment")
    firewall = AlignmentFirewall(state_dir)
    workspace = Path(".")
    loop = SelfHealingLoop(workspace)
    
    result = {
        "firewall": firewall.get_status(),
        "watchdog": loop.get_status()
    }
    click.echo(json.dumps(result, indent=2))

if __name__ == "__main__":
    cli()
