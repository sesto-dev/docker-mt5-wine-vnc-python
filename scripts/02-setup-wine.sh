#!/bin/bash

source /scripts/00-config.sh

log_message "INFO" "Setting up Wine environment..."

# Ensure the Wine directory exists with correct permissions
mkdir -p /config/.wine
chown -R abc:abc /config
chmod -R 755 /config/.wine

# Initialize Wine
su abc -c "winecfg"

log_message "INFO" "Wine environment setup completed."