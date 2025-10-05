#!/usr/bin/env python3
"""
Populate Live Leaderboard Data - Production Enhancement Script

This script generates real-time leaderboard data to make the Achievement section
and campus features fully functional with live data instead of empty results.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import logging
from motor.motor_asyncio import AsyncIOMotorClient

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_database, get_user_by_id
from gamification_service import GamificationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LiveLeaderboardPopulator:
    def __init__(self):
        self.db = None
        self.gamification = None

    async def initialize(self):
        """Initialize database connections"""
        self.db = await get_database()
        self.gamification = GamificationService(self.db)
        
    async def populate_live_leaderboards(self):
        """Populate all leaderboards with current live user data"""
        logger.info("🚀 Starting live leaderboard population...")
        
        # Get all active users
        users_cursor = self.db.users.find({"is_active": True})
        users = await users_cursor.to_list(None)
        
        logger.info(f"📊 Found {len(users)} active users to process")
        
        # Leaderboard types to populate
        leaderboard_types = ["savings", "streak", "points", "goals"]
        periods = ["weekly", "monthly", "all_time"]
        
        for user in users:
            try:
                user_id = user["_id"]
                
                # Calculate user statistics for each leaderboard type
                savings_stats = await self._calculate_user_savings(user_id)
                streak_stats = await self._calculate_user_streak(user_id)
                points_stats = await self._calculate_user_points(user_id)
                goals_stats = await self._calculate_user_goals(user_id)
                
                # Update user profile with calculated stats
                await self.db.users.update_one(
                    {"_id": user_id},
                    {
                        "$set": {
                            "net_savings": savings_stats["total"],
                            "current_streak": streak_stats["current"],
                            "experience_points": points_stats["total"],
                            "completed_goals_count": goals_stats["completed"]
                        }
                    }
                )
                
                # Update leaderboards for all types and periods
                for leaderboard_type in leaderboard_types:
                    for period in periods:
                        score = 0
                        if leaderboard_type == "savings":
                            if period == "weekly":
                                score = savings_stats["weekly"]
                            elif period == "monthly":
                                score = savings_stats["monthly"] 
                            else:
                                score = savings_stats["total"]
                        elif leaderboard_type == "streak":
                            score = streak_stats["current"]
                        elif leaderboard_type == "points":
                            score = points_stats["total"]
                        elif leaderboard_type == "goals":
                            score = goals_stats["completed"]
                        
                        # Update leaderboard entry
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
                                    "updated_at": datetime.now(timezone.utc)
                                }
                            },
                            upsert=True
                        )
                
                logger.info(f"✅ Updated leaderboards for {user.get('full_name', user_id)}")
                
            except Exception as e:
                logger.error(f"❌ Error processing user {user_id}: {str(e)}")
                continue
        
        # Recalculate ranks for all leaderboards
        logger.info("🔄 Recalculating leaderboard ranks...")
        for leaderboard_type in leaderboard_types:
            for period in periods:
                await self._recalculate_ranks(leaderboard_type, period)
        
        logger.info("🎉 Live leaderboard population completed!")
        
    async def _calculate_user_savings(self, user_id: str) -> Dict[str, float]:
        """Calculate user's savings statistics"""
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Total savings (income - expenses)
        total_income_pipeline = [
            {"$match": {"user_id": user_id, "type": "income"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        total_expenses_pipeline = [
            {"$match": {"user_id": user_id, "type": "expense"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        
        # Weekly savings
        weekly_income_pipeline = [
            {"$match": {"user_id": user_id, "type": "income", "date": {"$gte": week_ago}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        weekly_expenses_pipeline = [
            {"$match": {"user_id": user_id, "type": "expense", "date": {"$gte": week_ago}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        
        # Monthly savings
        monthly_income_pipeline = [
            {"$match": {"user_id": user_id, "type": "income", "date": {"$gte": month_ago}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        monthly_expenses_pipeline = [
            {"$match": {"user_id": user_id, "type": "expense", "date": {"$gte": month_ago}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        
        # Execute aggregations
        total_income = await self._execute_aggregation(total_income_pipeline)
        total_expenses = await self._execute_aggregation(total_expenses_pipeline)
        weekly_income = await self._execute_aggregation(weekly_income_pipeline)
        weekly_expenses = await self._execute_aggregation(weekly_expenses_pipeline)
        monthly_income = await self._execute_aggregation(monthly_income_pipeline)
        monthly_expenses = await self._execute_aggregation(monthly_expenses_pipeline)
        
        return {
            "total": max(0, total_income - total_expenses),
            "weekly": max(0, weekly_income - weekly_expenses),
            "monthly": max(0, monthly_income - monthly_expenses)
        }
    
    async def _calculate_user_streak(self, user_id: str) -> Dict[str, int]:
        """Calculate user's streak statistics"""
        # Get user's transactions ordered by date
        transactions = await self.db.transactions.find(
            {"user_id": user_id}
        ).sort("date", -1).to_list(None)
        
        if not transactions:
            return {"current": 0, "longest": 0}
        
        # Calculate current streak
        current_streak = 0
        current_date = datetime.now(timezone.utc).date()
        
        # Group transactions by date
        transaction_dates = set()
        for tx in transactions:
            tx_date = tx["date"].date() if hasattr(tx["date"], 'date') else tx["date"]
            transaction_dates.add(tx_date)
        
        # Calculate current streak from today backwards
        check_date = current_date
        while check_date in transaction_dates:
            current_streak += 1
            check_date = check_date - timedelta(days=1)
        
        # If no transaction today, check if there was one yesterday
        if current_streak == 0 and (current_date - timedelta(days=1)) in transaction_dates:
            current_streak = 1
            check_date = current_date - timedelta(days=2)
            while check_date in transaction_dates:
                current_streak += 1
                check_date = check_date - timedelta(days=1)
        
        return {"current": current_streak, "longest": current_streak}  # Simplified for now
    
    async def _calculate_user_points(self, user_id: str) -> Dict[str, int]:
        """Calculate user's experience points"""
        # Points from badges
        user_badges = await self.db.user_badges.find({"user_id": user_id}).to_list(None)
        badge_points = sum(badge.get("points_awarded", 0) for badge in user_badges)
        
        # Points from achievements
        achievements = await self.db.achievements.find({"user_id": user_id}).to_list(None)
        achievement_points = len(achievements) * 10  # 10 points per achievement
        
        # Points from transactions (1 point per transaction)
        transaction_count = await self.db.transactions.count_documents({"user_id": user_id})
        
        total_points = badge_points + achievement_points + transaction_count
        
        return {"total": total_points}
    
    async def _calculate_user_goals(self, user_id: str) -> Dict[str, int]:
        """Calculate user's completed goals"""
        completed_goals = await self.db.financial_goals.count_documents({
            "user_id": user_id,
            "is_completed": True
        })
        
        return {"completed": completed_goals}
    
    async def _execute_aggregation(self, pipeline: List[Dict]) -> float:
        """Execute aggregation pipeline and return result"""
        result = await self.db.transactions.aggregate(pipeline).to_list(None)
        return result[0]["total"] if result and result[0] else 0.0
    
    async def _recalculate_ranks(self, leaderboard_type: str, period: str):
        """Recalculate ranks for a specific leaderboard"""
        # Get all entries sorted by score (descending)
        entries = await self.db.leaderboards.find({
            "leaderboard_type": leaderboard_type,
            "period": period
        }).sort("score", -1).to_list(None)
        
        # Update ranks
        for i, entry in enumerate(entries):
            await self.db.leaderboards.update_one(
                {"_id": entry["_id"]},
                {"$set": {"rank": i + 1}}
            )
    
    async def populate_campus_data(self):
        """Populate campus-specific data for intercollege competitions"""
        logger.info("🏛️ Populating campus competition data...")
        
        # Get all universities
        universities = await self.db.users.distinct("university", {"is_active": True})
        
        # Create intercollege competitions
        competitions = [
            {
                "title": "Winter Savings Challenge 2025",
                "description": "Save ₹10,000 this winter and win exciting prizes!",
                "start_date": datetime.now(timezone.utc),
                "end_date": datetime.now(timezone.utc) + timedelta(days=60),
                "target_amount": 10000,
                "prize_pool": 50000,
                "status": "active",
                "participating_universities": universities[:20],  # Top 20 universities
                "created_at": datetime.now(timezone.utc)
            },
            {
                "title": "Financial Literacy Sprint",
                "description": "Complete 50 transactions and track your spending habits",
                "start_date": datetime.now(timezone.utc) - timedelta(days=15),
                "end_date": datetime.now(timezone.utc) + timedelta(days=45),
                "target_amount": 0,
                "target_transactions": 50,
                "prize_pool": 30000,
                "status": "active",
                "participating_universities": universities,
                "created_at": datetime.now(timezone.utc)
            },
            {
                "title": "Campus Budget Masters",
                "description": "Maintain budget discipline for 30 consecutive days",
                "start_date": datetime.now(timezone.utc) - timedelta(days=10),
                "end_date": datetime.now(timezone.utc) + timedelta(days=35),
                "target_amount": 0,
                "target_streak": 30,
                "prize_pool": 75000,
                "status": "active",
                "participating_universities": universities[:15],
                "created_at": datetime.now(timezone.utc)
            }
        ]
        
        for comp in competitions:
            await self.db.intercollege_competitions.update_one(
                {"title": comp["title"]},
                {"$set": comp},
                upsert=True
            )
        
        # Create prize challenges
        prize_challenges = [
            {
                "title": "Emergency Fund Builder",
                "description": "Build an emergency fund of ₹15,000",
                "target_amount": 15000,
                "reward_type": "cash",
                "reward_amount": 2000,
                "participants_count": 0,
                "max_participants": 100,
                "start_date": datetime.now(timezone.utc),
                "end_date": datetime.now(timezone.utc) + timedelta(days=90),
                "status": "active",
                "created_at": datetime.now(timezone.utc)
            },
            {
                "title": "Expense Tracker Pro",
                "description": "Track expenses for 60 consecutive days",
                "target_streak": 60,
                "reward_type": "voucher",
                "reward_amount": 1500,
                "participants_count": 0,
                "max_participants": 200,
                "start_date": datetime.now(timezone.utc) - timedelta(days=5),
                "end_date": datetime.now(timezone.utc) + timedelta(days=70),
                "status": "active",
                "created_at": datetime.now(timezone.utc)
            },
            {
                "title": "Side Hustle Champion",
                "description": "Earn ₹25,000 through side hustles",
                "target_amount": 25000,
                "reward_type": "cash",
                "reward_amount": 5000,
                "participants_count": 0,
                "max_participants": 50,
                "start_date": datetime.now(timezone.utc),
                "end_date": datetime.now(timezone.utc) + timedelta(days=120),
                "status": "active",
                "created_at": datetime.now(timezone.utc)
            }
        ]
        
        for challenge in prize_challenges:
            await self.db.prize_challenges.update_one(
                {"title": challenge["title"]},
                {"$set": challenge},
                upsert=True
            )
        
        # Populate campus reputation data
        for university in universities[:20]:  # Top 20 universities
            # Calculate university stats
            user_count = await self.db.users.count_documents({
                "university": university,
                "is_active": True
            })
            
            # Get total savings for this university
            savings_pipeline = [
                {
                    "$lookup": {
                        "from": "users",
                        "localField": "user_id", 
                        "foreignField": "_id",
                        "as": "user"
                    }
                },
                {
                    "$match": {
                        "user.university": university,
                        "type": "income"
                    }
                },
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]
            
            total_income = await self._execute_aggregation(savings_pipeline)
            
            reputation_score = (user_count * 10) + (total_income / 1000)
            
            await self.db.campus_reputation.update_one(
                {"university": university},
                {
                    "$set": {
                        "university": university,
                        "reputation_score": reputation_score,
                        "active_users": user_count,
                        "total_savings": total_income,
                        "achievements_count": user_count * 2,  # Estimated
                        "rank": 0,  # Will be calculated later
                        "trend": "up" if reputation_score > 100 else "stable",
                        "updated_at": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
        
        # Calculate campus reputation ranks
        campus_reputations = await self.db.campus_reputation.find().sort("reputation_score", -1).to_list(None)
        for i, campus in enumerate(campus_reputations):
            await self.db.campus_reputation.update_one(
                {"_id": campus["_id"]},
                {"$set": {"rank": i + 1}}
            )
        
        logger.info("✅ Campus competition data populated!")
    
    async def populate_viral_milestones(self):
        """Populate viral milestones data"""
        logger.info("🎉 Populating viral milestones data...")
        
        # Calculate app-wide statistics
        total_users = await self.db.users.count_documents({"is_active": True})
        total_savings_result = await self.db.transactions.aggregate([
            {"$match": {"type": "income"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(None)
        
        total_savings = total_savings_result[0]["total"] if total_savings_result else 0
        
        # Create milestone achievements
        milestones = []
        
        if total_savings >= 1000000:  # 10 lakhs
            milestones.append({
                "type": "app_wide",
                "milestone": 1000000,
                "current_value": total_savings,
                "achievement_text": f"🇮🇳 India's students have collectively saved over ₹{total_savings/100000:.1f} lakhs!",
                "celebration_level": "major" if total_savings >= 5000000 else "minor",
                "created_at": datetime.now(timezone.utc)
            })
        
        if total_users >= 1000:
            milestones.append({
                "type": "app_wide", 
                "milestone": 1000,
                "current_value": total_users,
                "achievement_text": f"🚀 Over {total_users} students are now building financial discipline!",
                "celebration_level": "major" if total_users >= 5000 else "minor",
                "created_at": datetime.now(timezone.utc)
            })
        
        # Campus-specific milestones
        top_campus_pipeline = [
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id", 
                    "as": "user"
                }
            },
            {"$match": {"type": "income", "user.university": {"$ne": None}}},
            {"$group": {"_id": "$user.university", "total_savings": {"$sum": "$amount"}}},
            {"$sort": {"total_savings": -1}},
            {"$limit": 5}
        ]
        
        top_campuses = await self.db.transactions.aggregate(top_campus_pipeline).to_list(None)
        
        for campus in top_campuses:
            if campus["total_savings"] >= 100000:  # 1 lakh
                milestones.append({
                    "type": "campus",
                    "campus": campus["_id"],
                    "milestone": 100000,
                    "current_value": campus["total_savings"],
                    "achievement_text": f"Students saved over ₹{campus['total_savings']/1000:.0f}K together!",
                    "celebration_level": "major" if campus["total_savings"] >= 500000 else "minor",
                    "created_at": datetime.now(timezone.utc)
                })
        
        # Store milestones
        for milestone in milestones:
            await self.db.viral_milestones.update_one(
                {
                    "type": milestone["type"],
                    "milestone": milestone["milestone"],
                    "campus": milestone.get("campus")
                },
                {"$set": milestone},
                upsert=True
            )
        
        logger.info(f"✅ Created {len(milestones)} viral milestones!")

async def main():
    """Main function to populate all live data"""
    populator = LiveLeaderboardPopulator()
    
    try:
        await populator.initialize()
        
        # Populate all live data
        await populator.populate_live_leaderboards()
        await populator.populate_campus_data()
        await populator.populate_viral_milestones()
        
        logger.info("🎉 All live data population completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during population: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
