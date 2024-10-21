#!/bin/bash

# Set variables
mt5setup_url="https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"
mt5file="/config/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe"
python_url="https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe"
wine_executable="wine"
metatrader_version="5.0.36"  # or whatever version you're using
mt5server_port=18812  # Default port for mt5linux

# Function to show messages
show_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Function to check if a Python package is installed in Wine
is_wine_python_package_installed() {
    $wine_executable python -c "import pkg_resources; pkg_resources.require('$1')" 2>/dev/null
    return $?
}

# Function to check if a Python package is installed in Linux
is_python_package_installed() {
    python3 -c "import pkg_resources; pkg_resources.require('$1')" 2>/dev/null
    return $?
}

# Check if MetaTrader 5 is installed
if [ -e "$mt5file" ]; then
    show_message "[2/7] File $mt5file already exists."
else
    show_message "[2/7] File $mt5file is not installed. Installing..."

    # Set Windows 10 mode in Wine and download and install MT5
    $wine_executable reg add "HKEY_CURRENT_USER\\Software\\Wine" /v Version /t REG_SZ /d "win10" /f
    show_message "[3/7] Downloading MT5 installer..."
    curl -o /config/.wine/drive_c/mt5setup.exe $mt5setup_url
    show_message "[3/7] Installing MetaTrader 5..."
    $wine_executable "/config/.wine/drive_c/mt5setup.exe" "/auto" &
    wait
    rm -f /config/.wine/drive_c/mt5setup.exe
fi

# Recheck if MetaTrader 5 is installed
if [ -e "$mt5file" ]; then
    show_message "[4/7] File $mt5file is installed. Running MT5..."
    $wine_executable "$mt5file" &
else
    show_message "[4/7] File $mt5file is not installed. MT5 cannot be run."
fi

# Install Python in Wine if not present
if ! $wine_executable python --version 2>/dev/null; then
    show_message "[5/7] Installing Python in Wine..."
    curl -L $python_url -o /tmp/python-installer.exe
    $wine_executable /tmp/python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
    rm /tmp/python-installer.exe
    show_message "[5/7] Python installed in Wine."
else
    show_message "[5/7] Python is already installed in Wine."
fi

show_message "Linux Python version:"
python3 --version
show_message "Wine Python version:"
$wine_executable python --version

# Upgrade pip and install required packages
show_message "[6/7] Installing Python libraries"
$wine_executable python -m pip install --upgrade --no-cache-dir pip

# Install MetaTrader5 library in Windows if not installed
show_message "[6/7] Installing MetaTrader5 library in Windows"
if ! is_wine_python_package_installed "MetaTrader5==$metatrader_version"; then
    $wine_executable python -m pip install --no-cache-dir MetaTrader5==$metatrader_version
fi

# Install mt5linux library in Windows if not installed
show_message "[6/7] Checking and installing mt5linux library in Windows if necessary"
if ! is_wine_python_package_installed "mt5linux"; then
    $wine_executable python -m pip install --no-cache-dir mt5linux
    if [ $? -ne 0 ]; then
        show_message "Failed to install mt5linux in Wine Python environment"
    fi
fi

# Install mt5linux library in Linux if not installed
show_message "[6/7] Checking and installing mt5linux library in Linux if necessary"
if ! is_python_package_installed "mt5linux"; then
    python3 -m pip install --upgrade --no-cache-dir mt5linux
    if [ $? -ne 0 ]; then
        show_message "Failed to install mt5linux in Linux Python environment"
    fi
fi

# Start the MT5 server on Windows side
show_message "[7/7] Starting the mt5linux server..."
$wine_executable python -m mt5linux $wine_executable python.exe > /tmp/mt5linux_server.log 2>&1 &

# Give the server some time to start
sleep 25

show_message "MT5Linux server log:"
cat /tmp/mt5linux_server.log

# Check if the server is running
if ss -tuln | grep ":$mt5server_port" > /dev/null; then
    show_message "[7/7] The mt5linux server is running on port $mt5server_port."
else
    show_message "[7/7] Failed to start the mt5linux server on port $mt5server_port."
fi

# Start the MT5 API server
show_message "[8/8] Starting the Flask API server..."
python3 /metatrader/mt5_api.py &

# Keep the script running
tail -f /dev/null
