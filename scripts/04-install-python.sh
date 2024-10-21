#!/bin/bash

source /scripts/02-common.sh

log_message "RUNNING 04-install-python.sh"

# Install Python in Wine if not present
if ! $wine_executable python --version > /tmp/wine_python_version 2>&1; then
    log_message "INFO" "Installing Python in Wine..."
    curl -L $python_url -o /tmp/python-installer.exe
    $wine_executable /tmp/python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 > /tmp/python_install.log 2>&1
    rm /tmp/python-installer.exe
    log_message "INFO" "Python installed in Wine. Installation log:"
    cat /tmp/python_install.log >> /var/log/mt5_setup.log
else
    log_message "INFO" "Python is already installed in Wine."
fi

log_message "INFO" "Linux Python version: $(python3 --version 2>&1)"
log_message "INFO" "Wine Python version: $($wine_executable python --version 2>&1)"

log_message "INFO" "Checking Wine Python environment..."
$wine_executable python -c "import sys; print(sys.prefix); print(sys.executable); print(sys.path)" >> /var/log/mt5_setup.log 2>&1

# Output Python and package information for Wine environment
log_message "INFO" "Wine Python installation details:"
$wine_executable python -c "import sys; print(f'Python version: {sys.version}')" >> /var/log/mt5_setup.log 2>&1
$wine_executable python -c "import sys; print(f'Python executable: {sys.executable}')" >> /var/log/mt5_setup.log 2>&1
$wine_executable python -c "import sys; print(f'Python path: {sys.path}')" >> /var/log/mt5_setup.log 2>&1
$wine_executable python -c "import site; print(f'Site packages: {site.getsitepackages()}')" >> /var/log/mt5_setup.log 2>&1

log_message "INFO" "Installed packages in Wine Python environment:"
$wine_executable python -m pip list >> /var/log/mt5_setup.log 2>&1