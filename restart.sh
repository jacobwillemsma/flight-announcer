#!/bin/bash
# Kill existing session if it exists
tmux kill-session -t myscript 2>/dev/null

# Pull latest code (if using git)
git pull

# Start new session
tmux new-session -d -s myscript 'source .venv/bin/activate && python src/main.py'

echo "Script restarted in tmux session 'myscript'"
echo "Attach with: tmux attach -t myscript"