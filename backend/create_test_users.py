#!/usr/bin/env python3
"""
Create Test Users for Testing Leaderboard and Referral Fixes
"""

import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta
import uuid
import bcrypt

# Add backend directory to path
sys.path.append(os.path.dirname(__file__))

from database import get_database
from gamification_service import GamificationService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_test_users():
    """Create several test users with different data for testing"""
    
    try:
        db = await get_database()
        
        logger.info("🚀 Creating test users for leaderboard and referral testing...")
        
        # Test users data
        test_users = [
            {
                "full_name": "Test User 1",
                "email": "test1@example.com",
                "university": "IIT Delhi",
                "avatar": "man",
                "role": "Student",
                "location": "New Delhi, India",
                "net_savings": 5000,
                "current_streak": 15,
                "experience_points": 1500
            },
            {
                "full_name": "Test User 2", 
                "email": "test2@example.com",
                "university": "IIT Mumbai",
                "avatar": "woman",
                "role": "Student",
                "location": "Mumbai, India",
                "net_savings": 7500,
                "current_streak": 25,
                "experience_points": 2000
            },
            {
                "full_name": "Test User 3",
                "email": "test3@example.com", 
                "university": "IIT Bangalore",
                "avatar": "boy",
                "role": "Student",
                "location": "Bangalore, India",
                "net_savings": 3000,
                "current_streak": 10,
                "experience_points": 800
            },
            {
                "full_name": "Test User 4",
                "email": "test4@example.com",
                "university": "IIT Chennai", 
                "avatar": "girl",
                "role": "Student",
                "location": "Chennai, India",
                "net_savings": 9000,
                "current_streak": 30,
                "experience_points": 2500
            },
            {
                "full_name": "Test User 5",
                "email": "test5@example.com",
                "university": "IIT Kharagpur",
                "avatar": "man", 
                "role": "Professional",
                "location": "Kolkata, India",
                "net_savings": 12000,
                "current_streak": 45,
                "experience_points": 3000
            }
        ]
        
        created_users = []
        gamification = GamificationService(db)
        
        for user_data in test_users:
            # Check if user already exists
            existing = await db.users.find_one({"email": user_data["email"]})
            if existing:
                logger.info(f"✅ User {user_data['full_name']} already exists")
                created_users.append(existing)
                continue
            
            # Create user
            hashed_password = bcrypt.hashpw("test123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            user_doc = {
                "id": str(uuid.uuid4()),
                "full_name": user_data["full_name"],
                "email": user_data["email"],
                "password": hashed_password,
                "university": user_data["university"],
                "avatar": user_data["avatar"],
                "role": user_data["role"],
                "location": user_data["location"],
                "skills": ["Coding", "Digital Marketing"],
                "is_active": True,
                "email_verified": True,
                "created_at": datetime.now(timezone.utc),
                "net_savings": user_data["net_savings"],
                "current_streak": user_data["current_streak"],
                "experience_points": user_data["experience_points"],
                "achievement_points": user_data["experience_points"],
                "level": max(1, user_data["experience_points"] // 500),
                "title": "Financial Warrior" if user_data["experience_points"] > 2000 else "Budget Tracker"
            }
            
            # Insert user
            await db.users.insert_one(user_doc)
            created_users.append(user_doc)
            
            # Create referral program for user  
            referral_code = user_doc["id"][:8] + str(int(datetime.now().timestamp()))[-6:]
            referral_program = {
                "referrer_id": user_doc["id"],
                "referral_code": referral_code,
                "total_referrals": 0,
                "successful_referrals": 0,
                "total_earnings": 0.0,
                "pending_earnings": 0.0,
                "created_at": datetime.now(timezone.utc)
            }
            await db.referral_programs.insert_one(referral_program)
            
            # Create some transactions for the user
            for i in range(3):
                transaction = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_doc["id"],
                    "amount": 500 + (i * 200),
                    "type": "income" if i % 2 == 0 else "expense",
                    "category": "Freelance" if i % 2 == 0 else "Food",
                    "description": f"Test transaction {i+1}",
                    "created_at": datetime.now(timezone.utc) - timedelta(days=i)
                }
                await db.transactions.insert_one(transaction)
            
            # Update leaderboards for this user
            await gamification.update_leaderboards(user_doc["id"])
            
            logger.info(f"✅ Created user: {user_data['full_name']} with leaderboards")
        
        # Create some friendships between users for testing
        if len(created_users) >= 2:
            friendship = {
                "id": str(uuid.uuid4()),
                "user1_id": created_users[0]["id"],
                "user2_id": created_users[1]["id"],
                "status": "active",
                "created_at": datetime.now(timezone.utc),
                "connection_type": "manual_invitation",
                "automatic": False
            }
            await db.friendships.insert_one(friendship)
            logger.info(f"✅ Created friendship between {created_users[0]['full_name']} and {created_users[1]['full_name']}")
        
        logger.info(f"🎉 Created {len(created_users)} test users successfully!")
        
        return created_users
        
    except Exception as e:
        logger.error(f"❌ Error creating test users: {str(e)}")
        raise

async def main():
    """Main function"""
    logger.info("🚀 Starting Test User Creation...")
    
    users = await create_test_users()
    
    logger.info("✅ Test user creation completed!")
    logger.info(f"👥 Created {len(users)} users for testing")
    
    return users

if __name__ == "__main__":
    asyncio.run(main())
