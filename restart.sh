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

echo \"Testing Python import...\" >> /tmp/flight-announcer.log
sudo .venv/bin/python -c \"print('\''Python test successful'\''); import sys; print('\''Python version:'\'', sys.version)\" 2>&1 >> /tmp/flight-announcer.log

echo \"Testing basic import...\" >> /tmp/flight-announcer.log  
sudo .venv/bin/python -c \"import os, sys; print('\''Current dir:'\'', os.getcwd()); sys.path.append('\''src'\''); import config; print('\''Config loaded successfully'\'')\" 2>&1 >> /tmp/flight-announcer.log

echo \"Starting application...\" >> /tmp/flight-announcer.log
echo \"===================================\" >> /tmp/flight-announcer.log
sudo .venv/bin/python src/main.py 2>&1 | tee -a /tmp/flight-announcer.log
EXIT_CODE=\$?
echo \"Application exited with code: \$EXIT_CODE\" >> /tmp/flight-announcer.log

if [ \$EXIT_CODE -ne 0 ]; then
    echo \"ERROR: Application failed to start properly\" >> /tmp/flight-announcer.log
fi

sleep 10
"'

echo "Script restarted in tmux session 'myscript'"
echo "Attach with: tmux attach -t myscript"
echo "View logs with: tail -f /tmp/flight-announcer.log"