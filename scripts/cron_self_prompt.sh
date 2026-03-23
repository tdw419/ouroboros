#!/bin/bash
# Ouroboros Self-Prompting Cron Script
# Runs the self-prompting loop autonomously on a schedule

set -e

# Configuration
PROJECT_DIR="/home/jericho/zion/projects/ouroboros/ouroboros"
STATE_DIR="$PROJECT_DIR/.ouroboros"
LOG_DIR="$STATE_DIR/logs"
LOG_FILE="$LOG_DIR/self_prompt_$(date +%Y%m%d_%H%M%S).log"

# Ensure directories exist
mkdir -p "$STATE_DIR"
mkdir -p "$LOG_DIR"

# Activate virtual environment if it exists
if [ -d "$PROJECT_DIR/venv" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
fi

# Change to project directory
cd "$PROJECT_DIR"

# Run the self-prompt loop
echo "=== Ouroboros Self-Prompt Loop ===" >> "$LOG_FILE"
echo "Started at: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

python3 -c "
from pathlib import Path
from src.ouroboros.core.self_prompt_loop import run_self_prompt_loop

state_dir = Path('$STATE_DIR')
state = run_self_prompt_loop(state_dir, max_iterations=3)
print(f'Completed {state.iterations} total iterations')
print(f'Current focus: {state.current_focus}')
if state.insights:
    print(f'Latest insight: {state.insights[-1]}')
" >> "$LOG_FILE" 2>&1

echo "" >> "$LOG_FILE"
echo "Completed at: $(date)" >> "$LOG_FILE"

# Clean up old logs (keep last 100)
cd "$LOG_DIR"
ls -t self_prompt_*.log 2>/dev/null | tail -n +101 | xargs -r rm

echo "Run complete. Log: $LOG_FILE"
