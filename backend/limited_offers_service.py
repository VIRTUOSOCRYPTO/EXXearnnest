import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from database import get_database, get_user_by_id

logger = logging.getLogger(__name__)

class LimitedOffersService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def create_offer(self, offer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new limited-time offer with FOMO mechanics"""
        try:
            offer_doc = {
                "id": offer_data.get("id"),
                "offer_type": offer_data["offer_type"],
                "title": offer_data["title"],
                "description": offer_data["description"],
                "offer_details": offer_data["offer_details"],
                "total_spots": offer_data.get("total_spots"),
                "spots_claimed": 0,
                "expires_at": offer_data["expires_at"],
                "created_at": datetime.now(timezone.utc),
                "eligible_users": offer_data.get("eligible_users"),
                "min_level": offer_data.get("min_level"),
                "min_streak": offer_data.get("min_streak"),
                "target_audience": offer_data.get("target_audience", "all"),
                "reward_type": offer_data["reward_type"],
                "reward_value": offer_data["reward_value"],
                "is_active": True,
                "auto_activate": offer_data.get("auto_activate", False),
                "urgency_level": offer_data.get("urgency_level", 3),
                "color_scheme": offer_data.get("color_scheme", "red"),
                "icon": offer_data.get("icon", "🔥"),
                # FOMO metrics
                "view_count": 0,
                "click_count": 0,
                "conversion_rate": 0.0,
                "last_activity": datetime.now(timezone.utc)
            }
            
            await self.db.limited_offers.insert_one(offer_doc)
            
            # Send notifications to eligible users if auto_activate is True
            if offer_data.get("auto_activate", False):
                await self._notify_eligible_users(offer_doc)
            
            logger.info(f"Created limited offer: {offer_doc['title']}")
            return offer_doc
            
        except Exception as e:
            logger.error(f"Create offer error: {str(e)}")
            raise

    async def get_active_offers_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get active offers that user is eligible for"""
        try:
            user = await get_user_by_id(user_id)
            if not user:
                return []
            
            current_time = datetime.now(timezone.utc)
            
            # Base query for active, non-expired offers
            base_query = {
                "is_active": True,
                "expires_at": {"$gt": current_time}
            }
            
            # Get all active offers
            offers = await self.db.limited_offers.find(base_query).to_list(None)
            
            # Filter offers based on user eligibility
            eligible_offers = []
            for offer in offers:
                if await self._is_user_eligible(user, offer):
                    # Check if user has already participated
                    participation = await self.db.offer_participations.find_one({
                        "user_id": user_id,
                        "offer_id": offer["id"]
                    })
                    
                    if not participation:
                        # Add real-time FOMO data
                        offer["spots_remaining"] = self._calculate_spots_remaining(offer)
                        offer["time_remaining"] = self._calculate_time_remaining(offer["expires_at"])
                        offer["urgency_message"] = self._generate_urgency_message(offer)
                        
                        eligible_offers.append(offer)
            
            # Sort by urgency level and expiry time
            eligible_offers.sort(key=lambda x: (x["urgency_level"], x["expires_at"]))
            
            return eligible_offers
            
        except Exception as e:
            logger.error(f"Get active offers error: {str(e)}")
            return []

    async def participate_in_offer(self, user_id: str, offer_id: str) -> Dict[str, Any]:
        """Handle user participation in a limited offer"""
        try:
            # Check if offer exists and is active
            offer = await self.db.limited_offers.find_one({
                "id": offer_id,
                "is_active": True,
                "expires_at": {"$gt": datetime.now(timezone.utc)}
            })
            
            if not offer:
                return {"success": False, "message": "Offer not found or expired"}
            
            # Check if user already participated
            existing_participation = await self.db.offer_participations.find_one({
                "user_id": user_id,
                "offer_id": offer_id
            })
            
            if existing_participation:
                return {"success": False, "message": "Already participated in this offer"}
            
            # Check spot availability for limited spots offers
            if offer.get("total_spots"):
                if offer["spots_claimed"] >= offer["total_spots"]:
                    return {"success": False, "message": "Sorry! All spots have been claimed"}
            
            # Check user eligibility
            user = await get_user_by_id(user_id)
            if not await self._is_user_eligible(user, offer):
                return {"success": False, "message": "You are not eligible for this offer"}
            
            # Create participation record
            participation_doc = {
                "id": f"participation_{user_id}_{offer_id}_{int(datetime.now(timezone.utc).timestamp())}",
                "user_id": user_id,
                "offer_id": offer_id,
                "status": "active",
                "progress": self._initialize_offer_progress(offer),
                "reward_claimed": False,
                "participated_at": datetime.now(timezone.utc)
            }
            
            await self.db.offer_participations.insert_one(participation_doc)
            
            # Update offer stats
            await self.db.limited_offers.update_one(
                {"id": offer_id},
                {
                    "$inc": {"spots_claimed": 1, "click_count": 1},
                    "$set": {"last_activity": datetime.now(timezone.utc)}
                }
            )
            
            # Handle immediate rewards for certain offer types
            reward_result = await self._process_immediate_rewards(user_id, offer, participation_doc)
            
            return {
                "success": True,
                "message": "Successfully joined the offer!",
                "participation_id": participation_doc["id"],
                "reward_info": reward_result,
                "spots_remaining": self._calculate_spots_remaining(offer) - 1
            }
            
        except Exception as e:
            logger.error(f"Participate in offer error: {str(e)}")
            return {"success": False, "message": "Failed to join offer"}

    async def update_participation_progress(self, user_id: str, offer_id: str, 
                                          progress_data: Dict[str, Any]) -> bool:
        """Update user's progress in an offer"""
        try:
            participation = await self.db.offer_participations.find_one({
                "user_id": user_id,
                "offer_id": offer_id,
                "status": "active"
            })
            
            if not participation:
                return False
            
            # Update progress
            updated_progress = {**participation.get("progress", {}), **progress_data}
            
            # Check if offer is completed
            offer = await self.db.limited_offers.find_one({"id": offer_id})
            completion_status = await self._check_offer_completion(offer, updated_progress)
            
            update_data = {
                "progress": updated_progress,
                "last_updated": datetime.now(timezone.utc)
            }
            
            if completion_status["completed"]:
                update_data["status"] = "completed"
                update_data["completed_at"] = datetime.now(timezone.utc)
                
                # Process completion rewards
                await self._process_completion_rewards(user_id, offer, participation)
            
            await self.db.offer_participations.update_one(
                {"user_id": user_id, "offer_id": offer_id},
                {"$set": update_data}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Update participation progress error: {str(e)}")
            return False

    async def get_user_participation_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's offer participation history"""
        try:
            participations = await self.db.offer_participations.find({
                "user_id": user_id
            }).sort("participated_at", -1).to_list(None)
            
            # Enrich with offer details
            for participation in participations:
                offer = await self.db.limited_offers.find_one({"id": participation["offer_id"]})
                if offer:
                    participation["offer_details"] = {
                        "title": offer["title"],
                        "description": offer["description"],
                        "offer_type": offer["offer_type"],
                        "reward_type": offer["reward_type"],
                        "reward_value": offer["reward_value"]
                    }
            
            return participations
            
        except Exception as e:
            logger.error(f"Get participation history error: {str(e)}")
            return []

    async def create_financial_challenge_offer(self, challenge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a financial challenge offer with deadline"""
        try:
            offer_data = {
                "id": f"challenge_{int(datetime.now(timezone.utc).timestamp())}",
                "offer_type": "challenge",
                "title": challenge_data["title"],
                "description": challenge_data["description"],
                "offer_details": {
                    "challenge_type": challenge_data["challenge_type"],  # "savings", "expense_reduction", "streak"
                    "target_amount": challenge_data.get("target_amount"),
                    "target_days": challenge_data.get("target_days"),
                    "difficulty_level": challenge_data.get("difficulty_level", "medium"),
                    "category_focus": challenge_data.get("category_focus"),
                    "success_criteria": challenge_data["success_criteria"]
                },
                "total_spots": challenge_data.get("max_participants"),
                "expires_at": challenge_data["deadline"],
                "reward_type": "points",
                "reward_value": challenge_data.get("reward_points", 100),
                "urgency_level": challenge_data.get("urgency_level", 3),
                "target_audience": challenge_data.get("target_audience", "all"),
                "color_scheme": "blue",
                "icon": "🎯",
                "auto_activate": True
            }
            
            return await self.create_offer(offer_data)
            
        except Exception as e:
            logger.error(f"Create financial challenge error: {str(e)}")
            raise

    async def create_premium_unlock_offer(self, unlock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a premium feature unlock offer with time limit"""
        try:
            offer_data = {
                "id": f"premium_{int(datetime.now(timezone.utc).timestamp())}",
                "offer_type": "premium_unlock",
                "title": unlock_data["title"],
                "description": unlock_data["description"],
                "offer_details": {
                    "feature_name": unlock_data["feature_name"],
                    "feature_description": unlock_data["feature_description"],
                    "unlock_duration": unlock_data.get("unlock_duration", "30_days"),
                    "original_price": unlock_data.get("original_price", "₹299"),
                    "discount_percentage": unlock_data.get("discount_percentage", 50)
                },
                "total_spots": unlock_data.get("limited_spots"),
                "expires_at": unlock_data["expires_at"],
                "reward_type": "premium_feature",
                "reward_value": unlock_data["feature_name"],
                "urgency_level": unlock_data.get("urgency_level", 4),
                "min_level": unlock_data.get("min_level", 2),
                "color_scheme": "purple",
                "icon": "⭐",
                "auto_activate": True
            }
            
            return await self.create_offer(offer_data)
            
        except Exception as e:
            logger.error(f"Create premium unlock error: {str(e)}")
            raise

    async def create_referral_bonus_offer(self, referral_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a referral bonus offer with expiry"""
        try:
            offer_data = {
                "id": f"referral_{int(datetime.now(timezone.utc).timestamp())}",
                "offer_type": "referral_bonus",
                "title": referral_data["title"],
                "description": referral_data["description"],
                "offer_details": {
                    "bonus_multiplier": referral_data.get("bonus_multiplier", 2.0),
                    "min_referrals": referral_data.get("min_referrals", 1),
                    "bonus_type": referral_data.get("bonus_type", "points"),
                    "referrer_bonus": referral_data.get("referrer_bonus", 100),
                    "referee_bonus": referral_data.get("referee_bonus", 50)
                },
                "expires_at": referral_data["expires_at"],
                "reward_type": "points",
                "reward_value": referral_data.get("referrer_bonus", 100),
                "urgency_level": referral_data.get("urgency_level", 3),
                "color_scheme": "green",
                "icon": "🤝",
                "auto_activate": True
            }
            
            return await self.create_offer(offer_data)
            
        except Exception as e:
            logger.error(f"Create referral bonus error: {str(e)}")
            raise

    async def expire_old_offers(self) -> int:
        """Expire old offers and handle cleanup"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Find expired offers
            expired_offers = await self.db.limited_offers.find({
                "expires_at": {"$lte": current_time},
                "is_active": True
            }).to_list(None)
            
            for offer in expired_offers:
                # Mark offer as inactive
                await self.db.limited_offers.update_one(
                    {"id": offer["id"]},
                    {"$set": {"is_active": False, "expired_at": current_time}}
                )
                
                # Update active participations to expired
                await self.db.offer_participations.update_many(
                    {"offer_id": offer["id"], "status": "active"},
                    {"$set": {"status": "expired", "expired_at": current_time}}
                )
            
            logger.info(f"Expired {len(expired_offers)} offers")
            return len(expired_offers)
            
        except Exception as e:
            logger.error(f"Expire old offers error: {str(e)}")
            return 0

    async def _is_user_eligible(self, user: Dict[str, Any], offer: Dict[str, Any]) -> bool:
        """Check if user is eligible for an offer"""
        try:
            # Check specific user list
            eligible_users = offer.get("eligible_users")
            if eligible_users and user["id"] not in eligible_users:
                return False
            
            # Check minimum level
            min_level = offer.get("min_level")
            if min_level and user.get("level", 1) < min_level:
                return False
            
            # Check minimum streak
            min_streak = offer.get("min_streak")
            if min_streak and user.get("current_streak", 0) < min_streak:
                return False
            
            # Check target audience
            target_audience = offer.get("target_audience", "all")
            if target_audience != "all":
                user_role = user.get("role", "").lower()
                if target_audience == "students" and "student" not in user_role:
                    return False
                elif target_audience == "professionals" and "professional" not in user_role:
                    return False
                elif target_audience == "new_users":
                    # Check if user is new (created within last 30 days)
                    created_at = user.get("created_at", datetime.min)
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    days_since_created = (datetime.now(timezone.utc) - created_at).days
                    if days_since_created > 30:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Check user eligibility error: {str(e)}")
            return False

    def _calculate_spots_remaining(self, offer: Dict[str, Any]) -> Optional[int]:
        """Calculate remaining spots for limited offers"""
        total_spots = offer.get("total_spots")
        if total_spots:
            return max(0, total_spots - offer.get("spots_claimed", 0))
        return None

    def _calculate_time_remaining(self, expires_at: datetime) -> Dict[str, Any]:
        """Calculate time remaining until offer expires"""
        try:
            now = datetime.now(timezone.utc)
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            
            time_diff = expires_at - now
            
            if time_diff.total_seconds() <= 0:
                return {"expired": True}
            
            days = time_diff.days
            hours, remainder = divmod(time_diff.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            return {
                "expired": False,
                "days": days,
                "hours": hours,
                "minutes": minutes,
                "total_seconds": int(time_diff.total_seconds()),
                "display": self._format_time_remaining(days, hours, minutes)
            }
            
        except Exception as e:
            logger.error(f"Calculate time remaining error: {str(e)}")
            return {"expired": True}

    def _format_time_remaining(self, days: int, hours: int, minutes: int) -> str:
        """Format time remaining for display"""
        if days > 0:
            return f"{days}d {hours}h left"
        elif hours > 0:
            return f"{hours}h {minutes}m left"
        else:
            return f"{minutes}m left"

    def _generate_urgency_message(self, offer: Dict[str, Any]) -> str:
        """Generate FOMO message based on offer data"""
        try:
            urgency_level = offer.get("urgency_level", 3)
            spots_remaining = self._calculate_spots_remaining(offer)
            time_remaining = self._calculate_time_remaining(offer["expires_at"])
            
            messages = []
            
            # Spots-based messages
            if spots_remaining is not None:
                if spots_remaining <= 5:
                    messages.append(f"⚡ Only {spots_remaining} spots left!")
                elif spots_remaining <= 20:
                    messages.append(f"🔥 {spots_remaining} spots remaining")
            
            # Time-based messages
            if not time_remaining.get("expired"):
                if time_remaining["days"] == 0 and time_remaining["hours"] < 6:
                    messages.append("⏰ Last few hours!")
                elif time_remaining["days"] == 0:
                    messages.append("⏳ Expires today!")
                elif time_remaining["days"] == 1:
                    messages.append("📅 1 day left!")
            
            # Urgency level based messages
            if urgency_level >= 4:
                messages.append("🚨 Limited time only!")
            elif urgency_level >= 3:
                messages.append("⚡ Act fast!")
            
            return " | ".join(messages) if messages else "🎯 Don't miss out!"
            
        except Exception as e:
            logger.error(f"Generate urgency message error: {str(e)}")
            return "🎯 Limited time offer!"

    def _initialize_offer_progress(self, offer: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize progress tracking for an offer"""
        offer_type = offer["offer_type"]
        
        if offer_type == "challenge":
            return {
                "started_at": datetime.now(timezone.utc).isoformat(),
                "current_amount": 0.0,
                "target_amount": offer["offer_details"].get("target_amount", 0),
                "days_completed": 0,
                "target_days": offer["offer_details"].get("target_days", 30),
                "milestones_reached": []
            }
        elif offer_type == "referral_bonus":
            return {
                "referrals_made": 0,
                "successful_referrals": 0,
                "bonus_earned": 0.0
            }
        else:
            return {"started_at": datetime.now(timezone.utc).isoformat()}

    async def _process_immediate_rewards(self, user_id: str, offer: Dict[str, Any], 
                                       participation: Dict[str, Any]) -> Dict[str, Any]:
        """Process immediate rewards for certain offer types"""
        try:
            reward_type = offer["reward_type"]
            reward_value = offer["reward_value"]
            
            if reward_type == "points":
                # Award points immediately for joining
                await self._award_points(user_id, int(reward_value))
                return {"type": "points", "value": reward_value, "immediate": True}
            elif reward_type == "premium_feature":
                # Unlock premium feature
                await self._unlock_premium_feature(user_id, str(reward_value))
                return {"type": "premium_unlock", "feature": reward_value, "immediate": True}
            
            return {"type": "pending", "message": "Complete the offer to earn rewards"}
            
        except Exception as e:
            logger.error(f"Process immediate rewards error: {str(e)}")
            return {"type": "error", "message": "Failed to process rewards"}

    async def _check_offer_completion(self, offer: Dict[str, Any], progress: Dict[str, Any]) -> Dict[str, Any]:
        """Check if offer completion criteria are met"""
        try:
            offer_type = offer["offer_type"]
            
            if offer_type == "challenge":
                success_criteria = offer["offer_details"]["success_criteria"]
                current_amount = progress.get("current_amount", 0)
                target_amount = progress.get("target_amount", 0)
                days_completed = progress.get("days_completed", 0)
                target_days = progress.get("target_days", 30)
                
                if success_criteria == "amount":
                    return {"completed": current_amount >= target_amount}
                elif success_criteria == "days":
                    return {"completed": days_completed >= target_days}
                elif success_criteria == "both":
                    return {"completed": current_amount >= target_amount and days_completed >= target_days}
            
            return {"completed": False}
            
        except Exception as e:
            logger.error(f"Check offer completion error: {str(e)}")
            return {"completed": False}

    async def _process_completion_rewards(self, user_id: str, offer: Dict[str, Any], 
                                        participation: Dict[str, Any]):
        """Process rewards when offer is completed"""
        try:
            reward_type = offer["reward_type"]
            reward_value = offer["reward_value"]
            
            if reward_type == "points":
                await self._award_points(user_id, int(reward_value))
            elif reward_type == "badge":
                await self._award_badge(user_id, str(reward_value))
            elif reward_type == "premium_feature":
                await self._unlock_premium_feature(user_id, str(reward_value))
            
            # Mark reward as claimed
            await self.db.offer_participations.update_one(
                {"id": participation["id"]},
                {"$set": {"reward_claimed": True, "reward_claimed_at": datetime.now(timezone.utc)}}
            )
            
        except Exception as e:
            logger.error(f"Process completion rewards error: {str(e)}")

    async def _award_points(self, user_id: str, points: int):
        """Award achievement points to user"""
        try:
            await self.db.users.update_one(
                {"id": user_id},
                {"$inc": {"achievement_points": points}}
            )
        except Exception as e:
            logger.error(f"Award points error: {str(e)}")

    async def _award_badge(self, user_id: str, badge_name: str):
        """Award badge to user"""
        try:
            badge_data = {
                "name": badge_name,
                "earned_at": datetime.now(timezone.utc),
                "type": "limited_offer"
            }
            
            await self.db.users.update_one(
                {"id": user_id},
                {"$push": {"badges": badge_data}}
            )
        except Exception as e:
            logger.error(f"Award badge error: {str(e)}")

    async def _unlock_premium_feature(self, user_id: str, feature_name: str):
        """Unlock premium feature for user"""
        try:
            # This would integrate with a premium features system
            # For now, we'll store it in user's profile
            unlock_data = {
                "feature": feature_name,
                "unlocked_at": datetime.now(timezone.utc),
                "source": "limited_offer"
            }
            
            await self.db.users.update_one(
                {"id": user_id},
                {"$push": {"premium_unlocks": unlock_data}}
            )
        except Exception as e:
            logger.error(f"Unlock premium feature error: {str(e)}")

    async def _notify_eligible_users(self, offer: Dict[str, Any]):
        """Send notifications to users eligible for the offer"""
        try:
            # Import here to avoid circular imports
            from push_notification_service import get_push_service
            
            # Get eligible users based on offer criteria
            target_audience = offer.get("target_audience", "all")
            query = {"is_active": True}
            
            if target_audience != "all":
                if target_audience == "students":
                    query["role"] = {"$regex": "Student", "$options": "i"}
                elif target_audience == "professionals":
                    query["role"] = {"$regex": "Professional", "$options": "i"}
                elif target_audience == "new_users":
                    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
                    query["created_at"] = {"$gte": week_ago}
            
            if offer.get("min_level"):
                query["level"] = {"$gte": offer["min_level"]}
            
            if offer.get("min_streak"):
                query["current_streak"] = {"$gte": offer["min_streak"]}
            
            eligible_users = await self.db.users.find(query).to_list(100)  # Limit to 100 for now
            
            push_service = await get_push_service()
            if push_service:
                for user in eligible_users:
                    notification_data = {
                        "title": f"🔥 {offer['title']}",
                        "message": offer["description"][:100] + "..." if len(offer["description"]) > 100 else offer["description"],
                        "type": "limited_offer",
                        "offer_id": offer["id"],
                        "urgency_level": offer["urgency_level"]
                    }
                    
                    await push_service.send_limited_offer_notification(user["id"], notification_data)
            
        except Exception as e:
            logger.error(f"Notify eligible users error: {str(e)}")

# Global instance
limited_offers_service = None

async def get_limited_offers_service() -> LimitedOffersService:
    global limited_offers_service
    if limited_offers_service is None:
        db = await get_database()
        limited_offers_service = LimitedOffersService(db)
    return limited_offers_service
