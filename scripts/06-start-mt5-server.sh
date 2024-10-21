#!/bin/bash

source /scripts/02-common.sh

log_message "RUNNING 06-start-mt5-server.sh"
# Start the MT5 server on Windows side
log_message "INFO" "Starting the mt5linux server..."
$wine_executable python -c "from mt5linux import MetaTrader5 as mt5; print(mt5.initialize())" > /tmp/mt5linux_server.log 2>&1 &
server_pid=$!

# Give the server some time to start
sleep 10

log_message "INFO" "MT5Linux server log:"
cat /tmp/mt5linux_server.log

# Check if the server process is still running
if ps -p $server_pid > /dev/null; then
    log_message "INFO" "The mt5linux server process is running with PID $server_pid."
else
    log_message "ERROR" "The mt5linux server process is not running."
    log_message "ERROR" "Server log:"
    cat /tmp/mt5linux_server.log
fi

# Check if the server is listening on the expected port
if ss -tuln | grep ":$mt5server_port" > /dev/null; then
    log_message "INFO" "The mt5linux server is listening on port $mt5server_port."
else
    log_message "ERROR" "The mt5linux server is not listening on port $mt5server_port."
fi

# Test connection to MT5 server
log_message "INFO" "Testing connection to MT5 server..."
python3 -c "from mt5linux import MetaTrader5 as mt5; print(mt5.initialize())" >> /var/log/mt5_setup.log 2>&1