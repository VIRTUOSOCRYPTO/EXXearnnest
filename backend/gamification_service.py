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
            # Enhanced Streak System - Phase 1 Gamification
            {
                "name": "Week Warrior",
                "description": "Maintained 7-day tracking streak",
                "category": "behavioral", 
                "icon": "🔥",
                "rarity": "bronze",
                "requirement_type": "streak_days",
                "requirement_value": 7.0,
                "points_awarded": 50,
                "is_active": True,
                "milestone_tier": 1,
                "special_perks": []
            },
            {
                "name": "Fortnight Fighter",
                "description": "Maintained 15-day tracking streak",
                "category": "behavioral",
                "icon": "🌟",
                "rarity": "silver",
                "requirement_type": "streak_days", 
                "requirement_value": 15.0,
                "points_awarded": 100,
                "is_active": True,
                "milestone_tier": 2,
                "special_perks": []
            },
            {
                "name": "Month Master",
                "description": "Maintained 30-day tracking streak",
                "category": "behavioral",
                "icon": "👑",
                "rarity": "gold",
                "requirement_type": "streak_days",
                "requirement_value": 30.0,
                "points_awarded": 250,
                "is_active": True,
                "milestone_tier": 3,
                "special_perks": ["referral_boost", "profile_highlight"]
            },
            {
                "name": "Consistency King",
                "description": "Maintained 60-day tracking streak",
                "category": "behavioral",
                "icon": "💎",
                "rarity": "platinum",
                "requirement_type": "streak_days",
                "requirement_value": 60.0,
                "points_awarded": 500,
                "is_active": True,
                "milestone_tier": 4,
                "special_perks": ["referral_boost", "profile_highlight", "priority_support"]
            },
            {
                "name": "Legendary Streaker",
                "description": "Maintained 100-day tracking streak",
                "category": "behavioral",
                "icon": "🏆",
                "rarity": "legendary",
                "requirement_type": "streak_days",
                "requirement_value": 100.0,
                "points_awarded": 1000,
                "is_active": True,
                "milestone_tier": 5,
                "special_perks": ["referral_boost", "profile_highlight", "priority_support", "exclusive_features"]
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
        """Get leaderboard rankings - ensures each user appears only once"""
        
        if university:
            # If university is specified, get only university-specific entries
            filter_query = {
                "leaderboard_type": leaderboard_type,
                "period": period,
                "university": university
            }
        else:
            # For global leaderboard, use aggregation to get unique users with best scores
            # Prioritize university-specific entries over global entries
            pipeline = [
                {
                    "$match": {
                        "leaderboard_type": leaderboard_type,
                        "period": period
                    }
                },
                {
                    "$sort": {
                        "user_id": 1,
                        "university": 1,  # Prioritize university-specific (non-null) entries
                        "score": -1
                    }
                },
                {
                    "$group": {
                        "_id": "$user_id",  # Group by user_id to ensure uniqueness
                        "score": {"$first": "$score"},
                        "university": {"$first": "$university"},
                        "updated_at": {"$first": "$updated_at"},
                        "leaderboard_type": {"$first": "$leaderboard_type"},
                        "period": {"$first": "$period"}
                    }
                },
                {
                    "$sort": {"score": -1}  # Sort by score descending
                },
                {
                    "$limit": limit
                }
            ]
            
            entries = await self.db.leaderboards.aggregate(pipeline).to_list(None)
            
            # Convert aggregation results to match expected format
            formatted_entries = []
            for i, entry in enumerate(entries):
                formatted_entries.append({
                    "user_id": entry["_id"],
                    "score": entry["score"],
                    "rank": i + 1,  # Assign sequential ranks
                    "university": entry.get("university"),
                    "leaderboard_type": entry["leaderboard_type"],
                    "period": entry["period"]
                })
            entries = formatted_entries
        
        if university:
            # For university-specific queries, use the original method
            entries = await self.db.leaderboards.find(filter_query).sort("rank", 1).limit(limit).to_list(None)
        
        # Get user details for each entry
        rankings = []
        seen_users = set()  # Extra safety to prevent duplicates
        
        for entry in entries:
            user_id = str(entry["user_id"])
            
            # Skip if we've already seen this user (extra safety check)
            if user_id in seen_users:
                continue
            seen_users.add(user_id)
            
            # Try to get user by _id (ObjectId) first, then by id (UUID string)
            user = await self.db.users.find_one({"_id": entry["user_id"]})
            if not user and isinstance(entry["user_id"], str):
                user = await get_user_by_id(entry["user_id"])
            
            if user:
                rankings.append({
                    "rank": entry["rank"],
                    "user_id": user_id,
                    "full_name": user.get("full_name", "Unknown"),
                    "avatar": user.get("avatar", "boy"),
                    "university": user.get("university"),
                    "level": user.get("level", 1),
                    "title": user.get("title", "Beginner"),
                    "score": entry["score"]
                })
        
        # Re-rank the final results to ensure proper sequential ranking
        for i, ranking in enumerate(rankings):
            ranking["rank"] = i + 1
        
        total_participants = len(rankings)
        
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

    # ===== ENHANCED STREAK TRACKING - PHASE 1 =====
    
    async def update_user_streak(self, user_id: str):
        """Update user's activity streak with enhanced milestone detection"""
        user = await get_user_by_id(user_id)
        if not user:
            return
        
        today = datetime.now(timezone.utc).date()
        last_activity_date = user.get("last_activity_date")
        old_streak = user.get("current_streak", 0)
        
        if last_activity_date:
            last_date = last_activity_date.date() if isinstance(last_activity_date, datetime) else last_activity_date
            
            if last_date == today:
                # Already active today, no change needed
                return
            elif last_date == today - timedelta(days=1):
                # Consecutive day, increment streak
                new_streak = old_streak + 1
            else:
                # Streak broken, reset to 1
                new_streak = 1
                # Create streak break notification
                await self._create_streak_break_notification(user_id, old_streak, (today - last_date).days)
        else:
            # First activity ever
            new_streak = 1
        
        # Update user's streak and last activity date
        await self.db.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "current_streak": new_streak,
                    "last_activity_date": datetime.now(timezone.utc),
                    "longest_streak": max(user.get("longest_streak", 0), new_streak)
                }
            }
        )
        
        # Check for milestone achievements
        milestone_reached = await self._check_streak_milestones(user_id, old_streak, new_streak)
        
        # Check for streak-related badges
        newly_earned_badges = await self.check_and_award_badges(user_id, "streak_updated", {"new_streak": new_streak})
        
        # Return milestone and badge data for immediate celebration
        return {
            "old_streak": old_streak,
            "new_streak": new_streak,
            "milestone_reached": milestone_reached,
            "badges_earned": newly_earned_badges,
            "longest_streak": max(user.get("longest_streak", 0), new_streak)
        }

    async def _check_streak_milestones(self, user_id: str, old_streak: int, new_streak: int) -> Dict[str, Any]:
        """Check if user hit a new streak milestone"""
        milestone_thresholds = [7, 15, 30, 60, 100]
        
        for threshold in milestone_thresholds:
            if old_streak < threshold <= new_streak:
                # User just hit this milestone
                milestone_data = {
                    "type": "streak",
                    "threshold": threshold,
                    "current_streak": new_streak,
                    "title": self._get_streak_milestone_title(threshold),
                    "message": self._get_streak_milestone_message(threshold),
                    "icon": self._get_streak_milestone_icon(threshold),
                    "special_perks": self._get_streak_milestone_perks(threshold)
                }
                
                # Create milestone achievement
                achievement_id = await self.create_streak_milestone_achievement(user_id, milestone_data)
                milestone_data["achievement_id"] = achievement_id
                
                # Create celebration notification
                await self._create_milestone_notification(user_id, milestone_data)
                
                return milestone_data
        
        return {}

    def _get_streak_milestone_title(self, threshold: int) -> str:
        """Get title for streak milestone"""
        titles = {
            7: "Week Warrior Achievement!",
            15: "Fortnight Fighter!",
            30: "Month Master!",
            60: "Consistency King!",
            100: "Legendary Streaker!"
        }
        return titles.get(threshold, f"{threshold}-Day Streak!")

    def _get_streak_milestone_message(self, threshold: int) -> str:
        """Get motivational message for streak milestone"""
        messages = {
            7: "You've built a solid habit! Keep the momentum going! 🔥",
            15: "Two weeks of consistency! You're on fire! 🌟",
            30: "A full month of tracking! You've unlocked special perks! 👑",
            60: "60 days of dedication! You're a consistency champion! 💎",
            100: "100 days! You're officially a legendary user! 🏆"
        }
        return messages.get(threshold, f"Amazing! {threshold} consecutive days!")

    def _get_streak_milestone_icon(self, threshold: int) -> str:
        """Get icon for streak milestone"""
        icons = {7: "🔥", 15: "🌟", 30: "👑", 60: "💎", 100: "🏆"}
        return icons.get(threshold, "🎯")

    def _get_streak_milestone_perks(self, threshold: int) -> List[str]:
        """Get special perks for streak milestone"""
        perks = {
            30: ["referral_boost", "profile_highlight"],
            60: ["referral_boost", "profile_highlight", "priority_support"],
            100: ["referral_boost", "profile_highlight", "priority_support", "exclusive_features"]
        }
        return perks.get(threshold, [])

    async def create_streak_milestone_achievement(self, user_id: str, milestone_data: Dict[str, Any]) -> str:
        """Create a streak milestone achievement"""
        # Calculate points based on milestone
        points_map = {7: 50, 15: 100, 30: 250, 60: 500, 100: 1000}
        points = points_map.get(milestone_data["threshold"], 25)
        
        achievement = {
            "user_id": user_id,
            "type": "streak_milestone",
            "title": milestone_data["title"],
            "description": milestone_data["message"],
            "icon": milestone_data["icon"],
            "achievement_data": {
                "milestone_type": "streak",
                "threshold": milestone_data["threshold"],
                "current_streak": milestone_data["current_streak"],
                "special_perks": milestone_data["special_perks"]
            },
            "points_earned": points,
            "created_at": datetime.now(timezone.utc),
            "is_shared": False,
            "reaction_count": 0,
            "celebration_data": {
                "should_celebrate": True,
                "celebration_type": "milestone_popup",
                "celebration_priority": "high" if milestone_data["threshold"] >= 30 else "normal"
            }
        }
        
        result = await self.db.achievements.insert_one(achievement)
        
        # Update user's experience points
        await self.db.users.update_one(
            {"_id": user_id},
            {"$inc": {"experience_points": points}}
        )
        
        return str(result.inserted_id)

    async def _create_milestone_notification(self, user_id: str, milestone_data: Dict[str, Any]):
        """Create in-app notification for milestone achievement"""
        notification = {
            "user_id": user_id,
            "type": "milestone_achieved",
            "title": milestone_data["title"],
            "message": milestone_data["message"],
            "icon": milestone_data["icon"],
            "action_url": f"/gamification?celebrate={milestone_data.get('achievement_id', '')}",
            "data": {
                "milestone_type": milestone_data["type"],
                "threshold": milestone_data["threshold"],
                "achievement_id": milestone_data.get("achievement_id"),
                "special_perks": milestone_data.get("special_perks", [])
            },
            "is_read": False,
            "created_at": datetime.now(timezone.utc),
            "priority": "high" if milestone_data["threshold"] >= 30 else "normal"
        }
        
        await self.db.notifications.insert_one(notification)

    async def _create_streak_break_notification(self, user_id: str, lost_streak: int, days_missed: int):
        """Create notification when streak breaks"""
        if lost_streak < 3:
            return  # Only notify for meaningful streaks
        
        # Determine notification urgency based on days missed
        if days_missed == 1:
            message = f"Don't let your {lost_streak}-day streak end! Come back today! 💪"
            urgency = "soft_reminder"
        elif days_missed == 3:
            message = f"You lost your {lost_streak}-day streak! Time to start fresh! 🔄"
            urgency = "strong_nudge"
        elif days_missed >= 7:
            message = f"Miss your {lost_streak}-day streak? Let's rebuild it together! 🚀"
            urgency = "reactivation_push"
        else:
            return
        
        notification = {
            "user_id": user_id,
            "type": "streak_reminder",
            "title": "Streak Alert!",
            "message": message,
            "icon": "⚡",
            "action_url": "/transaction",
            "data": {
                "lost_streak": lost_streak,
                "days_missed": days_missed,
                "urgency": urgency
            },
            "is_read": False,
            "created_at": datetime.now(timezone.utc),
            "priority": "high" if days_missed >= 3 else "normal"
        }
        
        await self.db.notifications.insert_one(notification)

    # ===== SOCIAL PROOF SYSTEM - PHASE 1 =====
    
    async def get_social_proof_stats(self, user_id: str) -> Dict[str, Any]:
        """Get social proof statistics for enhanced gamification"""
        today = datetime.now(timezone.utc).date()
        week_start = today - timedelta(days=today.weekday())
        
        # Get daily achievement statistics
        daily_achievements = await self.db.achievements.count_documents({
            "created_at": {"$gte": datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)},
            "type": {"$in": ["streak_milestone", "badge_earned", "milestone_reached"]}
        })
        
        # Get weekly milestone achievers
        weekly_milestones = await self.db.achievements.count_documents({
            "created_at": {"$gte": datetime.combine(week_start, datetime.min.time()).replace(tzinfo=timezone.utc)},
            "type": "streak_milestone"
        })
        
        # Get user's friends achievements for comparison
        user_friends = await self._get_user_friends(user_id)
        friends_achievements = []
        
        if user_friends:
            friends_recent_achievements = await self.db.achievements.find({
                "user_id": {"$in": user_friends},
                "created_at": {"$gte": datetime.combine(week_start, datetime.min.time()).replace(tzinfo=timezone.utc)}
            }).sort("created_at", -1).limit(10).to_list(None)
            
            for achievement in friends_recent_achievements:
                friend = await get_user_by_id(achievement["user_id"])
                if friend:
                    friends_achievements.append({
                        "friend_name": friend.get("full_name", "Friend"),
                        "achievement_title": achievement["title"],
                        "achievement_icon": achievement["icon"],
                        "earned_at": achievement["created_at"],
                        "points_earned": achievement.get("points_earned", 0)
                    })
        
        # Get popular achievements this week
        popular_achievements = await self.db.achievements.aggregate([
            {
                "$match": {
                    "created_at": {"$gte": datetime.combine(week_start, datetime.min.time()).replace(tzinfo=timezone.utc)}
                }
            },
            {
                "$group": {
                    "_id": "$title",
                    "count": {"$sum": 1},
                    "icon": {"$first": "$icon"},
                    "type": {"$first": "$type"}
                }
            },
            {
                "$sort": {"count": -1}
            },
            {
                "$limit": 5
            }
        ]).to_list(None)
        
        # Get user's rank among friends
        user = await get_user_by_id(user_id)
        friends_leaderboard = []
        if user_friends and user:
            friends_data = []
            friends_data.append({
                "user_id": user_id,
                "name": user.get("full_name", "You"),
                "points": user.get("experience_points", 0),
                "streak": user.get("current_streak", 0),
                "is_current_user": True
            })
            
            for friend_id in user_friends[:20]:  # Limit to top 20 friends
                friend = await get_user_by_id(friend_id)
                if friend:
                    friends_data.append({
                        "user_id": friend_id,
                        "name": friend.get("full_name", "Friend"),
                        "points": friend.get("experience_points", 0),
                        "streak": friend.get("current_streak", 0),
                        "is_current_user": False
                    })
            
            # Sort by points
            friends_leaderboard = sorted(friends_data, key=lambda x: x["points"], reverse=True)
            
            # Add rank
            for i, friend in enumerate(friends_leaderboard):
                friend["rank"] = i + 1
        
        return {
            "daily_achievements": daily_achievements,
            "weekly_milestones": weekly_milestones,
            "friends_achievements": friends_achievements,
            "popular_achievements": popular_achievements,
            "friends_leaderboard": friends_leaderboard,
            "social_messages": self._generate_social_proof_messages(daily_achievements, weekly_milestones, len(friends_achievements))
        }

    def _generate_social_proof_messages(self, daily_count: int, weekly_count: int, friends_active: int) -> List[str]:
        """Generate social proof messages"""
        messages = []
        
        if daily_count > 0:
            messages.append(f"🎉 {daily_count} users achieved milestones today!")
        
        if weekly_count > 5:
            messages.append(f"🔥 {weekly_count} streak milestones achieved this week!")
        
        if friends_active > 0:
            messages.append(f"👥 {friends_active} of your friends earned achievements this week!")
        
        if not messages:
            messages.append("🚀 Be the first among your friends to achieve a milestone today!")
        
        return messages

    async def _get_user_friends(self, user_id: str) -> List[str]:
        """Get list of user's friend IDs"""
        # This would integrate with your friendship system
        # For now, returning empty list - implement based on your friendship model
        friendships = await self.db.friendships.find({
            "$or": [
                {"user_id": user_id, "status": "active"},
                {"friend_id": user_id, "status": "active"}
            ]
        }).to_list(None)
        
        friend_ids = []
        for friendship in friendships:
            if friendship["user_id"] == user_id:
                friend_ids.append(friendship["friend_id"])
            else:
                friend_ids.append(friendship["user_id"])
        
        return friend_ids

    # ===== CELEBRATION QUEUE SYSTEM =====
    
    async def queue_celebration(self, user_id: str, celebration_data: Dict[str, Any]):
        """Queue celebration for offline users"""
        celebration = {
            "user_id": user_id,
            "celebration_type": celebration_data.get("type", "achievement"),
            "title": celebration_data.get("title", "Achievement Unlocked!"),
            "message": celebration_data.get("message", ""),
            "icon": celebration_data.get("icon", "🎉"),
            "data": celebration_data,
            "created_at": datetime.now(timezone.utc),
            "is_shown": False,
            "priority": celebration_data.get("priority", "normal")
        }
        
        await self.db.celebration_queue.insert_one(celebration)

    async def get_pending_celebrations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get pending celebrations for user login"""
        celebrations = await self.db.celebration_queue.find({
            "user_id": user_id,
            "is_shown": False
        }).sort("created_at", 1).to_list(None)
        
        # Mark as shown
        if celebrations:
            celebration_ids = [c["_id"] for c in celebrations]
            await self.db.celebration_queue.update_many(
                {"_id": {"$in": celebration_ids}},
                {"$set": {"is_shown": True, "shown_at": datetime.now(timezone.utc)}}
            )
        
        # Convert ObjectIds to strings
        for celebration in celebrations:
            celebration["id"] = str(celebration["_id"])
            del celebration["_id"]
        
        return celebrations

    async def get_enhanced_gamification_profile(self, user_id: str) -> Dict[str, Any]:
        """Enhanced gamification profile with social proof and celebrations"""
        base_profile = await self.get_user_gamification_profile(user_id)
        social_proof = await self.get_social_proof_stats(user_id)
        pending_celebrations = await self.get_pending_celebrations(user_id)
        
        # Add enhanced features
        base_profile.update({
            "social_proof": social_proof,
            "pending_celebrations": pending_celebrations,
            "streak_milestones": {
                "next_milestone": self._get_next_streak_milestone(base_profile.get("current_streak", 0)),
                "progress_to_next": self._calculate_streak_progress(base_profile.get("current_streak", 0))
            },
            "special_perks": await self._get_user_special_perks(user_id),
            "celebration_stats": {
                "total_achievements": len(base_profile.get("recent_achievements", [])),
                "this_week_achievements": await self._count_week_achievements(user_id),
                "milestone_count": await self._count_user_milestones(user_id)
            }
        })
        
        return base_profile

    def _get_next_streak_milestone(self, current_streak: int) -> int:
        """Get next streak milestone target"""
        milestones = [7, 15, 30, 60, 100]
        for milestone in milestones:
            if current_streak < milestone:
                return milestone
        return current_streak + 50  # For users beyond 100 days

    def _calculate_streak_progress(self, current_streak: int) -> Dict[str, Any]:
        """Calculate progress to next milestone"""
        next_milestone = self._get_next_streak_milestone(current_streak)
        if next_milestone == current_streak + 50:
            return {"percentage": 100, "days_remaining": 0}
        
        progress_percentage = (current_streak / next_milestone) * 100
        days_remaining = next_milestone - current_streak
        
        return {
            "percentage": min(100, progress_percentage),
            "days_remaining": max(0, days_remaining),
            "current": current_streak,
            "target": next_milestone
        }

    async def _get_user_special_perks(self, user_id: str) -> List[str]:
        """Get user's active special perks"""
        user_badges = await self.db.user_badges.find({"user_id": user_id}).to_list(None)
        special_perks = []
        
        for user_badge in user_badges:
            badge = await self.db.badges.find_one({"_id": ObjectId(user_badge["badge_id"])})
            if badge and badge.get("special_perks"):
                special_perks.extend(badge["special_perks"])
        
        return list(set(special_perks))  # Remove duplicates

    async def _count_week_achievements(self, user_id: str) -> int:
        """Count achievements this week"""
        week_start = datetime.now(timezone.utc).date() - timedelta(days=datetime.now(timezone.utc).weekday())
        return await self.db.achievements.count_documents({
            "user_id": user_id,
            "created_at": {"$gte": datetime.combine(week_start, datetime.min.time()).replace(tzinfo=timezone.utc)}
        })

    async def _count_user_milestones(self, user_id: str) -> int:
        """Count total milestones achieved"""
        return await self.db.achievements.count_documents({
            "user_id": user_id,
            "type": {"$in": ["streak_milestone", "milestone_reached"]}
        })

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
        raw_achievements = await self.db.achievements.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(5).to_list(None)
        
        # Convert ObjectIds to strings for JSON serialization
        recent_achievements = []
        for achievement in raw_achievements:
            achievement["id"] = str(achievement["_id"])
            del achievement["_id"]  # Remove the ObjectId field
            recent_achievements.append(achievement)
        
        # Get user's ranks in different leaderboards
        ranks = {}
        university = user.get("university")
        for lb_type in ["savings", "streak", "goals", "points"]:
            ranks[lb_type] = await self.get_user_rank(user_id, lb_type, "all_time")
            if university:
                ranks[f"{lb_type}_campus"] = await self.get_user_rank(user_id, lb_type, "all_time", university)
        
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
