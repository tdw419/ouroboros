# Plan: The Council of Ouroboros (Multi-Agent Swarm)

**Goal:** Implement a parallel, multi-agent architecture where multiple workers explore different branches of the Experiment Tree simultaneously using Git worktrees for isolation.

## 1. Architecture Overview

### Components
- **CouncilOrchestrator**: The "Master" process. Manages the shared `tree.yaml`, `goal.yaml`, and `results.tsv`. It identifies active frontier nodes and assigns them to available workers.
- **WorkerAgent**: The "Worker" process. Each worker manages a private workspace (Git worktree), runs a single-iteration `OuroborosLoop`, and reports the result back to the Orchestrator.
- **Git Worktree Isolation**: Each worker operates in `/tmp/ouroboros/worker-<N>`. This allows parallel workers to have different `git checkout` states without collision.

## 2. Key Changes

### Data Model Updates
- **ExperimentNode (`tree.py`)**: Add `locked_by` (worker_id) and `assigned_at` timestamp to prevent multiple workers from claiming the same branch.
- **ExperimentTree (`tree.py`)**: Add methods to `claim_node(node_id, worker_id)` and `release_node(node_id)`.

### New Core Module: `core/council.py`
- `CouncilConfig`: Dataclass for workers count, workspace prefix, etc.
- `Worker`: Handles the sub-process lifecycle and its dedicated Git worktree.
- `CouncilOrchestrator`: The main loop that monitors the tree, spawns workers, and merges results.

### CLI Updates (`cli.py`)
- `ouroboros council --workers N`: Launches the orchestrator.
- Integrated cleanup to remove temporary worktrees on exit.

## 3. Implementation Steps

### Phase 1: Isolation Infrastructure
1. Implement `WorktreeManager` to handle `git worktree add` and `git worktree remove`.
2. Ensure each worker has its own `.ouroboros` symlink or copy to communicate with the master project.

### Phase 2: Orchestration Logic
1. Update `ExperimentTree` with locking mechanisms.
2. Implement the Orchestrator loop:
   - Scan tree for `ACTIVE` nodes not locked by any worker.
   - Spawn `WorkerAgent` sub-processes for each available worker slot.
   - Collect results and update the master `tree.yaml`.

### Phase 3: CLI & Testing
1. Add the `council` command to `cli.py`.
2. Run a parallel demo on the `pi_approximator` to verify 2-4x speedup.

## 4. Verification & Testing
- **Concurrency Test**: Start 4 workers and verify they claim 4 different nodes.
- **Git Safety**: Verify that `git status` in the main repo is unaffected by worker checkouts.
- **Cleanup**: Verify `/tmp/ouroboros/` is empty after the command exits.
