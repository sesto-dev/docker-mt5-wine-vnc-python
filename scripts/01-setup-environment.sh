#!/bin/bash

source /scripts/00-config.sh

log_message "INFO" "Setting up the environment..."

# Update package lists and upgrade packages
apt-get update && apt-get upgrade -y

# Install required packages
apt-get install -y \
    dos2unix \
    python3-pip \
    wget \
    python3-pyxdg \
    netcat

pip3 install --upgrade pip
pip3 install flask pandas rpyc python-json-logger prometheus_client

# Add WineHQ repository key and APT source
wget -q https://dl.winehq.org/wine-builds/winehq.key
apt-key add winehq.key
add-apt-repository 'deb https://dl.winehq.org/wine-builds/debian/ bullseye main'
rm winehq.key

# Add i386 architecture and update package lists
dpkg --add-architecture i386
apt-get update

# Install WineHQ stable package and dependencies
apt-get install --install-recommends -y winehq-stable
apt-get clean
rm -rf /var/lib/apt/lists/*

log_message "INFO" "Environment setup completed."