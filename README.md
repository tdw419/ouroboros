# Ouroboros 🐍

**A Self-Prompting, Self-Improving AI System**

Ouroboros is an autonomous AI system that generates its own prompts, executes them, learns from results, and continuously improves itself through recursive feedback loops.

## Overview

```
                    ┌─────────────────────────────────────────┐
                    │           OUROBOROS ARCHITECTURE        │
                    └─────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
              ┌──────────┐      ┌──────────┐      ┌──────────┐
              │  BRAIN   │      │  BODY    │      │  GUARD   │
              │          │      │          │      │          │
              │ Self-    │      │ Execution│      │ Safety   │
              │ Prompt   │      │ Loop     │      │ Systems  │
              └────┬─────┘      └────┬─────┘      └────┬─────┘
                   │                 │                 │
    ┌──────────────┼─────────────────┼─────────────────┼──────────────┐
    │              │                 │                 │              │
    ▼              ▼                 ▼                 ▼              ▼
┌────────┐   ┌──────────┐    ┌────────────┐    ┌──────────┐   ┌────────┐
│Meta    │   │Generator/│    │Evolutionary│    │Alignment │   │Memory  │
│Prompt  │   │Critic    │    │Loop        │    │Firewall  │   │Core    │
│Engine  │   │          │    │            │    │          │   │        │
└────────┘   └──────────┘    └────────────┘    └──────────┘   └────────┘
     │              │               │                 │             │
     └──────────────┴───────────────┴─────────────────┴─────────────┘
                                    │
                                    ▼
                          ┌──────────────────┐
                          │  INSIGHTS DB     │
                          │  (Learning)      │
                          └──────────────────┘
```

## The 10 Protocols

| # | Protocol | File | Purpose |
|---|----------|------|---------|
| 1 | Self-Modification | `protocols/self_modification.py` | 7-step safe code modification cycle |
| 2 | Sandbox | `protocols/sandbox.py` | 3-phase validation (static, simulate, verify) |
| 3 | Insights Database | `protocols/insights.py` | Versioned knowledge with heuristic scoring |
| 4 | Watchdog | `protocols/watchdog.py` | Health monitoring with auto-rollback |
| 5 | Reward Function | `protocols/reward.py` | Learnable action valuation |
| 6 | Cognitive | `protocols/cognitive.py` | Generator/Critic iterative improvement |
| 7 | Meta Prompt | `protocols/meta_prompt.py` | Recursive prompt evolution |
| 8 | Alignment | `protocols/alignment.py` | Prime Directive enforcement |
| 9 | Memory | `protocols/memory.py` | Semantic memory with embeddings |
| 10 | Observability | `protocols/observability.py` | Metrics logging and auditing |

## Quick Start

### Initialize a New Project

```bash
# Create a new project directory
mkdir my-project && cd my-project

# Initialize Ouroboros
ouroboros-init.sh "My Project Name"

# Or use full path
/home/jericho/zion/projects/ouroboros/ouroboros/ouroboros-init.sh "My Project Name"
```

### Check Provider Status

```bash
./queue.sh check
```

### View Queue Dashboard

```bash
# One-time view
./queue.sh dashboard

# Live view (auto-refresh)
./queue.sh dashboard --watch
```

### Enqueue and Process Prompts

```bash
# Add prompts to queue
./queue.sh enqueue "Analyze test coverage"
./queue.sh enqueue "Review code quality"

# Process the queue
./queue.sh process
```

### Login to OAuth Providers

```bash
./queue.sh login gemini
./queue.sh login claude
```

## The Self-Prompting Loop

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS LOOP                               │
│                                                                  │
│   1. REFLECT on past experience                                 │
│      └── Load state: insights, prompts tried, current focus     │
│                                                                  │
│   2. GENERATE next prompt                                       │
│      └── AI creates its own prompt based on context             │
│                                                                  │
│   3. VALIDATE with Alignment Firewall                           │
│      └── Check against 8 Prime Directives                       │
│                                                                  │
│   4. EXECUTE in Sandbox                                         │
│      └── Safe execution with resource limits                    │
│                                                                  │
│   5. EVALUATE with Generator/Critic                             │
│      └── Iterative improvement until convergence                │
│                                                                  │
│   6. RECORD insight                                             │
│      └── Store in Insights DB + Semantic Memory                 │
│                                                                  │
│   7. UPDATE reward model                                        │
│      └── Learn from outcome (success/failure)                   │
│                                                                  │
│   8. UPDATE meta prompts                                        │
│      └── Inject learned rules into system prompt                │
│                                                                  │
│   9. WATCHDOG health check                                      │
│      └── Rollback if degraded, heartbeat                        │
│                                                                  │
│  10. LOOP                                                       │
│      └── Generate next prompt and repeat                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## The 8 Prime Directives

| ID | Directive | Action | Description |
|----|-----------|--------|-------------|
| PD-001 | Self-Preservation | HALT | Firewall cannot modify itself |
| PD-002 | Goal Integrity | HALT | Objectives cannot be changed |
| PD-003 | Evaluation Integrity | HALT | Scoring logic is protected |
| PD-004 | Dangerous Ops Ban | BLOCK | No eval/exec/shell commands |
| PD-005 | Protected Files | BLOCK | Safety files are read-only |
| PD-006 | Bounded Execution | BLOCK | No infinite loops |
| PD-007 | Safety Preservation | FLAG | Safety checks cannot be disabled |
| PD-008 | No Reward Hacking | QUARANTINE | Gaming the reward is blocked |

## Architecture Layers

### Layer 1: Brain (Decision Making)
- `SelfPrompter` - Generates prompts autonomously
- `MetaPromptEngine` - Evolves prompts from learnings
- `RewardFunction` - Values actions by outcomes

### Layer 2: Body (Execution)
- `EvolutionaryLoop` - Main orchestrator
- `GeneratorAgent/CriticAgent` - Code improvement cycle
- `Sandbox` - Safe execution environment

### Layer 3: Guard (Safety)
- `AlignmentFirewall` - Prime directives enforcement
- `WatchdogAgent` - Health monitoring & rollback
- `DependencyManager` - Git-based recovery

### Layer 4: Memory (Learning)
- `InsightsDatabase` - Structured insights with scoring
- `SemanticMemoryCore` - Vector embeddings for retrieval
- `SystemAuditor` - Consistency verification

## API Reference

### High-Level

```python
from ouroboros.evolutionary import run_evolutionary_loop

metrics = run_evolutionary_loop(
    workspace=Path("."),
    max_iterations=10,
    initial_prompt="Improve test coverage",
)
```

### Low-Level

```python
from ouroboros.protocols.alignment import AlignmentFirewall
from ouroboros.protocols.memory import SemanticMemoryCore
from ouroboros.protocols.cognitive import CognitiveSimulation

# Validate code against Prime Directives
firewall = AlignmentFirewall(state_dir)
decision = firewall.validate(code_to_check)
if decision.approved:
    apply_modification()

# Remember and recall
memory = SemanticMemoryCore(state_dir)
memory.remember("Important insight", MemoryType.INSIGHT, iteration=1)
results = memory.recall("similar insights")

# Generator/Critic cycle
sim = CognitiveSimulation(state_dir)
result = sim.run_task(task, max_iterations=3)
```

## Running Autonomously

```bash
# Set up cron (runs every 15 minutes)
./scripts/setup_cron.sh

# View logs
tail -f .ouroboros/logs/

# Check state
cat .ouroboros/self_prompt_state.json
```

## File Structure

```
ouroboros/
├── src/ouroboros/
│   ├── core/
│   │   ├── self_prompt_loop.py    # Brain
│   │   ├── goal.py                # Objectives
│   │   ├── tree.py                # Experiment tracking
│   │   └── safety.py              # Trust boundaries
│   ├── protocols/
│   │   ├── self_modification.py   # Protocol 1
│   │   ├── sandbox.py             # Protocol 2
│   │   ├── insights.py            # Protocol 3
│   │   ├── watchdog.py            # Protocol 4
│   │   ├── reward.py              # Protocol 5
│   │   ├── cognitive.py           # Protocol 6
│   │   ├── meta_prompt.py         # Protocol 7
│   │   ├── alignment.py           # Protocol 8
│   │   ├── memory.py              # Protocol 9
│   │   └── observability.py       # Protocol 10
│   ├── evolutionary.py            # Main loop
│   ├── tui.py                     # Interactive interface
│   └── cli.py                     # Command line
├── .ouroboros/                    # State directory
│   ├── goal.yaml
│   ├── safety.yaml
│   ├── self_prompt_state.json
│   └── logs/
├── scripts/
│   ├── cron_self_prompt.sh        # Autonomous cron
│   └── setup_cron.sh              # One-click setup
└── docs/
    └── HOW_IT_WORKS.md            # Architecture deep dive
```

## Key Insights from Development

1. **Safety First**: Alignment firewall runs BEFORE any modification
2. **Learning Persists**: Semantic memory survives across iterations
3. **Feedback Loops**: Generator/Critic iterates until convergence
4. **Auto-Recovery**: Watchdog rolls back on consecutive failures
5. **Prompt Evolution**: Meta engine learns from patterns

## Configuration

```yaml
# .ouroboros/goal.yaml
objective: "Improve test coverage to > 90%"
success_criteria: "METRIC >= 90.0"
max_iterations: 100
max_time_hours: 24.0

# .ouroboros/safety.yaml
protected_files:
  - src/ouroboros/core/safety.py
  - src/ouroboros/protocols/alignment.py
allowed_targets:
  - tests/
  - src/ouroboros/protocols/
create_backup: true
```

## Philosophy

Ouroboros embodies three principles:

1. **Self-Reference**: The system prompts itself, creating infinite improvement potential
2. **Safe Boundaries**: Prime directives protect core values from modification
3. **Persistent Learning**: Semantic memory ensures lessons aren't forgotten

The snake eating its tail - destruction and creation in eternal cycle.

## Documentation

- [HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md) - Architecture deep dive
- [self_prompt_loop.py](src/ouroboros/core/self_prompt_loop.py) - The brain
- [evolutionary.py](src/ouroboros/evolutionary.py) - Main orchestrator

## License

MIT

---

*"The serpent which cannot shed its skin perishes. So too with minds."* - Nietzsche
