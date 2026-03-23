import math
import decimal
from decimal import Decimal, getcontext

def calculate_pi_chudnovsky(precision_digits=20):
    """
    Calculate Pi using the Chudnovsky algorithm.
    
    Args:
        precision_digits (int): Number of decimal digits for precision.
        
    Returns:
        Decimal: The calculated value of Pi.
    """
    # Set precision slightly higher to avoid rounding errors at the end
    getcontext().prec = precision_digits + 5
    
    C = Decimal(426880) * Decimal(10005).sqrt()
    M = Decimal(1)
    L = Decimal(13591409)
    X = Decimal(1)
    K = Decimal(6)
    
    k = 0
    S = Decimal(13591409)
    
    # Iterate until convergence is achieved for the required precision
    # This loop logic approximates the number of terms needed
    # 12 digits per term is a rough heuristic for Chudnovsky
    for k in range(precision_digits // 12 + 2):
        M = M * (K**3 - 16*K) // ((k + 1)**3)
        L += 545140134
        X *= -262537412640768000
        K += 12
        S += Decimal(M * L) / X
        
    pi = C / S
    return pi

if __name__ == "__main__":
    # Target precision: We need error < 1e-10, so 12-15 digits should be sufficient.
    # Setting precision to 20 to be safe.
    calculated_pi = calculate_pi_chudnovsky(precision_digits=20)
    
    # Use standard float for comparison against the reference
    pi_float = float(calculated_pi)
    reference_pi = math.pi
    
    error = abs(pi_float - reference_pi)
    
    print(f"Calculated Pi: {calculated_pi}")
    print(f"Reference Pi:  {reference_pi}")
    print(f"Absolute Error: {error:.2e}")
    
    if error < 1e-10:
        print("SUCCESS: Error is below 1e-10")
    else:
        print("FAILURE: Error is too high")