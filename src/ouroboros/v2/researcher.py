import subprocess
import re
import json
import shutil
import time
from pathlib import Path
from typing import Optional, Dict, Any

class ResearchEngine:
    """
    The 'Body' of Ouroboros - executes autonomous experiments.
    Wraps the autoresearch train.py logic.
    """
    
    def __init__(self, workspace: Path, autoresearch_path: Path):
        self.workspace = workspace
        self.autoresearch_path = autoresearch_path
        self.results_file = workspace / ".ouroboros" / "research_results.json"
        self.results_file.parent.mkdir(exist_ok=True)
        
    def run_experiment(self, train_script: Path, timeout_seconds: int = 400) -> Dict[str, Any]:
        """
        Run a single training experiment and extract metrics.
        """
        start_time = time.time()
        
        # 1. Copy the training script to the autoresearch directory (as train.py)
        # We assume autoresearch is set up with dependencies
        target_script = self.autoresearch_path / "train.py"
        if train_script.resolve() != target_script.resolve():
            shutil.copy(train_script, target_script)
        
        try:
            # 2. Execute via uv run
            process = subprocess.run(
                ["uv", "run", "train.py"],
                cwd=self.autoresearch_path,
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )
            
            output = process.stdout + process.stderr
            
            # 3. Extract metrics
            metrics = self._parse_output(output)
            metrics["success"] = process.returncode == 0
            metrics["duration"] = time.time() - start_time
            
            if not metrics["success"]:
                metrics["error"] = process.stderr
                
            self._save_result(metrics)
            return metrics
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Experiment timed out", "duration": time.time() - start_time}
        except Exception as e:
            return {"success": False, "error": str(e), "duration": time.time() - start_time}

    def _parse_output(self, output: str) -> Dict[str, Any]:
        """Parse the output of train.py for metrics."""
        metrics = {}
        
        patterns = {
            "val_bpb": r"val_bpb:\s+([\d\.]+)",
            "peak_vram_mb": r"peak_vram_mb:\s+([\d\.]+)",
            "mfu_percent": r"mfu_percent:\s+([\d\.]+)",
            "num_params_M": r"num_params_M:\s+([\d\.]+)",
            "depth": r"depth:\s+(\d+)"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, output)
            if match:
                metrics[key] = float(match.group(1))
                
        return metrics

    def _save_result(self, result: Dict[str, Any]):
        """Append result to the history."""
        history = []
        if self.results_file.exists():
            with open(self.results_file, "r") as f:
                history = json.load(f)
        
        history.append({
            "timestamp": time.time(),
            "metrics": result
        })
        
        with open(self.results_file, "w") as f:
            json.dump(history, f, indent=2)

    def get_best_metric(self, metric_name: str = "val_bpb", minimize: bool = True) -> Optional[float]:
        """Get the best recorded metric value."""
        if not self.results_file.exists():
            return None
            
        with open(self.results_file, "r") as f:
            history = json.load(f)
            
        values = [h["metrics"].get(metric_name) for h in history if h["metrics"].get("success") and metric_name in h["metrics"]]
        
        if not values:
            return None
            
        return min(values) if minimize else max(values)
