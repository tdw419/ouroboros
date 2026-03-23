import subprocess
import re
import sys
import os

def get_coverage():
    try:
        # Attempt to use the virtual environment's pytest if it exists
        pytest_cmd = "pytest"
        if os.path.exists("venv/bin/pytest"):
            pytest_cmd = "venv/bin/pytest"
        elif os.path.exists(".venv/bin/pytest"):
            pytest_cmd = ".venv/bin/pytest"
            
        # Run pytest with coverage
        # Explicitly setting arguments to ensure coverage is captured correctly
        result = subprocess.run(
            [pytest_cmd, "--cov=src/ouroboros", "--cov-report=term-missing", "tests/"],
            capture_output=True,
            text=True,
            check=False  # Don't raise exception if tests fail, we just want coverage
        )
        
        # Combine stdout and stderr for parsing
        output = result.stdout + result.stderr
        
        # Debug: Print output to help diagnose if regex fails
        # print("DEBUG OUTPUT:\n", output) 
        
        # Regex to find coverage: "TOTAL 100 10 90%"
        # Handles variations in spacing
        match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
        if match:
            return float(match.group(1))
        
        # Fallback: Look for "Coverage: 90%" or similar if the table format fails
        fallback_match = re.search(r"coverage[:\s]+(\d+)%", output, re.IGNORECASE)
        if fallback_match:
            return float(fallback_match.group(1))
            
        return 0.0
    except Exception as e:
        print(f"Error executing coverage check: {e}")
        # Return 0.0 on error so the loop continues, rather than crashing
        return 0.0

if __name__ == "__main__":
    coverage = get_coverage()
    print(f"METRIC: {coverage}")
    sys.exit(0)