#!/bin/bash
# Kill existing session if it exists
tmux kill-session -t myscript 2>/dev/null

# Wait and verify the session is gone
while tmux has-session -t myscript 2>/dev/null; do
    echo "Waiting for session to terminate..."
    sleep 1
done

# Pull latest code (if using git)
git pull

# Start new session with comprehensive logging and error handling
tmux new-session -d -s myscript 'bash -c "
echo \"=== Flight Announcer Debug Log ===\" > /tmp/flight-announcer.log
echo \"Timestamp: \$(date)\" >> /tmp/flight-announcer.log
echo \"Working directory: \$(pwd)\" >> /tmp/flight-announcer.log
echo \"Python path: \$(which python)\" >> /tmp/flight-announcer.log
echo \"VEnv Python: \$PWD/.venv/bin/python\" >> /tmp/flight-announcer.log
echo \"VEnv exists: \$(test -f .venv/bin/python && echo YES || echo NO)\" >> /tmp/flight-announcer.log
echo \"Starting application...\" >> /tmp/flight-announcer.log
echo \"===================================\" >> /tmp/flight-announcer.log
sudo .venv/bin/python src/main.py 2>&1 | tee -a /tmp/flight-announcer.log
echo \"Application exited with code: \$?\" >> /tmp/flight-announcer.log
sleep 5
"'

echo "Script restarted in tmux session 'myscript'"
echo "Attach with: tmux attach -t myscript"
echo "View logs with: tail -f /tmp/flight-announcer.log"