#!/bin/bash

# Setup automatic startup without systemd (for containers)

echo "🔧 Setting up EarnNest automatic startup for containers..."

# 1. Create a cron job to run startup script periodically
echo "📅 Setting up cron job for service monitoring..."

# Create cron job that runs every 2 minutes to ensure services are up
(crontab -l 2>/dev/null; echo "*/2 * * * * /app/scripts/check_services.sh >> /var/log/earnest_cron.log 2>&1") | crontab -

# 2. Create a lightweight service checker
cat > /app/scripts/check_services.sh << 'EOF'
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
EOF

chmod +x /app/scripts/check_services.sh

# 3. Update .bashrc to run startup on shell login
if ! grep -q "startup.sh" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# Auto-start EarnNest services" >> ~/.bashrc
    echo "if [ -f /app/scripts/startup.sh ]; then" >> ~/.bashrc
    echo "    echo '🚀 Ensuring EarnNest services are running...'" >> ~/.bashrc
    echo "    /app/scripts/startup.sh > /dev/null 2>&1" >> ~/.bashrc
    echo "fi" >> ~/.bashrc
fi

# 4. Create a startup hook in supervisor config
cat > /etc/supervisor/conf.d/startup_hook.conf << 'EOF'
[program:startup_hook]
command=/app/scripts/startup.sh
autostart=true
autorestart=false
startretries=1
priority=50
startsecs=0
stdout_logfile=/var/log/supervisor/startup_hook.log
stderr_logfile=/var/log/supervisor/startup_hook.log
EOF

# 5. Start cron service
service cron start

# 6. Reload supervisor to include startup hook
supervisorctl reread
supervisorctl update

echo "✅ Automatic startup configured successfully!"
echo "📋 Services will now:"
echo "   - Start automatically when container starts"
echo "   - Be monitored every 2 minutes via cron"
echo "   - Auto-restart if they fail"
echo "   - Run health checks continuously"
