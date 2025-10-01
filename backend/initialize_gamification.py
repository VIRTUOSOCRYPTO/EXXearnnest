import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database import get_database
from datetime import datetime, timezone

async def initialize_universities():
    """Initialize popular Indian universities in the database"""
    db = await get_database()
    
    default_universities = [
        {
            "name": "Indian Institute of Technology Bombay",
            "short_name": "IIT-B",
            "location": "Mumbai, Maharashtra",
            "type": "institute",
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "Indian Institute of Technology Delhi", 
            "short_name": "IIT-D",
            "location": "New Delhi",
            "type": "institute",
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "Indian Institute of Management Bangalore",
            "short_name": "IIM-B",
            "location": "Bangalore, Karnataka",
            "type": "institute",
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "Delhi University",
            "short_name": "DU",
            "location": "New Delhi",
            "type": "university",
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "Jawaharlal Nehru University",
            "short_name": "JNU",
            "location": "New Delhi",
            "type": "university", 
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "University of Mumbai",
            "short_name": "MU",
            "location": "Mumbai, Maharashtra",
            "type": "university",
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "Bangalore University",
            "short_name": "BU",
            "location": "Bangalore, Karnataka",
            "type": "university",
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "Anna University",
            "short_name": "AU",
            "location": "Chennai, Tamil Nadu",
            "type": "university",
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "Pune University",
            "short_name": "PU",
            "location": "Pune, Maharashtra",
            "type": "university",
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "Osmania University",
            "short_name": "OU",
            "location": "Hyderabad, Telangana",
            "type": "university",
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        }
    ]
    
    for university_data in default_universities:
        # Check if university already exists
        existing = await db.universities.find_one({"short_name": university_data["short_name"]})
        if not existing:
            await db.universities.insert_one(university_data)
            print(f"✅ Initialized university: {university_data['name']}")
        else:
            print(f"⏭️  University already exists: {university_data['name']}")

    print(f"\n🎓 University initialization complete!")
    
    # Also initialize default badges
    from gamification_service import get_gamification_service
    gamification = await get_gamification_service()
    print(f"\n🏆 Gamification badges initialized!")

if __name__ == "__main__":
    print("🚀 Initializing EarnNest gamification system...")
    asyncio.run(initialize_universities())
