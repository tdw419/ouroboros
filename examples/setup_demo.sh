#!/bin/bash
# Demo: Set up and run Ouroboros on the Pi Approximator

set -e

echo "🐍 Ouroboros Hello World Demo"
echo "=============================="
echo ""

# Create demo workspace
DEMO_DIR="demo_pi_approximator"
mkdir -p $DEMO_DIR

# Copy the target script
cp examples/pi_approximator.py $DEMO_DIR/

cd $DEMO_DIR

# Initialize the loop
echo "📦 Initializing loop..."
ouroboros init \
    --objective "Improve the pi approximation algorithm to achieve error < 0.0001" \
    --criteria "error < 0.0001" \
    --max-iter 20

echo ""
echo "🎯 Target: Improve pi_approximator.py"
echo "📊 Success: error < 0.0001"
echo ""
echo "Run the loop:"
echo "  ouroboros run --dry-run  # See what it would do"
echo "  ouroboros run            # Actually run it"
echo ""
echo "Check status:"
echo "  ouroboros status"
