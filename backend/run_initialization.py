"""
Standalone initialization script that runs both super admin creation and university initialization
"""
import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from passlib.context import CryptContext
import uuid
from datetime import datetime, timezone

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def create_super_admin(db):
    """Create or update a super admin user"""
    print("\n" + "="*60)
    print("CREATING SUPER ADMIN")
    print("="*60)
    
    # Super admin details
    super_admin_email = "yash@earnaura.com"
    super_admin_password = "YaSh@4517"
    
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

async def initialize_universities(db):
    """Initialize comprehensive Indian universities database"""
    print("\n" + "="*60)
    print("INITIALIZING UNIVERSITIES DATABASE")
    print("="*60)
    
    # Clear existing universities to avoid duplicates
    deleted_count = await db.universities.delete_many({})
    print(f"🗑️  Cleared {deleted_count.deleted_count} existing universities")
    
    comprehensive_universities = [
        # === MAHARASHTRA ===
        {
            "name": "Indian Institute of Technology Bombay",
            "short_name": "IIT Bombay",
            "location": "Mumbai, Maharashtra",
            "city": "Mumbai",
            "state": "Maharashtra",
            "type": "engineering_institute",
            "student_levels": ["undergraduate", "graduate"],
            "categories": ["engineering", "technology", "research"],
            "ranking": 1,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "University of Mumbai",
            "short_name": "Mumbai University",
            "location": "Mumbai, Maharashtra",
            "city": "Mumbai", 
            "state": "Maharashtra",
            "type": "state_university",
            "student_levels": ["high_school", "undergraduate", "graduate"],
            "categories": ["general", "commerce", "science", "arts"],
            "ranking": 15,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "Indian Institute of Science Education and Research Pune",
            "short_name": "IISER Pune",
            "location": "Pune, Maharashtra",
            "city": "Pune",
            "state": "Maharashtra", 
            "type": "science_institute",
            "student_levels": ["undergraduate", "graduate"],
            "categories": ["science", "research"],
            "ranking": 8,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "Savitribai Phule Pune University",
            "short_name": "Pune University",
            "location": "Pune, Maharashtra",
            "city": "Pune",
            "state": "Maharashtra",
            "type": "state_university", 
            "student_levels": ["high_school", "undergraduate", "graduate"],
            "categories": ["general", "engineering", "management"],
            "ranking": 18,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        
        # === DELHI ===
        {
            "name": "Indian Institute of Technology Delhi",
            "short_name": "IIT Delhi",
            "location": "New Delhi",
            "city": "Delhi",
            "state": "Delhi",
            "type": "engineering_institute",
            "student_levels": ["undergraduate", "graduate"],
            "categories": ["engineering", "technology", "research"],
            "ranking": 2,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "Delhi University",
            "short_name": "DU",
            "location": "New Delhi",
            "city": "Delhi", 
            "state": "Delhi",
            "type": "central_university",
            "student_levels": ["high_school", "undergraduate", "graduate"],
            "categories": ["general", "commerce", "science", "arts", "law"],
            "ranking": 12,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "Jawaharlal Nehru University",
            "short_name": "JNU",
            "location": "New Delhi",
            "city": "Delhi",
            "state": "Delhi",
            "type": "central_university",
            "student_levels": ["undergraduate", "graduate"],
            "categories": ["arts", "humanities", "social_sciences"],
            "ranking": 7,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        
        # === KARNATAKA ===
        {
            "name": "Indian Institute of Science Bangalore",
            "short_name": "IISc Bangalore",
            "location": "Bangalore, Karnataka",
            "city": "Bangalore",
            "state": "Karnataka",
            "type": "science_institute",
            "student_levels": ["graduate"],
            "categories": ["science", "research", "technology"],
            "ranking": 1,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "Indian Institute of Management Bangalore",
            "short_name": "IIM Bangalore",
            "location": "Bangalore, Karnataka",
            "city": "Bangalore",
            "state": "Karnataka",
            "type": "management_institute",
            "student_levels": ["graduate"],
            "categories": ["management", "business"],
            "ranking": 1,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "Bangalore University",
            "short_name": "BU",
            "location": "Bangalore, Karnataka",
            "city": "Bangalore",
            "state": "Karnataka",
            "type": "state_university",
            "student_levels": ["high_school", "undergraduate", "graduate"],
            "categories": ["general", "science", "commerce", "arts"],
            "ranking": 25,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        
        # === TAMIL NADU ===
        {
            "name": "Indian Institute of Technology Madras",
            "short_name": "IIT Madras",
            "location": "Chennai, Tamil Nadu",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "type": "engineering_institute",
            "student_levels": ["undergraduate", "graduate"],
            "categories": ["engineering", "technology", "research"],
            "ranking": 1,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "Anna University",
            "short_name": "Anna University",
            "location": "Chennai, Tamil Nadu",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "type": "technical_university",
            "student_levels": ["undergraduate", "graduate"],
            "categories": ["engineering", "technology"],
            "ranking": 14,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "University of Madras",
            "short_name": "Madras University",
            "location": "Chennai, Tamil Nadu",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "type": "state_university",
            "student_levels": ["high_school", "undergraduate", "graduate"],
            "categories": ["general", "science", "arts", "commerce"],
            "ranking": 22,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        
        # === WEST BENGAL ===
        {
            "name": "Indian Institute of Technology Kharagpur",
            "short_name": "IIT Kharagpur",
            "location": "Kharagpur, West Bengal",
            "city": "Kharagpur",
            "state": "West Bengal",
            "type": "engineering_institute",
            "student_levels": ["undergraduate", "graduate"],
            "categories": ["engineering", "technology", "research"],
            "ranking": 4,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "University of Calcutta",
            "short_name": "Calcutta University",
            "location": "Kolkata, West Bengal",
            "city": "Kolkata",
            "state": "West Bengal",
            "type": "state_university",
            "student_levels": ["high_school", "undergraduate", "graduate"],
            "categories": ["general", "science", "arts", "commerce", "law"],
            "ranking": 16,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "Jadavpur University",
            "short_name": "JU",
            "location": "Kolkata, West Bengal",
            "city": "Kolkata",
            "state": "West Bengal",
            "type": "state_university",
            "student_levels": ["undergraduate", "graduate"],
            "categories": ["engineering", "science", "arts"],
            "ranking": 11,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
    ]
    
    # Insert all universities
    result = await db.universities.insert_many(comprehensive_universities)
    print(f"✅ Inserted {len(result.inserted_ids)} universities")
    
    # Display summary by state
    states = {}
    for uni in comprehensive_universities:
        state = uni['state']
        if state not in states:
            states[state] = []
        states[state].append(uni['short_name'])
    
    print(f"\n📊 Universities by State:")
    for state, unis in sorted(states.items()):
        print(f"   {state}: {len(unis)} universities")
        for uni in unis:
            print(f"      - {uni}")

async def main():
    """Main initialization function"""
    print("\n" + "="*60)
    print("EARNAURA INITIALIZATION SCRIPT")
    print("="*60)
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'moneymojo_db')
    
    print(f"\n📡 Connecting to MongoDB...")
    print(f"   URL: {mongo_url}")
    print(f"   Database: {db_name}")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Test connection
        await db.command('ping')
        print(f"✅ Connected to MongoDB successfully")
        
        # Run initializations
        await create_super_admin(db)
        await initialize_universities(db)
        
        print("\n" + "="*60)
        print("✅ INITIALIZATION COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nYou can now:")
        print("1. Start the backend: sudo supervisorctl restart backend")
        print("2. Start the frontend: sudo supervisorctl restart frontend")
        print("3. Login as super admin with credentials above")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())
