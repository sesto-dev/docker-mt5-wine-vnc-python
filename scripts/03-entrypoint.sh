#!/bin/bash

# Source common variables and functions
source /scripts/00-config.sh

log_message "INFO" "Running entrypoint script"

# Run installation scripts
/scripts/04-install-mono.sh
/scripts/05-install-mt5.sh
/scripts/06-install-python.sh
/scripts/07-install-libraries.sh
# Start servers
/scripts/08-start-mt5-server.sh
sleep 30  # Give MT5 server time to start
/scripts/09-start-flask-server.sh
# Keep the script running
tail -f /dev/null