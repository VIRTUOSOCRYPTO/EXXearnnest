#!/bin/bash

# Lightweight service checker for cron
check_and_restart() {
    local service=$1
    if ! sudo supervisorctl status "$service" | grep -q "RUNNING"; then
        echo "$(date): Restarting $service"
        sudo supervisorctl restart "$service"
    fi
}

# Check all services
check_and_restart mongodb
check_and_restart backend
check_and_restart frontend
check_and_restart code-server

# Quick health checks
if ! curl -s -f "http://localhost:8001/health" > /dev/null 2>&1; then
    echo "$(date): Backend health failed, restarting"
    sudo supervisorctl restart backend
fi

if ! curl -s -f "http://localhost:3000" > /dev/null 2>&1; then
    echo "$(date): Frontend health failed, restarting"  
    sudo supervisorctl restart frontend
fi
