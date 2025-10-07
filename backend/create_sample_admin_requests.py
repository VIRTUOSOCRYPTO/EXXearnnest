"""
Script to create sample campus admin requests for testing the super admin dashboard
Usage: python create_sample_admin_requests.py
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from security import hash_password
import uuid
from datetime import datetime, timezone

load_dotenv()

async def create_sample_data():
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'moneymojo_db')
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Create sample users who will request to become campus admins
    sample_users = [
        {
            "id": str(uuid.uuid4()),
            "email": "john.doe@vit.ac.in",
            "password_hash": hash_password("password123"),
            "full_name": "John Doe",
            "role": "Student",
            "student_level": "undergraduate",
            "university": "VIT Vellore",
            "skills": ["Event Management", "Leadership"],
            "availability_hours": 20,
            "location": "Vellore, Tamil Nadu",
            "bio": "Student leader with experience in organizing college events",
            "avatar": "man",
            "created_at": datetime.now(timezone.utc),
            "total_earnings": 0.0,
            "net_savings": 0.0,
            "current_streak": 0,
            "badges": [],
            "achievement_points": 50,
            "level": 2,
            "experience_points": 150,
            "title": "Event Coordinator",
            "achievements_shared": 0,
            "email_verified": True,
            "is_active": True,
            "is_admin": False,
            "is_super_admin": False,
            "admin_level": "user",
            "failed_login_attempts": 0
        },
        {
            "id": str(uuid.uuid4()),
            "email": "sarah.wilson@iitd.ac.in",
            "password_hash": hash_password("password123"),
            "full_name": "Sarah Wilson",
            "role": "Student",
            "student_level": "graduate",
            "university": "IIT Delhi",
            "skills": ["Computer Science", "Student Affairs"],
            "availability_hours": 25,
            "location": "New Delhi, Delhi",
            "bio": "Graduate student with strong technical and leadership background",
            "avatar": "woman",
            "created_at": datetime.now(timezone.utc),
            "total_earnings": 0.0,
            "net_savings": 0.0,
            "current_streak": 0,
            "badges": [],
            "achievement_points": 75,
            "level": 3,
            "experience_points": 200,
            "title": "Tech Lead",
            "achievements_shared": 0,
            "email_verified": True,
            "is_active": True,
            "is_admin": False,
            "is_super_admin": False,
            "admin_level": "user",
            "failed_login_attempts": 0
        },
        {
            "id": str(uuid.uuid4()),
            "email": "mike.kumar@bits-pilani.ac.in",
            "password_hash": hash_password("password123"),
            "full_name": "Mike Kumar",
            "role": "Professional",
            "student_level": "alumni",
            "university": "BITS Pilani",
            "skills": ["Business Development", "Alumni Relations"],
            "availability_hours": 15,
            "location": "Pilani, Rajasthan",
            "bio": "Alumni working as campus coordinator",
            "avatar": "man",
            "created_at": datetime.now(timezone.utc),
            "total_earnings": 0.0,
            "net_savings": 0.0,
            "current_streak": 0,
            "badges": [],
            "achievement_points": 100,
            "level": 4,
            "experience_points": 300,
            "title": "Campus Coordinator",
            "achievements_shared": 0,
            "email_verified": True,
            "is_active": True,
            "is_admin": False,
            "is_super_admin": False,
            "admin_level": "user",
            "failed_login_attempts": 0
        }
    ]
    
    # Insert sample users
    for user in sample_users:
        existing_user = await db.users.find_one({"email": user["email"]})
        if not existing_user:
            await db.users.insert_one(user)
            print(f"✅ Created sample user: {user['email']}")
        else:
            print(f"⚠️  User already exists: {user['email']}")
    
    # Create campus admin requests
    campus_requests = [
        {
            "id": str(uuid.uuid4()),
            "user_id": sample_users[0]["id"],
            "admin_type": "campus_admin",
            "university": "VIT Vellore",
            "college_name": "Vellore Institute of Technology",
            "position": "Student Council President",
            "experience": "2 years of student leadership, organized 5+ major events",
            "reason": "Want to help students with financial management and organize financial literacy programs",
            "additional_info": "Currently serving as Student Council President with 200+ active members under guidance",
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
            "institutional_email": "john.doe@vit.ac.in",
            "institutional_email_verified": True,
            "document_path": None,
            "review_notes": None,
            "reviewed_by": None,
            "reviewed_at": None
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": sample_users[1]["id"],
            "admin_type": "campus_admin",
            "university": "IIT Delhi",
            "college_name": "Indian Institute of Technology Delhi",
            "position": "PhD Student & Teaching Assistant",
            "experience": "3 years as TA, mentored 100+ students in financial planning",
            "reason": "Passionate about financial education and helping fellow students achieve financial independence",
            "additional_info": "Research focus on fintech solutions for student communities. Active in student welfare programs.",
            "status": "under_review",
            "created_at": datetime.now(timezone.utc),
            "institutional_email": "sarah.wilson@iitd.ac.in",
            "institutional_email_verified": True,
            "document_path": None,
            "review_notes": "Strong academic background, good leadership experience",
            "reviewed_by": None,
            "reviewed_at": None
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": sample_users[2]["id"],
            "admin_type": "campus_admin",
            "university": "BITS Pilani",
            "college_name": "Birla Institute of Technology and Science",
            "position": "Alumni Coordinator",
            "experience": "5 years in alumni relations, organized financial workshops",
            "reason": "Bridge the gap between students and alumni for financial mentorship opportunities",
            "additional_info": "Successfully organized 10+ financial literacy workshops with 500+ participants",
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
            "institutional_email": "mike.kumar@bits-pilani.ac.in",
            "institutional_email_verified": True,
            "document_path": None,
            "review_notes": None,
            "reviewed_by": None,
            "reviewed_at": None
        }
    ]
    
    # Insert campus admin requests
    for request in campus_requests:
        existing_request = await db.campus_admin_requests.find_one({"user_id": request["user_id"]})
        if not existing_request:
            await db.campus_admin_requests.insert_one(request)
            print(f"✅ Created campus admin request for: {request['institutional_email']}")
        else:
            print(f"⚠️  Campus admin request already exists for user: {request['user_id']}")
    
    print(f"\n🎯 Sample Data Creation Complete!")
    print(f"\n📋 Campus Admin Requests Created:")
    print(f"   1. John Doe (VIT Vellore) - Status: pending")
    print(f"   2. Sarah Wilson (IIT Delhi) - Status: under_review")  
    print(f"   3. Mike Kumar (BITS Pilani) - Status: pending")
    
    print(f"\n🔐 Super Admin can now:")
    print(f"   - Review and approve/reject campus admin applications")
    print(f"   - Access: https://admin-dashboard-275.preview.emergentagent.com/super-admin")
    print(f"   - Login: superadmin@earnnest.com / SuperAdmin@123")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_sample_data())
