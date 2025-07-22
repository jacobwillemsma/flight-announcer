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

# Start new session using system Python (cleaner, has rgbmatrix library)
tmux new-session -d -s myscript "sudo python3 src/main.py"

echo "Script restarted in tmux session 'myscript'"
echo "Attach with: tmux attach -t myscript"