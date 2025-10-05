#!/bin/bash

# EarnNest Service Monitor
# Continuously monitors and restarts failed services

MONITOR_INTERVAL=30  # Check every 30 seconds
LOG_FILE="/var/log/earnest_monitor.log"

log_message() {
    echo "$(date): $1" | tee -a "$LOG_FILE"
}

check_and_restart_service() {
    local service_name=$1
    
    if ! sudo supervisorctl status "$service_name" | grep -q "RUNNING"; then
        log_message "⚠️ Service $service_name is not running, attempting restart..."
        
        # Try to restart the service
        sudo supervisorctl restart "$service_name"
        
        # Wait a moment and check again
        sleep 5
        
        if sudo supervisorctl status "$service_name" | grep -q "RUNNING"; then
            log_message "✅ Service $service_name restarted successfully"
        else
            log_message "❌ Failed to restart service $service_name"
        fi
    fi
}

check_backend_health() {
    if ! curl -s -f "http://localhost:8001/health" > /dev/null 2>&1; then
        log_message "⚠️ Backend health check failed, restarting backend..."
        sudo supervisorctl restart backend
        sleep 10
    fi
}

check_frontend_health() {
    if ! curl -s -f "http://localhost:3000" > /dev/null 2>&1; then
        log_message "⚠️ Frontend health check failed, restarting frontend..."
        sudo supervisorctl restart frontend
        sleep 10
    fi
}

main_monitor_loop() {
    log_message "🔍 Starting EarnNest service monitor (checking every ${MONITOR_INTERVAL}s)"
    
    while true; do
        # Check each service
        check_and_restart_service "mongodb"
        check_and_restart_service "backend" 
        check_and_restart_service "frontend"
        check_and_restart_service "code-server"
        
        # Health checks for main services
        check_backend_health
        check_frontend_health
        
        # Wait before next check
        sleep "$MONITOR_INTERVAL"
    done
}

# Handle script termination
cleanup() {
    log_message "🛑 Service monitor stopping..."
    exit 0
}

trap cleanup SIGTERM SIGINT

# Start monitoring
main_monitor_loop
