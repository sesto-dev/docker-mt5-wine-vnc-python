#!/bin/bash

source /scripts/00-config.sh

log_message "INFO" "RUNNING 08-start-mt5-server.sh"
log_message "INFO" "Starting the mt5linux server..."

# Log Wine Python environment variables
$wine_executable python -c "
import os
print('PYTHONPATH:', os.environ.get('PYTHONPATH', 'Not set'))
print('PYTHONHOME:', os.environ.get('PYTHONHOME', 'Not set'))
print('PATH:', os.environ.get('PATH', 'Not set'))
" > /tmp/wine_python_env.log 2>&1

log_message "INFO" "Wine Python environment variables:"
cat /tmp/wine_python_env.log

# Test Python functionality in Wine
$wine_executable python -c "
import sys
print('Python version:', sys.version)
print('Python executable:', sys.executable)
print('Python path:', sys.path)
import os
print('Current working directory:', os.getcwd())
" > /tmp/wine_python_test.log 2>&1

log_message "INFO" "Wine Python functionality test:"
cat /tmp/wine_python_test.log

# Start the MT5 server on Windows side with more detailed output
$wine_executable python -c "
import sys
import traceback
print('Python version:', sys.version)
print('Python path:', sys.path)
try:
    from mt5linux import MetaTrader5 as mt5
    print('mt5linux imported successfully')
    if mt5.initialize():
        print('MT5 initialized successfully')
        mt5.shutdown()
    else:
        print('Failed to initialize MT5:', mt5.last_error())
except Exception as e:
    print('Error importing or initializing mt5linux:', str(e))
    print('Traceback:')
    traceback.print_exc()
" > /tmp/mt5linux_server.log 2>&1 &

server_pid=$!

# Give the server more time to start
sleep 20

log_message "INFO" "MT5Linux server log:"
cat /tmp/mt5linux_server.log

# Check if the server process is still running
if ps -p $server_pid > /dev/null; then
    log_message "INFO" "The mt5linux server process is running with PID $server_pid."
else
    log_message "ERROR" "The mt5linux server process is not running."
fi

# Check if the server is listening on the expected port
if ss -tuln | grep ":$mt5server_port" > /dev/null; then
    log_message "INFO" "The mt5linux server is listening on port $mt5server_port."
else
    log_message "ERROR" "The mt5linux server is not listening on port $mt5server_port."
fi