# 🔄 Quick URL Update Guide

## When You Get a New Emergent Preview URL

Follow these 3 simple steps to update your app for the new trial:

### Step 1: Update Backend Environment
Edit `/app/backend/.env` and change the `FRONTEND_URL`:

```bash
# From:
FRONTEND_URL=https://old-url.preview.emergentagent.com

# To:
FRONTEND_URL=https://new-url.preview.emergentagent.com
```

### Step 2: Restart Backend
```bash
sudo supervisorctl restart backend
```

### Step 3: Access Your App
Navigate to your new URL:
```
https://new-url.preview.emergentagent.com
```

## 📋 One-Line Command

For quick updates, use this command (replace `NEW_URL` with your actual URL):

```bash
# Update backend .env
sed -i 's|FRONTEND_URL=.*|FRONTEND_URL=NEW_URL|g' /app/backend/.env && sudo supervisorctl restart backend
```

Example:
```bash
sed -i 's|FRONTEND_URL=.*|FRONTEND_URL=https://my-new-app.preview.emergentagent.com|g' /app/backend/.env && sudo supervisorctl restart backend
```

## ✅ Verify Changes

Check if the update was successful:

```bash
# 1. Check environment variable
grep FRONTEND_URL /app/backend/.env

# 2. Check backend is running
sudo supervisorctl status backend

# 3. Test API endpoint
curl -s http://localhost:8001/api/auth/trending-skills | head -5
```

## 🎯 What Gets Updated?

When you change `FRONTEND_URL`, these features automatically use the new URL:
- ✅ Referral links (share with friends)
- ✅ Email notifications with links
- ✅ Social sharing features
- ✅ Password reset links
- ✅ Registration confirmation links

## ⚠️ Important Notes

1. **Frontend URL is already configured** by Emergent in `/app/frontend/.env` as `REACT_APP_BACKEND_URL`
2. **Don't change** `MONGO_URL` or `DB_NAME` - these should stay the same
3. **Always restart backend** after changing environment variables
4. **No code changes needed** - everything is environment-based

## 🚀 Super Admin Access

After updating the URL, access Super Admin at:
```
https://your-new-url.preview.emergentagent.com/super-admin
```

Login credentials (default):
- Email: `yash@earnaura.com`
- Password: `YaSh@4517`

---

**That's it!** Your app now works with the new Emergent preview URL. All features including Super Admin, referrals, and API calls will use the new URL automatically.
