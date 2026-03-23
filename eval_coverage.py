#!/usr/bin/env python3
"""
Evaluation script for Ouroboros self-improvement.
Measures test coverage and reports the metric.
"""

import subprocess
import sys
import re

def main():
    # Run pytest with coverage
    result = subprocess.run(
        ["python3", "-m", "pytest", "tests/", "--cov=src/ouroboros", "--cov-report=term", "-q"],
        capture_output=True,
        text=True,
        cwd="/home/jericho/zion/projects/ouroboros/ouroboros"
    )

    output = result.stdout + result.stderr
    print(output)

    # Extract total coverage percentage
    # Look for line like: TOTAL    1044    852    18%
    match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
    if match:
        coverage = float(match.group(1))
        print(f"\n📊 COVERAGE: {coverage}%")

        if coverage >= 90.0:
            print("✅ SUCCESS: Coverage target achieved!")
            sys.exit(0)
        else:
            print(f"❌ Not yet: {coverage}% < 90%")
            sys.exit(1)
    else:
        print("❌ Could not parse coverage")
        sys.exit(1)

if __name__ == "__main__":
    main()
