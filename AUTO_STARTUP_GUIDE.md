# EarnAura Automatic Startup Guide

## ✅ Setup Complete!

Your EarnAura application now has **automatic startup** configured! All backend services will start automatically and stay running without manual intervention.

## 🚀 What's Configured

### 1. **Automatic Service Startup**
- All services (MongoDB, Backend, Frontend, Code Server) start automatically when the container starts
- Services are configured with proper startup order and dependencies
- Failed services will automatically restart

### 2. **Continuous Monitoring**
- Cron job runs every 2 minutes to check service health
- Automatic restart of failed services
- Health checks for backend and frontend endpoints
- Logging of all monitoring activities

### 3. **Service Management CLI**
You now have a convenient `earnest` command available:

```bash
# Check status (default command)
earnest
earnest status

# Start/restart all services  
earnest start
earnest restart

# Stop all services
earnest stop

# View logs
earnest logs backend
earnest logs frontend
earnest logs all

# Start continuous monitoring
earnest monitor

# Show help
earnest help
```

## 🔧 Technical Details

### Files Created:
- `/app/scripts/startup.sh` - Main startup script
- `/app/scripts/check_services.sh` - Lightweight service checker
- `/app/scripts/monitor_services.sh` - Continuous monitoring
- `/app/scripts/earnest` - Management CLI
- `/etc/supervisor/conf.d/startup_hook.conf` - Supervisor startup hook

### Monitoring Features:
- **Supervisor**: Manages service processes with auto-restart
- **Cron**: Runs health checks every 2 minutes
- **Health Endpoints**: Checks backend (`:8001/health`) and frontend (`:3000`)
- **Automatic Recovery**: Restarts failed services automatically

### Startup Sequence:
1. **MongoDB** starts first (priority 100)
2. **Backend** starts after MongoDB (priority 200)
3. **Frontend** starts after backend (priority 300)  
4. **Code Server** starts last (priority 400)

## 🌐 Access Your Application

- **Frontend**: https://run-analyze.preview.emergentagent.com
- **Backend API**: https://run-analyze.preview.emergentagent.com/api
- **Health Check**: https://run-analyze.preview.emergentagent.com/api/health

## 📋 Logs Locations

- Backend: `/var/log/supervisor/backend.*.log`
- Frontend: `/var/log/supervisor/frontend.*.log`
- MongoDB: `/var/log/mongodb.*.log`
- Monitor: `/var/log/earnest_monitor.log`
- Cron: `/var/log/earnest_cron.log`

## 🔍 Troubleshooting

If services aren't starting automatically:

```bash
# Check service status
earnest status

# Manually restart everything
earnest restart

# Check logs for errors
earnest logs all

# Start continuous monitoring to see real-time status
earnest monitor
```

## ✨ Benefits

✅ **No Manual Intervention Required** - Services start automatically
✅ **High Availability** - Failed services auto-restart
✅ **Health Monitoring** - Continuous health checks
✅ **Easy Management** - Simple CLI for all operations
✅ **Comprehensive Logging** - Full activity logging
✅ **Proper Dependencies** - Services start in correct order

Your EarnAura application is now fully automated and self-managing! 🎉
