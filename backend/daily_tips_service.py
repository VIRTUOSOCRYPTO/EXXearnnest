import os
import json
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from database import get_database, get_user_by_id
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

class DailyTipsService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.llm_key = os.environ.get('EMERGENT_LLM_KEY')
        self.llm_chat = None
        if self.llm_key:
            try:
                self.llm_chat = LlmChat(api_key=self.llm_key)
            except Exception as e:
                logger.error(f"Failed to initialize LLM chat: {e}")

    async def generate_personalized_tip(self, user_id: str) -> Dict[str, Any]:
        """Generate AI-powered personalized financial tip for user"""
        try:
            # Get user data for personalization
            user = await get_user_by_id(user_id)
            if not user:
                return await self._get_fallback_tip()
            
            # Get user's financial context
            financial_context = await self._get_user_financial_context(user_id)
            personalization = await self._get_user_personalization(user_id)
            
            # Check if we already sent a tip today
            today = datetime.now(timezone.utc).date().isoformat()
            existing_tip = await self.db.daily_tip_notifications.find_one({
                "user_id": user_id,
                "date": today
            })
            
            if existing_tip:
                logger.info(f"Tip already sent today for user {user_id}")
                return existing_tip
            
            # Generate AI tip if LLM is available
            if self.llm_chat and financial_context:
                tip_data = await self._generate_ai_tip(user, financial_context, personalization)
            else:
                tip_data = await self._get_contextualized_fallback_tip(user, financial_context)
            
            # Store the tip
            tip_doc = {
                "tip_id": tip_data["tip_id"],
                "user_id": user_id,
                "date": today,
                "tip_title": tip_data["title"],
                "tip_content": tip_data["content"],
                "tip_type": tip_data.get("type", "tip"),
                "icon": tip_data.get("icon", "💡"),
                "sent_at": datetime.now(timezone.utc),
                "notification_method": personalization.get("notification_method", "both"),
                "metadata": tip_data.get("metadata", {})
            }
            
            await self.db.daily_tip_notifications.insert_one(tip_doc)
            return tip_doc
            
        except Exception as e:
            logger.error(f"Generate personalized tip error: {str(e)}")
            return await self._get_fallback_tip()

    async def _generate_ai_tip(self, user: Dict[str, Any], financial_context: Dict[str, Any], 
                              personalization: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered tip using user's financial data"""
        try:
            # Create personalized prompt
            prompt = f"""
            Generate a personalized daily financial tip for this user:
            
            User Profile:
            - Name: {user.get('full_name', 'User')}
            - Role: {user.get('role', 'Student')}
            - Level: {user.get('student_level', 'undergraduate')}
            - University: {user.get('university', 'Not specified')}
            
            Financial Context:
            - Current Streak: {financial_context.get('current_streak', 0)} days
            - Total Savings: ₹{financial_context.get('total_savings', 0):,.2f}
            - Monthly Spending: ₹{financial_context.get('monthly_spending', 0):,.2f}
            - Top Categories: {', '.join(financial_context.get('top_categories', []))}
            - Goals Progress: {financial_context.get('goals_progress', 'No active goals')}
            - Recent Activity: {financial_context.get('recent_activity', 'No recent activity')}
            
            User Preferences:
            - Learning Focus: {', '.join(personalization.get('learning_preferences', ['general']))}
            - Challenges: {', '.join(personalization.get('current_challenges', []))}
            
            Please generate a tip that is:
            1. Specific to their financial situation
            2. Actionable and practical
            3. Motivating and positive
            4. 50-80 words max
            5. Include relevant emojis
            6. Indian context (INR currency, local savings options)
            
            Respond in JSON format:
            {{
                "title": "Engaging tip title with emoji",
                "content": "Personalized tip content",
                "type": "tip",
                "icon": "💡",
                "category": "budgeting|saving|earning|investing",
                "confidence": 0.85
            }}
            """
            
            # Get AI response
            messages = [UserMessage(content=prompt)]
            response = await asyncio.to_thread(self.llm_chat.chat, messages)
            
            if response and response.content:
                try:
                    tip_data = json.loads(response.content)
                    tip_data["tip_id"] = f"ai_tip_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
                    tip_data["generated_by"] = "ai"
                    tip_data["metadata"] = {
                        "ai_confidence": tip_data.get("confidence", 0.0),
                        "personalization_factors": list(financial_context.keys()),
                        "generated_at": datetime.now(timezone.utc).isoformat()
                    }
                    return tip_data
                except json.JSONDecodeError:
                    logger.error("Invalid JSON response from AI")
                    
        except Exception as e:
            logger.error(f"AI tip generation error: {str(e)}")
        
        return await self._get_contextualized_fallback_tip(user, financial_context)

    async def _get_user_financial_context(self, user_id: str) -> Dict[str, Any]:
        """Get user's financial context for personalization"""
        try:
            context = {}
            
            # Get user basic info
            user = await get_user_by_id(user_id)
            if user:
                context["current_streak"] = user.get("current_streak", 0)
                context["total_savings"] = user.get("net_savings", 0)
                context["level"] = user.get("level", 1)
            
            # Get recent transactions for spending analysis
            recent_transactions = await self.db.transactions.find({
                "user_id": user_id,
                "created_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=30)}
            }).to_list(50)
            
            if recent_transactions:
                # Calculate monthly spending
                expenses = [t for t in recent_transactions if t.get("type") == "expense"]
                monthly_spending = sum(t.get("amount", 0) for t in expenses)
                context["monthly_spending"] = monthly_spending
                
                # Top spending categories
                category_spending = {}
                for transaction in expenses:
                    category = transaction.get("category", "Other")
                    category_spending[category] = category_spending.get(category, 0) + transaction.get("amount", 0)
                
                top_categories = sorted(category_spending.items(), key=lambda x: x[1], reverse=True)[:3]
                context["top_categories"] = [cat[0] for cat in top_categories]
                
                # Recent activity summary
                context["recent_activity"] = f"{len(recent_transactions)} transactions in last 30 days"
            else:
                context["monthly_spending"] = 0
                context["top_categories"] = []
                context["recent_activity"] = "No recent transactions"
            
            # Get financial goals progress
            goals = await self.db.financial_goals.find({"user_id": user_id, "status": "active"}).to_list(10)
            if goals:
                goals_summary = []
                for goal in goals:
                    progress = (goal.get("current_amount", 0) / goal.get("target_amount", 1)) * 100
                    goals_summary.append(f"{goal.get('category', 'Goal')}: {progress:.0f}%")
                context["goals_progress"] = "; ".join(goals_summary)
            else:
                context["goals_progress"] = "No active goals"
            
            return context
            
        except Exception as e:
            logger.error(f"Get financial context error: {str(e)}")
            return {}

    async def _get_user_personalization(self, user_id: str) -> Dict[str, Any]:
        """Get user's tip personalization preferences"""
        try:
            personalization = await self.db.daily_tip_personalizations.find_one({"user_id": user_id})
            
            if not personalization:
                # Create default personalization
                default_personalization = {
                    "user_id": user_id,
                    "learning_preferences": ["budgeting", "saving"],
                    "tip_delivery_time": "09:00",
                    "tip_frequency": "daily",
                    "notification_method": "both",
                    "engagement_score": 0.5,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
                await self.db.daily_tip_personalizations.insert_one(default_personalization)
                return default_personalization
            
            return personalization
            
        except Exception as e:
            logger.error(f"Get personalization error: {str(e)}")
            return {
                "learning_preferences": ["general"],
                "notification_method": "both",
                "engagement_score": 0.5
            }

    async def _get_contextualized_fallback_tip(self, user: Dict[str, Any], 
                                              financial_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get contextualized fallback tip based on user data"""
        try:
            from datetime import datetime
            import random
            
            # Contextualized tips based on user situation
            tips_by_context = []
            
            # Streak-based tips
            streak = financial_context.get("current_streak", 0)
            if streak == 0:
                tips_by_context.extend([
                    {
                        "title": "🌟 Start Your Financial Journey!",
                        "content": "Track just one transaction today to begin your streak. Small steps lead to big financial wins! Even ₹10 tracking counts.",
                        "category": "streak"
                    },
                    {
                        "title": "💪 First Step Matters!",
                        "content": "Begin your financial tracking journey today. Log your morning coffee expense and watch your awareness grow!",
                        "category": "streak"
                    }
                ])
            elif streak < 7:
                tips_by_context.extend([
                    {
                        "title": f"🔥 {streak}-Day Streak Building!",
                        "content": f"You're {7-streak} days away from your first week! Keep tracking daily to build lasting financial habits.",
                        "category": "streak"
                    }
                ])
            elif streak >= 30:
                tips_by_context.extend([
                    {
                        "title": f"🏆 {streak}-Day Champion!",
                        "content": "Your consistency is impressive! Use this habit to set bigger financial goals and track investment opportunities.",
                        "category": "advanced"
                    }
                ])
            
            # Savings-based tips
            savings = financial_context.get("total_savings", 0)
            if savings > 0:
                tips_by_context.extend([
                    {
                        "title": "💰 Growing Your ₹" + f"{savings:,.0f}",
                        "content": "Consider opening a high-yield savings account or exploring SIPs in mutual funds for your growing savings!",
                        "category": "investing"
                    }
                ])
            
            # Spending-based tips
            monthly_spending = financial_context.get("monthly_spending", 0)
            top_categories = financial_context.get("top_categories", [])
            
            if "Food" in top_categories or "Groceries" in top_categories:
                tips_by_context.append({
                    "title": "🍽️ Smart Food Budgeting",
                    "content": "Try meal prep Sundays! Plan your week's meals to reduce food delivery costs by 40-50%. Your wallet will thank you!",
                    "category": "budgeting"
                })
            
            if "Transportation" in top_categories:
                tips_by_context.append({
                    "title": "🚗 Transport Savings Hack",
                    "content": "Mix and match transport modes! Use public transport 3 days, bike/walk 2 days. Save ₹500-800 monthly easily!",
                    "category": "budgeting"
                })
            
            # Role-based tips
            role = user.get("role", "Student")
            if role == "Student":
                tips_by_context.extend([
                    {
                        "title": "🎓 Student Money Hack",
                        "content": "Use student discounts on software, food, and entertainment. Many offer 50%+ off - Amazon Prime, Spotify, Adobe!",
                        "category": "earning"
                    },
                    {
                        "title": "📚 Textbook Savings",
                        "content": "Buy used books or rent them online. Use library resources and study groups to cut costs by 60%!",
                        "category": "budgeting"
                    }
                ])
            
            # General financial tips
            general_tips = [
                {
                    "title": "🏦 Emergency Fund Rule",
                    "content": "Build an emergency fund worth 3-6 months of expenses. Start with just ₹500/month - consistency matters more than amount!",
                    "category": "saving"
                },
                {
                    "title": "📊 50-30-20 Budget Rule",
                    "content": "Allocate 50% needs, 30% wants, 20% savings. This simple rule helps balance enjoying today while securing tomorrow!",
                    "category": "budgeting"
                },
                {
                    "title": "💳 Credit Card Smart Use",
                    "content": "Pay full amount before due date to avoid interest. Use cards for rewards but never spend more than you have!",
                    "category": "budgeting"
                },
                {
                    "title": "🎯 SMART Financial Goals",
                    "content": "Make goals Specific, Measurable, Achievable, Relevant, Time-bound. Instead of 'save more', try 'save ₹5000 by March'!",
                    "category": "planning"
                }
            ]
            
            # Combine contextualized and general tips
            all_tips = tips_by_context + general_tips
            if not all_tips:
                all_tips = general_tips
            
            # Select random tip
            selected_tip = random.choice(all_tips)
            
            return {
                "tip_id": f"fallback_tip_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                "title": selected_tip["title"],
                "content": selected_tip["content"],
                "type": "tip",
                "icon": "💡",
                "generated_by": "fallback",
                "metadata": {
                    "category": selected_tip.get("category", "general"),
                    "contextualized": len(tips_by_context) > 0,
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Contextualized fallback tip error: {str(e)}")
            return await self._get_fallback_tip()

    async def _get_fallback_tip(self) -> Dict[str, Any]:
        """Get basic fallback tip when all else fails"""
        import random
        
        fallback_tips = [
            {
                "title": "💡 Daily Financial Wisdom",
                "content": "Track every expense, no matter how small. Awareness is the first step to financial freedom!",
            },
            {
                "title": "🎯 Save Smart Today",
                "content": "Start with small amounts. Even ₹50 saved daily becomes ₹18,250 in a year!",
            },
            {
                "title": "📱 Digital Tracking",
                "content": "Use apps to track expenses instantly. The habit of immediate logging builds financial awareness!",
            }
        ]
        
        selected_tip = random.choice(fallback_tips)
        
        return {
            "tip_id": f"basic_fallback_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "title": selected_tip["title"],
            "content": selected_tip["content"],
            "type": "tip",
            "icon": "💡",
            "generated_by": "basic_fallback",
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        }

    async def send_daily_tips_batch(self) -> int:
        """Send daily tips to all eligible users"""
        try:
            # Get all users who should receive tips
            eligible_users = await self._get_eligible_users_for_tips()
            
            tips_sent = 0
            for user in eligible_users:
                try:
                    tip = await self.generate_personalized_tip(user["id"])
                    if tip:
                        # Send via push notification if enabled
                        await self._send_tip_notification(user["id"], tip)
                        tips_sent += 1
                        
                except Exception as e:
                    logger.error(f"Failed to send tip to user {user['id']}: {str(e)}")
                    continue
            
            logger.info(f"Daily tips batch completed: {tips_sent} tips sent")
            return tips_sent
            
        except Exception as e:
            logger.error(f"Send daily tips batch error: {str(e)}")
            return 0

    async def _get_eligible_users_for_tips(self) -> List[Dict[str, Any]]:
        """Get users eligible for daily tips"""
        try:
            # Get users who haven't received a tip today
            today = datetime.now(timezone.utc).date().isoformat()
            
            # Find users who received tips today
            users_with_tips_today = await self.db.daily_tip_notifications.distinct("user_id", {"date": today})
            
            # Get all active users not in the above list
            users = await self.db.users.find({
                "is_active": True,
                "id": {"$nin": users_with_tips_today}
            }).to_list(None)
            
            # Filter based on personalization preferences
            eligible_users = []
            for user in users:
                personalization = await self._get_user_personalization(user["id"])
                
                # Check if user wants daily tips and it's their preferred time
                if self._is_tip_time_for_user(personalization):
                    eligible_users.append(user)
            
            return eligible_users
            
        except Exception as e:
            logger.error(f"Get eligible users error: {str(e)}")
            return []

    def _is_tip_time_for_user(self, personalization: Dict[str, Any]) -> bool:
        """Check if it's time to send tip to user based on their preferences"""
        try:
            frequency = personalization.get("tip_frequency", "daily")
            
            if frequency == "daily":
                return True
            elif frequency == "every_other_day":
                # Check if they got a tip yesterday
                yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
                return personalization.get("last_tip_sent") != yesterday
            elif frequency == "weekly":
                # Check if they got a tip in the last 7 days
                week_ago = datetime.now(timezone.utc) - timedelta(days=7)
                return personalization.get("last_tip_sent", datetime.min) < week_ago
            
            return True
            
        except Exception as e:
            logger.error(f"Check tip time error: {str(e)}")
            return False

    async def _send_tip_notification(self, user_id: str, tip: Dict[str, Any]):
        """Send tip via push notification"""
        try:
            # Import here to avoid circular imports
            from push_notification_service import get_push_service
            
            push_service = await get_push_service()
            if push_service:
                notification_data = {
                    "title": tip["tip_title"],
                    "message": tip["tip_content"],
                    "type": "daily_tip",
                    "tip_id": tip["tip_id"]
                }
                
                await push_service.send_daily_tip_notification(user_id, notification_data)
                
        except Exception as e:
            logger.error(f"Send tip notification error: {str(e)}")

    async def record_tip_interaction(self, user_id: str, tip_id: str, interaction_type: str, 
                                   interaction_data: Dict[str, Any] = None) -> bool:
        """Record user interaction with daily tip"""
        try:
            interaction_doc = {
                "user_id": user_id,
                "tip_id": tip_id,
                "interaction_type": interaction_type,
                "interaction_data": interaction_data or {},
                "created_at": datetime.now(timezone.utc)
            }
            
            await self.db.daily_tip_interactions.insert_one(interaction_doc)
            
            # Update tip viewed status if this is a view
            if interaction_type == "viewed":
                await self.db.daily_tip_notifications.update_one(
                    {"tip_id": tip_id, "user_id": user_id},
                    {"$set": {"viewed_at": datetime.now(timezone.utc)}}
                )
            
            # Update user's engagement score
            await self._update_user_engagement_score(user_id, interaction_type)
            
            return True
            
        except Exception as e:
            logger.error(f"Record tip interaction error: {str(e)}")
            return False

    async def _update_user_engagement_score(self, user_id: str, interaction_type: str):
        """Update user's engagement score based on interaction"""
        try:
            score_updates = {
                "viewed": 0.1,
                "liked": 0.3,
                "shared": 0.5,
                "saved": 0.4,
                "dismissed": -0.1
            }
            
            score_change = score_updates.get(interaction_type, 0)
            
            await self.db.daily_tip_personalizations.update_one(
                {"user_id": user_id},
                {
                    "$inc": {"engagement_score": score_change},
                    "$set": {"updated_at": datetime.now(timezone.utc)},
                    "$max": {"engagement_score": 1.0},
                    "$min": {"engagement_score": 0.0}
                }
            )
            
        except Exception as e:
            logger.error(f"Update engagement score error: {str(e)}")

# Global instance
daily_tips_service = None

async def get_daily_tips_service() -> DailyTipsService:
    global daily_tips_service
    if daily_tips_service is None:
        db = await get_database()
        daily_tips_service = DailyTipsService(db)
    return daily_tips_service
