#!/bin/bash

source /scripts/00-config.sh

log_message "INFO" "RUNNING 06-install-python.sh"

# Install Python in Wine if not present
if ! $wine_executable python --version > /dev/null 2>&1; then
    log_message "INFO" "Installing Python in Wine..."
    wget -O /tmp/python-installer.exe $python_url
    $wine_executable /tmp/python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    rm /tmp/python-installer.exe
    
    # Add Python to the Wine PATH
    $wine_executable reg add "HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Session Manager\Environment" /v PATH /t REG_EXPAND_SZ /d "%PATH%;C:\Python39;C:\Python39\Scripts" /f
    
    log_message "INFO" "Python installed in Wine."
else
    log_message "INFO" "Python is already installed in Wine."
fi

# Set PYTHONHOME and PYTHONPATH in Wine
$wine_executable reg add "HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Session Manager\Environment" /v PYTHONHOME /t REG_SZ /d "C:\Python39" /f
$wine_executable reg add "HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Session Manager\Environment" /v PYTHONPATH /t REG_SZ /d "C:\Python39;C:\Python39\Lib;C:\Python39\DLLs" /f

# Verify Python installation
log_message "INFO" "Verifying Python installation in Wine..."
$wine_executable python -c "import sys; print('Python version:', sys.version); print('Python executable:', sys.executable); print('Python path:', sys.path)" > /tmp/wine_python_verify.log 2>&1
cat /tmp/wine_python_verify.log
log_message "INFO" "Python verification complete."

# Install required packages
log_message "INFO" "Installing required Python packages in Wine..."
$wine_executable python -m pip install --upgrade pip
$wine_executable python -m pip install --no-cache-dir MetaTrader5==$metatrader_version mt5linux

log_message "INFO" "Installed packages in Wine Python environment:"
$wine_executable python -m pip list

log_message "INFO" "Wine Python installation completed."