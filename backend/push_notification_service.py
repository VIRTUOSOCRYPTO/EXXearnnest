import os
import json
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from database import get_database
from pywebpush import webpush, WebPushException

logger = logging.getLogger(__name__)

class PushNotificationService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        # VAPID keys for web push notifications
        self.vapid_private_key = os.environ.get("VAPID_PRIVATE_KEY")
        self.vapid_public_key = os.environ.get("VAPID_PUBLIC_KEY") 
        self.vapid_claims = {
            "sub": "mailto:admin@earnest.app"
        }

    async def send_milestone_notification(self, user_id: str, milestone_data: Dict[str, Any]):
        """Send push notification for milestone achievement"""
        try:
            # Get user's push subscription
            subscription = await self.db.push_subscriptions.find_one({
                "user_id": user_id,
                "is_active": True
            })
            
            if not subscription:
                logger.info(f"No active push subscription for user {user_id}")
                return False
            
            preferences = subscription.get("notification_preferences", {})
            if not preferences.get("milestone_achievements", True):
                logger.info(f"Milestone notifications disabled for user {user_id}")
                return False
            
            # Create notification payload
            notification_payload = {
                "title": f"🎉 {milestone_data['title']}",
                "body": milestone_data['message'],
                "icon": "/icons/achievement-icon.png",
                "badge": "/icons/badge-icon.png",
                "image": milestone_data.get('celebration_image'),
                "data": {
                    "type": "milestone_achievement",
                    "achievement_id": milestone_data.get('achievement_id'),
                    "url": "/gamification",
                    "milestone_type": milestone_data['type'],
                    "threshold": milestone_data['threshold']
                },
                "actions": [
                    {
                        "action": "view",
                        "title": "View Achievement"
                    },
                    {
                        "action": "share",
                        "title": "Share Achievement"
                    }
                ],
                "tag": f"milestone-{milestone_data['threshold']}",
                "requireInteraction": milestone_data.get('threshold', 0) >= 30  # Require interaction for major milestones
            }
            
            return await self._send_push_notification(subscription["subscription_data"], notification_payload)
            
        except Exception as e:
            logger.error(f"Send milestone notification error: {str(e)}")
            return False

    async def send_streak_reminder(self, user_id: str, reminder_type: str = "daily", streak_data: Dict[str, Any] = None):
        """Send streak reminder push notification"""
        try:
            subscription = await self.db.push_subscriptions.find_one({
                "user_id": user_id,
                "is_active": True
            })
            
            if not subscription:
                return False
            
            preferences = subscription.get("notification_preferences", {})
            if not preferences.get("streak_reminders", True):
                return False
            
            # Generate reminder message based on type
            if reminder_type == "daily":
                title = "⏰ Daily Tracking Reminder"
                body = f"Keep your {streak_data.get('current_streak', 0)}-day streak alive! Track today's finances."
                tag = "daily-reminder"
            elif reminder_type == "soft_reminder":
                title = "💪 Don't Break Your Streak!"
                body = f"You're on a {streak_data.get('lost_streak', 0)}-day streak! Come back today."
                tag = "streak-break-1"
            elif reminder_type == "strong_nudge":
                title = "🔄 Time to Restart!"
                body = f"You lost your {streak_data.get('lost_streak', 0)}-day streak. Let's build it back!"
                tag = "streak-break-3"
            elif reminder_type == "reactivation_push":
                title = "🚀 We Miss You!"
                body = f"Ready to rebuild your {streak_data.get('lost_streak', 0)}-day streak? Start fresh today!"
                tag = "streak-break-7"
            else:
                title = "📊 Track Your Finances"
                body = "Don't forget to log today's transactions!"
                tag = "general-reminder"
            
            notification_payload = {
                "title": title,
                "body": body,
                "icon": "/icons/streak-icon.png",
                "badge": "/icons/badge-icon.png",
                "data": {
                    "type": "streak_reminder",
                    "reminder_type": reminder_type,
                    "url": "/transaction",
                    "streak_data": streak_data
                },
                "actions": [
                    {
                        "action": "track",
                        "title": "Track Now"
                    },
                    {
                        "action": "dismiss",
                        "title": "Remind Later"
                    }
                ],
                "tag": tag,
                "requireInteraction": reminder_type in ["strong_nudge", "reactivation_push"]
            }
            
            return await self._send_push_notification(subscription["subscription_data"], notification_payload)
            
        except Exception as e:
            logger.error(f"Send streak reminder error: {str(e)}")
            return False

    async def send_friend_achievement_notification(self, user_id: str, friend_name: str, achievement_title: str):
        """Send notification when friend achieves milestone"""
        try:
            subscription = await self.db.push_subscriptions.find_one({
                "user_id": user_id,
                "is_active": True
            })
            
            if not subscription:
                return False
            
            preferences = subscription.get("notification_preferences", {})
            if not preferences.get("friend_activities", True):
                return False
            
            notification_payload = {
                "title": f"👥 Friend Achievement",
                "body": f"{friend_name} just earned: {achievement_title}",
                "icon": "/icons/friend-icon.png",
                "badge": "/icons/badge-icon.png",
                "data": {
                    "type": "friend_achievement",
                    "url": "/gamification",
                    "friend_name": friend_name,
                    "achievement": achievement_title
                },
                "actions": [
                    {
                        "action": "view",
                        "title": "View Friends"
                    }
                ],
                "tag": "friend-activity"
            }
            
            return await self._send_push_notification(subscription["subscription_data"], notification_payload)
            
        except Exception as e:
            logger.error(f"Send friend achievement notification error: {str(e)}")
            return False

    async def schedule_daily_reminders(self):
        """Schedule daily reminder notifications"""
        try:
            # Get all active subscriptions with daily reminders enabled
            subscriptions = await self.db.push_subscriptions.find({
                "is_active": True,
                "notification_preferences.daily_reminders": True
            }).to_list(None)
            
            current_time = datetime.now(timezone.utc)
            
            for subscription in subscriptions:
                preferences = subscription.get("notification_preferences", {})
                reminder_time = preferences.get("reminder_time", "19:00")  # 7 PM default
                
                # Parse reminder time
                try:
                    hour, minute = map(int, reminder_time.split(":"))
                    
                    # Check if it's time to send reminder (within 5 minutes window)
                    if (current_time.hour == hour and 
                        abs(current_time.minute - minute) <= 5):
                        
                        # Check if user was active today
                        user_id = subscription["user_id"]
                        if not await self._was_user_active_today(user_id):
                            # Get user's current streak
                            from database import get_user_by_id
                            user = await get_user_by_id(user_id)
                            if user:
                                streak_data = {
                                    "current_streak": user.get("current_streak", 0)
                                }
                                await self.send_streak_reminder(user_id, "daily", streak_data)
                        
                except ValueError:
                    logger.error(f"Invalid reminder time format: {reminder_time}")
                    continue
                    
        except Exception as e:
            logger.error(f"Schedule daily reminders error: {str(e)}")

    async def _send_push_notification(self, subscription_info: Dict[str, Any], payload: Dict[str, Any]) -> bool:
        """Send actual push notification using WebPush"""
        try:
            if not self.vapid_private_key or not self.vapid_public_key:
                logger.warning("VAPID keys not configured, skipping push notification")
                return False
            
            # Send the push notification
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=self.vapid_private_key,
                vapid_claims=self.vapid_claims
            )
            
            logger.info(f"Push notification sent successfully")
            return True
            
        except WebPushException as e:
            logger.error(f"WebPush error: {str(e)}")
            
            # If subscription is no longer valid, mark as inactive
            if e.response and e.response.status_code in [410, 413, 404]:
                await self._deactivate_subscription(subscription_info)
            
            return False
        except Exception as e:
            logger.error(f"Send push notification error: {str(e)}")
            return False

    async def _deactivate_subscription(self, subscription_info: Dict[str, Any]):
        """Deactivate invalid push subscription"""
        try:
            await self.db.push_subscriptions.update_one(
                {"subscription_data.endpoint": subscription_info.get("endpoint")},
                {"$set": {"is_active": False, "deactivated_at": datetime.now(timezone.utc)}}
            )
        except Exception as e:
            logger.error(f"Deactivate subscription error: {str(e)}")

    async def _was_user_active_today(self, user_id: str) -> bool:
        """Check if user was active today"""
        try:
            from database import get_user_by_id
            user = await get_user_by_id(user_id)
            
            if not user:
                return False
            
            last_activity = user.get("last_activity_date")
            if not last_activity:
                return False
            
            today = datetime.now(timezone.utc).date()
            activity_date = last_activity.date() if isinstance(last_activity, datetime) else last_activity
            
            return activity_date == today
            
        except Exception as e:
            logger.error(f"Check user activity error: {str(e)}")
            return False

    async def send_bulk_notifications(self, notifications: List[Dict[str, Any]]):
        """Send multiple notifications efficiently"""
        tasks = []
        
        for notification in notifications:
            if notification["type"] == "milestone":
                task = self.send_milestone_notification(
                    notification["user_id"], 
                    notification["data"]
                )
            elif notification["type"] == "streak_reminder":
                task = self.send_streak_reminder(
                    notification["user_id"],
                    notification["reminder_type"],
                    notification.get("streak_data")
                )
            elif notification["type"] == "friend_achievement":
                task = self.send_friend_achievement_notification(
                    notification["user_id"],
                    notification["friend_name"],
                    notification["achievement_title"]
                )
            else:
                continue
            
            tasks.append(task)
        
        # Execute all notifications concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            successful = sum(1 for result in results if result is True)
            logger.info(f"Bulk notifications: {successful}/{len(tasks)} sent successfully")
        
        return len(tasks)

    async def send_daily_tip_notification(self, user_id: str, tip_data: Dict[str, Any]):
        """Send push notification for daily financial tip"""
        try:
            subscription = await self.db.push_subscriptions.find_one({
                "user_id": user_id,
                "is_active": True
            })
            
            if not subscription:
                return False
            
            preferences = subscription.get("notification_preferences", {})
            if not preferences.get("daily_tips", True):
                return False
            
            notification_payload = {
                "title": f"💡 {tip_data['title']}",
                "body": tip_data['message'][:120] + "..." if len(tip_data['message']) > 120 else tip_data['message'],
                "icon": "/icons/tip-icon.png",
                "badge": "/icons/badge-icon.png",
                "data": {
                    "type": "daily_tip",
                    "tip_id": tip_data.get('tip_id'),
                    "url": "/dashboard",
                    "tip_category": tip_data.get('category', 'general')
                },
                "actions": [
                    {
                        "action": "view",
                        "title": "View Tip"
                    },
                    {
                        "action": "save",
                        "title": "Save for Later"
                    }
                ],
                "tag": "daily-tip"
            }
            
            return await self._send_push_notification(subscription["subscription_data"], notification_payload)
            
        except Exception as e:
            logger.error(f"Send daily tip notification error: {str(e)}")
            return False

    async def send_limited_offer_notification(self, user_id: str, offer_data: Dict[str, Any]):
        """Send push notification for limited-time offers"""
        try:
            subscription = await self.db.push_subscriptions.find_one({
                "user_id": user_id,
                "is_active": True
            })
            
            if not subscription:
                return False
            
            preferences = subscription.get("notification_preferences", {})
            if not preferences.get("limited_offers", True):
                return False
            
            urgency_level = offer_data.get('urgency_level', 3)
            require_interaction = urgency_level >= 4
            
            notification_payload = {
                "title": offer_data['title'],
                "body": offer_data['message'],
                "icon": "/icons/offer-icon.png",
                "badge": "/icons/badge-icon.png",
                "data": {
                    "type": "limited_offer",
                    "offer_id": offer_data.get('offer_id'),
                    "url": f"/offers/{offer_data.get('offer_id')}",
                    "urgency_level": urgency_level
                },
                "actions": [
                    {
                        "action": "view",
                        "title": "View Offer"
                    },
                    {
                        "action": "join",
                        "title": "Join Now!"
                    }
                ],
                "tag": f"offer-{offer_data.get('offer_id')}",
                "requireInteraction": require_interaction
            }
            
            return await self._send_push_notification(subscription["subscription_data"], notification_payload)
            
        except Exception as e:
            logger.error(f"Send limited offer notification error: {str(e)}")
            return False

    async def send_friend_activity_notification(self, user_id: str, activity_data: Dict[str, Any]):
        """Send push notification for friend activities"""
        try:
            subscription = await self.db.push_subscriptions.find_one({
                "user_id": user_id,
                "is_active": True
            })
            
            if not subscription:
                return False
            
            preferences = subscription.get("notification_preferences", {})
            if not preferences.get("friend_activities", True):
                return False
            
            friend_name = activity_data.get('friend_name', 'A friend')
            activity_type = activity_data.get('activity_type', 'achieved something')
            
            # Customize notification based on activity type
            if activity_type == "milestone":
                title = f"🎉 {friend_name} Hit a Milestone!"
                body = f"{friend_name} {activity_data.get('description', 'achieved a financial milestone')}. Motivate them!"
                icon_path = "/icons/milestone-icon.png"
            elif activity_type == "goal_completed":
                title = f"🏆 {friend_name} Completed a Goal!"
                body = f"{friend_name} {activity_data.get('description', 'completed their financial goal')}. Celebrate with them!"
                icon_path = "/icons/goal-icon.png"
            elif activity_type == "streak":
                title = f"🔥 {friend_name}'s Streak!"
                body = f"{friend_name} {activity_data.get('description', 'extended their tracking streak')}. Keep up the motivation!"
                icon_path = "/icons/streak-icon.png"
            else:
                title = f"👥 Friend Update"
                body = f"{friend_name} {activity_data.get('description', 'has new activity')} on EarnAura"
                icon_path = "/icons/friend-icon.png"
            
            notification_payload = {
                "title": title,
                "body": body,
                "icon": icon_path,
                "badge": "/icons/badge-icon.png",
                "data": {
                    "type": "friend_activity",
                    "friend_id": activity_data.get('friend_id'),
                    "activity_id": activity_data.get('activity_id'),
                    "url": "/friends",
                    "activity_type": activity_type
                },
                "actions": [
                    {
                        "action": "view",
                        "title": "View Activity"
                    },
                    {
                        "action": "react",
                        "title": "React"
                    }
                ],
                "tag": "friend-activity"
            }
            
            return await self._send_push_notification(subscription["subscription_data"], notification_payload)
            
        except Exception as e:
            logger.error(f"Send friend activity notification error: {str(e)}")
            return False

    async def send_timeline_reaction_notification(self, user_id: str, reaction_data: Dict[str, Any]):
        """Send push notification when someone reacts to user's timeline event"""
        try:
            subscription = await self.db.push_subscriptions.find_one({
                "user_id": user_id,
                "is_active": True
            })
            
            if not subscription:
                return False
            
            preferences = subscription.get("notification_preferences", {})
            if not preferences.get("friend_activities", True):
                return False
            
            reactor_name = reaction_data.get('reactor_name', 'Someone')
            reaction_type = reaction_data.get('reaction_type', 'liked')
            event_title = reaction_data.get('event_title', 'your activity')
            
            # Reaction emojis
            reaction_emojis = {
                "like": "👍",
                "celebrate": "🎉", 
                "motivate": "💪",
                "inspire": "✨"
            }
            
            emoji = reaction_emojis.get(reaction_type, "👍")
            
            notification_payload = {
                "title": f"{emoji} New Reaction!",
                "body": f"{reactor_name} {reaction_type}d {event_title}",
                "icon": "/icons/reaction-icon.png",
                "badge": "/icons/badge-icon.png",
                "data": {
                    "type": "timeline_reaction",
                    "reactor_id": reaction_data.get('reactor_id'),
                    "event_id": reaction_data.get('event_id'),
                    "url": f"/timeline?event_id={reaction_data.get('event_id')}",
                    "reaction_type": reaction_type
                },
                "actions": [
                    {
                        "action": "view",
                        "title": "View Timeline"
                    }
                ],
                "tag": "timeline-reaction"
            }
            
            return await self._send_push_notification(subscription["subscription_data"], notification_payload)
            
        except Exception as e:
            logger.error(f"Send timeline reaction notification error: {str(e)}")
            return False

    async def send_challenge_update_notification(self, user_id: str, challenge_data: Dict[str, Any]):
        """Send push notification for challenge updates"""
        try:
            subscription = await self.db.push_subscriptions.find_one({
                "user_id": user_id,
                "is_active": True
            })
            
            if not subscription:
                return False
            
            preferences = subscription.get("notification_preferences", {})
            if not preferences.get("challenge_updates", True):
                return False
            
            update_type = challenge_data.get('update_type')
            challenge_title = challenge_data.get('title', 'Challenge')
            
            if update_type == "deadline_approaching":
                title = f"⏰ Challenge Deadline Soon!"
                body = f"{challenge_title} ends in {challenge_data.get('time_remaining', 'soon')}. Push to finish!"
                require_interaction = True
            elif update_type == "progress_milestone":
                title = f"📈 Challenge Progress!"
                body = f"You're {challenge_data.get('progress', '50')}% done with {challenge_title}. Keep going!"
                require_interaction = False
            elif update_type == "leaderboard_change":
                title = f"🏆 Leaderboard Update!"
                body = f"You're now #{challenge_data.get('rank', '?')} in {challenge_title}!"
                require_interaction = False
            else:
                title = f"🎯 Challenge Update"
                body = f"New update for {challenge_title}"
                require_interaction = False
            
            notification_payload = {
                "title": title,
                "body": body,
                "icon": "/icons/challenge-icon.png",
                "badge": "/icons/badge-icon.png",
                "data": {
                    "type": "challenge_update",
                    "challenge_id": challenge_data.get('challenge_id'),
                    "url": f"/challenges/{challenge_data.get('challenge_id')}",
                    "update_type": update_type
                },
                "actions": [
                    {
                        "action": "view",
                        "title": "View Challenge"
                    }
                ],
                "tag": f"challenge-{challenge_data.get('challenge_id')}",
                "requireInteraction": require_interaction
            }
            
            return await self._send_push_notification(subscription["subscription_data"], notification_payload)
            
        except Exception as e:
            logger.error(f"Send challenge update notification error: {str(e)}")
            return False

    async def create_push_subscription(self, user_id: str, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update push notification subscription for user"""
        try:
            # Check if subscription already exists
            existing = await self.db.push_subscriptions.find_one({
                "user_id": user_id,
                "subscription_data.endpoint": subscription_data["subscription_data"]["endpoint"]
            })
            
            if existing:
                # Update existing subscription
                await self.db.push_subscriptions.update_one(
                    {"user_id": user_id, "subscription_data.endpoint": subscription_data["subscription_data"]["endpoint"]},
                    {
                        "$set": {
                            "subscription_data": subscription_data["subscription_data"],
                            "device_type": subscription_data.get("device_type", "web"),
                            "browser_info": subscription_data.get("browser_info"),
                            "is_active": True,
                            "last_used_at": datetime.now(timezone.utc)
                        }
                    }
                )
                return {"success": True, "message": "Subscription updated"}
            else:
                # Create new subscription
                subscription_doc = {
                    "id": f"sub_{user_id}_{int(datetime.now(timezone.utc).timestamp())}",
                    "user_id": user_id,
                    "subscription_data": subscription_data["subscription_data"],
                    "device_type": subscription_data.get("device_type", "web"),
                    "browser_info": subscription_data.get("browser_info"),
                    "notification_preferences": subscription_data.get("notification_preferences", {
                        "friend_activities": True,
                        "milestone_achievements": True,
                        "streak_reminders": True,
                        "daily_tips": True,
                        "limited_offers": True,
                        "challenge_updates": True
                    }),
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc),
                    "last_used_at": datetime.now(timezone.utc)
                }
                
                await self.db.push_subscriptions.insert_one(subscription_doc)
                return {"success": True, "message": "Subscription created"}
                
        except Exception as e:
            logger.error(f"Create push subscription error: {str(e)}")
            return {"success": False, "message": "Failed to create subscription"}

    async def update_notification_preferences(self, user_id: str, preferences: Dict[str, bool]) -> bool:
        """Update user's notification preferences"""
        try:
            result = await self.db.push_subscriptions.update_many(
                {"user_id": user_id},
                {"$set": {"notification_preferences": preferences}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Update notification preferences error: {str(e)}")
            return False

    async def get_user_notification_preferences(self, user_id: str) -> Dict[str, bool]:
        """Get user's notification preferences"""
        try:
            subscription = await self.db.push_subscriptions.find_one({
                "user_id": user_id,
                "is_active": True
            })
            
            if subscription:
                return subscription.get("notification_preferences", {})
            
            # Return default preferences
            return {
                "friend_activities": True,
                "milestone_achievements": True,
                "streak_reminders": True,
                "daily_tips": True,
                "limited_offers": True,
                "challenge_updates": True
            }
            
        except Exception as e:
            logger.error(f"Get notification preferences error: {str(e)}")
            return {}

# Global instance
push_service = None

async def get_push_service() -> PushNotificationService:
    global push_service
    if push_service is None:
        db = await get_database()
        push_service = PushNotificationService(db)
    return push_service
