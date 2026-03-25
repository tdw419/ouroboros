import click
import json
from pathlib import Path
from src.ouroboros.protocols.meta_prompt import MetaPromptEngine

@click.group()
def cli():
    """Ouroboros Meta-Prompt Engine - Recursive Prompt Evolution."""
    pass

@cli.command()
@click.argument('insights_json')
def update(insights_json):
    """Update system prompt based on recent insights."""
    state_dir = Path(".ouroboros/v2/meta")
    engine = MetaPromptEngine(state_dir)
    
    try:
        insights = json.loads(insights_json)
        new_rules = engine.update_from_insights(insights)
        
        result = {
            "new_rules": [r.to_dict() for r in new_rules],
            "full_prompt": engine.get_current_prompt(),
            "statistics": engine.get_statistics()
        }
        click.echo(json.dumps(result, indent=2))
    except Exception as e:
        click.echo(json.dumps({"error": str(e)}))

@cli.command()
def get_prompt():
    """Get the current evolved system prompt."""
    state_dir = Path(".ouroboros/v2/meta")
    engine = MetaPromptEngine(state_dir)
    click.echo(engine.get_current_prompt())


@cli.command("get-current")
def get_current():
    """Get current meta-prompt rules."""
    state_dir = Path(".ouroboros/v2/meta")
    engine = MetaPromptEngine(state_dir)

    try:
        prompt = engine.get_current_prompt()
        stats = engine.get_statistics()

        # Extract rules from prompt (simple extraction)
        rules = []
        if "Learned Rules" in prompt:
            rules_section = prompt.split("Learned Rules")[1].split("\n\n")[0]
            rules = [r.strip("- ") for r in rules_section.strip().split("\n") if r.strip()]

        click.echo(json.dumps({
            "rules": rules,
            "statistics": stats,
            "prompt_length": len(prompt),
        }, indent=2))
    except Exception as e:
        click.echo(json.dumps({"error": str(e), "rules": []}))


if __name__ == "__main__":
    cli()
