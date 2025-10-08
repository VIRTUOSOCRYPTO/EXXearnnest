"""
Script to create or update a super admin user
Usage: python create_super_admin.py
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from security import hash_password

load_dotenv()

async def create_super_admin():
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'moneymojo_db')
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]  # Use the configured database
    
    # Super admin details
    super_admin_email = "yash@earnaura.com"
    super_admin_password = "YaSh@4517"  # Change this in production
    
    # Check if super admin already exists
    existing_admin = await db.users.find_one({"email": super_admin_email})
    
    if existing_admin:
        print(f"✅ Super admin already exists: {super_admin_email}")
        # Update to ensure super admin flags are set
        await db.users.update_one(
            {"email": super_admin_email},
            {
                "$set": {
                    "is_admin": True,
                    "is_super_admin": True,
                    "admin_level": "super_admin"
                }
            }
        )
        print(f"✅ Updated super admin flags for {super_admin_email}")
    else:
        # Create new super admin user
        from models import User
        import uuid
        from datetime import datetime, timezone
        
        super_admin = {
            "id": str(uuid.uuid4()),
            "email": super_admin_email,
            "password_hash": hash_password(super_admin_password),
            "full_name": "Super Admin",
            "role": "Professional",
            "student_level": "graduate",
            "university": "EarnNest Platform",
            "skills": ["Platform Management", "System Administration"],
            "availability_hours": 40,
            "location": "Platform HQ, Global",
            "bio": "Super Administrator with full oversight privileges",
            "avatar": "man",
            "created_at": datetime.now(timezone.utc),
            "total_earnings": 0.0,
            "net_savings": 0.0,
            "current_streak": 0,
            "badges": [],
            "achievement_points": 0,
            "level": 1,
            "experience_points": 0,
            "title": "Super Administrator",
            "achievements_shared": 0,
            "email_verified": True,
            "is_active": True,
            "is_admin": True,
            "is_super_admin": True,
            "admin_level": "super_admin",
            "failed_login_attempts": 0
        }
        
        await db.users.insert_one(super_admin)
        print(f"✅ Created new super admin user: {super_admin_email}")
    
    print(f"\n🔐 Super Admin Credentials:")
    print(f"   Email: {super_admin_email}")
    print(f"   Password: {super_admin_password}")
    print(f"\n⚠️  Please change the password after first login!")
    
    # Also update any existing admin users to have the new fields
    print(f"\n🔄 Updating existing admin users with new admin hierarchy fields...")
    result = await db.users.update_many(
        {"is_admin": True, "admin_level": {"$exists": False}},
        {"$set": {"admin_level": "super_admin", "is_super_admin": True}}
    )
    print(f"✅ Updated {result.modified_count} existing admin users")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_super_admin())
