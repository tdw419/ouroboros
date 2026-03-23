#!/usr/bin/env python3
"""
Ouroboros → pxOS Autonomous Loop Demo

Shows how the recursive AI brain connects to the pixel substrate.
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))

from integrations.pxos_bridge import PxOSAdapter, OuroborosPxOSBridge


def demo_autonomous_optimization():
    """
    Demo: Run an autonomous optimization loop.
    
    This is a simplified version. Full Ouroboros uses:
    - SelfPromptGenerator for AI-driven hypothesis creation
    - ExperimentTree for branching/rollback
    - SafetyManager for guardrails
    """
    print("=" * 70)
    print("OUROBOROS → pxOS AUTONOMOUS OPTIMIZATION DEMO")
    print("=" * 70)
    
    bridge = OuroborosPxOSBridge()
    
    # Define goal
    goal = {
        "objective": "Optimize VM throughput",
        "criteria": "ops_per_sec >= 5000000",
        "target": "sync/synthetic-glyph-vm.js",
        "metric_name": "gpu_ops_sec",
        "max_iterations": 10,
        "budget": 1
    }
    
    print(f"\nGoal: {goal['objective']}")
    print(f"Criteria: {goal['criteria']}")
    print(f"Target: {goal['target']}")
    print()
    
    # Get baseline
    print("BASELINE:")
    cells = bridge.adapter.get_cells()
    baseline = cells.get("gpu_ops_sec", 0)
    print(f"  Current ops/sec: {baseline:,}")
    print()
    
    # Run optimization (simplified loop)
    print("RUNNING AUTONOMOUS LOOP:")
    print("-" * 70)
    
    best_metric = baseline
    iterations = 0
    
    for i in range(goal["max_iterations"]):
        iterations = i + 1
        
        # Get current state
        cells = bridge.adapter.get_cells()
        current = cells.get("gpu_ops_sec", 0)
        
        print(f"\nIteration {iterations}:")
        print(f"  Current: {current:,} ops/sec")
        print(f"  Best: {best_metric:,} ops/sec")
        
        # Check goal
        if current >= 5000000:
            print("\n✓ GOAL ACHIEVED!")
            break
        
        # Generate hypothesis (in full Ouroboros, AI does this)
        hypothesis = f"Optimization attempt {iterations}"
        
        # Run experiment
        spec = bridge.format_ascii_spec(
            hypothesis=hypothesis,
            target=goal["target"],
            metric=goal["criteria"],
            budget=goal["budget"]
        )
        
        result = bridge.adapter.run_experiment(spec, x=0, y=100 + i * 20)
        status = result.get("status", "unknown")
        
        print(f"  Experiment: {status}")
        
        # Update best
        if current > best_metric:
            best_metric = current
            print(f"  ↑ NEW BEST!")
    
    print()
    print("=" * 70)
    print("OPTIMIZATION COMPLETE")
    print("=" * 70)
    print(f"\nIterations: {iterations}")
    print(f"Baseline: {baseline:,} ops/sec")
    print(f"Best: {best_metric:,} ops/sec")
    print(f"Improvement: {((best_metric - baseline) / baseline * 100):.1f}%" if baseline > 0 else "N/A")
    
    bridge.adapter.close()
    return {
        "iterations": iterations,
        "baseline": baseline,
        "best": best_metric
    }


def demo_vm_execution():
    """Demo: Execute VM programs via the bridge."""
    print("=" * 70)
    print("VM EXECUTION DEMO")
    print("=" * 70)
    
    with PxOSAdapter() as adapter:
        # Reset VM
        print("\n1. Resetting VM...")
        adapter.reset_vm()
        
        # Check state
        state = adapter.get_vm_state()
        print(f"   PC: {state['pc']}, Cycles: {state['cycles']}")
        
        # Load and execute a simple program
        print("\n2. Executing program...")
        # Program: MOV 10 to R0, MOV 20 to R1, DRAW
        program = [
            [206, 0, 10, 0, 0],   # MOV R0, 10
            [206, 0, 11, 20, 0],  # MOV R1, 20
            [215, 0, 10, 20, 2],  # DRAW at (10, 20)
        ]
        
        result = adapter.execute_vm(program, max_cycles=1000)
        print(f"   Cycles executed: {result['cycles']}")
        print(f"   Halted: {result['halted']}")
        
        # Check final state
        state = adapter.get_vm_state()
        print(f"\n3. Final state:")
        print(f"   PC: {state['pc']}, Cycles: {state['cycles']}")
        
        print("\n" + "=" * 70)
        print("VM EXECUTION COMPLETE")
        print("=" * 70)


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("OUROBOROS → pxOS INTEGRATION DEMOS")
    print("=" * 70)
    
    print("\nChoose demo:")
    print("  1. Autonomous Optimization")
    print("  2. VM Execution")
    print("  3. Both")
    
    choice = input("\nChoice [1-3]: ").strip() or "3"
    
    if choice in ("1", "3"):
        demo_autonomous_optimization()
    
    if choice in ("2", "3"):
        demo_vm_execution()
    
    print("\n" + "=" * 70)
    print("INTEGRATION READY")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Wire into OuroborosLoop (core/loop.py)")
    print("  2. Add SelfPromptGenerator for AI hypotheses")
    print("  3. Enable ExperimentTree for branching")
    print("  4. Run full autonomous optimization")


if __name__ == "__main__":
    main()
