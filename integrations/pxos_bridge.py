"""
Ouroboros → pxOS Integration

Wires the recursive AI brain (Ouroboros) to the pixel substrate (pxOS).

Architecture:
    Ouroboros (Brain) → pxOS Adapter → pxOS Server → Pixels

The adapter:
1. Reads pxOS experiment results via HTTP API
2. Sends hypotheses to pxOS for execution
3. Returns metrics to Ouroboros for evaluation
"""

import httpx
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class PxOSConfig:
    """Configuration for pxOS connection."""
    base_url: str = "http://localhost:3839"
    timeout: float = 30.0


class PxOSAdapter:
    """
    Bridges Ouroboros to pxOS.
    
    Provides:
    - run_experiment(spec) → Execute ASCII spec on pxOS
    - get_results() → Read experiment results
    - get_metrics() → Get current system metrics
    - push_to_vm(program) → Execute VM program
    """
    
    def __init__(self, config: Optional[PxOSConfig] = None):
        self.config = config or PxOSConfig()
        self.client = httpx.Client(base_url=self.config.base_url, timeout=self.config.timeout)
    
    def health_check(self) -> bool:
        """Check if pxOS server is running."""
        try:
            resp = self.client.get("/api/v1/cells")
            return resp.status_code == 200
        except:
            return False
    
    def get_cells(self) -> Dict[str, Any]:
        """Get current cell values (metrics)."""
        resp = self.client.get("/api/v1/cells")
        resp.raise_for_status()
        return resp.json()
    
    def set_cells(self, cells: Dict[str, Any]) -> Dict[str, Any]:
        """Set cell values."""
        resp = self.client.post("/api/v1/cells", json=cells)
        resp.raise_for_status()
        return resp.json()
    
    def run_experiment(self, spec: str, x: int = 0, y: int = 0) -> Dict[str, Any]:
        """
        Run an ASCII experiment spec on pxOS.
        
        Args:
            spec: ASCII spec string (H: hypothesis, T: target, M: metric, B: budget)
            x, y: Canvas coordinates for result rendering
        
        Returns:
            Experiment result with status, metric, etc.
        """
        payload = {
            "spec": spec,
            "x": x,
            "y": y
        }
        resp = self.client.post("/api/v1/experiments/run", json=payload)
        resp.raise_for_status()
        return resp.json()
    
    def get_vm_state(self) -> Dict[str, Any]:
        """Get current VM state."""
        resp = self.client.get("/api/v1/vm/state")
        resp.raise_for_status()
        return resp.json()
    
    def execute_vm(self, program: list, max_cycles: int = 10000) -> Dict[str, Any]:
        """
        Execute a VM program.
        
        Args:
            program: List of [opcode, target, flags, ...] instructions
            max_cycles: Maximum cycles to execute
        
        Returns:
            Execution result with cycles, halted state, pixels
        """
        payload = {
            "program": program,
            "maxCycles": max_cycles
        }
        resp = self.client.post("/api/v1/vm/execute", json=payload)
        resp.raise_for_status()
        return resp.json()
    
    def reset_vm(self) -> Dict[str, Any]:
        """Reset VM to initial state."""
        resp = self.client.post("/api/v1/vm/reset")
        resp.raise_for_status()
        return resp.json()
    
    def get_render(self) -> bytes:
        """Get current pixel buffer as PNG."""
        resp = self.client.get("/api/v1/render")
        resp.raise_for_status()
        return resp.content
    
    def close(self):
        """Close HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


# Integration with Ouroboros
class OuroborosPxOSBridge:
    """
    Full integration bridge between Ouroboros and pxOS.
    
    Usage:
        bridge = OuroborosPxOSBridge()
        
        # Run autonomous optimization
        result = bridge.run_goal(
            objective="Optimize VM to 10M ops/sec",
            criteria="ops_per_sec >= 10000000",
            max_iterations=50
        )
    """
    
    def __init__(self, pxos_config: Optional[PxOSConfig] = None):
        self.adapter = PxOSAdapter(pxos_config)
    
    def extract_metric(self, cells: Dict[str, Any], metric_name: str) -> Optional[float]:
        """Extract a specific metric from cells."""
        return cells.get(metric_name)
    
    def format_ascii_spec(self, hypothesis: str, target: str, metric: str, budget: int) -> str:
        """Format an ASCII experiment spec."""
        return f"""H: {hypothesis}
T: {target}
M: {metric}
B: {budget}"""
    
    def run_experiment(self, spec: str, x: int = 0, y: int = 0) -> Dict[str, Any]:
        """
        Run an ASCII experiment spec on pxOS.
        
        Args:
            spec: ASCII spec string (H: hypothesis, T: target, M: metric, B: budget)
            x, y: Canvas coordinates for result rendering
        
        Returns:
            Experiment result with status, metric, etc.
        """
        payload = {
            "spec": spec,
            "x": x,
            "y": y
        }
        resp = self.client.post("/api/v1/experiments/run", json=payload)
        resp.raise_for_status()
        return resp.json()
    
    def run_goal(self, 
                 objective: str,
                 criteria: str,
                 target: str = "sync/synthetic-glyph-vm.js",
                 metric_name: str = "gpu_ops_sec",
                 max_iterations: int = 50,
                 budget: int = 5) -> Dict[str, Any]:
        """
        Run an autonomous optimization goal.
        
        This is a simplified loop. For full recursive AI,
        use OuroborosLoop from core/loop.py.
        """
        results = []
        
        for i in range(max_iterations):
            # Get current metrics
            cells = self.adapter.get_cells()
            current_metric = self.extract_metric(cells, metric_name)
            
            print(f"Iteration {i+1}: {metric_name} = {current_metric}")
            
            # Check if goal achieved
            # (simplified - real criteria parsing in Ouroboros)
            if current_metric and current_metric >= 10000000:
                print("✓ Goal achieved!")
                return {
                    "status": "achieved",
                    "iterations": i + 1,
                    "final_metric": current_metric,
                    "results": results
                }
            
            # Generate hypothesis (simplified - real AI in Ouroboros)
            hypothesis = f"Optimization attempt {i+1}"
            
            # Run experiment
            spec = self.format_ascii_spec(hypothesis, target, f"{metric_name} >= target", budget)
            result = self.adapter.run_experiment(spec, x=0, y=100 + i * 20)
            results.append(result)
            
            print(f"  Result: {result.get('status', 'unknown')}")
        
        return {
            "status": "exhausted",
            "iterations": max_iterations,
            "results": results
        }


def demo():
    """Demo: Test the bridge."""
    print("=" * 60)
    print("OUROBOROS → pxOS BRIDGE DEMO")
    print("=" * 60)
    
    with PxOSAdapter() as adapter:
        # Health check
        print("\n1. Health check:")
        print(f"   pxOS running: {adapter.health_check()}")
        
        # Get current metrics
        print("\n2. Current metrics:")
        cells = adapter.get_cells()
        for key in ["gpu_ops_sec", "cpu", "mem", "gpu"]:
            if key in cells:
                print(f"   {key}: {cells[key]}")
        
        # Get VM state
        print("\n3. VM state:")
        vm = adapter.get_vm_state()
        print(f"   PC: {vm['pc']}, Cycles: {vm['cycles']}, Halted: {vm['halted']}")
        
        # Run a simple experiment
        print("\n4. Running experiment:")
        spec = """H: Test bridge connection
T: sync/server.js
M: response_time < 100ms
B: 1"""
        result = adapter.run_experiment(spec, x=0, y=200)
        print(f"   Status: {result.get('status', 'unknown')}")
        
        print("\n" + "=" * 60)
        print("BRIDGE READY")
        print("=" * 60)
        print("\nNext: Wire into OuroborosLoop for autonomous AI")


if __name__ == "__main__":
    demo()
