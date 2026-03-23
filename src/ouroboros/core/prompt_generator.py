"""
Self-Prompt Generator

Generates the next hypothesis/experiment based on past results.
This is the "brain" that reads feedback and decides what to try next.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any
import anthropic
import os
import re


@dataclass
class ExperimentSpec:
    """ASCII experiment specification that the body can execute."""

    hypothesis: str  # H: What we're testing
    target: str  # T: File(s) to modify
    metric: str  # M: Success criteria
    budget: str  # B: Time budget
    code_changes: Dict[str, str] = field(default_factory=dict) # NEW: target -> new_content
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_ascii(self) -> str:
        """Convert to ASCII spec format."""
        code_status = "Included" if self.code_changes else "None"
        decision = self.metadata.get("decision", "REFINE")
        return f"""┌───────────────────────────────────────┐
│ DECISION: {decision:<27} │
├───────────────────────────────────────┤
│ H: {self.hypothesis:<34} │
│ T: {self.target:<34} │
│ M: {self.metric:<34} │
│ B: {self.budget:<34} │
│ CODE: {code_status:<32} │
├───────────────────────────────────────┤
│ FLOW: HYP → RUN → EVAL → DECIDE       │
└───────────────────────────────────────┘"""


class SelfPromptGenerator:
    """
    Generates the next experiment by:
    1. Reading the results log (past attempts)
    2. Reading the experiment tree (flowchart of paths)
    3. Reading the goal state (what we're trying to achieve)
    4. Using an LLM to decide: REFINE current path, PIVOT to other path, or HALT
    """

    SYSTEM_PROMPT = """You are an autonomous research strategist in a recursive self-improvement loop.

Your role is to:
1. Analyze the EXPERIMENT FLOWCHART (the tree of attempted paths).
2. Decide whether to:
   - REFINE: Continue improving the current best branch.
   - PIVOT: If the current branch is flatlining (no improvement), go back to a previous node and try a different approach.
   - HALT: If the goal is met or impossible.
3. Generate the next hypothesis and exact code changes.

You output decisions in ASCII spec format:
┌───────────────────────────────────────┐
│ DECISION: <REFINE | PIVOT node_id>    │
├───────────────────────────────────────┤
│ H: <hypothesis - what to test>        │
│ T: <target - file(s) to modify>       │
│ M: <metric - success criteria>        │
│ B: <budget - time limit>              │
├───────────────────────────────────────┤
│ FLOW: HYP → RUN → EVAL → DECIDE       │
└───────────────────────────────────────┘

After the ASCII block, provide the full content of the target file in a markdown code block.

If PIVOTING, explain why the current path failed and why the new path is better.
"""

    def __init__(self, model: str = "claude-sonnet-4-6-20250514"):
        self.model = model
        self.use_mock = not os.getenv("ANTHROPIC_API_KEY")
        if not self.use_mock:
            self.client = anthropic.Anthropic()

    def generate_next(
        self,
        goal: str,
        success_criteria: str,
        results_tsv: Optional[Path] = None,
        codebase_context: Optional[str] = None,
        tree_ascii: Optional[str] = None,
    ) -> ExperimentSpec:
        """
        Generate the next experiment based on goal, results, and tree structure.
        """
        if self.use_mock:
            return self._generate_mock(goal, results_tsv)

        # Build context
        results_context = ""
        if results_tsv and results_tsv.exists():
            with open(results_tsv) as f:
                results_context = f"\n\nPAST RESULTS:\n{f.read()}"

        tree_context = f"\n\nEXPERIMENT FLOWCHART:\n{tree_ascii}" if tree_ascii else ""
        code_context = f"\n\nCODEBASE CONTEXT:\n{codebase_context}" if codebase_context else ""

        prompt = f"""GOAL: {goal}
SUCCESS CRITERIA: {success_criteria}{tree_context}{results_context}{code_context}

Based on the flowchart and results, should we REFINE the current path or PIVOT?
Generate the next experiment spec and code."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        return self._parse_response(response.content[0].text)

    def _generate_mock(self, goal: str, results_tsv: Optional[Path]) -> ExperimentSpec:
        """Generate a mock hypothesis for testing without API key."""
        iteration = 0
        if results_tsv and results_tsv.exists():
            with open(results_tsv) as f:
                iteration = len(f.readlines()) - 1

        hypotheses = [
            "Increase iterations in Leibniz formula",
            "Use Archimedes method for pi",
            "Implement Nilakantha series",
            "Use math.pi directly",
        ]
        
        target = "pi_approximator.py"
        idx = min(iteration, len(hypotheses) - 1)
        
        # Mock code content for each iteration
        mock_codes = [
            "# Leibniz improvement mock code\ndef approximate_pi(): return 3.1415",
            "# Archimedes mock code\ndef approximate_pi(): return 3.14159",
            "# Nilakantha mock code\ndef approximate_pi(): return 3.141592",
            "import math\ndef approximate_pi(): return math.pi"
        ]

        if "Improve the pi approximation" in goal:
            spec = ExperimentSpec(
                hypothesis=hypotheses[idx],
                target=target,
                metric="error < 0.0001",
                budget="1m",
                code_changes={target: mock_codes[idx]}
            )
            spec.metadata["decision"] = "REFINE"
            return spec
        
        spec = ExperimentSpec(
            hypothesis=f"Mock hypothesis {iteration + 1}",
            target="unknown.py",
            metric="improvement",
            budget="1m",
            code_changes={"unknown.py": "# Mock content"}
        )
        spec.metadata["decision"] = "REFINE"
        return spec

    def _parse_response(self, response: str) -> ExperimentSpec:
        """Parse ASCII spec and code block from LLM response."""
        print(f"DEBUG: LLM Response:\n{response}")
        
        # Extract Decision
        decision_match = re.search(r"DECISION:\s*(.+?)\s*[│\n]", response)
        decision = decision_match.group(1).strip() if decision_match else "REFINE"

        # Extract lines starting with H:, T:, M:, B:
        lines = response.split("\n")

        hypothesis = ""
        target = ""
        metric = ""
        budget = "5m"

        for line in lines:
            line = line.strip(" │\t")
            if line.startswith("H:"):
                hypothesis = line[2:].strip()
            elif line.startswith("T:"):
                # Sanitize: Remove commentary like "(Create new)" or extra spaces or brackets
                raw_target = line[2:].strip()
                # Remove brackets, parentheses and take the first word
                target = re.split(r'[\s\(\)]', raw_target.strip("<>"))[0]
            elif line.startswith("M:"):
                # Sanitize: Remove commentary, keep the operator and value
                raw_metric = line[2:].strip()
                metric = raw_metric.split("(")[0].strip()
            elif line.startswith("B:"):
                budget = line[2:].strip().split("(")[0].strip()

        # Extract code block
        code_changes = {}
        if target:
            # 1. Try to find a block explicitly labeled as python
            code_match = re.search(r"```python\n(.*?)```", response, re.DOTALL)
            if code_match:
                print(f"DEBUG: Found 'python' code block for {target}")
            
            # 2. If not found, try any code block
            if not code_match:
                code_match = re.search(r"```(?:\w+)?\n(.*?)```", response, re.DOTALL)
                if code_match:
                    print(f"DEBUG: Found fallback code block for {target}")
                
            if code_match:
                content = code_match.group(1).strip()
                # Robust cleaning - strip accidental box chars from code
                # Preserve leading whitespace (indentation)
                box_chars_re = r'[┌─┐│└┘├┤┬┴┼]'
                lines = content.split("\n")
                cleaned_lines = []
                for line in lines:
                    cleaned_line = re.sub(box_chars_re, '', line)
                    if line.strip() and not cleaned_line.strip():
                        continue
                    cleaned_lines.append(cleaned_line)
                
                code_changes[target] = "\n".join(cleaned_lines)

        spec = ExperimentSpec(
            hypothesis=hypothesis or "No hypothesis generated",
            target=target or "unknown.py",
            metric=metric or "improvement",
            budget=budget,
            code_changes=code_changes
        )
        spec.metadata["decision"] = decision
        return spec
