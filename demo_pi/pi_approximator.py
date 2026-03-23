"""
Hello World Demo: Pi Approximator

A simple script that approximates pi using various methods.
The Ouroboros loop will try to improve the approximation.
"""

import math

# Current approximation method - Ouroboros will try to improve this
def approximate_pi() -> float:
    """Approximate pi using the current method."""
    # Leibniz formula (not very efficient)
    pi = 0.0
    for i in range(1000):
        sign = (-1) ** i
        pi += sign / (2 * i + 1)
    return 4 * pi


def evaluate() -> float:
    """
    Evaluate the current approximation.
    Returns error rate (lower is better).
    """
    approx = approximate_pi()
    actual = math.pi
    error = abs(approx - actual)
    return error


if __name__ == "__main__":
    error = evaluate()
    print(f"Pi approximation error: {error:.10f}")

    # Success criteria: error < 0.0001
    if error < 0.0001:
        print("✅ SUCCESS: Error is below threshold!")
    else:
        print(f"❌ Not yet: error {error:.10f} >= 0.0001")
