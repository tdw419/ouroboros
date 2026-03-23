import math
import random

def calculate_pi_mc(num_points):
    """
    Approximates Pi using the Monte Carlo method.
    
    Args:
    num_points (int): The number of random points to generate.
    
    Returns:
    float: The approximated value of Pi.
    """
    points_inside_circle = 0
    
    for _ in range(num_points):
        # Generate a random point (x, y) in the range [0, 1]
        x = random.random()
        y = random.random()
        
        # Check if the point lies inside the unit circle (x^2 + y^2 <= 1)
        if x**2 + y**2 <= 1:
            points_inside_circle += 1
            
    # The ratio of points inside the circle to total points is pi/4
    # Therefore, pi = 4 * (points_inside / total_points)
    return 4 * points_inside_circle / num_points

if __name__ == "__main__":
    # Set number of points to 1,000,000 to reduce statistical variance
    N = 1_000_000
    
    approx_pi = calculate_pi_mc(N)
    actual_pi = math.pi
    
    error = abs(actual_pi - approx_pi)
    
    print(f"Approximation: {approx_pi}")
    print(f"Actual Pi:     {actual_pi}")
    print(f"Error:         {error}")
    
    # Check success criteria
    if error < 0.0001:
        print("SUCCESS: Error is within target threshold.")
    else:
        print("FAILURE: Error exceeds target threshold.")