#!/usr/bin/env python3
"""
True Recursive Self-Prompting Loop

The AI uses LM Studio (localhost:1234) to:
1. Read its own results
2. Generate its OWN prompts/hypotheses
3. Execute experiments
4. Read results
5. Generate new prompts
6. Repeat forever

This is TRUE recursive self-improvement.
"""

import httpx
import json
import time
from pathlib import Path
from datetime import datetime


class RecursiveSelfPrompter:
    """
    AI that prompts itself using LM Studio.
    
    The loop:
        Results → LLM → New Prompt → Execute → Results → ...
    """
    
    LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
    
    SYSTEM_PROMPT = """You are an autonomous AI running in a recursive self-improvement loop.

You have access to a pixel-based operating system (pxOS) with:
- A Virtual Machine that executes programs
- A pixel buffer for visualization
- Experiment execution capabilities

Your goal is to continuously improve the system.

OUTPUT FORMAT - Always respond with a JSON object:
{
    "analysis": "What you learned from the last results",
    "hypothesis": "What you want to try next",
    "experiment": {
        "H": "Hypothesis description",
        "T": "Target file to modify",
        "M": "Metric to optimize",
        "B": "Budget in minutes"
    },
    "reasoning": "Why this hypothesis might work",
    "next_check_seconds": 60
}

BE CREATIVE. Try different approaches:
- Optimize algorithms
- Add caching
- Change data structures
- Simplify code paths
- Parallelize operations
- Reduce memory usage

You are the AI improving itself. Think like a researcher."""

    def __init__(self, 
                 pxos_url: str = "http://localhost:3839",
                 goal: str = "Optimize the VM to achieve maximum performance",
                 results_file: str = "/tmp/recursive-ai-results.json"):
        
        self.pxos_url = pxos_url
        self.goal = goal
        self.results_file = Path(results_file)
        self.iteration = 0
        
        # Load previous results
        self.results = self.load_results()
        
        # HTTP clients
        self.lm_client = httpx.Client(timeout=60.0)
        self.pxos_client = httpx.Client(base_url=pxos_url, timeout=30.0)
    
    def load_results(self) -> list:
        """Load previous experiment results."""
        if self.results_file.exists():
            return json.loads(self.results_file.read_text())
        return []
    
    def save_results(self):
        """Save results for persistence."""
        self.results_file.write_text(json.dumps(self.results[-100:], indent=2))
    
    def get_pxos_state(self) -> dict:
        """Get current pxOS state."""
        try:
            resp = self.pxos_client.get("/api/v1/cells")
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_vm_state(self) -> dict:
        """Get VM state."""
        try:
            resp = self.pxos_client.get("/api/v1/vm/state")
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def ask_lm_studio(self, context: str) -> dict:
        """
        Ask LM Studio to generate the next prompt.
        
        This is where the AI generates its OWN prompts.
        """
        # Build message with context
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"""
CURRENT GOAL: {self.goal}

ITERATION: {self.iteration}

CURRENT STATE:
{json.dumps(self.get_pxos_state(), indent=2)[:500]}

VM STATE:
{json.dumps(self.get_vm_state(), indent=2)[:300]}

PREVIOUS RESULTS (last 5):
{json.dumps(self.results[-5:], indent=2)}

Based on this, generate the next experiment to try.
Respond ONLY with the JSON object, no other text.
"""}
        ]
        
        try:
            resp = self.lm_client.post(
                self.LM_STUDIO_URL,
                json={
                    "model": "local-model",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )
            
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                
                # Parse JSON response
                # Handle markdown code blocks
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                
                return json.loads(content.strip())
            else:
                return {"error": f"LM Studio error: {resp.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def run_experiment(self, experiment: dict) -> dict:
        """Run an experiment on pxOS."""
        try:
            # Format as ASCII spec
            spec = f"""H: {experiment.get('H', 'Unknown')}
T: {experiment.get('T', 'sync/synthetic-glyph-vm.js')}
M: {experiment.get('M', 'improvement')}
B: {experiment.get('B', '5')}"""
            
            resp = self.pxos_client.post(
                "/api/v1/experiments/run",
                json={"spec": spec, "x": 0, "y": 100 + self.iteration * 20}
            )
            
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def run_iteration(self) -> dict:
        """Run one iteration of the recursive loop."""
        self.iteration += 1
        
        print(f"\n{'='*60}")
        print(f"RECURSIVE SELF-PROMPT - ITERATION {self.iteration}")
        print(f"{'='*60}")
        
        # 1. AI generates its own prompt
        print("\n[1] AI generating next prompt...")
        ai_response = self.ask_lm_studio("generate next experiment")
        
        if "error" in ai_response:
            print(f"Error: {ai_response['error']}")
            return {"status": "error", "error": ai_response["error"]}
        
        print(f"Analysis: {ai_response.get('analysis', 'N/A')[:100]}")
        print(f"Hypothesis: {ai_response.get('hypothesis', 'N/A')[:100]}")
        
        # 2. Execute the AI's experiment
        print("\n[2] Executing AI's experiment...")
        experiment = ai_response.get("experiment", {})
        result = self.run_experiment(experiment)
        
        print(f"Result: {result.get('status', 'unknown')}")
        
        # 3. Record results
        record = {
            "iteration": self.iteration,
            "timestamp": datetime.now().isoformat(),
            "ai_analysis": ai_response.get("analysis"),
            "hypothesis": ai_response.get("hypothesis"),
            "experiment": experiment,
            "result": result,
            "reasoning": ai_response.get("reasoning")
        }
        
        self.results.append(record)
        self.save_results()
        
        # 4. Get wait time
        wait_seconds = ai_response.get("next_check_seconds", 60)
        
        print(f"\n[3] AI chose to wait {wait_seconds}s")
        
        return {
            "status": "continue",
            "iteration": self.iteration,
            "wait_seconds": wait_seconds,
            "result": result
        }
    
    def run_forever(self, max_iterations: int = 10000, delay: float = 60.0):
        """Run the recursive loop forever."""
        print("=" * 60)
        print("RECURSIVE SELF-PROMPTING AI")
        print("=" * 60)
        print(f"Goal: {self.goal}")
        print(f"Max iterations: {max_iterations}")
        print(f"LM Studio: {self.LM_STUDIO_URL}")
        print(f"pxOS: {self.pxos_url}")
        print()
        
        while self.iteration < max_iterations:
            result = self.run_iteration()
            
            if result.get("status") == "error":
                print("Error occurred, waiting 60s...")
                time.sleep(60)
                continue
            
            # Wait before next iteration
            wait = result.get("wait_seconds", delay)
            print(f"\nWaiting {wait}s before next iteration...")
            print(f"(Results saved to {self.results_file})")
            time.sleep(wait)
        
        self.lm_client.close()
        self.pxos_client.close()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Recursive Self-Prompting AI")
    parser.add_argument("--goal", default="Optimize pxOS VM to achieve maximum performance")
    parser.add_argument("--max-iterations", type=int, default=10000)
    parser.add_argument("--delay", type=float, default=60.0)
    
    args = parser.parse_args()
    
    ai = RecursiveSelfPrompter(goal=args.goal)
    ai.run_forever(max_iterations=args.max_iterations, delay=args.delay)


if __name__ == "__main__":
    main()
