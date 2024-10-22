#!/bin/bash

source /scripts/02-common.sh

log_message "RUNNING" "06-install-libraries.sh"

# Install MetaTrader5 library in Windows if not installed
log_message "INFO" "Installing MetaTrader5 library in Windows"
if ! is_wine_python_package_installed "MetaTrader5==$metatrader_version"; then
    $wine_executable python -m pip install --no-cache-dir MetaTrader5==$metatrader_version
fi

# Install mt5linux library in Windows if not installed
log_message "INFO" "Checking and installing mt5linux library in Windows if necessary"
if ! is_wine_python_package_installed "mt5linux"; then
    $wine_executable python -m pip install --no-cache-dir mt5linux
    if [ $? -ne 0 ]; then
        log_message "ERROR" "Failed to install mt5linux in Wine Python environment"
    fi
fi

# Install mt5linux library in Linux if not installed
log_message "INFO" "Checking and installing mt5linux library in Linux if necessary"
if ! is_python_package_installed "mt5linux"; then
    python3 -m pip install --upgrade --no-cache-dir mt5linux
    if [ $? -ne 0 ]; then
        log_message "ERROR" "Failed to install mt5linux in Linux Python environment"
    fi
fi