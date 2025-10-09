# 🚀 Automatic Initialization Setup Guide

This guide shows you how to automatically run backend setup scripts on first deployment.

## 📋 What Gets Initialized Automatically?

1. ✅ Budget format validation
2. ✅ Leaderboard cleanup (removes fake entries)
3. ✅ Super admin creation
4. ✅ University database population (27 institutions)
5. ✅ Test user creation (3 students)
6. ✅ WebSocket library installation

---

## 🎯 THREE METHODS TO AUTO-RUN SCRIPTS

### **METHOD 1: Master Initialization Script** ⭐ RECOMMENDED

The easiest way - runs all scripts in one command.

#### ✅ Already Created:
- `initialize_app.py` - Master script that runs everything

#### 🔧 How to Use:

**Option A: Run manually after first deployment**
```bash
cd /app/backend
python3 initialize_app.py
```

**Option B: Run automatically in startup.sh** (ALREADY CONFIGURED ✅)
The `/app/scripts/startup.sh` has been updated to automatically run `initialize_app.py` on first startup.

**How it works:**
- On first run: Executes all setup scripts
- On subsequent runs: Checks initialization flag and skips
- To force re-run: `python3 initialize_app.py --force`

---

### **METHOD 2: Supervisor Startup Script** 🔄

The startup script now includes automatic initialization.

#### ✅ Already Updated:
- `/app/scripts/startup.sh` includes `run_initialization()` function

#### 🔧 How it Works:
1. MongoDB starts
2. Initialization scripts run automatically (only first time)
3. Backend starts with clean data
4. Frontend starts

**To use:**
```bash
bash /app/scripts/startup.sh
```

Or just restart services - initialization happens automatically:
```bash
sudo supervisorctl restart all
```

---

### **METHOD 3: FastAPI Startup Event** 🎯

Run initialization when FastAPI server starts.

#### ✅ Already Created:
- `startup_tasks.py` - Contains startup initialization logic

#### 🔧 How to Integrate:

Add to your `server.py` (around line 3300 where other startup events are):

```python
from startup_tasks import check_and_initialize

@app.on_event("startup")
async def run_initialization():
    """Run first-time initialization tasks"""
    await check_and_initialize()
```

**Pros:**
- Runs automatically every time backend starts
- No separate script needed
- Integrated with FastAPI lifecycle

**Cons:**
- Adds ~5-10 seconds to server startup (only first time)
- May delay server readiness checks

---

## 🎮 Manual Testing Commands

### Run Individual Scripts:
```bash
cd /app/backend

# Fix budget format
python3 fix_budget_moth_format.py

# Clean leaderboards
python3 fix_leaderboard_duplicates.py

# Create super admin
python3 create_super_admin.py

# Initialize universities
python3 initialize_comprehensive_universities.py

# Create test users
python3 quick_test_users.py
```

### Check Initialization Status:
```bash
cd /app/backend
python3 -c "
import asyncio
from database import get_database

async def check():
    db = await get_database()
    flag = await db.system_config.find_one({'key': 'app_initialized'})
    if flag:
        print('✅ App is initialized')
        print(f'Initialized at: {flag.get(\"initialized_at\")}')
    else:
        print('❌ App is NOT initialized')

asyncio.run(check())
"
```

### Force Re-initialization:
```bash
cd /app/backend
python3 initialize_app.py --force
```

---

## 📊 Database Collections Created

After initialization, these collections will be populated:

```
✅ users: 5 users (1 super admin + 4 students)
✅ transactions: 9 transactions
✅ leaderboards: 96 entries (real users only)
✅ universities: 27 universities
✅ category_suggestions: 32 categories
✅ emergency_types: 6 types
✅ system_config: Initialization flag
```

---

## 🔐 Default Credentials Created

**Test Students:**
- student1@test.com / Test@123 (Raj Kumar - IIT Delhi)
- student2@test.com / Test@123 (Priya Sharma - IIT Mumbai)
- student3@test.com / Test@123 (Arjun Reddy - IIT Bangalore)

**Super Admin:**
- yash@earnaura.com / YaSh@4517

---

## 🐛 Troubleshooting

### Issue: Scripts not running automatically

**Solution 1: Check startup.sh**
```bash
bash /app/scripts/startup.sh
```

**Solution 2: Run manually**
```bash
cd /app/backend
python3 initialize_app.py
```

**Solution 3: Check logs**
```bash
tail -n 100 /var/log/supervisor/backend.err.log | grep -i "initialization"
```

### Issue: "Already initialized" message

This is normal! The scripts only run once. To re-run:
```bash
cd /app/backend
python3 initialize_app.py --force
```

### Issue: Import errors

Make sure you're in the backend directory:
```bash
cd /app/backend
source /root/.venv/bin/activate
python3 initialize_app.py
```

---

## 🎯 Recommended Setup for Production

1. **First Deployment:**
   ```bash
   # Clone/deploy your code
   cd /app
   
   # Run startup script
   bash scripts/startup.sh
   ```
   
   This will automatically:
   - Install dependencies
   - Start MongoDB
   - Run initialization scripts (first time only)
   - Start backend and frontend

2. **Subsequent Deployments:**
   ```bash
   # Just restart services
   sudo supervisorctl restart all
   ```
   
   Initialization is skipped automatically!

---

## ✅ Current Status

Your application now has **automatic initialization** configured via:

1. ✅ `initialize_app.py` - Master initialization script
2. ✅ `startup.sh` - Includes initialization in startup flow
3. ✅ `startup_tasks.py` - FastAPI integration (optional)

**Next deployment will automatically run all setup scripts! 🎉**

---

## 📞 Support

If you encounter issues:
1. Check `/var/log/supervisor/backend.err.log` for errors
2. Verify MongoDB is running: `sudo supervisorctl status mongodb`
3. Run initialization manually: `python3 initialize_app.py`
4. Force re-initialization: `python3 initialize_app.py --force`

---

**Last Updated:** $(date)
