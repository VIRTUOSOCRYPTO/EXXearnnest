import os
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from database import get_database, get_user_by_id
import logging

logger = logging.getLogger(__name__)

class GamificationService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    # ===== BADGE SYSTEM =====
    
    async def initialize_badges(self):
        """Initialize default badges in the database"""
        default_badges = [
            # Financial Achievements
            {
                "name": "First Saver",
                "description": "Saved your first ₹100",
                "category": "financial",
                "icon": "💰",
                "rarity": "bronze",
                "requirement_type": "amount_saved",
                "requirement_value": 100.0,
                "points_awarded": 10,
                "is_active": True
            },
            {
                "name": "Thrifty Thousand",
                "description": "Saved ₹1,000",
                "category": "financial",
                "icon": "🏆",
                "rarity": "silver",
                "requirement_type": "amount_saved",
                "requirement_value": 1000.0,
                "points_awarded": 50,
                "is_active": True
            },
            {
                "name": "Budget Boss",
                "description": "Stayed within budget for 7 consecutive days",
                "category": "behavioral",
                "icon": "📊",
                "rarity": "gold",
                "requirement_type": "budget_streak",
                "requirement_value": 7.0,
                "points_awarded": 100,
                "is_active": True
            },
            {
                "name": "Goal Crusher",
                "description": "Completed your first financial goal",
                "category": "financial",
                "icon": "🎯",
                "rarity": "gold",
                "requirement_type": "goals_completed",
                "requirement_value": 1.0,
                "points_awarded": 150,
                "is_active": True
            },
            {
                "name": "Hustle Hero",
                "description": "Completed your first side hustle",
                "category": "side_hustle",
                "icon": "💼",
                "rarity": "silver",
                "requirement_type": "hustles_completed",
                "requirement_value": 1.0,
                "points_awarded": 75,
                "is_active": True
            },
            {
                "name": "Social Saver",
                "description": "Shared 5 achievements with the community",
                "category": "social",
                "icon": "📱",
                "rarity": "silver",
                "requirement_type": "achievements_shared",
                "requirement_value": 5.0,
                "points_awarded": 50,
                "is_active": True
            },
            {
                "name": "Streak Master",
                "description": "Maintained 30-day tracking streak",
                "category": "behavioral",
                "icon": "🔥",
                "rarity": "platinum",
                "requirement_type": "streak_days",
                "requirement_value": 30.0,
                "points_awarded": 200,
                "is_active": True
            },
            {
                "name": "Campus Champion",
                "description": "Top 10 in your university's leaderboard",
                "category": "social",
                "icon": "🏅",
                "rarity": "gold",
                "requirement_type": "campus_rank",
                "requirement_value": 10.0,
                "points_awarded": 150,
                "is_active": True
            },
            {
                "name": "Five Figure Finisher",
                "description": "Saved ₹10,000",
                "category": "financial",
                "icon": "💎",
                "rarity": "platinum",
                "requirement_type": "amount_saved",
                "requirement_value": 10000.0,
                "points_awarded": 250,
                "is_active": True
            },
            {
                "name": "Legendary Saver",
                "description": "Saved ₹1,00,000",
                "category": "financial",
                "icon": "👑",
                "rarity": "legendary",
                "requirement_type": "amount_saved",
                "requirement_value": 100000.0,
                "points_awarded": 500,
                "is_active": True
            }
        ]
        
        for badge_data in default_badges:
            # Check if badge already exists
            existing_badge = await self.db.badges.find_one({"name": badge_data["name"]})
            if not existing_badge:
                badge_data["created_at"] = datetime.now(timezone.utc)
                await self.db.badges.insert_one(badge_data)
                logger.info(f"Initialized badge: {badge_data['name']}")

    async def check_and_award_badges(self, user_id: str, event_type: str, event_data: Dict[str, Any]):
        """Check if user has earned new badges based on an event"""
        user = await get_user_by_id(user_id)
        if not user:
            return []
        
        # Get all active badges
        badges = await self.db.badges.find({"is_active": True}).to_list(None)
        
        # Get user's current badges
        user_badges = await self.db.user_badges.find({"user_id": user_id}).to_list(None)
        earned_badge_ids = [ub["badge_id"] for ub in user_badges]
        
        newly_earned_badges = []
        
        for badge in badges:
            # Convert badge ObjectId to string for comparison
            badge_id_str = str(badge["_id"])
            if badge_id_str in earned_badge_ids:
                continue  # User already has this badge
                
            if await self._check_badge_requirement(user, badge, event_type, event_data):
                # Award the badge
                user_badge = {
                    "user_id": user_id,
                    "badge_id": str(badge["_id"]),
                    "earned_at": datetime.now(timezone.utc),
                    "progress_when_earned": {
                        "net_savings": user.get("net_savings", 0),
                        "current_streak": user.get("current_streak", 0),
                        "total_earnings": user.get("total_earnings", 0),
                        "experience_points": user.get("experience_points", 0)
                    },
                    "is_showcased": len(newly_earned_badges) == 0,  # Showcase first earned badge
                    "shared_count": 0
                }
                
                await self.db.user_badges.insert_one(user_badge)
                
                # Update user's experience points
                new_experience = user.get("experience_points", 0) + badge["points_awarded"]
                new_level, new_title = self._calculate_level_and_title(new_experience)
                
                await self.db.users.update_one(
                    {"_id": user["_id"]},
                    {
                        "$set": {
                            "experience_points": new_experience,
                            "level": new_level,
                            "title": new_title
                        }
                    }
                )
                
                # Create achievement record
                achievement = {
                    "user_id": user_id,
                    "type": "badge_earned",
                    "title": f"Earned {badge['name']} Badge!",
                    "description": badge["description"],
                    "icon": badge["icon"],
                    "achievement_data": {
                        "badge_id": str(badge["_id"]),
                        "badge_name": badge["name"],
                        "badge_rarity": badge["rarity"],
                        "points_earned": badge["points_awarded"]
                    },
                    "points_earned": badge["points_awarded"],
                    "created_at": datetime.now(timezone.utc),
                    "is_shared": False,
                    "reaction_count": 0
                }
                
                result = await self.db.achievements.insert_one(achievement)
                badge["achievement_id"] = str(result.inserted_id)
                newly_earned_badges.append(badge)
                
                logger.info(f"User {user_id} earned badge: {badge['name']}")
        
        return newly_earned_badges

    async def _check_badge_requirement(self, user: Dict, badge: Dict, event_type: str, event_data: Dict) -> bool:
        """Check if user meets the requirement for a specific badge"""
        requirement_type = badge["requirement_type"]
        requirement_value = badge["requirement_value"]
        
        if requirement_type == "amount_saved":
            return user.get("net_savings", 0) >= requirement_value
            
        elif requirement_type == "streak_days":
            return user.get("current_streak", 0) >= requirement_value
            
        elif requirement_type == "goals_completed":
            completed_goals = await self.db.financial_goals.count_documents({
                "user_id": user["_id"],
                "is_completed": True
            })
            return completed_goals >= requirement_value
            
        elif requirement_type == "hustles_completed":
            # Count applications that were accepted/completed
            completed_hustles = await self.db.hustle_applications.count_documents({
                "user_id": user["_id"],
                "status": "accepted"  # or you might have a "completed" status
            })
            return completed_hustles >= requirement_value
            
        elif requirement_type == "achievements_shared":
            return user.get("achievements_shared", 0) >= requirement_value
            
        elif requirement_type == "campus_rank":
            # Check if user is in top N in their campus leaderboard
            if not user.get("university"):
                return False
            rank = await self._get_user_campus_rank(user["_id"], user["university"])
            return rank <= requirement_value if rank else False
            
        elif requirement_type == "budget_streak":
            # Check if user has maintained budget for consecutive days
            # This would need more complex logic based on transaction history
            return await self._check_budget_streak(user["_id"], requirement_value)
        
        return False

    def _calculate_level_and_title(self, experience_points: int) -> tuple:
        """Calculate user level and title based on experience points"""
        level = 1 + (experience_points // 100)  # Every 100 XP = 1 level
        
        if level <= 5:
            title = "Beginner"
        elif level <= 10:
            title = "Saver"
        elif level <= 20:
            title = "Budget Master"
        elif level <= 35:
            title = "Financial Guru"
        elif level <= 50:
            title = "Money Manager"
        else:
            title = "Legendary Financer"
        
        return level, title

    # ===== LEADERBOARD SYSTEM =====
    
    async def update_leaderboards(self, user_id: str):
        """Update all relevant leaderboards for a user"""
        user = await get_user_by_id(user_id)
        if not user:
            return
        
        leaderboard_types = ["savings", "streak", "goals", "points"]
        periods = ["weekly", "monthly", "all_time"]
        
        for lb_type in leaderboard_types:
            for period in periods:
                await self._update_user_leaderboard_entry(user, lb_type, period)
                
                # Also update campus-specific leaderboard if user has university
                if user.get("university"):
                    await self._update_user_leaderboard_entry(user, lb_type, period, user["university"])

    async def _update_user_leaderboard_entry(self, user: Dict, leaderboard_type: str, period: str, university: Optional[str] = None):
        """Update a specific leaderboard entry for a user"""
        score = await self._calculate_leaderboard_score(user, leaderboard_type, period)
        
        # Update or create leaderboard entry
        await self.db.leaderboards.update_one(
            {
                "user_id": user["_id"],
                "leaderboard_type": leaderboard_type,
                "period": period,
                "university": university
            },
            {
                "$set": {
                    "score": score,
                    "updated_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        
        # Recalculate ranks for this leaderboard
        await self._recalculate_leaderboard_ranks(leaderboard_type, period, university)

    async def _calculate_leaderboard_score(self, user: Dict, leaderboard_type: str, period: str) -> float:
        """Calculate score for a user in a specific leaderboard"""
        if leaderboard_type == "savings":
            return user.get("net_savings", 0)
        elif leaderboard_type == "streak":
            return user.get("current_streak", 0)
        elif leaderboard_type == "points":
            return user.get("experience_points", 0)
        elif leaderboard_type == "goals":
            completed_goals = await self.db.financial_goals.count_documents({
                "user_id": user["_id"],
                "is_completed": True
            })
            return completed_goals
        
        return 0.0

    async def _recalculate_leaderboard_ranks(self, leaderboard_type: str, period: str, university: Optional[str] = None):
        """Recalculate ranks for a specific leaderboard"""
        filter_query = {
            "leaderboard_type": leaderboard_type,
            "period": period
        }
        if university:
            filter_query["university"] = university
        
        # Get all entries sorted by score (descending)
        entries = await self.db.leaderboards.find(filter_query).sort("score", -1).to_list(None)
        
        # Update ranks
        for i, entry in enumerate(entries):
            await self.db.leaderboards.update_one(
                {"_id": entry["_id"]},
                {"$set": {"rank": i + 1}}
            )

    async def get_leaderboard(self, leaderboard_type: str, period: str = "all_time", university: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """Get leaderboard rankings"""
        filter_query = {
            "leaderboard_type": leaderboard_type,
            "period": period
        }
        if university:
            filter_query["university"] = university
        
        # Get top entries
        entries = await self.db.leaderboards.find(filter_query).sort("rank", 1).limit(limit).to_list(None)
        
        # Get user details for each entry
        rankings = []
        for entry in entries:
            user = await get_user_by_id(entry["user_id"])
            if user:
                rankings.append({
                    "rank": entry["rank"],
                    "user_id": entry["user_id"],
                    "full_name": user.get("full_name", "Unknown"),
                    "avatar": user.get("avatar", "boy"),
                    "university": user.get("university"),
                    "level": user.get("level", 1),
                    "title": user.get("title", "Beginner"),
                    "score": entry["score"]
                })
        
        total_participants = await self.db.leaderboards.count_documents(filter_query)
        
        return {
            "leaderboard_type": leaderboard_type,
            "period": period,
            "university": university,
            "rankings": rankings,
            "total_participants": total_participants
        }

    async def get_user_rank(self, user_id: str, leaderboard_type: str, period: str = "all_time", university: Optional[str] = None) -> Optional[int]:
        """Get user's rank in a specific leaderboard"""
        filter_query = {
            "user_id": user_id,
            "leaderboard_type": leaderboard_type,
            "period": period
        }
        if university:
            filter_query["university"] = university
        
        entry = await self.db.leaderboards.find_one(filter_query)
        return entry["rank"] if entry else None

    async def _get_user_campus_rank(self, user_id: str, university: str) -> Optional[int]:
        """Get user's overall campus rank (based on points)"""
        return await self.get_user_rank(user_id, "points", "all_time", university)

    # ===== ACHIEVEMENT SYSTEM =====
    
    async def create_milestone_achievement(self, user_id: str, milestone_type: str, milestone_data: Dict[str, Any]):
        """Create a milestone achievement (not badge-related)"""
        achievement_templates = {
            "first_transaction": {
                "title": "First Step!",
                "description": "Recorded your first transaction",
                "icon": "🎉",
                "points": 5
            },
            "first_budget": {
                "title": "Budget Planner",
                "description": "Created your first budget",
                "icon": "📋",
                "points": 10
            },
            "goal_progress_50": {
                "title": "Halfway Hero",
                "description": "Reached 50% of a financial goal",
                "icon": "⭐",
                "points": 25
            }
        }
        
        if milestone_type not in achievement_templates:
            return None
        
        template = achievement_templates[milestone_type]
        
        achievement = {
            "user_id": user_id,
            "type": "milestone_reached",
            "title": template["title"],
            "description": template["description"],
            "icon": template["icon"],
            "achievement_data": milestone_data,
            "points_earned": template["points"],
            "created_at": datetime.now(timezone.utc),
            "is_shared": False,
            "reaction_count": 0
        }
        
        result = await self.db.achievements.insert_one(achievement)
        
        # Update user's experience points
        await self.db.users.update_one(
            {"_id": user_id},
            {"$inc": {"experience_points": template["points"]}}
        )
        
        return str(result.inserted_id)

    # ===== STREAK TRACKING =====
    
    async def update_user_streak(self, user_id: str):
        """Update user's activity streak"""
        user = await get_user_by_id(user_id)
        if not user:
            return
        
        today = datetime.now(timezone.utc).date()
        last_activity_date = user.get("last_activity_date")
        
        if last_activity_date:
            last_date = last_activity_date.date() if isinstance(last_activity_date, datetime) else last_activity_date
            
            if last_date == today:
                # Already active today, no change needed
                return
            elif last_date == today - timedelta(days=1):
                # Consecutive day, increment streak
                new_streak = user.get("current_streak", 0) + 1
            else:
                # Streak broken, reset to 1
                new_streak = 1
        else:
            # First activity ever
            new_streak = 1
        
        # Update user's streak and last activity date
        await self.db.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "current_streak": new_streak,
                    "last_activity_date": datetime.now(timezone.utc)
                }
            }
        )
        
        # Check for streak-related badges
        await self.check_and_award_badges(user_id, "streak_updated", {"new_streak": new_streak})

    # ===== UTILITY METHODS =====
    
    async def _check_budget_streak(self, user_id: str, required_days: float) -> bool:
        """Check if user has maintained budget for consecutive days"""
        # This is a simplified implementation
        # In a real app, you'd analyze transaction history vs budget allocations
        # end_date = datetime.now(timezone.utc)
        # start_date = end_date - timedelta(days=int(required_days))
        
        # Count days where expenses were within budget
        # This would need more complex logic based on your specific requirements
        return True  # Placeholder - implement based on your budget tracking logic

    async def get_user_gamification_profile(self, user_id: str) -> Dict[str, Any]:
        """Get complete gamification profile for a user"""
        user = await get_user_by_id(user_id)
        if not user:
            return {}
        
        # Get user's badges
        user_badges = await self.db.user_badges.find({"user_id": user_id}).to_list(None)
        badge_details = []
        for user_badge in user_badges:
            # Convert badge_id to ObjectId if it's a string
            badge_id = user_badge["badge_id"]
            if isinstance(badge_id, str):
                badge_id = ObjectId(badge_id)
            
            badge = await self.db.badges.find_one({"_id": badge_id})
            if badge:
                badge_details.append({
                    "badge_id": str(badge["_id"]),
                    "name": badge["name"],
                    "description": badge["description"],
                    "icon": badge["icon"],
                    "rarity": badge["rarity"],
                    "earned_at": user_badge["earned_at"],
                    "is_showcased": user_badge.get("is_showcased", False)
                })
        
        # Get recent achievements
        recent_achievements = await self.db.achievements.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(5).to_list(None)
        
        # Get user's ranks in different leaderboards
        ranks = {}
        university = user.get("university")
        for lb_type in ["savings", "streak", "goals", "points"]:
            ranks[lb_type] = await self.get_user_rank(user_id, lb_type)
            if university:
                ranks[f"{lb_type}_campus"] = await self.get_user_rank(user_id, lb_type, university=university)
        
        return {
            "level": user.get("level", 1),
            "title": user.get("title", "Beginner"),
            "experience_points": user.get("experience_points", 0),
            "current_streak": user.get("current_streak", 0),
            "badges": badge_details,
            "recent_achievements": recent_achievements,
            "ranks": ranks,
            "total_badges": len(badge_details),
            "achievements_shared": user.get("achievements_shared", 0)
        }

# Global instance
gamification_service = None

async def get_gamification_service() -> GamificationService:
    global gamification_service
    if gamification_service is None:
        db = await get_database()
        gamification_service = GamificationService(db)
        # Initialize default badges
        await gamification_service.initialize_badges()
    return gamification_service
