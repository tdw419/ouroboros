import click
import json
import re
from pathlib import Path
from typing import List, Dict

class RoadmapManager:
    def __init__(self, roadmap_path: Path):
        self.roadmap_path = roadmap_path
        if not self.roadmap_path.exists():
            self._create_default_roadmap()

    def _create_default_roadmap(self):
        content = """# Ouroboros V2 Strategic Roadmap

## Phase 1: Capacity Optimization [ACTIVE]
- [x] Establish baseline metrics (val_bpb)
- [ ] Optimize embedding dimensions (n_embd)
- [ ] Refine model depth (n_layer)
- [ ] Achieve val_bpb < 1.90

## Phase 2: Training Dynamics
- [ ] Tune Learning Rate schedule
- [ ] Experiment with Optimizer weight decay
- [ ] Increase sequence length (MAX_SEQ_LEN)

## Phase 3: Code Hardening
- [ ] Implement comprehensive unit tests for protocols
- [ ] Add docstrings to all v2 modules
- [ ] Refine Alignment Firewall regex patterns

## Phase 4: Final Validation
- [ ] Run 50-iteration stability test
- [ ] Final performance report
"""
        self.roadmap_path.write_text(content)

    def get_current_milestone(self) -> str:
        content = self.roadmap_path.read_text()
        match = re.search(r"## (.*?) \[ACTIVE\]", content)
        if match:
            return match.group(1)
        return "Unknown Milestone"

    def get_active_tasks(self) -> List[str]:
        content = self.roadmap_path.read_text()
        active_section = re.split(r"## ", content)
        for section in active_section:
            if "[ACTIVE]" in section:
                tasks = re.findall(r"- \[ \] (.*)", section)
                return tasks
        return []

    def mark_task_complete(self, task_description: str):
        content = self.roadmap_path.read_text()
        # Case-insensitive partial match
        pattern = re.compile(re.escape(task_description), re.IGNORECASE)
        lines = content.splitlines()
        new_lines = []
        for line in lines:
            if "- [ ]" in line and pattern.search(line):
                new_lines.append(line.replace("- [ ]", "- [x]"))
            else:
                new_lines.append(line)
        self.roadmap_path.write_text("\n".join(new_lines))

@click.group()
def cli():
    pass

@cli.command()
def status():
    manager = RoadmapManager(Path("ROADMAP.md"))
    result = {
        "current_milestone": manager.get_current_milestone(),
        "active_tasks": manager.get_active_tasks()
    }
    click.echo(json.dumps(result, indent=2))

@cli.command()
@click.argument('task')
def complete(task):
    manager = RoadmapManager(Path("ROADMAP.md"))
    manager.mark_task_complete(task)
    click.echo(json.dumps({"success": True, "completed": task}))

if __name__ == "__main__":
    cli()
