import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database import get_database
from datetime import datetime, timezone

async def initialize_comprehensive_universities():
    """Initialize comprehensive Indian universities database with location and level mapping"""
    db = await get_database()
    
    # Clear existing universities to avoid duplicates
    await db.universities.delete_many({})
    
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
            "name": "Indian Institute of Technology Pune",
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
            "name": "Pune University",
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
            "categories": ["liberal_arts", "social_sciences", "languages"],
            "ranking": 10,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "Indian Institute of Management Delhi",
            "short_name": "IIM Delhi",
            "location": "New Delhi",
            "city": "Delhi",
            "state": "Delhi", 
            "type": "management_institute",
            "student_levels": ["graduate"],
            "categories": ["management", "business"],
            "ranking": 4,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        
        # === KARNATAKA ===
        {
            "name": "Indian Institute of Science",
            "short_name": "IISc Bangalore",
            "location": "Bangalore, Karnataka",
            "city": "Bangalore",
            "state": "Karnataka",
            "type": "science_institute",
            "student_levels": ["undergraduate", "graduate"],
            "categories": ["science", "engineering", "research"],
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
            "ranking": 2,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "Bangalore University",
            "short_name": "Bangalore University",
            "location": "Bangalore, Karnataka",
            "city": "Bangalore",
            "state": "Karnataka",
            "type": "state_university",
            "student_levels": ["high_school", "undergraduate", "graduate"],
            "categories": ["general", "science", "commerce", "arts"],
            "ranking": 20,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "National Institute of Technology Karnataka",
            "short_name": "NIT Surathkal",
            "location": "Surathkal, Karnataka",
            "city": "Mangalore",
            "state": "Karnataka",
            "type": "engineering_institute", 
            "student_levels": ["undergraduate", "graduate"],
            "categories": ["engineering", "technology"],
            "ranking": 13,
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
            "ranking": 3,
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
            "student_levels": ["high_school", "undergraduate", "graduate"],
            "categories": ["engineering", "technology", "applied_sciences"],
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
            "ranking": 5,
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
            "short_name": "Jadavpur University",
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
        
        # === RAJASTHAN ===
        {
            "name": "Indian Institute of Technology Jodhpur",
            "short_name": "IIT Jodhpur", 
            "location": "Jodhpur, Rajasthan",
            "city": "Jodhpur",
            "state": "Rajasthan",
            "type": "engineering_institute",
            "student_levels": ["undergraduate", "graduate"],
            "categories": ["engineering", "technology"],
            "ranking": 17,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "University of Rajasthan",
            "short_name": "Rajasthan University",
            "location": "Jaipur, Rajasthan",
            "city": "Jaipur",
            "state": "Rajasthan",
            "type": "state_university",
            "student_levels": ["high_school", "undergraduate", "graduate"],
            "categories": ["general", "science", "arts", "commerce"],
            "ranking": 25,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        
        # === UTTAR PRADESH ===
        {
            "name": "Indian Institute of Technology Kanpur",
            "short_name": "IIT Kanpur",
            "location": "Kanpur, Uttar Pradesh",
            "city": "Kanpur", 
            "state": "Uttar Pradesh",
            "type": "engineering_institute",
            "student_levels": ["undergraduate", "graduate"],
            "categories": ["engineering", "technology", "research"],
            "ranking": 6,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "Banaras Hindu University",
            "short_name": "BHU",
            "location": "Varanasi, Uttar Pradesh",
            "city": "Varanasi",
            "state": "Uttar Pradesh", 
            "type": "central_university",
            "student_levels": ["high_school", "undergraduate", "graduate"],
            "categories": ["general", "engineering", "medicine", "arts"],
            "ranking": 19,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "Lucknow University",
            "short_name": "Lucknow University",
            "location": "Lucknow, Uttar Pradesh",
            "city": "Lucknow",
            "state": "Uttar Pradesh",
            "type": "state_university",
            "student_levels": ["high_school", "undergraduate", "graduate"],
            "categories": ["general", "science", "arts", "commerce", "law"],
            "ranking": 24,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        
        # === ANDHRA PRADESH & TELANGANA ===
        {
            "name": "Indian Institute of Technology Hyderabad",
            "short_name": "IIT Hyderabad",
            "location": "Hyderabad, Telangana",
            "city": "Hyderabad",
            "state": "Telangana",
            "type": "engineering_institute",
            "student_levels": ["undergraduate", "graduate"], 
            "categories": ["engineering", "technology"],
            "ranking": 16,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "Osmania University",
            "short_name": "Osmania University",
            "location": "Hyderabad, Telangana",
            "city": "Hyderabad",
            "state": "Telangana",
            "type": "state_university",
            "student_levels": ["high_school", "undergraduate", "graduate"],
            "categories": ["general", "science", "engineering", "medicine"],
            "ranking": 21,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        
        # === GUJARAT ===
        {
            "name": "Indian Institute of Technology Gandhinagar",
            "short_name": "IIT Gandhinagar",
            "location": "Gandhinagar, Gujarat",
            "city": "Gandhinagar",
            "state": "Gujarat",
            "type": "engineering_institute",
            "student_levels": ["undergraduate", "graduate"],
            "categories": ["engineering", "technology"],
            "ranking": 18,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "name": "Gujarat University",
            "short_name": "Gujarat University", 
            "location": "Ahmedabad, Gujarat",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "type": "state_university",
            "student_levels": ["high_school", "undergraduate", "graduate"],
            "categories": ["general", "science", "commerce", "arts"],
            "ranking": 23,
            "is_verified": True,
            "student_count": 0,
            "created_at": datetime.now(timezone.utc)
        }
    ]
    
    for university_data in comprehensive_universities:
        await db.universities.insert_one(university_data)
        print(f"✅ Added: {university_data['name']} - {university_data['city']}, {university_data['state']}")

    print(f"\n🎓 Comprehensive university database initialized with {len(comprehensive_universities)} institutions!")

if __name__ == "__main__":
    print("🚀 Initializing comprehensive university database...")
    asyncio.run(initialize_comprehensive_universities())
