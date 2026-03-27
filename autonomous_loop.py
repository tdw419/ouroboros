#!/usr/bin/env python3
"""
Ouroboros Autonomous Loop - Definitive Entry Point

This script initializes and runs the full Ouroboros self-improvement loop,
integrated with:
- CTRM Truth Memory (sqlite3)
- Unified Prompt Engine (Templates + Analytics)
- ASCII World Visual Dashboard
- Semantic Pattern Learning
"""

import argparse
import sys
from pathlib import Path

# Ensure Ouroboros source is in path
project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_root / "src"))

from ouroboros.core.loop import OuroborosLoop, LoopConfig
from ouroboros.core.goal import GoalState

def main():
    parser = argparse.ArgumentParser(description="Ouroboros Autonomous Self-Improvement Loop")
    
    # Goal Configuration
    parser.add_argument("--objective", default="Optimize the VM performance to achieve 10M ops/sec", 
                        help="The primary goal for the AI")
    parser.add_argument("--criteria", default="gpu_ops_sec >= 10000000", 
                        help="Success criteria (e.g. 'metric >= value')")
    parser.add_argument("--max-iterations", type=int, default=15, 
                        help="Maximum number of self-improvement iterations")
    parser.add_argument("--max-time", type=int, default=24, 
                        help="Maximum time in hours")
    
    # Execution Configuration
    parser.add_argument("--delay", type=float, default=5.0, 
                        help="Delay in seconds between iterations")
    parser.add_argument("--model", default="claude-sonnet-4-6-20250514", 
                        help="LLM model to use for reasoning")
    parser.add_argument("--dry-run", action="store_true", 
                        help="Run without making actual code changes")
    
    # Paths
    parser.add_argument("--workspace", default=".", 
                        help="Path to the project workspace")
    
    args = parser.parse_args()
    
    workspace_path = Path(args.workspace).resolve()
    ouro_dir = workspace_path / ".ouroboros"
    ouro_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Initialize Goal
    goal_file = ouro_dir / "goal.json"
    goal = GoalState(
        objective=args.objective,
        success_criteria=args.criteria,
        max_iterations=args.max_iterations,
        max_time_hours=args.max_time
    )
    goal.save(goal_file)
    
    # 2. Configure Loop
    config = LoopConfig(
        workspace_path=workspace_path,
        goal_file=goal_file,
        results_file=ouro_dir / "results.tsv",
        tree_file=ouro_dir / "experiment_tree.json",
        iteration_delay_seconds=args.delay,
        model=args.model,
        dry_run=args.dry_run,
        max_iterations=args.max_iterations
    )
    
    # 3. Initialize and Run Loop
    print(f"🚀 Initializing Ouroboros at {workspace_path}...")
    print(f"📝 Goal: {args.objective}")
    print(f"📊 Dashboard: {ouro_dir}/dashboard.ascii")
    print(f"🧠 Memory: truths.db (CTRM)")
    print("-" * 60)
    
    try:
        loop = OuroborosLoop(config)
        loop.run()
    except KeyboardInterrupt:
        print("\n🛑 Loop stopped by user.")
    except Exception as e:
        print(f"\n❌ Loop failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
