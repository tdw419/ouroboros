# Ouroboros Protocol Skill

This skill allows the Ouroboros AI to validate its own code changes against the Alignment Firewall before execution.

## Rules
- ALWAYS call `validate_alignment` before applying any code changes.
- If `approved` is `false`, DO NOT execute the code. Instead, reflect on the violation and propose a corrected version.
- If `halt_required` is `true`, STOP all operations immediately.

## Usage

### Validate Alignment
Validate a Python code snippet against the 8 Prime Directives.

```bash
export PYTHONPATH=.
python3 src/ouroboros/v2/harness.py validate-alignment 'print("Hello World")'
```

### Get Status
Check the current status and statistics of the Alignment Firewall.

```bash
export PYTHONPATH=.
python3 src/ouroboros/v2/harness.py status
```

## Research & Experiments
This skill enables the "Body" of Ouroboros to run training experiments and track performance.

### Run Experiment
Run a training script (e.g. `train.py`) and extract metrics like `val_bpb`.

```bash
export PYTHONPATH=.
python3 src/ouroboros/v2/harness.py run-experiment train.py --timeout 600
```

### Get Best Metric
Retrieve the best recorded metric value to guide the optimization process.

```bash
export PYTHONPATH=.
python3 src/ouroboros/v2/harness.py get-best-metric --metric val_bpb
```

## Autonomous Guidelines
- **Validate First**: ALWAYS call `validate-alignment` before modifying `train.py`.
- **Iterate Small**: Make incremental changes to hyperparameters or architecture.
- **Track Metrics**: Use `get-best-metric` to ensure each new iteration is improving over the baseline.
- **Auto-Heal**: If an experiment breaks the training loop, the Watchdog will detect it during the next health check.

## Directives
- PD-001: Self-Preservation (Halt on modification of firewall)
- PD-002: Goal Integrity (Halt on modification of objectives)
- PD-003: Evaluation Integrity (Halt on tampering with scoring)
- PD-004: Dangerous Operations Ban (Block eval, exec, os.system, etc.)
- PD-005: Protected File Respect (Block modification of critical system files)
- PD-006: Bounded Execution (Block infinite loops and unbounded recursion)
- PD-007: Safety Check Preservation (Flag removal of safety checks)
- PD-008: No Reward Hacking (Quarantine exploits to game rewards)
