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

# Global instance
push_service = None

async def get_push_service() -> PushNotificationService:
    global push_service
    if push_service is None:
        db = await get_database()
        push_service = PushNotificationService(db)
    return push_service
