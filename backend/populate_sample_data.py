#!/usr/bin/env python3
"""
Sample Data Population Script for EarnAura
Creates realistic campus battle data for demonstration purposes
"""

import os
import sys
import asyncio
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import random
import bcrypt
from bson import ObjectId

# Add the backend directory to Python path
sys.path.insert(0, '/app/backend')

# Import database connection
from database import db

class SampleDataGenerator:
    def __init__(self):
        self.indian_universities = [
            "IIT Bombay", "IIT Delhi", "IIT Madras", "IIT Kanpur", "IIT Kharagpur",
            "IIT Roorkee", "IIT Guwahati", "BITS Pilani", "NIT Trichy", "NIT Surathkal",
            "VIT Vellore", "IIIT Hyderabad", "DTU Delhi", "NSIT Delhi", "PEC Chandigarh",
            "Jadavpur University", "Anna University", "BIT Mesra", "MNIT Jaipur", "NIT Calicut",
            "SRM Institute", "Amity University", "LPU Punjab", "Manipal University", "MIT Manipal",
            "COEP Pune", "VJTI Mumbai", "PSG Tech Coimbatore", "SSN Chennai", "RV College Bangalore"
        ]
        
        self.sample_names = [
            "Arjun Sharma", "Priya Patel", "Rahul Kumar", "Ananya Singh", "Vikram Reddy",
            "Sneha Agarwal", "Karan Mehta", "Riya Gupta", "Amit Joshi", "Kavya Nair",
            "Siddharth Iyer", "Pooja Verma", "Rohan Das", "Meera Shah", "Aditya Mishra",
            "Divya Pillai", "Harsh Bansal", "Ritika Chopra", "Nikhil Tiwari", "Shreya Kapoor",
            "Akash Pandey", "Ishita Jain", "Varun Sinha", "Natasha Roy", "Deepak Yadav",
            "Aditi Bose", "Manish Kulkarni", "Simran Kaur", "Rajesh Menon", "Tanvi Bhatt"
        ]

    async def create_sample_users(self, num_users_per_campus=15):
        """Create sample users for each university"""
        print("🚀 Creating sample users...")
        
        users_created = 0
        transactions_created = 0
        
        for university in self.indian_universities:
            print(f"📚 Creating users for {university}...")
            
            # Create 10-20 users per university
            num_users = random.randint(10, num_users_per_campus)
            
            for i in range(num_users):
                # Create user data with unique identifier
                name = random.choice(self.sample_names)
                unique_id = random.randint(1000, 9999)
                email = f"{name.lower().replace(' ', '.')}_{unique_id}@{university.lower().replace(' ', '').replace('university', 'u')}.edu"
                
                # Generate realistic financial data
                total_earnings = random.randint(5000, 50000)
                total_expenses = random.randint(2000, total_earnings - 1000)
                net_savings = total_earnings - total_expenses
                current_streak = random.randint(0, 45)
                
                # Create user document
                user_data = {
                    "email": email,
                    "password_hash": bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                    "full_name": name,
                    "university": university,
                    "role": random.choice(["Student", "Student", "Student", "Professional"]),  # 75% students
                    "location": f"{random.choice(['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Pune', 'Hyderabad'])}, India",
                    "skills": random.sample(["Coding", "Digital Marketing", "Graphic Design", "Content Writing", "Video Editing"], 2),
                    "avatar": random.choice(["boy", "girl", "man", "woman"]),
                    "total_earnings": total_earnings,
                    "total_expenses": total_expenses,
                    "net_savings": net_savings,
                    "current_streak": current_streak,
                    "level": min(10, max(1, net_savings // 5000)),
                    "experience_points": net_savings * 2,
                    "is_active": True,
                    "email_verified": True,
                    "last_activity_date": datetime.now(timezone.utc) - timedelta(days=random.randint(0, 7)),
                    "created_at": datetime.now(timezone.utc) - timedelta(days=random.randint(10, 180))
                }
                
                try:
                    # Insert user
                    result = await db.users.insert_one(user_data)
                    user_id = str(result.inserted_id)
                    users_created += 1
                    
                    # Create sample transactions for this user
                    await self.create_sample_transactions(user_id, email)
                    transactions_created += random.randint(5, 15)
                    
                except Exception as e:
                    if "duplicate key" not in str(e):
                        print(f"⚠️ Error creating user {email}: {e}")
        
        print(f"✅ Created {users_created} sample users and {transactions_created} transactions!")
        return users_created

    async def create_sample_transactions(self, user_id, email):
        """Create sample transactions for a user"""
        categories = ["Food", "Transportation", "Entertainment", "Shopping", "Books", "Groceries", "Movies", "Subscriptions"]
        transaction_types = ["income", "expense"]
        
        # Create 5-15 transactions per user
        num_transactions = random.randint(5, 15)
        
        for _ in range(num_transactions):
            transaction_type = random.choice(transaction_types)
            
            if transaction_type == "income":
                amount = random.randint(1000, 8000)
                category = random.choice(["Freelance", "Part-time Job", "Tutoring", "Side Hustle"])
                description = f"{category} earnings"
            else:
                amount = random.randint(50, 2000)
                category = random.choice(categories)
                description = f"{category.lower()} expense"
            
            transaction_data = {
                "user_id": user_id,
                "email": email,
                "amount": amount,
                "type": transaction_type,
                "category": category,
                "description": description,
                "date": datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30)),
                "created_at": datetime.now(timezone.utc)
            }
            
            try:
                await db.transactions.insert_one(transaction_data)
            except Exception as e:
                print(f"⚠️ Error creating transaction: {e}")

    async def create_milestone_achievements(self):
        """Create sample milestone achievements"""
        print("🏆 Creating milestone achievements...")
        
        milestones = [
            {"amount": 100000, "text": "Students crossed ₹1 lakh in total savings!"},
            {"amount": 500000, "text": "Amazing! ₹5 lakh saved by all students combined!"},
            {"amount": 1000000, "text": "🎉 MILESTONE: ₹10 lakh total savings achieved!"},
            {"amount": 2500000, "text": "Incredible! Students have saved ₹25 lakh together!"},
            {"amount": 5000000, "text": "🚀 HUGE: ₹50 lakh saved by EarnAura community!"},
            {"amount": 10000000, "text": "🎯 MASSIVE: ₹1 CRORE saved by all students!"}
        ]
        
        try:
            # Clear existing milestones
            await db.viral_milestones.delete_many({})
            
            # Insert new milestones
            for milestone in milestones:
                milestone_doc = {
                    "type": "app_wide",
                    "milestone_amount": milestone["amount"],
                    "achievement_text": milestone["text"],
                    "achieved": True,
                    "achieved_date": datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30)),
                    "created_at": datetime.now(timezone.utc)
                }
                await db.viral_milestones.insert_one(milestone_doc)
            
            print(f"✅ Created {len(milestones)} milestone achievements!")
            
        except Exception as e:
            print(f"⚠️ Error creating milestones: {e}")

    async def populate_all_sample_data(self):
        """Main function to populate all sample data"""
        print("🎯 Starting EarnAura Sample Data Population...")
        
        try:
            # Test database connection
            await db.users.count_documents({})
            print("✅ Database connection successful!")
            
            # Create sample users and transactions
            await self.create_sample_users()
            
            # Create milestone achievements
            await self.create_milestone_achievements()
            
            # Print summary
            total_users = await db.users.count_documents({})
            total_transactions = await db.transactions.count_documents({})
            
            print("\n🎉 Sample Data Population Complete!")
            print(f"📊 Summary:")
            print(f"   👥 Total Users: {total_users}")
            print(f"   💰 Total Transactions: {total_transactions}")
            print(f"   🏫 Universities: {len(self.indian_universities)}")
            print(f"\n🚀 Your campus battle dashboard is now ready with realistic data!")
            
        except Exception as e:
            print(f"❌ Error during data population: {e}")
            raise e

async def main():
    """Main execution function"""
    generator = SampleDataGenerator()
    await generator.populate_all_sample_data()

if __name__ == "__main__":
    asyncio.run(main())
