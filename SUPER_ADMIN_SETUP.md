# Super Admin Setup Guide for Any Emergent Trial

This guide explains how to set up and access the Super Admin dashboard on any Emergent preview URL.

## 🎯 Overview

The Super Admin system is designed to work with **ANY** Emergent preview URL automatically. No hardcoded URLs or domain-specific configurations are needed.

## 🔧 Environment Configuration

### Step 1: Update Frontend URL (When URL Changes)

When you get a new preview URL from Emergent, update the `FRONTEND_URL` in backend environment file:

```bash
# Edit /app/backend/.env
FRONTEND_URL=https://your-new-url.preview.emergentagent.com
```

**Important:** The frontend `.env` file already contains `REACT_APP_BACKEND_URL` which should match your backend URL. This is automatically configured by Emergent.

### Current Configuration Files

**Backend (.env):**
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="moneymojo_db"
CORS_ORIGINS="*"
EMERGENT_LLM_KEY=sk-emergent-11aA6E9353b036bC02
FRONTEND_URL=https://my-app-runner.preview.emergentagent.com
```

**Frontend (.env):**
```
REACT_APP_BACKEND_URL=https://my-app-runner.preview.emergentagent.com
WDS_SOCKET_PORT=443
```

## 👤 Creating a Super Admin User

### Method 1: Using the Built-in Script (Recommended)

Run the super admin creation script:

```bash
cd /app/backend
python create_super_admin.py
```

This will create a super admin with:
- **Email:** `yash@earnaura.com`
- **Password:** `YaSh@4517`

### Method 2: Manual Creation via MongoDB

If you need to create a different super admin or update existing user:

```bash
# Connect to MongoDB
mongosh mongodb://localhost:27017/moneymojo_db

# Create or update super admin
db.users.updateOne(
  { "email": "your-email@example.com" },
  { 
    $set: {
      "is_admin": true,
      "is_super_admin": true,
      "admin_level": "super_admin",
      "email_verified": true,
      "is_active": true
    }
  }
)
```

## 🚀 Accessing Super Admin Dashboard

### Step 1: Login

1. Go to your Emergent preview URL: `https://your-url.preview.emergentagent.com`
2. Click **Login** or navigate to `/login`
3. Enter super admin credentials:
   - Email: `yash@earnaura.com`
   - Password: `YaSh@4517`

### Step 2: Access Dashboard

After login, navigate to:
```
https://your-url.preview.emergentagent.com/super-admin
```

Or click on the **Super Admin Dashboard** link in the navigation menu (only visible to super admins).

## 📱 Super Admin Features

The Super Admin dashboard includes 6 main sections:

### 1. Dashboard
- Overview of all admins (Campus & Club)
- Pending requests and alerts
- Recent activity metrics
- Top performing admins

### 2. Campus Admin Requests
- View all pending campus admin applications
- Approve/Reject requests with notes
- Set permissions and expiry dates
- Review credentials and documentation

### 3. Campus Admins Oversight
- Monitor all campus admins across universities
- View performance metrics
- Suspend/Revoke/Reactivate privileges
- Track activities and competitions

### 4. Club Admins Visibility
- View all club admins across campuses
- See which campus admin manages which club admin
- Filter by college and status
- Monitor club admin activities

### 5. Audit Logs
- Complete action history with IP tracking
- Filter by severity, action type, date range
- Track all admin actions for compliance
- Security monitoring

### 6. Real-time Alerts
- Receive instant notifications for critical actions
- Filter by severity (info/warning/error/critical)
- Mark alerts as read
- Security and compliance alerts

## 🔄 URL Dynamic Configuration

### How It Works

All URLs in the application are dynamically configured using environment variables:

1. **Frontend API Calls:** Use `process.env.REACT_APP_BACKEND_URL`
2. **Backend Referral Links:** Use `FRONTEND_URL` environment variable
3. **No Hardcoded URLs:** All domain references use environment variables

### Benefits

- ✅ Works with any Emergent preview URL
- ✅ Easy to update when URL changes
- ✅ No code changes needed for new trials
- ✅ Automatic configuration

## 🛠️ Troubleshooting

### Can't Access Super Admin Dashboard

1. **Check user permissions:**
   ```bash
   cd /app/backend
   python -c "
   import asyncio
   from motor.motor_asyncio import AsyncIOMotorClient
   
   async def check():
       client = AsyncIOMotorClient('mongodb://localhost:27017')
       db = client.moneymojo_db
       user = await db.users.find_one({'email': 'yash@earnaura.com'})
       print('User:', user.get('email'))
       print('Is Super Admin:', user.get('is_super_admin'))
       print('Admin Level:', user.get('admin_level'))
   
   asyncio.run(check())
   "
   ```

2. **Run the super admin script again:**
   ```bash
   cd /app/backend
   python create_super_admin.py
   ```

3. **Check if services are running:**
   ```bash
   sudo supervisorctl status
   ```

### Dashboard Shows Access Denied

- Make sure you're logged in with super admin credentials
- Clear browser cache and cookies
- Try logging out and logging in again

### Referral Links Not Working

- Check that `FRONTEND_URL` is correctly set in `/app/backend/.env`
- Restart backend service: `sudo supervisorctl restart backend`

## 🔐 Security Best Practices

1. **Change Default Password:** After first login, update the super admin password
2. **Restrict Access:** Only share super admin credentials with trusted administrators
3. **Monitor Audit Logs:** Regularly review the audit logs for suspicious activity
4. **Use Strong Passwords:** When creating new super admins, use strong, unique passwords

## 📝 Quick Reference

| Action | Command/URL |
|--------|-------------|
| Access Dashboard | `https://your-url.preview.emergentagent.com/super-admin` |
| Create Super Admin | `cd /app/backend && python create_super_admin.py` |
| Update Frontend URL | Edit `/app/backend/.env` → `FRONTEND_URL=...` |
| Restart Backend | `sudo supervisorctl restart backend` |
| Check Services | `sudo supervisorctl status` |

## 🎓 Admin Hierarchy

```
Super Admin (Top Level)
    ↓
Campus Admins (University Level)
    ↓
Club Admins (College Club Level)
```

- **Super Admins:** Full oversight of all admins, can approve/suspend/revoke
- **Campus Admins:** Manage competitions and club admins for their university
- **Club Admins:** Manage events and activities for their specific club

## 📞 Support

If you encounter any issues:
1. Check the backend logs: `tail -f /var/log/supervisor/backend.*.log`
2. Check the frontend logs: `tail -f /var/log/supervisor/frontend.*.log`
3. Review this guide for common solutions
4. Contact technical support with log details

---

**Note:** This setup works with any Emergent preview URL. Simply update the `FRONTEND_URL` environment variable when you receive a new trial URL, and everything will continue working seamlessly.
