#!/usr/bin/env python3
"""
Test script to verify live data is working in APIs
"""

import asyncio
import aiohttp
import json
import sys

# Add the backend directory to Python path
sys.path.insert(0, '/app/backend')

from database import get_database

async def create_test_user_and_login():
    """Create a test user and get authentication token"""
    
    # Register a test user
    register_data = {
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User",
        "university": "IIT Bombay",
        "role": "Student",
        "location": "Mumbai, India",
        "skills": ["Coding", "Digital Marketing"],
        "avatar": "boy"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # Register user
            async with session.post('http://localhost:8001/api/auth/register', json=register_data) as response:
                if response.status == 200:
                    result = await response.json()
                    token = result.get('access_token')
                    print(f"✅ User registered and logged in! Token: {token[:20]}...")
                    return token
                else:
                    # Try to login if user already exists
                    login_data = {"email": register_data["email"], "password": register_data["password"]}
                    async with session.post('http://localhost:8001/api/auth/login', json=login_data) as login_response:
                        if login_response.status == 200:
                            result = await login_response.json()
                            token = result.get('access_token')
                            print(f"✅ User logged in! Token: {token[:20]}...")
                            return token
                        else:
                            print(f"❌ Failed to login: {await login_response.text()}")
                            return None
                            
        except Exception as e:
            print(f"❌ Error during authentication: {e}")
            return None

async def test_api_endpoints(token):
    """Test all campus and viral feature APIs"""
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    endpoints_to_test = [
        ("/api/inter-college/competitions", "Inter-college Competitions"),
        ("/api/prize-challenges", "Prize Challenges"), 
        ("/api/campus/reputation", "Campus Reputation"),
        ("/api/milestones/check", "Viral Milestones"),
        ("/api/insights/campus-spending/IIT%20Bombay", "Campus Spending Insights"),
        ("/api/insights/friend-comparison", "Friend Comparisons")
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint, name in endpoints_to_test:
            try:
                async with session.get(f'http://localhost:8001{endpoint}', headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Check if data is not empty
                        if isinstance(data, dict):
                            if endpoint == "/api/inter-college/competitions":
                                competitions = data.get('competitions', [])
                                print(f"✅ {name}: {len(competitions)} competitions found")
                                if competitions:
                                    print(f"   Sample: {competitions[0].get('title', 'No title')}")
                                    
                            elif endpoint == "/api/prize-challenges":
                                challenges = data.get('challenges', [])
                                print(f"✅ {name}: {len(challenges)} challenges found")
                                if challenges:
                                    print(f"   Sample: {challenges[0].get('title', 'No title')}")
                                    
                            elif endpoint == "/api/campus/reputation":
                                leaderboard = data.get('campus_leaderboard', [])
                                print(f"✅ {name}: {len(leaderboard)} campus entries found")
                                if leaderboard:
                                    print(f"   Top campus: {leaderboard[0].get('campus', 'No name')}")
                                    
                            elif endpoint == "/api/milestones/check":
                                app_milestones = data.get('app_wide_milestones', [])
                                campus_milestones = data.get('campus_milestones', [])
                                print(f"✅ {name}: {len(app_milestones)} app + {len(campus_milestones)} campus milestones")
                                
                            else:
                                print(f"✅ {name}: Data received")
                                
                        else:
                            print(f"✅ {name}: Response received")
                            
                    else:
                        error_text = await response.text()
                        print(f"❌ {name}: HTTP {response.status} - {error_text[:100]}")
                        
            except Exception as e:
                print(f"❌ {name}: Error - {e}")

async def check_database_counts():
    """Check current database state"""
    print("\n📊 Database Statistics:")
    
    db = await get_database()
    
    collections = [
        'users', 'transactions', 'inter_college_competitions', 
        'prize_challenges', 'viral_milestones', 'campus_reputation'
    ]
    
    for collection_name in collections:
        count = await getattr(db, collection_name).count_documents({})
        print(f"   {collection_name}: {count} documents")

async def main():
    """Main test function"""
    print("🧪 Testing Live Data APIs...")
    
    # Check database state
    await check_database_counts()
    
    # Get authentication token
    token = await create_test_user_and_login()
    
    if token:
        print("\n🔍 Testing API Endpoints...")
        await test_api_endpoints(token)
    else:
        print("❌ Could not authenticate - skipping API tests")

if __name__ == "__main__":
    asyncio.run(main())
