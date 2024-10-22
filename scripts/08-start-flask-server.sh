#!/bin/bash

# Source common variables and functions
source /scripts/02-common.sh

log_message "RUNNING" "08-start-flask-server.sh"

log_message "INFO" "Starting Flask server..."

# Change to the directory containing mt5_api.py
cd /app

# Start the Flask server in the background
python3 mt5_api.py &

# Capture the PID of the Flask server
FLASK_PID=$!

# Wait a moment to ensure the server has started
sleep 2

# Check if the Flask server is running
if ps -p $FLASK_PID > /dev/null
then
    log_message "INFO" "Flask server started successfully with PID $FLASK_PID"
else
    log_message "ERROR" "Failed to start Flask server"
    exit 1
fi