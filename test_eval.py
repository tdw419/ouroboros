import subprocess
import re
import sys

def get_coverage():
    try:
        # Run pytest with coverage
        result = subprocess.run(
            ["pytest", "--cov=src/ouroboros", "--cov-report=term-missing", "tests/"],
            capture_output=True,
            text=True
        )
        
        # Look for the TOTAL line
        output = result.stdout
        match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
        if match:
            return float(match.group(1))
        return 0.0
    except Exception as e:
        print(f"Error: {e}")
        return 0.0

if __name__ == "__main__":
    coverage = get_coverage()
    print(f"TOTAL_COVERAGE: {coverage}")
    # Exit with success if coverage is extracted
    sys.exit(0)
