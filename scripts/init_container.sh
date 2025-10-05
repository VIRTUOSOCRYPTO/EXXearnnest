#!/bin/bash

# EarnNest Container Initialization Script
# This script runs automatically when the container starts

set -e

echo "🎯 EarnNest Container Initialization - $(date)"

# Create necessary directories
mkdir -p /app/scripts
mkdir -p /app/backend/uploads
mkdir -p /var/log/supervisor

# Ensure proper permissions
chown -R root:root /app/scripts
chmod +x /app/scripts/*.sh

# Setup improved supervisor configuration
echo "⚙️ Setting up supervisor configuration..."
/app/scripts/setup_supervisor.sh

# Enable and start the automatic startup service
echo "🔄 Enabling automatic startup service..."
systemctl daemon-reload
systemctl enable earnest-autostart.service

# Start all services
echo "🚀 Starting EarnNest services..."
/app/scripts/startup.sh

echo "✅ Container initialization complete!"
echo "🌐 Access your app at: https://run-analyze.preview.emergentagent.com"
