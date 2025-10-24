import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from database import get_database, get_user_by_id

logger = logging.getLogger(__name__)

class TimelineService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def create_timeline_event(self, user_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new timeline event"""
        try:
            event_doc = {
                "id": event_data.get("id", f"event_{user_id}_{int(datetime.now(timezone.utc).timestamp())}"),
                "user_id": user_id,
                "event_type": event_data["event_type"],
                "category": event_data["category"],
                "subcategory": event_data.get("subcategory"),
                "title": event_data["title"],
                "description": event_data["description"],
                "amount": event_data.get("amount"),
                "metadata": event_data.get("metadata", {}),
                "related_user_id": event_data.get("related_user_id"),
                "related_entity_id": event_data.get("related_entity_id"),
                "icon": event_data.get("icon", "📊"),
                "color": event_data.get("color", "#3B82F6"),
                "image_url": event_data.get("image_url"),
                "event_date": event_data.get("event_date", datetime.now(timezone.utc)),
                "created_at": datetime.now(timezone.utc),
                "visibility": event_data.get("visibility", "friends"),
                "is_featured": event_data.get("is_featured", False),
                # Engagement metrics
                "reaction_count": 0,
                "view_count": 0,
                "share_count": 0
            }
            
            await self.db.timeline_events.insert_one(event_doc)
            
            # Auto-create social timeline events for friends
            if event_data["event_type"] == "personal" and event_data.get("visibility") in ["friends", "public"]:
                await self._create_friend_timeline_events(user_id, event_doc)
            
            logger.info(f"Created timeline event: {event_doc['title']}")
            return event_doc
            
        except Exception as e:
            logger.error(f"Create timeline event error: {str(e)}")
            raise

    async def get_user_timeline(self, user_id: str, timeline_type: str = "combined", 
                              limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get user's timeline (personal, social, or combined)"""
        try:
            query = {"user_id": user_id}
            
            if timeline_type == "personal":
                query["event_type"] = "personal"
            elif timeline_type == "social":
                query["event_type"] = "social"
            # For "combined", we get both personal and social events
            
            # Get timeline events
            events = await self.db.timeline_events.find(query)\
                .sort("event_date", -1)\
                .skip(offset)\
                .limit(limit)\
                .to_list(None)
            
            # Enrich events with additional data
            enriched_events = []
            for event in events:
                enriched_event = await self._enrich_timeline_event(event, user_id)
                enriched_events.append(enriched_event)
            
            return enriched_events
            
        except Exception as e:
            logger.error(f"Get user timeline error: {str(e)}")
            return []

    async def get_friend_activities_timeline(self, user_id: str, limit: int = 15, 
                                           offset: int = 0) -> List[Dict[str, Any]]:
        """Get timeline of friend activities"""
        try:
            # Get user's friends
            friends = await self._get_user_friends(user_id)
            friend_ids = [friend["id"] for friend in friends]
            
            if not friend_ids:
                return []
            
            # Get friends' personal timeline events that are visible to friends
            query = {
                "user_id": {"$in": friend_ids},
                "event_type": "personal",
                "visibility": {"$in": ["friends", "public"]}
            }
            
            events = await self.db.timeline_events.find(query)\
                .sort("event_date", -1)\
                .skip(offset)\
                .limit(limit)\
                .to_list(None)
            
            # Enrich events with friend information
            enriched_events = []
            for event in events:
                enriched_event = await self._enrich_timeline_event(event, user_id)
                # Add friend information
                friend_info = next((f for f in friends if f["id"] == event["user_id"]), None)
                if friend_info:
                    enriched_event["friend_info"] = {
                        "name": friend_info.get("full_name", "Friend"),
                        "avatar": friend_info.get("avatar", "boy"),
                        "university": friend_info.get("university")
                    }
                enriched_events.append(enriched_event)
            
            return enriched_events
            
        except Exception as e:
            logger.error(f"Get friend activities timeline error: {str(e)}")
            return []

    async def add_reaction_to_event(self, user_id: str, event_id: str, reaction_type: str) -> bool:
        """Add a reaction to a timeline event"""
        try:
            # Check if user already reacted to this event
            existing_reaction = await self.db.timeline_reactions.find_one({
                "user_id": user_id,
                "timeline_event_id": event_id
            })
            
            if existing_reaction:
                # Update existing reaction
                await self.db.timeline_reactions.update_one(
                    {"user_id": user_id, "timeline_event_id": event_id},
                    {"$set": {"reaction_type": reaction_type, "created_at": datetime.now(timezone.utc)}}
                )
            else:
                # Create new reaction
                reaction_doc = {
                    "id": f"reaction_{user_id}_{event_id}_{int(datetime.now(timezone.utc).timestamp())}",
                    "user_id": user_id,
                    "timeline_event_id": event_id,
                    "reaction_type": reaction_type,
                    "created_at": datetime.now(timezone.utc)
                }
                
                await self.db.timeline_reactions.insert_one(reaction_doc)
                
                # Update event reaction count
                await self.db.timeline_events.update_one(
                    {"id": event_id},
                    {"$inc": {"reaction_count": 1}}
                )
            
            # Create notification for event owner if it's not their own reaction
            event = await self.db.timeline_events.find_one({"id": event_id})
            if event and event["user_id"] != user_id:
                await self._create_reaction_notification(user_id, event, reaction_type)
            
            return True
            
        except Exception as e:
            logger.error(f"Add reaction error: {str(e)}")
            return False

    async def auto_create_transaction_event(self, user_id: str, transaction: Dict[str, Any]):
        """Automatically create timeline event for significant transactions"""
        try:
            transaction_type = transaction.get("type")
            amount = transaction.get("amount", 0)
            category = transaction.get("category", "Other")
            
            # Only create events for significant transactions
            if not self._is_significant_transaction(transaction):
                return
            
            # Determine event details based on transaction
            if transaction_type == "income":
                event_data = {
                    "event_type": "personal",
                    "category": "transaction",
                    "subcategory": "income",
                    "title": self._generate_income_title(amount, category, transaction),
                    "description": self._generate_income_description(amount, category, transaction),
                    "amount": amount,
                    "icon": self._get_income_icon(category),
                    "color": "#10B981",  # Green for income
                    "visibility": "friends",
                    "metadata": {
                        "transaction_id": transaction.get("id"),
                        "category": category,
                        "source": transaction.get("source", "other")
                    }
                }
            else:  # expense
                event_data = {
                    "event_type": "personal",
                    "category": "transaction",
                    "subcategory": "expense",
                    "title": self._generate_expense_title(amount, category, transaction),
                    "description": self._generate_expense_description(amount, category, transaction),
                    "amount": amount,
                    "icon": self._get_expense_icon(category),
                    "color": "#EF4444",  # Red for expense
                    "visibility": "private",  # Expenses are private by default
                    "metadata": {
                        "transaction_id": transaction.get("id"),
                        "category": category
                    }
                }
            
            await self.create_timeline_event(user_id, event_data)
            
        except Exception as e:
            logger.error(f"Auto create transaction event error: {str(e)}")

    async def auto_create_milestone_event(self, user_id: str, milestone: Dict[str, Any]):
        """Automatically create timeline event for milestones"""
        try:
            milestone_type = milestone.get("type")
            threshold = milestone.get("threshold")
            
            event_data = {
                "event_type": "personal",
                "category": "milestone",
                "subcategory": milestone_type,
                "title": self._generate_milestone_title(milestone),
                "description": self._generate_milestone_description(milestone),
                "icon": self._get_milestone_icon(milestone_type),
                "color": "#8B5CF6",  # Purple for milestones
                "visibility": "public",  # Milestones are shareable
                "is_featured": True,  # Milestones are featured
                "metadata": {
                    "milestone_type": milestone_type,
                    "threshold": threshold,
                    "achievement_id": milestone.get("achievement_id")
                }
            }
            
            await self.create_timeline_event(user_id, event_data)
            
        except Exception as e:
            logger.error(f"Auto create milestone event error: {str(e)}")

    async def auto_create_goal_event(self, user_id: str, goal: Dict[str, Any], event_type: str):
        """Automatically create timeline event for goal activities"""
        try:
            if event_type == "created":
                title = f"🎯 Set New Goal: {goal.get('category', 'Financial Goal')}"
                description = f"Target: ₹{goal.get('target_amount', 0):,.0f}"
                icon = "🎯"
            elif event_type == "completed":
                title = f"✅ Goal Achieved: {goal.get('category', 'Financial Goal')}"
                description = f"Successfully saved ₹{goal.get('target_amount', 0):,.0f}!"
                icon = "🏆"
            elif event_type == "milestone":
                progress = (goal.get('current_amount', 0) / goal.get('target_amount', 1)) * 100
                title = f"📈 Goal Progress: {progress:.0f}% Complete"
                description = f"{goal.get('category', 'Goal')}: ₹{goal.get('current_amount', 0):,.0f} / ₹{goal.get('target_amount', 0):,.0f}"
                icon = "📈"
            else:
                return
            
            event_data = {
                "event_type": "personal",
                "category": "goal",
                "subcategory": event_type,
                "title": title,
                "description": description,
                "amount": goal.get('current_amount') if event_type != "created" else goal.get('target_amount'),
                "icon": icon,
                "color": "#F59E0B",  # Orange for goals
                "visibility": "friends",
                "is_featured": event_type == "completed",
                "metadata": {
                    "goal_id": goal.get("id"),
                    "goal_category": goal.get("category"),
                    "target_amount": goal.get("target_amount"),
                    "current_amount": goal.get("current_amount")
                }
            }
            
            await self.create_timeline_event(user_id, event_data)
            
        except Exception as e:
            logger.error(f"Auto create goal event error: {str(e)}")

    async def get_timeline_stats(self, user_id: str) -> Dict[str, Any]:
        """Get timeline statistics for user"""
        try:
            # Count events by category
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": "$category",
                    "count": {"$sum": 1},
                    "total_reactions": {"$sum": "$reaction_count"}
                }}
            ]
            
            category_stats = await self.db.timeline_events.aggregate(pipeline).to_list(None)
            
            # Get total stats
            total_events = await self.db.timeline_events.count_documents({"user_id": user_id})
            total_reactions = await self.db.timeline_reactions.count_documents({"timeline_event_id": {"$in": 
                [event["id"] for event in await self.db.timeline_events.find({"user_id": user_id}).to_list(None)]}})
            
            # Get featured events count
            featured_events = await self.db.timeline_events.count_documents({
                "user_id": user_id,
                "is_featured": True
            })
            
            # Get recent activity
            recent_events = await self.db.timeline_events.find({
                "user_id": user_id,
                "created_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=7)}
            }).count()
            
            return {
                "total_events": total_events,
                "total_reactions": total_reactions,
                "featured_events": featured_events,
                "recent_activity": recent_events,
                "category_breakdown": {stat["_id"]: stat["count"] for stat in category_stats},
                "engagement_score": self._calculate_engagement_score(total_events, total_reactions)
            }
            
        except Exception as e:
            logger.error(f"Get timeline stats error: {str(e)}")
            return {}

    async def _enrich_timeline_event(self, event: Dict[str, Any], viewer_user_id: str) -> Dict[str, Any]:
        """Enrich timeline event with additional data"""
        try:
            enriched_event = event.copy()
            
            # Get reactions for this event
            reactions = await self.db.timeline_reactions.find({
                "timeline_event_id": event["id"]
            }).to_list(None)
            
            # Group reactions by type
            reaction_summary = {}
            for reaction in reactions:
                reaction_type = reaction["reaction_type"]
                reaction_summary[reaction_type] = reaction_summary.get(reaction_type, 0) + 1
            
            enriched_event["reactions"] = reaction_summary
            
            # Check if current user reacted
            user_reaction = next(
                (r["reaction_type"] for r in reactions if r["user_id"] == viewer_user_id),
                None
            )
            enriched_event["user_reaction"] = user_reaction
            
            # Add relative time
            enriched_event["relative_time"] = self._get_relative_time(event["event_date"])
            
            # Add user info if it's a social event
            if event["event_type"] == "social" and event.get("related_user_id"):
                related_user = await get_user_by_id(event["related_user_id"])
                if related_user:
                    enriched_event["related_user_info"] = {
                        "name": related_user.get("full_name", "User"),
                        "avatar": related_user.get("avatar", "boy")
                    }
            
            return enriched_event
            
        except Exception as e:
            logger.error(f"Enrich timeline event error: {str(e)}")
            return event

    async def _create_friend_timeline_events(self, user_id: str, personal_event: Dict[str, Any]):
        """Create social timeline events for user's friends"""
        try:
            # Get user's friends
            friends = await self._get_user_friends(user_id)
            
            if not friends:
                return
            
            # Create social events for friends' timelines
            for friend in friends:
                social_event_data = {
                    "event_type": "social",
                    "category": personal_event["category"],
                    "subcategory": personal_event.get("subcategory"),
                    "title": f"Friend Activity: {personal_event['title']}",
                    "description": personal_event["description"],
                    "amount": personal_event.get("amount"),
                    "metadata": personal_event.get("metadata", {}),
                    "related_user_id": user_id,
                    "related_entity_id": personal_event["id"],
                    "icon": personal_event.get("icon", "👥"),
                    "color": personal_event.get("color", "#6B7280"),
                    "event_date": personal_event["event_date"],
                    "visibility": "friends"
                }
                
                await self.create_timeline_event(friend["id"], social_event_data)
            
        except Exception as e:
            logger.error(f"Create friend timeline events error: {str(e)}")

    async def _get_user_friends(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's friends list"""
        try:
            # Get friendships where user is involved (FIXED: use user1_id/user2_id)
            friendships = await self.db.friendships.find({
                "$or": [
                    {"user1_id": user_id},
                    {"user2_id": user_id}
                ],
                "status": "active"
            }).to_list(None)
            
            friend_ids = []
            for friendship in friendships:
                friend_id = friendship["user2_id"] if friendship["user1_id"] == user_id else friendship["user1_id"]
                friend_ids.append(friend_id)
            
            # Get friend user details
            friends = []
            for friend_id in friend_ids:
                friend = await get_user_by_id(friend_id)
                if friend:
                    friends.append(friend)
            
            return friends
            
        except Exception as e:
            logger.error(f"Get user friends error: {str(e)}")
            return []

    async def _create_reaction_notification(self, reactor_user_id: str, event: Dict[str, Any], reaction_type: str):
        """Create notification for event owner about reaction"""
        try:
            # Get reactor user info
            reactor = await get_user_by_id(reactor_user_id)
            if not reactor:
                return
            
            notification_data = {
                "user_id": event["user_id"],
                "type": "timeline_reaction",
                "title": f"New Reaction on Your Activity",
                "message": f"{reactor.get('full_name', 'Someone')} {reaction_type}d your {event['category']}",
                "action_url": f"/timeline?event_id={event['id']}",
                "metadata": {
                    "reactor_id": reactor_user_id,
                    "reactor_name": reactor.get("full_name", "Someone"),
                    "event_id": event["id"],
                    "reaction_type": reaction_type
                }
            }
            
            await self.db.in_app_notifications.insert_one(notification_data)
            
        except Exception as e:
            logger.error(f"Create reaction notification error: {str(e)}")

    def _is_significant_transaction(self, transaction: Dict[str, Any]) -> bool:
        """Determine if transaction is significant enough for timeline"""
        amount = transaction.get("amount", 0)
        transaction_type = transaction.get("type")
        
        # Income transactions are more likely to be shared
        if transaction_type == "income":
            return amount >= 500  # ₹500+ income
        else:  # expense
            return amount >= 1000  # ₹1000+ expense
    
    def _generate_income_title(self, amount: float, category: str, transaction: Dict[str, Any]) -> str:
        """Generate title for income transaction"""
        source = transaction.get("source", "other")
        
        if source == "freelance":
            return f"💼 Earned ₹{amount:,.0f} from Freelancing"
        elif source == "salary":
            return f"💰 Salary Credited: ₹{amount:,.0f}"
        elif source == "scholarship":
            return f"🎓 Scholarship Received: ₹{amount:,.0f}"
        else:
            return f"💵 Income: ₹{amount:,.0f} ({category})"

    def _generate_income_description(self, amount: float, category: str, transaction: Dict[str, Any]) -> str:
        """Generate description for income transaction"""
        description = transaction.get("description", "")
        if description:
            return f"Earned ₹{amount:,.0f} - {description}"
        else:
            return f"Added ₹{amount:,.0f} to my earnings from {category.lower()}"

    def _generate_expense_title(self, amount: float, category: str, transaction: Dict[str, Any]) -> str:
        """Generate title for expense transaction"""
        return f"💳 Spent ₹{amount:,.0f} on {category}"

    def _generate_expense_description(self, amount: float, category: str, transaction: Dict[str, Any]) -> str:
        """Generate description for expense transaction"""
        description = transaction.get("description", "")
        if description:
            return f"₹{amount:,.0f} spent - {description}"
        else:
            return f"Purchased {category.lower()} items worth ₹{amount:,.0f}"

    def _get_income_icon(self, category: str) -> str:
        """Get icon for income category"""
        icons = {
            "freelance": "💼",
            "salary": "💰",
            "scholarship": "🎓",
            "investment": "📈",
            "part_time": "⏰"
        }
        return icons.get(category.lower(), "💵")

    def _get_expense_icon(self, category: str) -> str:
        """Get icon for expense category"""
        icons = {
            "food": "🍽️",
            "transportation": "🚗",
            "entertainment": "🎬",
            "shopping": "🛍️",
            "books": "📚",
            "groceries": "🛒",
            "utilities": "🏠"
        }
        return icons.get(category.lower(), "💳")

    def _generate_milestone_title(self, milestone: Dict[str, Any]) -> str:
        """Generate title for milestone achievement"""
        milestone_type = milestone.get("type")
        threshold = milestone.get("threshold")
        
        if milestone_type == "savings":
            return f"🏆 Savings Milestone: ₹{threshold:,.0f}"
        elif milestone_type == "streak":
            return f"🔥 {threshold}-Day Streak Achieved!"
        elif milestone_type == "transaction_count":
            return f"📊 {threshold} Transactions Milestone!"
        else:
            return f"🎉 New Achievement Unlocked!"

    def _generate_milestone_description(self, milestone: Dict[str, Any]) -> str:
        """Generate description for milestone achievement"""
        milestone_type = milestone.get("type")
        threshold = milestone.get("threshold")
        
        if milestone_type == "savings":
            return f"Successfully saved ₹{threshold:,.0f}! Keep building that financial foundation! 💪"
        elif milestone_type == "streak":
            return f"{threshold} consecutive days of financial tracking! Consistency is key to financial success! 🌟"
        elif milestone_type == "transaction_count":
            return f"Tracked {threshold} transactions! Your financial awareness is growing strong! 📈"
        else:
            return "Another step forward in your financial journey!"

    def _get_milestone_icon(self, milestone_type: str) -> str:
        """Get icon for milestone type"""
        icons = {
            "savings": "💰",
            "streak": "🔥",
            "transaction_count": "📊",
            "goal_completion": "🎯"
        }
        return icons.get(milestone_type, "🏆")

    def _get_relative_time(self, event_date: datetime) -> str:
        """Get relative time string for event"""
        try:
            if isinstance(event_date, str):
                event_date = datetime.fromisoformat(event_date.replace('Z', '+00:00'))
            
            now = datetime.now(timezone.utc)
            diff = now - event_date
            
            if diff.days > 0:
                if diff.days == 1:
                    return "1 day ago"
                elif diff.days < 30:
                    return f"{diff.days} days ago"
                elif diff.days < 365:
                    months = diff.days // 30
                    return f"{months} month{'s' if months > 1 else ''} ago"
                else:
                    years = diff.days // 365
                    return f"{years} year{'s' if years > 1 else ''} ago"
            else:
                hours = diff.seconds // 3600
                if hours > 0:
                    return f"{hours} hour{'s' if hours > 1 else ''} ago"
                else:
                    minutes = diff.seconds // 60
                    if minutes > 0:
                        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
                    else:
                        return "Just now"
                        
        except Exception as e:
            logger.error(f"Get relative time error: {str(e)}")
            return "Unknown"

    def _calculate_engagement_score(self, total_events: int, total_reactions: int) -> float:
        """Calculate engagement score based on events and reactions"""
        if total_events == 0:
            return 0.0
        
        reaction_ratio = total_reactions / total_events
        # Normalize to 0-1 scale (assuming 5 reactions per event is high engagement)
        return min(1.0, reaction_ratio / 5.0)

# Global instance
timeline_service = None

async def get_timeline_service() -> TimelineService:
    global timeline_service
    if timeline_service is None:
        db = await get_database()
        timeline_service = TimelineService(db)
    return timeline_service
