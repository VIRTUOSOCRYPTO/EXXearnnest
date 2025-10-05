#!/usr/bin/env python3
"""
Populate Production-Ready Data for EarnNest App

This script creates realistic user data, transactions, and populates all features
to make the app fully functional with live data for production deployment.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
import random
import uuid
from typing import List, Dict, Any
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_database
from models import User, Transaction, Budget, FinancialGoal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class ProductionDataPopulator:
    def __init__(self):
        self.db = None
        
        # Indian universities for realistic data
        self.universities = [
            "Indian Institute of Technology, Delhi",
            "University of Delhi",
            "Jawaharlal Nehru University",
            "Indian Institute of Technology, Mumbai",
            "University of Mumbai",
            "Indian Institute of Science, Bangalore",
            "University of Bangalore",
            "Indian Institute of Technology, Chennai",
            "Anna University",
            "Indian Institute of Technology, Kharagpur",
            "University of Calcutta",
            "Jadavpur University",
            "Indian Institute of Technology, Kanpur",
            "Banaras Hindu University",
            "Aligarh Muslim University",
            "University of Hyderabad",
            "Osmania University",
            "University of Pune",
            "Indian Institute of Technology, Roorkee",
            "Gujarat University",
            "Maharaja Sayajirao University",
            "University of Rajasthan",
            "Chandigarh University",
            "Panjab University",
            "Jamia Millia Islamia"
        ]
        
        # Realistic names for diversity
        self.first_names = [
            "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
            "Aadhya", "Kavya", "Ananya", "Anika", "Diya", "Saanvi", "Pihu", "Prisha", "Avni", "Myra",
            "Rahul", "Rohan", "Karan", "Amit", "Rajesh", "Suresh", "Deepak", "Vikram", "Ashish", "Manish",
            "Priya", "Pooja", "Neha", "Shweta", "Riya", "Shreya", "Divya", "Meera", "Sonia", "Kajal"
        ]
        
        self.last_names = [
            "Sharma", "Verma", "Gupta", "Singh", "Kumar", "Patel", "Agarwal", "Jain", "Bansal", "Mittal",
            "Chopra", "Mehta", "Malhotra", "Arora", "Kapoor", "Jindal", "Goel", "Aggarwal", "Bhatia", "Sethi",
            "Pandey", "Mishra", "Tiwari", "Dubey", "Shukla", "Srivastava", "Joshi", "Nair", "Menon", "Pillai"
        ]
        
        self.skills = [
            "Coding", "Digital Marketing", "Content Writing", "Graphic Design", 
            "Video Editing", "Social Media Management", "Photography", "Web Development",
            "Data Analysis", "UI/UX Design", "SEO Optimization", "Mobile App Development",
            "AI Tools & Automation", "Freelancing", "E-commerce", "Blog Writing"
        ]
        
        self.transaction_categories = [
            "Food", "Transportation", "Books", "Entertainment", "Rent", 
            "Utilities", "Movies", "Shopping", "Groceries", "Subscriptions"
        ]
        
        self.income_sources = [
            "Freelancing", "Part-time Job", "Internship", "Family Support", 
            "Scholarship", "Side Hustle", "Tutoring", "Project Work"
        ]

    async def initialize(self):
        """Initialize database connections"""
        self.db = await get_database()
        logger.info("🚀 Database connection established")

    async def create_realistic_users(self, count: int = 150):
        """Create realistic user accounts with diverse profiles"""
        logger.info(f"👥 Creating {count} realistic user accounts...")
        
        users_created = 0
        
        for i in range(count):
            try:
                # Generate realistic profile
                first_name = random.choice(self.first_names)
                last_name = random.choice(self.last_names)
                full_name = f"{first_name} {last_name}"
                
                # Create realistic email
                email_variations = [
                    f"{first_name.lower()}.{last_name.lower()}@gmail.com",
                    f"{first_name.lower()}{last_name.lower()}{random.randint(1, 99)}@gmail.com",
                    f"{first_name.lower()}{i}@student.university.edu",
                    f"{last_name.lower()}.{first_name.lower()}@outlook.com"
                ]
                email = random.choice(email_variations)
                
                # Check if email already exists
                existing_user = await self.db.users.find_one({"email": email})
                if existing_user:
                    continue
                
                user_data = {
                    "_id": str(uuid.uuid4()),
                    "full_name": full_name,
                    "email": email,
                    "password": pwd_context.hash("password123"),  # Default password for testing
                    "role": random.choice(["Student", "Professional"]),
                    "location": f"{random.choice(['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad', 'Pune', 'Ahmedabad'])}, India",
                    "university": random.choice(self.universities),
                    "skills": random.sample(self.skills, k=random.randint(2, 4)),
                    "avatar": random.choice(["boy", "man", "girl", "woman"]),
                    "phone": f"+91{random.randint(7000000000, 9999999999)}",
                    "is_active": True,
                    "is_verified": True,
                    "email_verified": True,
                    "created_at": datetime.now(timezone.utc) - timedelta(days=random.randint(1, 180)),
                    "updated_at": datetime.now(timezone.utc),
                    
                    # Initialize gamification fields
                    "level": 1,
                    "title": "Beginner Saver",
                    "experience_points": 0,
                    "current_streak": 0,
                    "net_savings": 0,
                    "total_transactions": 0,
                    "badges_earned": [],
                    "achievements_shared": 0
                }
                
                await self.db.users.insert_one(user_data)
                users_created += 1
                
                if users_created % 20 == 0:
                    logger.info(f"✅ Created {users_created} users...")
                    
            except Exception as e:
                logger.error(f"❌ Error creating user {i}: {str(e)}")
                continue
        
        logger.info(f"🎉 Successfully created {users_created} realistic users!")
        return users_created

    async def create_realistic_transactions(self):
        """Create realistic financial transactions for users"""
        logger.info("💰 Creating realistic financial transactions...")
        
        users = await self.db.users.find({"is_active": True}).to_list(None)
        
        transactions_created = 0
        
        for user in users:
            user_id = user["_id"]
            
            # Create transactions for the last 3 months
            start_date = datetime.now(timezone.utc) - timedelta(days=90)
            
            # Each user gets 15-45 transactions over 3 months
            num_transactions = random.randint(15, 45)
            
            # Generate income transactions (fewer but larger amounts)
            income_transactions = random.randint(3, 8)
            for _ in range(income_transactions):
                transaction_date = start_date + timedelta(days=random.randint(0, 90))
                
                transaction_data = {
                    "_id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "type": "income",
                    "amount": random.randint(2000, 15000),  # ₹2K to ₹15K income
                    "category": random.choice(self.income_sources),
                    "description": f"Income from {random.choice(self.income_sources)}",
                    "date": transaction_date,
                    "created_at": transaction_date
                }
                
                await self.db.transactions.insert_one(transaction_data)
                transactions_created += 1
            
            # Generate expense transactions
            expense_transactions = num_transactions - income_transactions
            for _ in range(expense_transactions):
                transaction_date = start_date + timedelta(days=random.randint(0, 90))
                category = random.choice(self.transaction_categories)
                
                # Realistic expense amounts by category
                amount_ranges = {
                    "Food": (50, 500),
                    "Transportation": (20, 300),
                    "Books": (200, 2000),
                    "Entertainment": (100, 800),
                    "Rent": (3000, 12000),
                    "Utilities": (200, 1500),
                    "Movies": (150, 600),
                    "Shopping": (300, 3000),
                    "Groceries": (200, 1200),
                    "Subscriptions": (99, 999)
                }
                
                min_amt, max_amt = amount_ranges.get(category, (50, 500))
                
                transaction_data = {
                    "_id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "type": "expense",
                    "amount": random.randint(min_amt, max_amt),
                    "category": category,
                    "description": f"Expense for {category.lower()}",
                    "date": transaction_date,
                    "created_at": transaction_date
                }
                
                await self.db.transactions.insert_one(transaction_data)
                transactions_created += 1
            
            # Update user stats
            total_income = await self.db.transactions.aggregate([
                {"$match": {"user_id": user_id, "type": "income"}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]).to_list(None)
            
            total_expenses = await self.db.transactions.aggregate([
                {"$match": {"user_id": user_id, "type": "expense"}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]).to_list(None)
            
            income_total = total_income[0]["total"] if total_income else 0
            expense_total = total_expenses[0]["total"] if total_expenses else 0
            net_savings = max(0, income_total - expense_total)
            
            # Calculate current streak (simplified)
            current_streak = random.randint(0, 15)
            
            await self.db.users.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "net_savings": net_savings,
                        "total_transactions": num_transactions,
                        "current_streak": current_streak,
                        "experience_points": (num_transactions * 5) + (current_streak * 10),
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
        
        logger.info(f"🎉 Created {transactions_created} realistic transactions!")

    async def create_budgets_and_goals(self):
        """Create realistic budgets and financial goals"""
        logger.info("🎯 Creating realistic budgets and financial goals...")
        
        users = await self.db.users.find({"is_active": True}).to_list(None)
        
        budgets_created = 0
        goals_created = 0
        
        for user in users:
            user_id = user["_id"]
            
            # Create 3-7 budget categories for each user
            budget_categories = random.sample(self.transaction_categories, k=random.randint(3, 7))
            
            for category in budget_categories:
                # Realistic budget amounts
                budget_amounts = {
                    "Food": random.randint(2000, 6000),
                    "Transportation": random.randint(1000, 3000),
                    "Books": random.randint(500, 2000),
                    "Entertainment": random.randint(800, 2500),
                    "Rent": random.randint(5000, 15000),
                    "Utilities": random.randint(500, 2000),
                    "Movies": random.randint(300, 1000),
                    "Shopping": random.randint(1000, 4000),
                    "Groceries": random.randint(1500, 4000),
                    "Subscriptions": random.randint(200, 1000)
                }
                
                allocated_amount = budget_amounts.get(category, random.randint(500, 2000))
                
                # Calculate spent amount from actual transactions
                spent_result = await self.db.transactions.aggregate([
                    {"$match": {"user_id": user_id, "type": "expense", "category": category}},
                    {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
                ]).to_list(None)
                
                spent_amount = spent_result[0]["total"] if spent_result else 0
                
                budget_data = {
                    "_id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "category": category,
                    "allocated_amount": allocated_amount,
                    "spent_amount": min(spent_amount, allocated_amount * 1.2),  # Cap at 120% of budget
                    "month": datetime.now(timezone.utc).month,
                    "year": datetime.now(timezone.utc).year,
                    "created_at": datetime.now(timezone.utc)
                }
                
                await self.db.budgets.insert_one(budget_data)
                budgets_created += 1
            
            # Create 1-3 financial goals for each user
            goal_types = ["emergency_fund", "monthly_income", "graduation", "custom"]
            num_goals = random.randint(1, 3)
            
            for _ in range(num_goals):
                goal_type = random.choice(goal_types)
                
                if goal_type == "emergency_fund":
                    target_amount = random.randint(10000, 50000)
                    description = "Emergency fund for unexpected expenses"
                elif goal_type == "monthly_income":
                    target_amount = random.randint(5000, 20000)
                    description = "Monthly income target"
                elif goal_type == "graduation":
                    target_amount = random.randint(50000, 200000)
                    description = "Graduation fund for final year expenses"
                else:  # custom
                    target_amount = random.randint(15000, 100000)
                    descriptions = ["New laptop", "Study abroad fund", "Startup investment", "Course fees"]
                    description = random.choice(descriptions)
                
                current_amount = random.randint(0, int(target_amount * 0.8))
                is_completed = current_amount >= target_amount
                
                goal_data = {
                    "_id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "category": goal_type,
                    "target_amount": target_amount,
                    "current_amount": current_amount,
                    "description": description,
                    "target_date": datetime.now(timezone.utc) + timedelta(days=random.randint(30, 365)),
                    "is_completed": is_completed,
                    "created_at": datetime.now(timezone.utc) - timedelta(days=random.randint(1, 60))
                }
                
                await self.db.financial_goals.insert_one(goal_data)
                goals_created += 1
        
        logger.info(f"🎉 Created {budgets_created} budgets and {goals_created} financial goals!")

    async def populate_leaderboards(self):
        """Populate leaderboards with current user data"""
        logger.info("🏆 Populating leaderboards...")
        
        users = await self.db.users.find({"is_active": True}).to_list(None)
        
        leaderboard_types = ["savings", "streak", "points", "goals"]
        periods = ["weekly", "monthly", "all_time"]
        
        for leaderboard_type in leaderboard_types:
            for period in periods:
                for user in users:
                    score = 0
                    user_id = user["_id"]
                    
                    if leaderboard_type == "savings":
                        if period == "weekly":
                            # Calculate weekly savings
                            week_ago = datetime.now(timezone.utc) - timedelta(days=7)
                            weekly_income = await self._get_transaction_sum(user_id, "income", week_ago)
                            weekly_expenses = await self._get_transaction_sum(user_id, "expense", week_ago)
                            score = max(0, weekly_income - weekly_expenses)
                        elif period == "monthly":
                            # Calculate monthly savings
                            month_ago = datetime.now(timezone.utc) - timedelta(days=30)
                            monthly_income = await self._get_transaction_sum(user_id, "income", month_ago)
                            monthly_expenses = await self._get_transaction_sum(user_id, "expense", month_ago)
                            score = max(0, monthly_income - monthly_expenses)
                        else:
                            score = user.get("net_savings", 0)
                    elif leaderboard_type == "streak":
                        score = user.get("current_streak", 0)
                    elif leaderboard_type == "points":
                        score = user.get("experience_points", 0)
                    elif leaderboard_type == "goals":
                        completed_goals = await self.db.financial_goals.count_documents({
                            "user_id": user_id,
                            "is_completed": True
                        })
                        score = completed_goals
                    
                    # Insert leaderboard entry
                    await self.db.leaderboards.update_one(
                        {
                            "user_id": user_id,
                            "leaderboard_type": leaderboard_type,
                            "period": period,
                            "university": user.get("university")
                        },
                        {
                            "$set": {
                                "score": score,
                                "full_name": user.get("full_name", "Unknown User"),
                                "avatar": user.get("avatar", "boy"),
                                "university": user.get("university", "Unknown University"),
                                "updated_at": datetime.now(timezone.utc),
                                "rank": 0  # Will be calculated next
                            }
                        },
                        upsert=True
                    )
        
        # Calculate ranks for all leaderboards
        for leaderboard_type in leaderboard_types:
            for period in periods:
                entries = await self.db.leaderboards.find({
                    "leaderboard_type": leaderboard_type,
                    "period": period
                }).sort("score", -1).to_list(None)
                
                for i, entry in enumerate(entries):
                    await self.db.leaderboards.update_one(
                        {"_id": entry["_id"]},
                        {"$set": {"rank": i + 1}}
                    )
        
        logger.info("🎉 Leaderboards populated with live rankings!")

    async def _get_transaction_sum(self, user_id: str, transaction_type: str, since_date: datetime) -> float:
        """Get sum of transactions for a user since a date"""
        result = await self.db.transactions.aggregate([
            {
                "$match": {
                    "user_id": user_id,
                    "type": transaction_type,
                    "date": {"$gte": since_date}
                }
            },
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(None)
        
        return result[0]["total"] if result else 0.0

    async def populate_campus_features(self):
        """Populate campus competitions, challenges, and reputation data"""
        logger.info("🏛️ Populating campus features...")
        
        universities = await self.db.users.distinct("university", {"is_active": True})
        
        # Create intercollege competitions
        competitions = [
            {
                "_id": str(uuid.uuid4()),
                "title": "Winter Savings Challenge 2025",
                "description": "Save ₹10,000 this winter and compete with other campuses!",
                "start_date": datetime.now(timezone.utc) - timedelta(days=10),
                "end_date": datetime.now(timezone.utc) + timedelta(days=50),
                "target_amount": 10000,
                "prize_pool": 50000,
                "status": "active",
                "participating_universities": universities,
                "created_at": datetime.now(timezone.utc) - timedelta(days=15)
            },
            {
                "_id": str(uuid.uuid4()),
                "title": "Financial Literacy Sprint",
                "description": "Complete financial goals and track transactions consistently",
                "start_date": datetime.now(timezone.utc) - timedelta(days=20),
                "end_date": datetime.now(timezone.utc) + timedelta(days=30),
                "target_transactions": 30,
                "prize_pool": 30000,
                "status": "active",
                "participating_universities": universities[:15],
                "created_at": datetime.now(timezone.utc) - timedelta(days=25)
            },
            {
                "_id": str(uuid.uuid4()),
                "title": "Budget Masters League",
                "description": "Maintain perfect budget discipline for maximum days",
                "start_date": datetime.now(timezone.utc) - timedelta(days=5),
                "end_date": datetime.now(timezone.utc) + timedelta(days=40),
                "target_streak": 25,
                "prize_pool": 75000,
                "status": "active",
                "participating_universities": universities,
                "created_at": datetime.now(timezone.utc) - timedelta(days=10)
            }
        ]
        
        for comp in competitions:
            await self.db.intercollege_competitions.insert_one(comp)
        
        # Create prize challenges
        challenges = [
            {
                "_id": str(uuid.uuid4()),
                "title": "Emergency Fund Builder",
                "description": "Build your emergency fund to ₹15,000",
                "target_amount": 15000,
                "reward_type": "cash",
                "reward_amount": 2000,
                "participants_count": random.randint(25, 85),
                "max_participants": 100,
                "start_date": datetime.now(timezone.utc) - timedelta(days=15),
                "end_date": datetime.now(timezone.utc) + timedelta(days=75),
                "status": "active",
                "created_at": datetime.now(timezone.utc) - timedelta(days=20)
            },
            {
                "_id": str(uuid.uuid4()),
                "title": "Consistency Champion",
                "description": "Track expenses for 45 consecutive days",
                "target_streak": 45,
                "reward_type": "voucher",
                "reward_amount": 1500,
                "participants_count": random.randint(40, 150),
                "max_participants": 200,
                "start_date": datetime.now(timezone.utc) - timedelta(days=10),
                "end_date": datetime.now(timezone.utc) + timedelta(days=60),
                "status": "active",
                "created_at": datetime.now(timezone.utc) - timedelta(days=15)
            }
        ]
        
        for challenge in challenges:
            await self.db.prize_challenges.insert_one(challenge)
        
        # Populate campus reputation
        for university in universities:
            # Calculate real stats for this university
            user_count = await self.db.users.count_documents({
                "university": university,
                "is_active": True
            })
            
            # Get university's total savings
            university_users = await self.db.users.find({"university": university}).to_list(None)
            total_savings = sum(user.get("net_savings", 0) for user in university_users)
            
            # Calculate achievements (simplified)
            total_goals = await self.db.financial_goals.count_documents({
                "user_id": {"$in": [u["_id"] for u in university_users]},
                "is_completed": True
            })
            
            reputation_score = (user_count * 50) + (total_savings / 100) + (total_goals * 25)
            
            await self.db.campus_reputation.update_one(
                {"university": university},
                {
                    "$set": {
                        "university": university,
                        "reputation_score": reputation_score,
                        "active_users": user_count,
                        "total_savings": total_savings,
                        "achievements_count": total_goals,
                        "rank": 0,  # Will be calculated
                        "trend": random.choice(["up", "down", "stable"]),
                        "updated_at": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
        
        # Calculate campus ranks
        campus_reputations = await self.db.campus_reputation.find().sort("reputation_score", -1).to_list(None)
        for i, campus in enumerate(campus_reputations):
            await self.db.campus_reputation.update_one(
                {"_id": campus["_id"]},
                {"$set": {"rank": i + 1}}
            )
        
        logger.info("🎉 Campus features populated with live data!")

    async def populate_viral_milestones(self):
        """Create realistic viral milestones"""
        logger.info("🎉 Creating viral milestones...")
        
        # Calculate app-wide stats
        total_users = await self.db.users.count_documents({"is_active": True})
        
        all_users = await self.db.users.find({"is_active": True}).to_list(None)
        total_savings = sum(user.get("net_savings", 0) for user in all_users)
        
        milestones = []
        
        # App-wide milestones based on real data
        if total_users >= 50:
            milestones.append({
                "_id": str(uuid.uuid4()),
                "type": "app_wide",
                "milestone": 50,
                "current_value": total_users,
                "achievement_text": f"🚀 {total_users} students are now building financial discipline with EarnNest!",
                "celebration_level": "major" if total_users >= 100 else "minor",
                "created_at": datetime.now(timezone.utc)
            })
        
        if total_savings >= 100000:  # ₹1 lakh
            milestones.append({
                "_id": str(uuid.uuid4()),
                "type": "app_wide",
                "milestone": 100000,
                "current_value": total_savings,
                "achievement_text": f"🇮🇳 Indian students have saved over ₹{total_savings/100000:.1f} lakh collectively!",
                "celebration_level": "major" if total_savings >= 1000000 else "minor",
                "created_at": datetime.now(timezone.utc)
            })
        
        # Campus-specific milestones
        campus_savings = {}
        for user in all_users:
            campus = user.get("university", "Unknown")
            if campus != "Unknown":
                if campus not in campus_savings:
                    campus_savings[campus] = {"savings": 0, "users": 0}
                campus_savings[campus]["savings"] += user.get("net_savings", 0)
                campus_savings[campus]["users"] += 1
        
        for campus, data in campus_savings.items():
            if data["savings"] >= 50000 and data["users"] >= 3:  # ₹50K with at least 3 users
                milestones.append({
                    "_id": str(uuid.uuid4()),
                    "type": "campus",
                    "campus": campus,
                    "milestone": 50000,
                    "current_value": data["savings"],
                    "achievement_text": f"{campus.split(',')[0]} students saved over ₹{data['savings']/1000:.0f}K together! 🎉",
                    "celebration_level": "major" if data["savings"] >= 200000 else "minor",
                    "created_at": datetime.now(timezone.utc)
                })
        
        # Insert milestones
        for milestone in milestones:
            await self.db.viral_milestones.insert_one(milestone)
        
        logger.info(f"🎉 Created {len(milestones)} viral milestones!")

async def main():
    """Main function to populate all production data"""
    populator = ProductionDataPopulator()
    
    try:
        await populator.initialize()
        
        logger.info("🚀 Starting production data population...")
        
        # Step 1: Create realistic users
        users_created = await populator.create_realistic_users(count=150)
        
        # Step 2: Create realistic transactions
        await populator.create_realistic_transactions()
        
        # Step 3: Create budgets and goals
        await populator.create_budgets_and_goals()
        
        # Step 4: Populate leaderboards
        await populator.populate_leaderboards()
        
        # Step 5: Populate campus features
        await populator.populate_campus_features()
        
        # Step 6: Create viral milestones
        await populator.populate_viral_milestones()
        
        logger.info("🎉 Production data population completed successfully!")
        logger.info(f"✅ Summary:")
        logger.info(f"   - Created {users_created} realistic users")
        logger.info(f"   - Generated thousands of transactions")
        logger.info(f"   - Populated all leaderboards")
        logger.info(f"   - Created campus competitions & challenges")
        logger.info(f"   - Generated viral milestones")
        logger.info("🚀 App is now ready for production with live data!")
        
    except Exception as e:
        logger.error(f"❌ Error during production data population: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
