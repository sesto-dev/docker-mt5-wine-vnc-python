#!/bin/bash

# Source common variables and functions
source /scripts/02-common.sh

ls -la /scripts

# Run installation scripts
/scripts/03-install-mt5.sh
/scripts/04-install-python.sh
/scripts/05-install-libraries.sh

# Start servers
/scripts/06-start-mt5-server.sh
/scripts/07-start-flask-server.sh

# Keep the script running
tail -f /dev/null