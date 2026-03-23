# Ouroboros

**Recursive Self-Prompting AI Loop**

The "brain" that drives autonomous experimentation by reading results, generating hypotheses, and iterating until a goal is achieved.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    OROBOROS (Brain)                         │
│  SelfPromptGenerator → reads results, generates hypotheses  │
├─────────────────────────────────────────────────────────────┤
│                    GOAL STATE                               │
│  Objective, success criteria, limits, best metric           │
├─────────────────────────────────────────────────────────────┤
│                 openspec+autoresearch (Body)                │
│  ExperimentLoop, TrustBoundary, ResultsLog                  │
└─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
# Install openspec+autoresearch (the body)
pip install -e /path/to/openspec+autoresearch

# Install ouroboros (the brain)
pip install -e .
```

## Quick Start

```bash
# Initialize a new loop with a goal
ouroboros init \
    --objective "Improve the algorithm to achieve accuracy >= 0.95" \
    --criteria "accuracy >= 0.95" \
    --workspace ./my_project

# Run the loop
ouroboros run --workspace ./my_project

# Check status
ouroboros status --workspace ./my_project
```

## How It Works

1. **Read Goal State** - Load objective, success criteria, and limits
2. **Read Results Log** - Analyze past attempts and outcomes
3. **Generate Hypothesis** - LLM creates next experiment to try
4. **Execute Experiment** - Run code changes and evaluation
5. **Extract Metric** - Parse output for success metric
6. **Update State** - Log result, update best metric
7. **Repeat** - Continue until goal achieved or exhausted

## Hello World Demo

See `examples/pi_approximator.py` for a simple optimization problem:

```bash
cd examples
./setup_demo.sh
ouroboros run --dry-run
```

## Components

| Component | File | Purpose |
|-----------|------|---------|
| `GoalState` | `core/goal.py` | Persistent goal and progress |
| `SelfPromptGenerator` | `core/prompt_generator.py` | LLM-based hypothesis generation |
| `OuroborosLoop` | `core/loop.py` | Recursive driver |
| `cli` | `cli.py` | Command-line interface |

## Tree Visualization

View the experiment tree/flowchart:

```bash
# Show the experiment flowchart
ouroboros tree

# Show statistics about the tree
ouroboros tree --stats
```

The tree shows:
- **Nodes**: Each experiment attempt
- **Metrics**: The result metric (M: 0.000123)
- **Timing**: Time spent on each node (30s)
- **Convergence**: Improvement direction (-0.1 = improving)
- **Status**: [ACTIVE], [EXHAUSTED], [ACHIEVED], [BASELINE]

Example output:
```
EXPERIMENT FLOWCHART
====================
└── root: Initial state [BASELINE]
    ├── node_1: Increase Leibniz iterations (M: 0.042310) 45s [EXHAUSTED]
    └── node_2: Switch to Nilakantha series (M: 0.000006) 32s -0.999 [ACTIVE]
```

### Strategic Backtracking

The AI can decide to **PIVOT** to a previous node when a path is exhausted:

```
Current Path: node_5
PIVOTING to node: node_2
```

This allows exploring alternative approaches without losing progress.

### Status Command

The `ouroboros status` command now shows a tree summary:

```bash
ouroboros status
```

Shows:
- Goal state (objective, criteria, iterations)
- Recent results (last 5 experiments)
- Experiment tree summary (nodes, depth, best node)

## Integration with openspec+autoresearch

Ouroboros is designed to work with [openspec+autoresearch](../openspec+autoresearch), which provides:

- `ExperimentLoop` - Keep-or-revert experiment execution
- `TrustBoundary` - Prevent self-modification of rules
- `ResultsLog` - Persistent memory of attempts
- `ASCIISpec` - Structured experiment format

## Safety

- **Iteration limits** - Prevent runaway loops
- **Time budgets** - Maximum execution time
- **Trust boundaries** - AI cannot modify evaluation criteria
- **Dry-run mode** - Test without execution

## License

MIT
