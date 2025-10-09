# 🚀 Deployment Checklist for New Emergent Trials

## ✅ Pre-Deployment (One-Time Setup)

- [x] Super Admin system implemented with 3-tier hierarchy
- [x] All URLs configured via environment variables (no hardcoding)
- [x] Frontend uses `REACT_APP_BACKEND_URL` for API calls
- [x] Backend uses `FRONTEND_URL` for referral and email links
- [x] Super Admin creation script available
- [x] Documentation created

## 🔄 For Each New Trial/URL

### 1. Update Environment Variables (1 minute)

```bash
# Update backend .env with new frontend URL
nano /app/backend/.env
# Change: FRONTEND_URL=https://your-new-url.preview.emergentagent.com
```

### 2. Restart Services (30 seconds)

```bash
sudo supervisorctl restart backend
```

### 3. Create/Verify Super Admin (30 seconds)

```bash
cd /app/backend
python create_super_admin.py
```

### 4. Verify Everything Works (2 minutes)

```bash
# Check services
sudo supervisorctl status

# Test backend API
curl http://localhost:8001/api/auth/trending-skills

# Test frontend (in browser)
# Navigate to: https://your-new-url.preview.emergentagent.com
```

### 5. Access Super Admin Dashboard

1. Login with credentials:
   - Email: `yash@earnaura.com`
   - Password: `YaSh@4517`

2. Navigate to: `/super-admin`

3. Verify dashboard loads with all 6 tabs:
   - Dashboard
   - Campus Admin Requests
   - Campus Admins Oversight
   - Club Admins Visibility
   - Audit Logs
   - Real-time Alerts

## 📝 Current Configuration

### Services Running
```
✓ Backend:  Port 8001 (FastAPI)
✓ Frontend: Port 3000 (React)
✓ MongoDB:  Port 27017
```

### Environment Files

**Backend** (`/app/backend/.env`):
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="moneymojo_db"
CORS_ORIGINS="*"
EMERGENT_LLM_KEY=sk-emergent-11aA6E9353b036bC02
FRONTEND_URL=https://my-app-runner.preview.emergentagent.com
```

**Frontend** (`/app/frontend/.env`):
```
REACT_APP_BACKEND_URL=https://my-app-runner.preview.emergentagent.com
WDS_SOCKET_PORT=443
```

### Super Admin Credentials (Default)
```
Email:    yash@earnaura.com
Password: YaSh@4517
```

## 🎯 What Works with Any URL

✅ **Automatic Features:**
- Super Admin dashboard routes
- All API endpoints
- WebSocket connections
- Referral link generation
- Email notification links
- Social sharing
- Password reset flows
- User registration
- All authentication endpoints

✅ **No Manual Updates Needed:**
- Frontend routing
- API calls from frontend
- Backend API routes
- Database connections
- WebSocket paths

## 🔍 Troubleshooting

### Backend Not Starting
```bash
# Check logs
tail -f /var/log/supervisor/backend.*.log

# Common fix: Install missing dependencies
cd /app/backend
pip install -r requirements.txt
sudo supervisorctl restart backend
```

### Frontend Not Loading
```bash
# Check logs
tail -f /var/log/supervisor/frontend.*.log

# Common fix: Reinstall dependencies
cd /app/frontend
yarn install
sudo supervisorctl restart frontend
```

### Super Admin Access Denied
```bash
# Recreate super admin
cd /app/backend
python create_super_admin.py

# Or manually check database
mongosh mongodb://localhost:27017/moneymojo_db
db.users.findOne({email: "yash@earnaura.com"})
```

### URL Not Updating
```bash
# Verify .env file
cat /app/backend/.env | grep FRONTEND_URL

# Ensure backend restarted
sudo supervisorctl restart backend

# Check backend loaded new URL
curl http://localhost:8001/api/referrals/link
```

## 📚 Documentation Files

- `SUPER_ADMIN_SETUP.md` - Complete super admin setup guide
- `UPDATE_URL.md` - Quick URL update reference
- `DEPLOYMENT_CHECKLIST.md` - This file
- `test_result.md` - Complete testing history and status

## 🎉 Success Criteria

Your deployment is successful when:

1. ✅ All services show `RUNNING` status
2. ✅ Backend API responds to test requests
3. ✅ Frontend loads at the preview URL
4. ✅ Super admin can login and access dashboard
5. ✅ All 6 super admin tabs load correctly
6. ✅ Users can register and login
7. ✅ Referral links use the correct new URL

## 🔐 Security Reminders

1. Change super admin password after first login
2. Create unique super admin accounts for each environment
3. Regularly review audit logs
4. Monitor real-time alerts for suspicious activity
5. Keep admin credentials secure

## ⏱️ Total Setup Time

- First time setup: ~10 minutes
- URL change for new trial: ~5 minutes
- Verification: ~2 minutes

---

**Quick Start Command** (for new trials):
```bash
# Update URL, restart backend, verify
sed -i 's|FRONTEND_URL=.*|FRONTEND_URL=https://NEW-URL.preview.emergentagent.com|g' /app/backend/.env && \
sudo supervisorctl restart backend && \
sleep 3 && \
sudo supervisorctl status && \
cd /app/backend && \
python create_super_admin.py
```

Replace `NEW-URL.preview.emergentagent.com` with your actual Emergent preview URL.
