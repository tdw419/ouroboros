import subprocess
import re
import sys
import os

def get_coverage():
    try:
        # Run pytest with coverage
        # Use the venv's pytest if available
        pytest_cmd = "pytest"
        if os.path.exists("venv/bin/pytest"):
            pytest_cmd = "venv/bin/pytest"
            
        result = subprocess.run(
            [pytest_cmd, "--cov=src/ouroboros", "tests/"],
            capture_output=True,
            text=True
        )
        
        # Look for the TOTAL line
        output = result.stdout + result.stderr
        match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
        if match:
            return float(match.group(1))
        return 0.0
    except Exception as e:
        print(f"Error: {e}")
        return 0.0

if __name__ == "__main__":
    coverage = get_coverage()
    print(f"METRIC: {coverage}")
    # Always exit with success so the loop can extract the metric
    sys.exit(0)
