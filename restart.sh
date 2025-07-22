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

# Start new session with logging
tmux new-session -d -s myscript 'echo "Starting flight announcer..."; echo "Python path: $(which python)"; echo "VEnv Python: $PWD/.venv/bin/python"; echo "Working directory: $(pwd)"; echo "Starting application..."; sudo .venv/bin/python src/main.py 2>&1 | tee /tmp/flight-announcer.log'

echo "Script restarted in tmux session 'myscript'"
echo "Attach with: tmux attach -t myscript"
echo "View logs with: tail -f /tmp/flight-announcer.log"