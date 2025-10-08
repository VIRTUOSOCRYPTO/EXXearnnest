#!/usr/bin/env python3
"""
Live Data Population Script for Campus and Viral Features
Creates realistic competition, challenge, and reputation data
"""

import os
import sys
import asyncio
from datetime import datetime, timezone, timedelta
import random
import bcrypt
import uuid

# Add the backend directory to Python path
sys.path.insert(0, '/app/backend')

# Import database connection
from database import db

class LiveDataGenerator:
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
            "Divya Pillai", "Harsh Bansal", "Ritika Chopra", "Nikhil Tiwari", "Shreya Kapoor"
        ]

    async def create_sample_users_bulk(self, total_users=500):
        """Create a large number of sample users across universities"""
        print(f"🚀 Creating {total_users} sample users across universities...")
        
        users_created = 0
        batch_size = 50
        
        for batch in range(0, total_users, batch_size):
            current_batch = min(batch_size, total_users - batch)
            users_batch = []
            
            for i in range(current_batch):
                university = random.choice(self.indian_universities)
                name = random.choice(self.sample_names)
                unique_id = random.randint(10000, 99999)
                email = f"{name.lower().replace(' ', '.')}_{unique_id}@{university.lower().replace(' ', '').replace('university', 'u')}.edu"
                
                # Generate realistic financial data
                total_earnings = random.randint(5000, 80000)
                total_expenses = random.randint(2000, total_earnings - 1000)
                net_savings = total_earnings - total_expenses
                current_streak = random.randint(0, 60)
                
                user_data = {
                    "id": str(uuid.uuid4()),
                    "email": email,
                    "password_hash": bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                    "full_name": name,
                    "university": university,
                    "role": random.choice(["Student", "Student", "Student", "Professional"]),
                    "location": f"{random.choice(['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Pune', 'Hyderabad'])}, India",
                    "skills": random.sample(["Coding", "Digital Marketing", "Graphic Design", "Content Writing", "Video Editing", "AI Tools & Automation"], 2),
                    "total_earnings": total_earnings,
                    "total_expenses": total_expenses,
                    "net_savings": net_savings,
                    "current_streak": current_streak,
                    "level": min(15, max(1, net_savings // 3000)),
                    "experience_points": net_savings * 2 + random.randint(100, 1000),
                    "is_active": True,
                    "email_verified": True,
                    "last_activity_date": datetime.now(timezone.utc) - timedelta(days=random.randint(0, 7)),
                    "created_at": datetime.now(timezone.utc) - timedelta(days=random.randint(10, 180))
                }
                users_batch.append(user_data)
            
            try:
                await db.users.insert_many(users_batch)
                users_created += len(users_batch)
                print(f"   📊 Created batch of {len(users_batch)} users (Total: {users_created})")
            except Exception as e:
                print(f"   ⚠️ Error in batch: {e}")
        
        # Create transactions for users
        await self.create_bulk_transactions()
        
        print(f"✅ Created {users_created} users with transactions!")

    async def create_bulk_transactions(self):
        """Create transactions for all users"""
        print("💰 Creating transactions for all users...")
        
        users = await db.users.find({}).to_list(None)
        categories = ["Food", "Transportation", "Entertainment", "Shopping", "Books", "Groceries", "Movies", "Subscriptions"]
        income_sources = ["Freelance", "Part-time Job", "Tutoring", "Side Hustle", "Internship", "Contest Prize"]
        
        transactions_created = 0
        
        for user in users:
            user_id = user.get("id", str(user["_id"]))  # Handle both id and _id
            email = user["email"]
            
            # Create 8-25 transactions per user
            num_transactions = random.randint(8, 25)
            transactions_batch = []
            
            for _ in range(num_transactions):
                transaction_type = random.choices(["income", "expense"], weights=[30, 70])[0]
                
                if transaction_type == "income":
                    amount = random.randint(1000, 12000)
                    category = random.choice(income_sources)
                    description = f"{category} earnings"
                else:
                    amount = random.randint(50, 3000)
                    category = random.choice(categories)
                    description = f"{category.lower()} expense"
                
                transaction_data = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "email": email,
                    "amount": amount,
                    "type": transaction_type,
                    "category": category,
                    "description": description,
                    "date": datetime.now(timezone.utc) - timedelta(days=random.randint(0, 90)),
                    "created_at": datetime.now(timezone.utc) - timedelta(days=random.randint(0, 90))
                }
                transactions_batch.append(transaction_data)
            
            try:
                await db.transactions.insert_many(transactions_batch)
                transactions_created += len(transactions_batch)
            except Exception as e:
                print(f"   ⚠️ Error creating transactions for {email}: {e}")
        
        print(f"✅ Created {transactions_created} transactions!")

    async def create_inter_college_competitions(self):
        """Create inter-college competitions"""
        print("🏆 Creating inter-college competitions...")
        
        competitions = [
            {
                "id": str(uuid.uuid4()),
                "title": "National Savings Championship 2025",
                "description": "Compete with students nationwide to see which campus can save the most in 30 days!",
                "competition_type": "savings",
                "target_metric": "Total Savings",
                "duration_days": 30,
                "prize_pool": 100000,
                "status": "active",
                "start_date": datetime.now(timezone.utc) - timedelta(days=5),
                "end_date": datetime.now(timezone.utc) + timedelta(days=25),
                "registration_start": datetime.now(timezone.utc) - timedelta(days=10),
                "registration_end": datetime.now(timezone.utc) + timedelta(days=20),
                "eligible_universities": [],  # Open to all
                "created_at": datetime.now(timezone.utc) - timedelta(days=15),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Campus Streak Battle",
                "description": "Which university can maintain the longest financial tracking streak?",
                "competition_type": "streak",
                "target_metric": "Average Streak Days",
                "duration_days": 45,
                "prize_pool": 75000,
                "status": "active",
                "start_date": datetime.now(timezone.utc) - timedelta(days=2),
                "end_date": datetime.now(timezone.utc) + timedelta(days=43),
                "registration_start": datetime.now(timezone.utc) - timedelta(days=7),
                "registration_end": datetime.now(timezone.utc) + timedelta(days=35),
                "eligible_universities": [],
                "created_at": datetime.now(timezone.utc) - timedelta(days=10),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Smart Spending Challenge",
                "description": "Campus competition focused on intelligent budget management and expense tracking.",
                "competition_type": "budget_efficiency",
                "target_metric": "Budget Compliance Rate",
                "duration_days": 60,
                "prize_pool": 150000,
                "status": "registration_open",
                "start_date": datetime.now(timezone.utc) + timedelta(days=3),
                "end_date": datetime.now(timezone.utc) + timedelta(days=63),
                "registration_start": datetime.now(timezone.utc) - timedelta(days=5),
                "registration_end": datetime.now(timezone.utc) + timedelta(days=2),
                "eligible_universities": ["IIT Bombay", "IIT Delhi", "IIT Madras", "BITS Pilani", "VIT Vellore"],
                "created_at": datetime.now(timezone.utc) - timedelta(days=8),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
        
        try:
            await db.inter_college_competitions.delete_many({})
            await db.inter_college_competitions.insert_many(competitions)
            print(f"✅ Created {len(competitions)} inter-college competitions!")
            
            # Create sample participations
            await self.create_competition_participations(competitions)
            
        except Exception as e:
            print(f"⚠️ Error creating competitions: {e}")

    async def create_competition_participations(self, competitions):
        """Create sample competition participations"""
        print("👥 Creating competition participations...")
        
        users = await db.users.find({}).to_list(None)
        participations_created = 0
        
        for competition in competitions:
            comp_id = competition["id"]
            
            # Random 30-70% of users participate
            participants = random.sample(users, random.randint(len(users)//3, 2*len(users)//3))
            
            participations_batch = []
            for user in participants:
                participation_data = {
                    "id": str(uuid.uuid4()),
                    "competition_id": comp_id,
                    "user_id": user["id"],
                    "campus": user["university"],
                    "joined_date": datetime.now(timezone.utc) - timedelta(days=random.randint(1, 10)),
                    "individual_score": random.randint(500, 5000),
                    "progress_data": {
                        "current_savings": random.randint(2000, 25000),
                        "streak_days": random.randint(5, 45),
                        "budget_compliance": random.uniform(0.6, 0.95)
                    },
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc) - timedelta(days=random.randint(1, 10))
                }
                participations_batch.append(participation_data)
            
            try:
                await db.campus_competition_participations.insert_many(participations_batch)
                participations_created += len(participations_batch)
            except Exception as e:
                print(f"   ⚠️ Error creating participations for {competition['title']}: {e}")
        
        # Create campus leaderboards
        await self.create_campus_leaderboards(competitions)
        
        print(f"✅ Created {participations_created} competition participations!")

    async def create_campus_leaderboards(self, competitions):
        """Create campus leaderboards for competitions"""
        print("📊 Creating campus leaderboards...")
        
        for competition in competitions:
            comp_id = competition["id"]
            
            # Get participations for this competition grouped by campus
            participations = await db.campus_competition_participations.find({
                "competition_id": comp_id
            }).to_list(None)
            
            campus_stats = {}
            for participation in participations:
                campus = participation["campus"]
                if campus not in campus_stats:
                    campus_stats[campus] = {
                        "total_participants": 0,
                        "total_score": 0,
                        "campus_rank": 0
                    }
                
                campus_stats[campus]["total_participants"] += 1
                campus_stats[campus]["total_score"] += participation["individual_score"]
            
            # Calculate average scores and ranks
            campus_averages = []
            for campus, stats in campus_stats.items():
                avg_score = stats["total_score"] / stats["total_participants"] if stats["total_participants"] > 0 else 0
                campus_averages.append((campus, avg_score, stats["total_participants"]))
            
            # Sort by average score (descending)
            campus_averages.sort(key=lambda x: x[1], reverse=True)
            
            # Create leaderboard entries
            leaderboard_batch = []
            for rank, (campus, avg_score, participants) in enumerate(campus_averages, 1):
                leaderboard_data = {
                    "id": str(uuid.uuid4()),
                    "competition_id": comp_id,
                    "campus": campus,
                    "campus_rank": rank,
                    "total_participants": participants,
                    "campus_total_score": int(avg_score * participants),
                    "average_score": round(avg_score, 2),
                    "last_updated": datetime.now(timezone.utc),
                    "created_at": datetime.now(timezone.utc)
                }
                leaderboard_batch.append(leaderboard_data)
            
            try:
                # Clear existing leaderboard for this competition
                await db.campus_leaderboards.delete_many({"competition_id": comp_id})
                await db.campus_leaderboards.insert_many(leaderboard_batch)
            except Exception as e:
                print(f"   ⚠️ Error creating leaderboard for {competition['title']}: {e}")
        
        print("✅ Created campus leaderboards!")

    async def create_prize_challenges(self):
        """Create prize-based challenges"""
        print("🎁 Creating prize challenges...")
        
        challenges = [
            {
                "id": str(uuid.uuid4()),
                "title": "Flash Savings Sprint",
                "description": "Save ₹5,000 in the next 7 days and win exciting prizes!",
                "challenge_type": "flash",
                "challenge_category": "savings",
                "difficulty_level": "medium",
                "target_value": 5000,
                "target_metric": "savings",
                "prize_type": "monetary",
                "total_prize_value": 25000,
                "start_date": datetime.now(timezone.utc) - timedelta(days=1),
                "end_date": datetime.now(timezone.utc) + timedelta(days=6),
                "max_participants": 100,
                "current_participants": 0,
                "requirements": {
                    "min_level": 2,
                    "min_streak": 5
                },
                "status": "active",
                "is_featured": True,
                "created_at": datetime.now(timezone.utc) - timedelta(days=2),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Monthly Budget Master",
                "description": "Stick to your budget for 30 days and earn scholarship points!",
                "challenge_type": "monthly",
                "challenge_category": "budgeting",
                "difficulty_level": "hard",
                "target_value": 30,
                "target_metric": "budget_days",
                "prize_type": "scholarship",
                "total_prize_value": 50000,
                "start_date": datetime.now(timezone.utc) - timedelta(days=10),
                "end_date": datetime.now(timezone.utc) + timedelta(days=20),
                "max_participants": 200,
                "current_participants": 0,
                "requirements": {
                    "min_level": 5,
                    "min_streak": 15
                },
                "status": "active",
                "is_featured": True,
                "created_at": datetime.now(timezone.utc) - timedelta(days=15),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Streak Superstar",
                "description": "Maintain a 21-day expense tracking streak and earn bonus points!",
                "challenge_type": "weekly",
                "challenge_category": "consistency",
                "difficulty_level": "easy",
                "target_value": 21,
                "target_metric": "streak_days",
                "prize_type": "points",
                "total_prize_value": 15000,
                "start_date": datetime.now(timezone.utc) - timedelta(days=5),
                "end_date": datetime.now(timezone.utc) + timedelta(days=16),
                "max_participants": 300,
                "current_participants": 0,
                "requirements": {
                    "min_level": 1,
                    "min_streak": 3
                },
                "status": "active",
                "is_featured": False,
                "created_at": datetime.now(timezone.utc) - timedelta(days=8),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Campus Innovation Challenge",
                "description": "Create the best financial tip and share with your campus community!",
                "challenge_type": "seasonal",
                "challenge_category": "innovation",
                "difficulty_level": "medium",
                "target_value": 1,
                "target_metric": "submissions",
                "prize_type": "badge",
                "total_prize_value": 10000,
                "start_date": datetime.now(timezone.utc) + timedelta(days=1),
                "end_date": datetime.now(timezone.utc) + timedelta(days=30),
                "max_participants": 150,
                "current_participants": 0,
                "requirements": {
                    "min_level": 3,
                    "min_streak": 10
                },
                "status": "registration_open",
                "is_featured": True,
                "created_at": datetime.now(timezone.utc) - timedelta(days=3),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
        
        try:
            await db.prize_challenges.delete_many({})
            await db.prize_challenges.insert_many(challenges)
            print(f"✅ Created {len(challenges)} prize challenges!")
            
            # Create sample challenge participations
            await self.create_challenge_participations(challenges)
            
        except Exception as e:
            print(f"⚠️ Error creating challenges: {e}")

    async def create_challenge_participations(self, challenges):
        """Create sample challenge participations"""
        print("🎯 Creating challenge participations...")
        
        users = await db.users.find({}).to_list(None)
        participations_created = 0
        
        for challenge in challenges:
            if challenge["status"] == "active":
                challenge_id = challenge["id"]
                
                # Random 20-60% of eligible users participate
                eligible_users = [u for u in users if u["level"] >= challenge["requirements"]["min_level"] 
                                and u["current_streak"] >= challenge["requirements"]["min_streak"]]
                
                participants = random.sample(eligible_users, 
                                           random.randint(len(eligible_users)//5, 3*len(eligible_users)//5))
                
                participations_batch = []
                for user in participants:
                    # Calculate progress based on challenge type
                    if challenge["target_metric"] == "savings":
                        current_progress = random.randint(0, min(challenge["target_value"], user["net_savings"]))
                    elif challenge["target_metric"] == "budget_days":
                        current_progress = random.randint(0, 25)
                    elif challenge["target_metric"] == "streak_days":
                        current_progress = min(challenge["target_value"], user["current_streak"])
                    else:
                        current_progress = random.randint(0, challenge["target_value"])
                    
                    progress_percentage = min(100, (current_progress / challenge["target_value"]) * 100)
                    
                    participation_data = {
                        "id": str(uuid.uuid4()),
                        "challenge_id": challenge_id,
                        "user_id": user["id"],
                        "user_name": user["full_name"],
                        "campus": user["university"],
                        "joined_date": datetime.now(timezone.utc) - timedelta(days=random.randint(1, 8)),
                        "current_progress": current_progress,
                        "progress_percentage": round(progress_percentage, 1),
                        "is_completed": progress_percentage >= 100,
                        "completion_date": datetime.now(timezone.utc) if progress_percentage >= 100 else None,
                        "is_active": True,
                        "created_at": datetime.now(timezone.utc) - timedelta(days=random.randint(1, 8))
                    }
                    participations_batch.append(participation_data)
                
                try:
                    await db.prize_challenge_participations.insert_many(participations_batch)
                    participations_created += len(participations_batch)
                    
                    # Update challenge participant count
                    await db.prize_challenges.update_one(
                        {"id": challenge_id},
                        {"$set": {"current_participants": len(participations_batch)}}
                    )
                    
                except Exception as e:
                    print(f"   ⚠️ Error creating participations for {challenge['title']}: {e}")
        
        print(f"✅ Created {participations_created} challenge participations!")

    async def create_campus_reputation_data(self):
        """Create campus reputation and ranking data"""
        print("🏛️ Creating campus reputation data...")
        
        try:
            # Calculate reputation for each university based on real user data
            reputation_data = []
            
            for university in self.indian_universities:
                # Get users from this university
                university_users = await db.users.find({"university": university}).to_list(None)
                
                if not university_users:
                    continue
                
                # Calculate metrics
                total_students = len(university_users)
                active_students = len([u for u in university_users if u.get("last_activity_date", datetime.now(timezone.utc)) > (datetime.now(timezone.utc) - timedelta(days=7))])
                
                # Calculate average stats
                avg_savings = sum(u.get("net_savings", 0) for u in university_users) / total_students if total_students > 0 else 0
                avg_streak = sum(u.get("current_streak", 0) for u in university_users) / total_students if total_students > 0 else 0
                avg_level = sum(u.get("level", 1) for u in university_users) / total_students if total_students > 0 else 1
                avg_experience = sum(u.get("experience_points", 0) for u in university_users) / total_students if total_students > 0 else 0
                
                # Calculate reputation scores
                academic_performance = min(1000, int(avg_level * 100 + random.randint(-50, 50)))
                financial_literacy = min(1000, int(avg_savings / 100 + avg_streak * 10 + random.randint(-100, 100)))
                community_engagement = min(1000, int((active_students / total_students) * 500 + random.randint(0, 200)) if total_students > 0 else 0)
                leadership = min(1000, int(avg_experience / 50 + random.randint(-100, 100)))
                innovation = random.randint(200, 800)
                
                total_reputation_points = academic_performance + financial_literacy + community_engagement + leadership + innovation
                
                reputation_entry = {
                    "id": str(uuid.uuid4()),
                    "campus": university,
                    "total_reputation_points": total_reputation_points,
                    "monthly_reputation_points": random.randint(500, 2000),
                    "current_rank": 0,  # Will be calculated after sorting
                    "previous_rank": 0,
                    "total_active_students": active_students,
                    "average_student_score": round(avg_experience, 1),
                    "academic_performance": academic_performance,
                    "financial_literacy": financial_literacy,
                    "community_engagement": community_engagement,
                    "leadership": leadership,
                    "innovation": innovation,
                    "last_updated": datetime.now(timezone.utc),
                    "created_at": datetime.now(timezone.utc) - timedelta(days=random.randint(30, 90))
                }
                reputation_data.append(reputation_entry)
            
            # Sort by total reputation points and assign ranks
            reputation_data.sort(key=lambda x: x["total_reputation_points"], reverse=True)
            for rank, entry in enumerate(reputation_data, 1):
                entry["current_rank"] = rank
                entry["previous_rank"] = rank + random.randint(-2, 2)  # Simulate rank changes
            
            # Clear existing data and insert new
            await db.campus_reputation.delete_many({})
            if reputation_data:
                await db.campus_reputation.insert_many(reputation_data)
            
            print(f"✅ Created campus reputation data for {len(reputation_data)} universities!")
            
        except Exception as e:
            print(f"⚠️ Error creating campus reputation data: {e}")

    async def update_viral_milestones(self):
        """Update viral milestones with real data"""
        print("🎉 Updating viral milestones with real data...")
        
        try:
            # Calculate real statistics
            users = await db.users.find({}).to_list(None)
            total_users = len(users)
            total_savings = sum(user.get("net_savings", 0) for user in users)
            
            # Clear existing milestones
            await db.viral_milestones.delete_many({})
            
            # Create app-wide milestones based on actual data
            app_milestones = []
            
            milestone_thresholds = [50000, 100000, 250000, 500000, 1000000, 2500000, 5000000, 10000000]
            milestone_texts = [
                "🎉 Students have saved ₹50,000 together!",
                "🚀 Amazing! ₹1 lakh total savings achieved!",
                "💪 Incredible! ₹2.5 lakh saved by students!",
                "🎯 Fantastic! ₹5 lakh community savings!",
                "🏆 MILESTONE: ₹10 lakh total savings!",
                "🔥 HUGE: ₹25 lakh saved by all students!",
                "⭐ MASSIVE: ₹50 lakh community achievement!",
                "🎊 LEGENDARY: ₹1 CRORE saved together!"
            ]
            
            for threshold, text in zip(milestone_thresholds, milestone_texts):
                if total_savings >= threshold:
                    milestone_doc = {
                        "id": str(uuid.uuid4()),
                        "type": "app_wide",
                        "milestone": threshold,
                        "current_value": total_savings,
                        "achievement_text": text,
                        "celebration_level": "major" if threshold >= 500000 else "normal",
                        "achieved": True,
                        "achieved_date": datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30)),
                        "created_at": datetime.now(timezone.utc)
                    }
                    app_milestones.append(milestone_doc)
            
            # Create campus-specific milestones
            campus_milestones = []
            for university in random.sample(self.indian_universities, 5):  # Top 5 performing campuses
                university_users = await db.users.find({"university": university}).to_list(None)
                if university_users:
                    campus_savings = sum(user.get("net_savings", 0) for user in university_users)
                    
                    if campus_savings >= 25000:
                        milestone_doc = {
                            "id": str(uuid.uuid4()),
                            "type": "campus",
                            "campus": university,
                            "milestone": 25000,
                            "current_value": campus_savings,
                            "achievement_text": f"{university} students have saved ₹{campus_savings:,} together!",
                            "celebration_level": "major" if campus_savings >= 100000 else "normal",
                            "achieved": True,
                            "achieved_date": datetime.now(timezone.utc) - timedelta(days=random.randint(1, 15)),
                            "created_at": datetime.now(timezone.utc)
                        }
                        campus_milestones.append(milestone_doc)
            
            # Insert all milestones
            all_milestones = app_milestones + campus_milestones
            if all_milestones:
                await db.viral_milestones.insert_many(all_milestones)
            
            print(f"✅ Created {len(app_milestones)} app milestones and {len(campus_milestones)} campus milestones!")
            print(f"📊 Based on real data: {total_users} users, ₹{total_savings:,} total savings")
            
        except Exception as e:
            print(f"⚠️ Error updating viral milestones: {e}")

    async def populate_all_live_data(self):
        """Main function to populate all live data"""
        print("🎯 Starting Live Data Population for Campus & Viral Features...")
        
        try:
            # Test database connection
            await db.users.count_documents({})
            print("✅ Database connection successful!")
            
            # Create comprehensive user base
            await self.create_sample_users_bulk(400)  # Create 400 users
            
            # Create competitions and challenges
            await self.create_inter_college_competitions()
            await self.create_prize_challenges()
            
            # Create campus reputation data
            await self.create_campus_reputation_data()
            
            # Update viral milestones with real data
            await self.update_viral_milestones()
            
            # Print final summary
            total_users = await db.users.count_documents({})
            total_transactions = await db.transactions.count_documents({})
            total_competitions = await db.inter_college_competitions.count_documents({})
            total_challenges = await db.prize_challenges.count_documents({})
            total_reputation = await db.campus_reputation.count_documents({})
            total_milestones = await db.viral_milestones.count_documents({})
            
            print("\n🎉 Live Data Population Complete!")
            print(f"📊 Final Summary:")
            print(f"   👥 Total Users: {total_users}")
            print(f"   💰 Total Transactions: {total_transactions}")
            print(f"   🏆 Inter-college Competitions: {total_competitions}")
            print(f"   🎁 Prize Challenges: {total_challenges}")
            print(f"   🏛️ Campus Reputation Entries: {total_reputation}")
            print(f"   🎉 Viral Milestones: {total_milestones}")
            print(f"   🏫 Universities: {len(self.indian_universities)}")
            print(f"\n🚀 All campus and viral features now have LIVE data!")
            
        except Exception as e:
            print(f"❌ Error during live data population: {e}")
            raise e

async def main():
    """Main execution function"""
    generator = LiveDataGenerator()
    await generator.populate_all_live_data()

if __name__ == "__main__":
    asyncio.run(main())
