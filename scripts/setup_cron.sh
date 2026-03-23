#!/bin/bash
# Setup script to install the ouroboros cron job

CRON_JOB="*/15 * * * * /home/jericho/zion/projects/ouroboros/ouroboros/scripts/cron_self_prompt.sh"

# Check if already installed
if crontab -l 2>/dev/null | grep -q "cron_self_prompt.sh"; then
    echo "Cron job already installed."
    echo "To view: crontab -l"
    echo "To remove: crontab -e (then delete the line)"
    exit 0
fi

# Add to crontab
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "Cron job installed!"
echo ""
echo "Schedule: Every 15 minutes"
echo "Command: $CRON_JOB"
echo ""
echo "Useful commands:"
echo "  View logs:  tail -f /home/jericho/zion/projects/ouroboros/ouroboros/.ouroboros/logs/"
echo "  View state: cat /home/jericho/zion/projects/ouroboros/ouroboros/.ouroboros/self_prompt_state.json"
echo "  Stop cron:  crontab -e (remove the line)"
