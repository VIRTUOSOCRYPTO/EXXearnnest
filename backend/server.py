from fastapi import FastAPI, APIRouter, HTTPException, Depends, File, UploadFile, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from pathlib import Path
import os
import logging
import shutil
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

# Import our enhanced modules
from models import *
from security import *
from database import *
from email_service import email_service
from emergentintegrations.llm.chat import LlmChat, UserMessage
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from cache_service import cache_service
from fallback_hospital_db import fallback_db

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Ensure uploads directory exists
UPLOADS_DIR = ROOT_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# Create the main app
app = FastAPI(
    title="EarnNest - Student Finance & Side Hustle Platform",
    description="Production-ready platform for student financial management and side hustles",
    version="2.0.0",
    docs_url="/api/docs" if os.environ.get("ENVIRONMENT") != "production" else None,
    redoc_url="/api/redoc" if os.environ.get("ENVIRONMENT") != "production" else None
)

# Serve static files for uploads
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Create API router
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# LLM Chat instance
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Rate limiting setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Trust only specific hosts in production
if os.environ.get("ENVIRONMENT") == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=os.environ.get("ALLOWED_HOSTS", "localhost").split(',')
    )

# Add rate limiting error handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    response = JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"}
    )
    response = request.app.state.limiter._inject_headers(response, request.state.view_rate_limit)
    return response

# Global exception handler for better error messages
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."}
    )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Get current authenticated user"""
    user_id = verify_jwt_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Check if user exists and is active
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Account deactivated")
    
    return user_id

async def get_current_admin(user_id: str = Depends(get_current_user)) -> str:
    """Get current authenticated admin user"""
    user = await get_user_by_id(user_id)
    if not user or not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id

async def get_enhanced_ai_hustle_recommendations(user_skills: List[str], availability: int, recent_earnings: float, location: str = None) -> List[Dict]:
    """Generate enhanced AI-powered hustle recommendations based on user skills"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"hustle_rec_{uuid.uuid4()}",
            system_message="""You are an AI advisor for student side hustles in India. Based on user skills, generate personalized side hustle recommendations. 
            
            Skill-based recommendations:
            - Freelancing → "Freelance Services", "Remote Work", "Consultation"
            - Graphic Design → "Logo Design", "Social Media Graphics", "Poster/Flyer Design"  
            - Coding → "Website Development", "App Development", "Automation Scripts"
            - Digital Marketing → "Social Media Campaigns", "SEO Consulting", "Content Strategy"
            - Content Writing → "Blog Writing", "Copywriting", "Technical Writing"
            - Video Editing → "YouTube Shorts", "Promotional Videos", "TikTok Content"
            - AI Tools & Automation → "Chatbot Development", "AI Content Generation", "Process Automation"
            - Social Media Management → "Account Management", "Content Planning", "Community Building"
            
            Return ONLY a JSON array with this exact format:
            [
                {
                    "title": "Exact hustle title based on skills",
                    "description": "Brief description for Indian market",
                    "category": "tutoring|freelance|content_creation|delivery|micro_tasks",
                    "estimated_pay": number (in INR per hour),
                    "time_commitment": "X hours/week",
                    "required_skills": ["skill1", "skill2"],
                    "difficulty_level": "beginner|intermediate|advanced",
                    "platform": "Platform name or method",
                    "match_score": number between 0-100
                }
            ]"""
        ).with_model("openai", "gpt-4o")
        
        location_context = f" in {location}" if location else " in India"
        earnings_context = f"Current monthly earnings: ₹{recent_earnings}" if recent_earnings > 0 else "No current side hustle earnings"
        
        user_message = UserMessage(
            text=f"User skills: {', '.join(user_skills) if user_skills else 'General skills'}. Available {availability} hours/week{location_context}. {earnings_context}. Generate 6 personalized side hustle opportunities based on these specific skills with Indian market focus and INR rates."
        )
        
        response = await chat.send_message(user_message)
        
        # Try to parse JSON response
        import json
        try:
            recommendations = json.loads(response)
            return recommendations[:6]  # Ensure max 6 recommendations
        except json.JSONDecodeError:
            # Fallback recommendations based on skills
            skill_based_hustles = []
            
            for skill in user_skills:
                if "graphic design" in skill.lower():
                    skill_based_hustles.extend([
                        {
                            "title": "Freelance Logo Design",
                            "description": "Design logos for small Indian businesses and startups",
                            "category": "freelance",
                            "estimated_pay": 500.0,
                            "time_commitment": "8-12 hours/week",
                            "required_skills": ["Graphic Design", "Creative Thinking"],
                            "difficulty_level": "intermediate",
                            "platform": "Upwork, Fiverr, Truelancer",
                            "match_score": 95.0
                        },
                        {
                            "title": "Social Media Graphics Designer",
                            "description": "Create graphics for Indian social media campaigns",
                            "category": "content_creation",
                            "estimated_pay": 400.0,
                            "time_commitment": "10-15 hours/week",
                            "required_skills": ["Graphic Design", "Social Media"],
                            "difficulty_level": "beginner",
                            "platform": "Direct Client Outreach, Instagram",
                            "match_score": 90.0
                        }
                    ])
                
                if "coding" in skill.lower():
                    skill_based_hustles.extend([
                        {
                            "title": "Website Development",
                            "description": "Build websites for Indian small businesses",
                            "category": "freelance",
                            "estimated_pay": 800.0,
                            "time_commitment": "15-20 hours/week",
                            "required_skills": ["Coding", "Web Development"],
                            "difficulty_level": "intermediate",
                            "platform": "Upwork, Freelancer, Local Contacts",
                            "match_score": 95.0
                        },
                        {
                            "title": "App Development",
                            "description": "Create mobile apps for Indian startups",
                            "category": "freelance",
                            "estimated_pay": 1000.0,
                            "time_commitment": "20+ hours/week",
                            "required_skills": ["Coding", "Mobile Development"],
                            "difficulty_level": "advanced",
                            "platform": "Upwork, AngelList, Direct Contacts",
                            "match_score": 90.0
                        }
                    ])
                
                if "digital marketing" in skill.lower():
                    skill_based_hustles.extend([
                        {
                            "title": "Social Media Campaign Management",
                            "description": "Manage social media campaigns for Indian brands",
                            "category": "content_creation",
                            "estimated_pay": 600.0,
                            "time_commitment": "10-15 hours/week",
                            "required_skills": ["Digital Marketing", "Analytics"],
                            "difficulty_level": "intermediate",
                            "platform": "Direct Client Outreach",
                            "match_score": 88.0
                        }
                    ])
                
                if "content writing" in skill.lower():
                    skill_based_hustles.extend([
                        {
                            "title": "Blog Writing for Indian Businesses",
                            "description": "Write blogs and articles for Indian companies",
                            "category": "freelance",
                            "estimated_pay": 300.0,
                            "time_commitment": "8-12 hours/week",
                            "required_skills": ["Content Writing", "Research"],
                            "difficulty_level": "beginner",
                            "platform": "Upwork, ContentKing, Truelancer",
                            "match_score": 85.0
                        }
                    ])
            
            # If no skill-based hustles found, return general recommendations
            if not skill_based_hustles:
                return [
                    {
                        "title": "Online Tutoring (BYJU'S/Vedantu)",
                        "description": "Teach subjects you excel in to students across India",
                        "category": "tutoring",
                        "estimated_pay": 300.0,
                        "time_commitment": "10-15 hours/week",
                        "required_skills": user_skills[:2] if user_skills else ["Subject Knowledge"],
                        "difficulty_level": "beginner",
                        "platform": "BYJU'S, Vedantu, Unacademy",
                        "match_score": 80.0
                    }
                ]
            
            return skill_based_hustles[:6]
            
    except Exception as e:
        logging.error(f"AI recommendation error: {e}")
        return []

async def get_dynamic_financial_insights(user_id: str) -> Dict[str, Any]:
    """Generate dynamic AI-powered financial insights based on user activity"""
    try:
        # Get user's financial data
        user_doc = await get_user_by_id(user_id)
        transactions = await get_user_transactions(user_id, limit=50)
        budgets = await get_user_budgets(user_id)
        goals = await get_user_financial_goals(user_id)
        
        if not transactions:
            return {"insights": ["Start tracking your expenses to get personalized insights!"]}
        
        # Calculate comprehensive stats
        total_income = sum(t["amount"] for t in transactions if t["type"] == "income")
        total_expenses = sum(t["amount"] for t in transactions if t["type"] == "expense")
        net_savings = total_income - total_expenses
        
        # Calculate budget utilization
        budget_stats = {}
        for budget in budgets:
            category = budget["category"]
            utilization = (budget["spent_amount"] / budget["allocated_amount"]) * 100
            budget_stats[category] = {
                "allocated": budget["allocated_amount"],
                "spent": budget["spent_amount"],
                "remaining": budget["allocated_amount"] - budget["spent_amount"],
                "utilization": utilization
            }
        
        # Calculate goal progress
        goal_stats = {}
        for goal in goals:
            progress = (goal["current_amount"] / goal["target_amount"]) * 100
            goal_stats[goal["name"]] = {
                "target": goal["target_amount"],
                "current": goal["current_amount"],
                "progress": progress,
                "remaining": goal["target_amount"] - goal["current_amount"]
            }
        
        # Income streak calculation (days with income since registration)
        income_transactions = [t for t in transactions if t["type"] == "income"]
        income_dates = [t["date"] for t in income_transactions]
        income_streak = calculate_income_streak(income_dates, user_doc.get("created_at"))
        
        # Generate dynamic insights
        insights = []
        
        # Savings insights
        if net_savings > 0:
            savings_rate = (net_savings / total_income) * 100 if total_income > 0 else 0
            if savings_rate > 20:
                insights.append(f"Excellent! You're saving {savings_rate:.1f}% of your income - keep up the great work! 🎉")
            elif savings_rate > 10:
                insights.append(f"Good job! You're saving {savings_rate:.1f}% of your income. Aim for 20% for better financial health! 💪")
            else:
                insights.append(f"You're saving {savings_rate:.1f}% of your income. Try to increase savings to 20% for better financial security! 📈")
        
        # Budget insights
        over_budget_categories = [cat for cat, stats in budget_stats.items() if stats["utilization"] > 90]
        under_budget_categories = [cat for cat, stats in budget_stats.items() if stats["utilization"] < 50]
        
        if over_budget_categories:
            for category in over_budget_categories[:2]:  # Limit to 2 categories
                remaining = budget_stats[category]["remaining"]
                if remaining <= 0:
                    insights.append(f"⚠️ You've exceeded your {category} budget! Consider reducing expenses in this category.")
                else:
                    insights.append(f"⚠️ You're close to your {category} budget limit. Only ₹{remaining:.0f} remaining!")
        
        if under_budget_categories:
            best_category = min(under_budget_categories, key=lambda x: budget_stats[x]["utilization"])
            saved_amount = budget_stats[best_category]["remaining"]
            insights.append(f"Great job! Your {best_category} budget is under control. You've saved ₹{saved_amount:.0f} this month! 🎯")
        
        # Goal insights
        for goal_name, stats in goal_stats.items():
            if stats["progress"] > 75:
                insights.append(f"🎊 You're {stats['progress']:.0f}% towards your {goal_name} goal! Almost there!")
            elif stats["progress"] > 50:
                insights.append(f"💪 You've reached {stats['progress']:.0f}% of your {goal_name} target. Keep going!")
            elif stats["progress"] > 25:
                insights.append(f"📈 You're {stats['progress']:.0f}% towards your {goal_name}. Consider increasing your savings rate!")
        
        # Income streak insights
        if income_streak >= 7:
            insights.append(f"🔥 Amazing! You're on a {income_streak}-day income streak - achievement unlocked soon!")
        elif income_streak >= 3:
            insights.append(f"💼 Good momentum! You're on a {income_streak}-day income streak. Keep it up!")
        
        # Spending pattern insights
        expense_categories = {}
        for transaction in transactions:
            if transaction["type"] == "expense":
                category = transaction["category"]
                expense_categories[category] = expense_categories.get(category, 0) + transaction["amount"]
        
        if expense_categories:
            highest_expense_category = max(expense_categories, key=expense_categories.get)
            highest_amount = expense_categories[highest_expense_category]
            insights.append(f"💡 Your highest expense category is {highest_expense_category} (₹{highest_amount:.0f}). Consider reviewing these expenses!")
        
        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_savings": net_savings,
            "savings_rate": (net_savings / total_income) * 100 if total_income > 0 else 0,
            "income_streak": income_streak,
            "budget_stats": budget_stats,
            "goal_stats": goal_stats,
            "insights": insights[:5]  # Limit to 5 most relevant insights
        }
        
    except Exception as e:
        logging.error(f"Dynamic financial insights error: {e}")
        return {"insights": ["Keep tracking your finances to unlock AI-powered insights!"]}

def calculate_income_streak(income_dates, registration_date=None):
    """Calculate income days since registration"""
    if not income_dates:
        return 0
    
    # If no registration date provided, fall back to old logic
    if not registration_date:
        sorted_dates = sorted(income_dates, reverse=True)
        current_date = datetime.now(timezone.utc).date()
        
        streak = 0
        check_date = current_date
        
        for income_date in sorted_dates:
            income_day = income_date.date() if hasattr(income_date, 'date') else income_date
            days_diff = (check_date - income_day).days
            
            if days_diff <= 1:
                streak += 1
                check_date = income_day - timedelta(days=1)
            else:
                break
        return streak
    
    # New logic: Count days with income since registration
    reg_date = registration_date.date() if hasattr(registration_date, 'date') else registration_date
    
    # Get unique income days since registration
    income_days = set()
    for income_date in income_dates:
        income_day = income_date.date() if hasattr(income_date, 'date') else income_date
        if income_day >= reg_date:
            income_days.add(income_day)
    
    return len(income_days)

async def update_monthly_income_goal_progress(user_id: str):
    """Update Monthly Income Goal progress based on actual income transactions"""
    try:
        # Find the monthly income goal
        monthly_goal = await db.financial_goals.find_one({
            "user_id": user_id,
            "category": "monthly_income",
            "is_active": True
        })
        
        if not monthly_goal:
            return  # No monthly income goal to update
        
        # Calculate current month's income
        current_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = current_month.replace(month=current_month.month + 1) if current_month.month < 12 else current_month.replace(year=current_month.year + 1, month=1)
        
        # Get income transactions for current month
        income_transactions = await db.transactions.find({
            "user_id": user_id,
            "type": "income",
            "date": {"$gte": current_month, "$lt": next_month}
        }).to_list(None)
        
        # Calculate total monthly income
        monthly_income = sum(transaction["amount"] for transaction in income_transactions)
        
        # Update the goal's current amount
        await db.financial_goals.update_one(
            {"_id": monthly_goal["_id"]},
            {
                "$set": {
                    "current_amount": monthly_income,
                    "updated_at": datetime.now(timezone.utc),
                    "is_completed": monthly_income >= monthly_goal["target_amount"]
                }
            }
        )
        
        logger.info(f"Updated monthly income goal for user {user_id}: ₹{monthly_income}/₹{monthly_goal['target_amount']}")
        
    except Exception as e:
        logger.error(f"Error updating monthly income goal: {e}")
        # Don't raise exception as this is a background update

# Emergency Services Helper Functions
async def get_area_info_from_coordinates(latitude: float, longitude: float) -> Dict[str, str]:
    """Get area information from coordinates (simplified implementation)"""
    try:
        # This is a simplified implementation
        # In production, you would use a proper geocoding service like Google Maps API
        return {
            "area": "Central Area",
            "city": "Bangalore",
            "state": "Karnataka"
        }
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        return {"area": "Unknown Area", "city": "Bangalore", "state": "Karnataka"}

async def get_nearby_emergency_hospitals(latitude: float, longitude: float) -> List[Dict]:
    """Get nearby emergency hospitals"""
    # Mock data - in production, integrate with Google Places API or similar
    hospitals = [
        {
            "name": "Manipal Hospital",
            "address": "98, Rustom Bagh, Airport Rd, Bangalore",
            "phone": "+91-80-2502-4444",
            "distance": "2.3 km",
            "emergency_services": ["24/7 Emergency", "Trauma Center", "ICU"],
            "rating": 4.2
        },
        {
            "name": "Fortis Hospital",
            "address": "154/9, Bannerghatta Rd, Bangalore",
            "phone": "+91-80-6621-4444",
            "distance": "3.1 km",
            "emergency_services": ["Emergency Ward", "Cardiac Care", "Ambulance"],
            "rating": 4.1
        },
        {
            "name": "Apollo Hospital",
            "address": "154/11, Bannerghatta Rd, Bangalore",
            "phone": "+91-80-2630-0300",
            "distance": "4.2 km",
            "emergency_services": ["24/7 Emergency", "Multi-specialty", "Blood Bank"],
            "rating": 4.3
        }
    ]
    return hospitals

async def get_nearby_police_stations(latitude: float, longitude: float) -> List[Dict]:
    """Get nearby police stations"""
    police_stations = [
        {
            "name": "Koramangala Police Station",
            "address": "80 Feet Rd, 5th Block, Koramangala, Bangalore",
            "phone": "+91-80-2553-2324",
            "distance": "1.8 km",
            "services": ["Emergency Response", "FIR Registration", "Traffic Police"],
            "emergency_number": "100"
        },
        {
            "name": "BTM Layout Police Station",
            "address": "16th Main Rd, BTM 2nd Stage, Bangalore",
            "phone": "+91-80-2668-1101",
            "distance": "2.5 km",
            "services": ["Crime Investigation", "Women Safety", "Cyber Crime"],
            "emergency_number": "100"
        }
    ]
    return police_stations

async def get_nearby_atms_banks(latitude: float, longitude: float) -> List[Dict]:
    """Get nearby ATMs and banks"""
    atms_banks = [
        {
            "name": "SBI ATM",
            "type": "ATM",
            "address": "Forum Mall, Koramangala, Bangalore",
            "distance": "0.8 km",
            "services": ["Cash Withdrawal", "Balance Inquiry", "24/7 Available"],
            "bank": "State Bank of India"
        },
        {
            "name": "HDFC Bank",
            "type": "Bank",
            "address": "Koramangala 5th Block, Bangalore",
            "distance": "1.2 km",
            "services": ["Banking Services", "ATM", "Emergency Cash"],
            "phone": "+91-80-2553-4567",
            "hours": "10:00 AM - 4:00 PM"
        },
        {
            "name": "ICICI Bank ATM",
            "type": "ATM",
            "address": "BTM Layout, Bangalore",
            "distance": "1.5 km",
            "services": ["Cash Withdrawal", "Mini Statement", "24/7 Available"],
            "bank": "ICICI Bank"
        }
    ]
    return atms_banks

async def get_nearby_pharmacies(latitude: float, longitude: float) -> List[Dict]:
    """Get nearby pharmacies"""
    pharmacies = [
        {
            "name": "Apollo Pharmacy",
            "address": "Forum Mall, Koramangala, Bangalore",
            "phone": "+91-80-2553-7890",
            "distance": "0.9 km",
            "services": ["24/7 Open", "Emergency Medicines", "Home Delivery"],
            "rating": 4.2
        },
        {
            "name": "MedPlus",
            "address": "5th Block, Koramangala, Bangalore",
            "phone": "+91-80-2553-1234",
            "distance": "1.1 km",
            "services": ["Prescription Medicines", "Health Products", "Online Orders"],
            "rating": 4.0
        },
        {
            "name": "Netmeds",
            "address": "BTM Layout, Bangalore",
            "phone": "+91-80-2668-5678",
            "distance": "2.0 km",
            "services": ["Medicine Delivery", "Health Checkups", "24/7 Support"],
            "rating": 4.1
        }
    ]
    return pharmacies

async def get_nearby_gas_stations(latitude: float, longitude: float) -> List[Dict]:
    """Get nearby gas stations"""
    gas_stations = [
        {
            "name": "Indian Oil Petrol Pump",
            "address": "Hosur Main Rd, Koramangala, Bangalore",
            "distance": "1.3 km",
            "services": ["Petrol", "Diesel", "Air & Water", "24/7 Open"],
            "fuel_types": ["Petrol", "Diesel", "CNG"]
        },
        {
            "name": "HP Petrol Pump",
            "address": "Bannerghatta Rd, BTM Layout, Bangalore",
            "distance": "2.1 km",
            "services": ["Fuel", "Convenience Store", "ATM"],
            "fuel_types": ["Petrol", "Diesel"]
        }
    ]
    return gas_stations

async def get_nearby_fire_stations(latitude: float, longitude: float) -> List[Dict]:
    """Get nearby fire stations"""
    fire_stations = [
        {
            "name": "Koramangala Fire Station",
            "address": "80 Feet Rd, Koramangala, Bangalore",
            "phone": "+91-80-2553-0101",
            "distance": "2.0 km",
            "services": ["Fire Emergency", "Rescue Operations", "Ambulance"],
            "emergency_number": "101"
        },
        {
            "name": "BTM Fire Station",
            "address": "BTM Layout, Bangalore",
            "phone": "+91-80-2668-0101",
            "distance": "3.2 km",
            "services": ["Fire Fighting", "Emergency Response", "Safety Training"],
            "emergency_number": "101"
        }
    ]
    return fire_stations

async def get_nearby_emergency_shelters(latitude: float, longitude: float) -> List[Dict]:
    """Get nearby emergency shelters"""
    shelters = [
        {
            "name": "Government Emergency Shelter",
            "address": "Koramangala Social Welfare Office, Bangalore",
            "phone": "+91-80-2553-2000",
            "distance": "2.5 km",
            "services": ["Temporary Accommodation", "Food", "Medical Aid"],
            "capacity": "50 people",
            "availability": "24/7"
        },
        {
            "name": "NGO Relief Center",
            "address": "BTM Layout Community Center, Bangalore",
            "phone": "+91-80-2668-3000",
            "distance": "3.0 km",
            "services": ["Emergency Housing", "Counseling", "Basic Necessities"],
            "capacity": "30 people",
            "availability": "Emergency basis"
        }
    ]
    return shelters

async def get_local_emergency_contacts(city: str = "Bangalore") -> Dict[str, List[Dict]]:
    """Get local emergency contacts"""
    contacts = {
        "emergency_numbers": [
            {"service": "Police", "number": "100", "description": "Police Emergency"},
            {"service": "Fire", "number": "101", "description": "Fire Emergency"},
            {"service": "Ambulance", "number": "102", "description": "Medical Emergency"},
            {"service": "Disaster Management", "number": "108", "description": "Emergency Response"}
        ],
        "helplines": [
            {"service": "Women Helpline", "number": "1091", "description": "Women in Distress"},
            {"service": "Child Helpline", "number": "1098", "description": "Child Emergency"},
            {"service": "Senior Citizen", "number": "14567", "description": "Elder Care Emergency"},
            {"service": "Mental Health", "number": "9152987821", "description": "Crisis Counseling"}
        ],
        "local_services": [
            {"service": "BBMP Control Room", "number": "+91-80-2221-1111", "description": "Bangalore City Services"},
            {"service": "Traffic Police", "number": "+91-80-2294-2444", "description": "Traffic Emergency"},
            {"service": "Electricity Board", "number": "1912", "description": "Power Emergency"},
            {"service": "Water Board", "number": "+91-80-2294-4444", "description": "Water Emergency"}
        ]
    }
    return contacts
# Enhanced Authentication Routes with Comprehensive OTP Security
@api_router.get("/auth/trending-skills")
async def get_trending_skills():
    """Get trending skills for registration and profile updates"""
    trending_skills = [
        {"name": "Freelancing", "category": "Business", "icon": "💼"},
        {"name": "Graphic Design", "category": "Creative", "icon": "🎨"},
        {"name": "Coding", "category": "Technical", "icon": "💻"},
        {"name": "Digital Marketing", "category": "Marketing", "icon": "📱"},
        {"name": "Content Writing", "category": "Creative", "icon": "✍️"},
        {"name": "Video Editing", "category": "Creative", "icon": "🎬"},
        {"name": "AI Tools & Automation", "category": "Technical", "icon": "🤖"},
        {"name": "Social Media Management", "category": "Marketing", "icon": "📊"}
    ]
    return {"trending_skills": trending_skills}

@api_router.get("/auth/avatars")
async def get_available_avatars():
    """Get available avatar options"""
    avatars = [
        {"value": "boy", "label": "Boy", "category": "youth"},
        {"value": "man", "label": "Man", "category": "adult"},
        {"value": "girl", "label": "Girl", "category": "youth"},
        {"value": "woman", "label": "Woman", "category": "adult"},
        {"value": "grandfather", "label": "Grandfather (GF)", "category": "senior"},
        {"value": "grandmother", "label": "Grandmother (GM)", "category": "senior"}
    ]
    return {"avatars": avatars}

@api_router.post("/auth/register")
@limiter.limit("5/minute")
async def register_user(request: Request, user_data: UserCreate):
    """
    Direct user registration without email verification
    
    Features:
    - Immediate account activation
    - JWT token provided instantly
    - Password strength validation
    - Rate limiting for security
    """
    try:
        # Check if user exists
        existing_user = await get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Validate and sanitize input
        user_dict = user_data.dict()
        user_dict["full_name"] = sanitize_input(user_dict["full_name"])
        user_dict["bio"] = sanitize_input(user_dict.get("bio", ""))
        user_dict["location"] = sanitize_input(user_dict.get("location", ""))
        
        # Hash password and create user
        hashed_password = hash_password(user_data.password)
        del user_dict["password"]
        
        user = User(**user_dict)
        user_doc = user.dict()
        user_doc["password_hash"] = hashed_password
        user_doc["email_verified"] = True  # Direct login without email verification
        user_doc["is_active"] = True  # Activate immediately
        
        await create_user(user_doc)
        
        # Create JWT token immediately - no email verification needed
        token = create_jwt_token(user_doc["id"])
        
        # Remove password hash from response
        del user_doc["password_hash"]
        user = User(**user_doc)
        
        return {
            "message": "Registration successful! Welcome to EarnNest - Your journey to financial success starts now!",
            "token": token,
            "user": user.dict(),
            "email": user_data.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")

# Removed email verification endpoints - direct registration without verification

@api_router.post("/auth/login")
@limiter.limit("5/minute")
async def login_user(request: Request, login_data: UserLogin):
    """Login user with enhanced security"""
    try:
        # Find user
        user_doc = await get_user_by_email(login_data.email)
        if not user_doc:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if account is locked
        if is_account_locked(
            user_doc.get("failed_login_attempts", 0),
            user_doc.get("last_failed_login")
        ):
            remaining_time = get_lockout_remaining_time(user_doc.get("last_failed_login"))
            raise HTTPException(
                status_code=423,
                detail=f"Account locked due to too many failed attempts. Try again in {remaining_time} minutes."
            )
        
        # Verify password
        if not verify_password(login_data.password, user_doc["password_hash"]):
            # Increment failed login attempts
            failed_attempts = user_doc.get("failed_login_attempts", 0) + 1
            await update_user(
                user_doc["id"],
                {
                    "failed_login_attempts": failed_attempts,
                    "last_failed_login": datetime.now(timezone.utc)
                }
            )
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if account is active
        if not user_doc.get("is_active", True):
            raise HTTPException(status_code=401, detail="Account deactivated")
        
        # Reset failed login attempts on successful login
        await update_user(
            user_doc["id"],
            {
                "failed_login_attempts": 0,
                "last_failed_login": None,
                "last_login": datetime.now(timezone.utc)
            }
        )
        
        # Create JWT token
        token = create_jwt_token(user_doc["id"])
        
        # Remove password hash from response
        del user_doc["password_hash"]
        user = User(**user_doc)
        
        return {
            "message": "Login successful",
            "token": token,
            "user": user.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@api_router.post("/auth/password-strength")
async def check_password_strength_endpoint(request: Request, password_data: dict):
    """Enhanced password strength checker with detailed feedback"""
    password = password_data.get("password", "")
    strength_info = check_password_strength(password)
    return strength_info

@api_router.get("/auth/otp-config")
async def get_otp_configuration():
    """
    Get current OTP system configuration for debugging and monitoring
    
    Returns current OTP settings including:
    - OTP length configuration
    - Expiry time settings
    - Rate limiting configuration
    - Security feature status
    """
    config = get_otp_config()
    
    return {
        "otp_system": {
            "version": "2.0",
            "features": [
                "Dynamic OTP length (6-8 digits)",
                "5-minute expiry for enhanced security", 
                "Email-specific rate limiting",
                "Comprehensive security logging",
                "Enhanced email validation",
                "Automatic cleanup of expired codes",
                "Client IP tracking",
                "Security event monitoring"
            ]
        },
        "configuration": config,
        "security_status": "Enhanced",
        "last_updated": datetime.now(timezone.utc).isoformat()
    }

# Removed forgot-password endpoint - direct password reset only

@api_router.post("/auth/reset-password")
@limiter.limit("5/minute")
async def reset_password(request: Request, reset_data: dict):
    """Simple password reset with email + new password"""
    try:
        email = reset_data.get("email")
        new_password = reset_data.get("new_password")
        
        if not email or not new_password:
            raise HTTPException(status_code=400, detail="Email and new password are required")
        
        # Get user for password update
        user = await get_user_by_email(email)
        if not user:
            # Don't reveal if user exists for security
            return {"message": "If the email exists, password has been reset successfully"}
        
        # Validate new password strength
        password_strength = check_password_strength(new_password)
        if password_strength["score"] < 40:  # Require at least medium strength
            raise HTTPException(
                status_code=400, 
                detail=f"Password too weak (score: {password_strength['score']}/100). " + 
                       ", ".join(password_strength["feedback"])
            )
        
        # Update password
        hashed_password = hash_password(new_password)
        await update_user(
            user["id"], 
            {
                "password_hash": hashed_password,
                "failed_login_attempts": 0,
                "last_failed_login": None,
                "password_changed_at": datetime.now(timezone.utc)
            }
        )
        
        return {
            "message": "Password reset successfully! Your account is now secure.",
            "password_strength": {
                "score": password_strength["score"],
                "strength": password_strength["strength"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        raise HTTPException(status_code=500, detail="Password reset failed")

# User Routes
@api_router.get("/user/profile", response_model=User)
@limiter.limit("30/minute")
async def get_user_profile(request: Request, user_id: str = Depends(get_current_user)):
    """Get user profile with auto-calculated earnings and achievements"""
    user_doc = await get_user_by_id(user_id)
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Calculate total earnings from transactions
    transactions = await get_user_transactions(user_id, limit=1000)
    total_earnings = sum(t["amount"] for t in transactions if t["type"] == "income")
    total_expenses = sum(t["amount"] for t in transactions if t["type"] == "expense")
    net_savings = total_earnings - total_expenses
    
    # Calculate achievements
    achievements = []
    
    # Income-based achievements
    if total_earnings >= 100000:
        achievements.append({
            "id": "lakh_earner",
            "title": "Lakh Earner",
            "description": "Earned ₹1 Lakh or more",
            "icon": "💰",
            "earned": True,
            "category": "earnings"
        })
    elif total_earnings >= 50000:
        achievements.append({
            "id": "fifty_k_earner",
            "title": "Growing Earner",
            "description": "Earned ₹50,000 or more",
            "icon": "💵",
            "earned": True,
            "category": "earnings"
        })
    elif total_earnings >= 10000:
        achievements.append({
            "id": "first_ten_k",
            "title": "First 10K",
            "description": "Earned your first ₹10,000",
            "icon": "💸",
            "earned": True,
            "category": "earnings"
        })
    
    # Streak-based achievements
    income_transactions = [t for t in transactions if t["type"] == "income"]
    income_dates = [t["date"] for t in income_transactions]
    current_streak = calculate_income_streak(income_dates, user_doc.get("created_at"))
    
    if current_streak >= 30:
        achievements.append({
            "id": "month_streaker",
            "title": "Monthly Streaker",
            "description": "30+ days with income",
            "icon": "🔥",
            "earned": True,
            "category": "consistency"
        })
    elif current_streak >= 7:
        achievements.append({
            "id": "week_streaker",
            "title": "Weekly Warrior",
            "description": "7+ days with income",
            "icon": "⚡",
            "earned": True,
            "category": "consistency"
        })
    
    # Savings-based achievements
    if net_savings >= 50000:
        achievements.append({
            "id": "super_saver",
            "title": "Super Saver",
            "description": "Saved ₹50,000 or more",
            "icon": "🏆",
            "earned": True,
            "category": "savings"
        })
    elif net_savings >= 10000:
        achievements.append({
            "id": "good_saver",
            "title": "Good Saver",
            "description": "Saved ₹10,000 or more",
            "icon": "🎯",
            "earned": True,
            "category": "savings"
        })
    
    # Update user document with calculated values
    await db.users.update_one(
        {"id": user_id},
        {
            "$set": {
                "total_earnings": total_earnings,
                "net_savings": net_savings,
                "current_streak": current_streak,
                "achievements": achievements
            }
        }
    )
    
    # Update user_doc with calculated values for response
    user_doc["total_earnings"] = total_earnings
    user_doc["net_savings"] = net_savings
    user_doc["current_streak"] = current_streak
    user_doc["achievements"] = achievements
    
    del user_doc["password_hash"]
    return User(**user_doc)

@api_router.put("/user/profile")
@limiter.limit("10/minute")
async def update_user_profile(request: Request, updated_data: UserUpdate, user_id: str = Depends(get_current_user)):
    """Update user profile with validation"""
    try:
        update_data = {k: v for k, v in updated_data.dict().items() if v is not None}
        
        # Sanitize inputs
        if "full_name" in update_data:
            update_data["full_name"] = sanitize_input(update_data["full_name"])
        if "bio" in update_data:
            update_data["bio"] = sanitize_input(update_data["bio"])
        if "location" in update_data:
            update_data["location"] = sanitize_input(update_data["location"])
        
        if update_data:
            await update_user(user_id, update_data)
        
        return {"message": "Profile updated successfully"}
        
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        raise HTTPException(status_code=500, detail="Profile update failed")

# Transaction Routes
@api_router.post("/transactions", response_model=Transaction)
@limiter.limit("20/minute")
async def create_transaction_endpoint(request: Request, transaction_data: TransactionCreate, user_id: str = Depends(get_current_user)):
    """Create transaction with budget validation and automatic deduction"""
    try:
        transaction_dict = transaction_data.dict()
        transaction_dict["user_id"] = user_id
        transaction_dict["description"] = sanitize_input(transaction_dict["description"])
        transaction_dict["category"] = sanitize_input(transaction_dict["category"])
        
        # Budget validation logic for EXPENSES only
        if transaction_data.type == "expense":
            current_month = datetime.now(timezone.utc).strftime("%Y-%m")
            
            # Find the budget for this category and month
            budget = await db.budgets.find_one({
                "user_id": user_id,
                "category": transaction_dict["category"],
                "month": current_month
            })
            
            if not budget:
                raise HTTPException(
                    status_code=400, 
                    detail=f"No budget allocated for '{transaction_dict['category']}' category. Please allocate budget first."
                )
            
            # Check if expense exceeds remaining budget
            remaining_budget = budget["allocated_amount"] - budget["spent_amount"]
            if transaction_data.amount > remaining_budget:
                raise HTTPException(
                    status_code=400,
                    detail=f"No money, you reached the limit! Remaining budget for '{transaction_dict['category']}': ₹{remaining_budget:.2f}, but you're trying to spend ₹{transaction_data.amount:.2f}"
                )
            
            # Create the transaction first
            transaction = Transaction(**transaction_dict)
            await create_transaction(transaction.dict())
            
            # Update the budget's spent amount
            await db.budgets.update_one(
                {"_id": budget["_id"]},
                {"$inc": {"spent_amount": transaction_data.amount}}
            )
            
        else:
            # For income transactions, no budget validation needed
            transaction = Transaction(**transaction_dict)
            await create_transaction(transaction.dict())
            
            # Update user's total earnings and current streak if it's income
            await db.users.update_one(
                {"id": user_id},
                {"$inc": {"total_earnings": transaction.amount}}
            )
            
            # Recalculate and update income streak
            user_doc = await get_user_by_id(user_id)
            user_transactions = await get_user_transactions(user_id, limit=1000)
            income_transactions = [t for t in user_transactions if t["type"] == "income"]
            income_dates = [t["date"] for t in income_transactions]
            current_streak = calculate_income_streak(income_dates, user_doc.get("created_at"))
            
            await db.users.update_one(
                {"id": user_id},
                {"$set": {"current_streak": current_streak}}
            )

            # Update Monthly Income Goal progress automatically
            await update_monthly_income_goal_progress(user_id)
        
        return transaction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transaction creation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Transaction creation failed")

@api_router.get("/transactions", response_model=List[Transaction])
@limiter.limit("30/minute")
async def get_transactions_endpoint(request: Request, user_id: str = Depends(get_current_user), limit: int = 50, skip: int = 0):
    """Get user transactions"""
    transactions = await get_user_transactions(user_id, limit, skip)
    return [Transaction(**t) for t in transactions]

@api_router.get("/transactions/summary")
@limiter.limit("30/minute")
async def get_transaction_summary_endpoint(request: Request, user_id: str = Depends(get_current_user)):
    """Get transaction summary with large number support"""
    # Get current month transactions
    current_month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    results = await get_transaction_summary(user_id, current_month_start)
    
    summary = {"income": 0, "expense": 0, "income_count": 0, "expense_count": 0}
    for result in results:
        if result["_id"] == "income":
            summary["income"] = result["total"]
            summary["income_count"] = result["count"]
        elif result["_id"] == "expense":
            summary["expense"] = result["total"]
            summary["expense_count"] = result["count"]
    
    summary["net_savings"] = summary["income"] - summary["expense"]
    return summary

# Hustle Routes
@api_router.get("/hustles/recommendations")
@limiter.limit("10/minute")
async def get_hustle_recommendations_endpoint(request: Request, user_id: str = Depends(get_current_user)):
    """Get AI-powered hustle recommendations"""
    # Get user profile
    user_doc = await get_user_by_id(user_id)
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get AI recommendations
    ai_recommendations = await get_enhanced_ai_hustle_recommendations(
        user_doc.get("skills", []),
        user_doc.get("availability_hours", 10),
        user_doc.get("total_earnings", 0.0),
        user_doc.get("location")
    )
    
    # Convert to HustleOpportunity objects
    hustles = []
    for rec in ai_recommendations:
        hustle = HustleOpportunity(
            title=rec.get("title", ""),
            description=rec.get("description", ""),
            category=rec.get("category", "micro_tasks"),
            estimated_pay=rec.get("estimated_pay", 200.0),
            time_commitment=rec.get("time_commitment", "Flexible"),
            required_skills=rec.get("required_skills", []),
            difficulty_level=rec.get("difficulty_level", "beginner"),
            platform=rec.get("platform", "Various"),
            ai_recommended=True,
            match_score=rec.get("match_score", 50.0)
        )
        hustles.append(hustle)
    
    return hustles

@api_router.get("/hustles/user-posted")
@limiter.limit("10/minute")
async def get_user_posted_hustles_endpoint(request: Request, user_id: str = Depends(get_current_user)):
    """Get all user-posted hustles"""
    hustles = await get_active_hustles()
    
    # Add creator info
    for hustle in hustles:
        creator = await get_user_by_id(hustle["created_by"])
        if creator:
            hustle["creator_name"] = creator.get("full_name", "Anonymous")
            hustle["creator_photo"] = creator.get("profile_photo")
    
    return [UserHustle(**hustle) for hustle in hustles]

@api_router.get("/hustles/admin-posted")
@limiter.limit("10/minute")
async def get_admin_posted_hustles_endpoint(request: Request, user_id: str = Depends(get_current_user)):
    """Get admin-posted hustles"""
    cursor = db.user_hustles.find({"is_admin_posted": True, "status": "active"}).sort("created_at", -1)
    hustles = await cursor.to_list(100)
    return [UserHustle(**hustle) for hustle in hustles]

@api_router.post("/hustles/create", response_model=UserHustle)
@limiter.limit("5/minute")
async def create_user_hustle_endpoint(request: Request, hustle_data: UserHustleCreate, user_id: str = Depends(get_current_user)):
    """Create a new user-posted side hustle"""
    try:
        hustle_dict = hustle_data.dict()
        hustle_dict["created_by"] = user_id
        hustle_dict["title"] = sanitize_input(hustle_dict["title"])
        hustle_dict["description"] = sanitize_input(hustle_dict["description"])
        # Note: contact_info is a ContactInfo object, not a string, so we don't sanitize it
        
        hustle = UserHustle(**hustle_dict)
        await create_hustle(hustle.dict())
        
        return hustle
        
    except Exception as e:
        logger.error(f"Hustle creation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Hustle creation failed")

@api_router.post("/hustles/admin/create", response_model=UserHustle)
@limiter.limit("10/minute")
async def create_admin_hustle(request: Request, hustle_data: AdminHustleCreate, admin_id: str = Depends(get_current_admin)):
    """Create admin-posted hustle"""
    try:
        hustle_dict = hustle_data.dict()
        hustle_dict["created_by"] = admin_id
        hustle_dict["is_admin_posted"] = True
        hustle_dict["pay_rate"] = hustle_data.estimated_pay
        hustle_dict["pay_type"] = "estimated"
        hustle_dict["contact_info"] = hustle_data.application_link or "admin@earnwise.app"
        hustle_dict["is_remote"] = True
        
        hustle = UserHustle(**hustle_dict)
        await create_hustle(hustle.dict())
        
        return hustle
        
    except Exception as e:
        logger.error(f"Admin hustle creation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Admin hustle creation failed")

@api_router.post("/hustles/{hustle_id}/apply")
@limiter.limit("10/minute")
async def apply_to_hustle_endpoint(request: Request, hustle_id: str, application_data: HustleApplicationCreate, user_id: str = Depends(get_current_user)):
    """Apply to a user-posted hustle"""
    try:
        # Get hustle
        hustle = await db.user_hustles.find_one({"id": hustle_id})
        if not hustle:
            raise HTTPException(status_code=404, detail="Hustle not found")
        
        # Check if already applied
        if user_id in hustle.get("applicants", []):
            raise HTTPException(status_code=400, detail="Already applied to this hustle")
        
        # Get user info
        user = await get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create application
        application_dict = application_data.dict()
        application_dict["cover_message"] = sanitize_input(application_dict["cover_message"])
        
        application = HustleApplication(
            hustle_id=hustle_id,
            applicant_id=user_id,
            applicant_name=user["full_name"],
            applicant_email=user["email"],
            **application_dict
        )
        
        await create_hustle_application(application.dict())
        
        # Add to hustle applicants
        await db.user_hustles.update_one(
            {"id": hustle_id},
            {"$push": {"applicants": user_id}}
        )
        
        return {"message": "Application submitted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hustle application error: {str(e)}")
        raise HTTPException(status_code=500, detail="Hustle application failed")

@api_router.get("/hustles/my-applications")
@limiter.limit("20/minute")
async def get_my_applications_endpoint(request: Request, user_id: str = Depends(get_current_user)):
    """Get user's hustle applications"""
    applications = await get_user_applications(user_id)
    
    # Add hustle info
    for app in applications:
        hustle = await db.user_hustles.find_one({"id": app["hustle_id"]})
        if hustle:
            app["hustle_title"] = hustle.get("title")
            app["hustle_category"] = hustle.get("category")
    
    return [HustleApplication(**app) for app in applications]

@api_router.get("/hustles/categories")
async def get_hustle_categories_endpoint():
    """Get hustle categories with trending indicators"""
    categories = [
        {"name": "tutoring", "display": "Tutoring & Teaching", "icon": "📚", "trending": True},
        {"name": "freelance", "display": "Freelance Work", "icon": "💻", "trending": True},
        {"name": "content_creation", "display": "Content Creation", "icon": "🎨", "trending": True},
        {"name": "delivery", "display": "Delivery & Transportation", "icon": "🚗", "trending": False},
        {"name": "micro_tasks", "display": "Micro Tasks", "icon": "⚡", "trending": True},
        {"name": "digital_marketing", "display": "Digital Marketing", "icon": "📱", "trending": True},
        {"name": "graphic_design", "display": "Graphic Design", "icon": "🎨", "trending": True},
        {"name": "video_editing", "display": "Video Editing", "icon": "🎬", "trending": True},
        {"name": "social_media", "display": "Social Media Management", "icon": "📊", "trending": True},
        {"name": "data_entry", "display": "Data Entry", "icon": "📝", "trending": False},
        {"name": "virtual_assistant", "display": "Virtual Assistant", "icon": "🤝", "trending": True},
        {"name": "other", "display": "Other", "icon": "💼", "trending": False}
    ]
    return categories

# User Hustle Management Routes
@api_router.get("/hustles/my-posted")
@limiter.limit("20/minute")
async def get_my_posted_hustles_endpoint(request: Request, user_id: str = Depends(get_current_user)):
    """Get user's own posted hustles"""
    cursor = db.user_hustles.find({"created_by": user_id}).sort("created_at", -1)
    hustles = await cursor.to_list(100)
    return [UserHustle(**hustle) for hustle in hustles]

@api_router.put("/hustles/{hustle_id}")
@limiter.limit("10/minute")
async def update_user_hustle_endpoint(request: Request, hustle_id: str, hustle_update: UserHustleUpdate, user_id: str = Depends(get_current_user)):
    """Update user's posted hustle"""
    try:
        # Check if hustle exists and belongs to user
        existing_hustle = await db.user_hustles.find_one({"id": hustle_id, "created_by": user_id})
        if not existing_hustle:
            raise HTTPException(status_code=404, detail="Hustle not found or not authorized")
        
        # Prepare update data
        update_data = {k: v for k, v in hustle_update.dict().items() if v is not None}
        
        if "title" in update_data:
            update_data["title"] = sanitize_input(update_data["title"])
        if "description" in update_data:
            update_data["description"] = sanitize_input(update_data["description"])
        
        if update_data:
            await db.user_hustles.update_one(
                {"id": hustle_id, "created_by": user_id},
                {"$set": update_data}
            )
        
        return {"message": "Hustle updated successfully"}
        
    except Exception as e:
        logger.error(f"Hustle update error: {str(e)}")
        raise HTTPException(status_code=500, detail="Hustle update failed")

@api_router.delete("/hustles/{hustle_id}")
@limiter.limit("10/minute")
async def delete_user_hustle_endpoint(request: Request, hustle_id: str, user_id: str = Depends(get_current_user)):
    """Delete user's posted hustle"""
    try:
        # Check if hustle exists and belongs to user
        existing_hustle = await db.user_hustles.find_one({"id": hustle_id, "created_by": user_id})
        if not existing_hustle:
            raise HTTPException(status_code=404, detail="Hustle not found or not authorized")
        
        # Delete the hustle
        result = await db.user_hustles.delete_one({"id": hustle_id, "created_by": user_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Hustle not found")
        
        return {"message": "Hustle deleted successfully"}
        
    except Exception as e:
        logger.error(f"Hustle deletion error: {str(e)}")
        raise HTTPException(status_code=500, detail="Hustle deletion failed")

# Budget Routes
@api_router.get("/budgets/category/{category}")
@limiter.limit("30/minute")
async def get_category_budget_endpoint(request: Request, category: str, user_id: str = Depends(get_current_user)):
    """Get budget information for a specific category"""
    try:
        current_month = datetime.now(timezone.utc).strftime("%Y-%m")
        budget = await db.budgets.find_one({
            "user_id": user_id,
            "category": category,
            "month": current_month
        })
        
        if not budget:
            return {
                "category": category,
                "allocated_amount": 0.0,
                "spent_amount": 0.0,
                "remaining_amount": 0.0,
                "has_budget": False,
                "month": current_month
            }
        
        remaining = budget["allocated_amount"] - budget["spent_amount"]
        return {
            "category": category,
            "allocated_amount": budget["allocated_amount"],
            "spent_amount": budget["spent_amount"],
            "remaining_amount": remaining,
            "has_budget": True,
            "month": current_month,
            "budget_id": budget["id"]
        }
        
    except Exception as e:
        logger.error(f"Budget category lookup error: {str(e)}")
        raise HTTPException(status_code=500, detail="Budget lookup failed")

@api_router.post("/budgets", response_model=Budget)
@limiter.limit("10/minute")
async def create_budget_endpoint(request: Request, budget_data: BudgetCreate, user_id: str = Depends(get_current_user)):
    """Create budget"""
    budget_dict = budget_data.dict()
    budget_dict["user_id"] = user_id
    budget_dict["category"] = sanitize_input(budget_dict["category"])
    
    budget = Budget(**budget_dict)
    await create_budget(budget.dict())
    
    return budget

@api_router.get("/budgets", response_model=List[Budget])
@limiter.limit("20/minute")
async def get_budgets_endpoint(request: Request, user_id: str = Depends(get_current_user)):
    """Get user budgets"""
    budgets = await get_user_budgets(user_id)
    return [Budget(**b) for b in budgets]

@api_router.delete("/budgets/{budget_id}")
@limiter.limit("10/minute")
async def delete_budget_endpoint(request: Request, budget_id: str, user_id: str = Depends(get_current_user)):
    """Delete budget"""
    try:
        # Verify budget belongs to user
        budget = await db.budgets.find_one({"id": budget_id, "user_id": user_id})
        if not budget:
            raise HTTPException(status_code=404, detail="Budget not found")
        
        await db.budgets.delete_one({"id": budget_id, "user_id": user_id})
        return {"message": "Budget deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Budget deletion error: {str(e)}")
        raise HTTPException(status_code=500, detail="Budget deletion failed")

@api_router.put("/budgets/{budget_id}", response_model=Budget)
@limiter.limit("10/minute")
async def update_budget_endpoint(request: Request, budget_id: str, budget_update: BudgetUpdate, user_id: str = Depends(get_current_user)):
    """Update budget allocation"""
    try:
        # Verify budget belongs to user
        budget = await db.budgets.find_one({"id": budget_id, "user_id": user_id})
        if not budget:
            raise HTTPException(status_code=404, detail="Budget not found")
        
        # Prepare update data
        update_data = {k: v for k, v in budget_update.dict().items() if v is not None}
        
        if "category" in update_data:
            update_data["category"] = sanitize_input(update_data["category"])
        
        # Update the budget
        await db.budgets.update_one(
            {"id": budget_id, "user_id": user_id}, 
            {"$set": update_data}
        )
        
        # Return updated budget
        updated_budget = await db.budgets.find_one({"id": budget_id, "user_id": user_id})
        return Budget(**updated_budget)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Budget update error: {str(e)}")
        raise HTTPException(status_code=500, detail="Budget update failed")

# Analytics Routes
@api_router.get("/analytics/insights")
@limiter.limit("10/minute")
async def get_analytics_insights_endpoint(request: Request, user_id: str = Depends(get_current_user)):
    """Get dynamic AI-powered financial insights"""
    insights = await get_dynamic_financial_insights(user_id)
    return insights

# Financial Goals Routes
@api_router.post("/financial-goals", response_model=FinancialGoal)
@limiter.limit("10/minute")
async def create_financial_goal_endpoint(request: Request, goal_data: FinancialGoalCreate, user_id: str = Depends(get_current_user)):
    """Create financial goal"""
    try:
        goal_dict = goal_data.dict()
        goal_dict["user_id"] = user_id
        goal_dict["name"] = sanitize_input(goal_dict["name"])
        if goal_dict.get("description"):
            goal_dict["description"] = sanitize_input(goal_dict["description"])
        
        goal = FinancialGoal(**goal_dict)
        await create_financial_goal(goal.dict())
        
        return goal
        
    except Exception as e:
        logger.error(f"Financial goal creation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Financial goal creation failed")

@api_router.get("/financial-goals", response_model=List[FinancialGoal])
@limiter.limit("20/minute")
async def get_financial_goals_endpoint(request: Request, user_id: str = Depends(get_current_user)):
    """Get user's financial goals"""
    goals = await get_user_financial_goals(user_id)
    return [FinancialGoal(**g) for g in goals]

@api_router.put("/financial-goals/{goal_id}")
@limiter.limit("10/minute")
async def update_financial_goal_endpoint(request: Request, goal_id: str, goal_update: FinancialGoalUpdate, user_id: str = Depends(get_current_user)):
    """Update financial goal"""
    try:
        update_data = {k: v for k, v in goal_update.dict().items() if v is not None}
        
        if "name" in update_data:
            update_data["name"] = sanitize_input(update_data["name"])
        if "description" in update_data:
            update_data["description"] = sanitize_input(update_data["description"])
        
        if update_data:
            await update_financial_goal(goal_id, user_id, update_data)
        
        return {"message": "Financial goal updated successfully"}
        
    except Exception as e:
        logger.error(f"Financial goal update error: {str(e)}")
        raise HTTPException(status_code=500, detail="Financial goal update failed")

@api_router.delete("/financial-goals/{goal_id}")
@limiter.limit("10/minute")
async def delete_financial_goal_endpoint(request: Request, goal_id: str, user_id: str = Depends(get_current_user)):
    """Delete financial goal"""
    try:
        await delete_financial_goal(goal_id, user_id)
        return {"message": "Financial goal deleted successfully"}
        
    except Exception as e:
        logger.error(f"Financial goal deletion error: {str(e)}")
        raise HTTPException(status_code=500, detail="Financial goal deletion failed")

@api_router.get("/analytics/leaderboard")
@limiter.limit("20/minute")
async def get_leaderboard_endpoint(request: Request, user_id: str = Depends(get_current_user)):
    """Get earnings leaderboard (excluding test users)"""
    # Get top earners (last 30 days)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    pipeline = [
        {"$match": {"type": "income", "date": {"$gte": thirty_days_ago}}},
        {"$group": {"_id": "$user_id", "total_earnings": {"$sum": "$amount"}}},
        {"$sort": {"total_earnings": -1}},
        {"$limit": 10}
    ]
    
    leaderboard_data = await db.transactions.aggregate(pipeline).to_list(10)
    
    # Get user names for leaderboard (exclude test users)
    leaderboard = []
    for item in leaderboard_data:
        user = await get_user_by_id(item["_id"])
        if user and not any(test_word in user.get("email", "").lower() for test_word in ['test', 'dummy', 'example', 'demo']):
            leaderboard.append({
                "user_name": user.get("full_name", "Anonymous"),
                "profile_photo": user.get("profile_photo"),
                "total_earnings": item["total_earnings"],
                "rank": len(leaderboard) + 1
            })
    
    return leaderboard

# Admin Routes
@api_router.get("/admin/users")
@limiter.limit("20/minute")
async def get_all_users(request: Request, admin_id: str = Depends(get_current_admin), skip: int = 0, limit: int = 50):
    """Get all users (Admin only)"""
    cursor = db.users.find({}).skip(skip).limit(limit).sort("created_at", -1)
    users = await cursor.to_list(limit)
    
    # Remove password hashes
    for user in users:
        if "password_hash" in user:
            del user["password_hash"]
    
    return users

@api_router.put("/admin/users/{user_id}/status")
@limiter.limit("10/minute")
async def update_user_status(request: Request, user_id: str, is_active: bool, admin_id: str = Depends(get_current_admin)):
    """Update user active status (Admin only)"""
    await update_user(user_id, {"is_active": is_active})
    return {"message": f"User {'activated' if is_active else 'deactivated'} successfully"}

# Router will be included after all endpoints are defined

# Category Suggestions and Emergency Features Routes
@api_router.get("/category-suggestions/{category}")
@limiter.limit("30/minute")
async def get_category_suggestions_endpoint(request: Request, category: str, user_id: str = Depends(get_current_user)):
    """Get app/website suggestions for a transaction category"""
    try:
        suggestions = await get_category_suggestions(category)
        
        # Get popular suggestions based on user clicks (analytics)
        popular_suggestions = await get_popular_suggestions(category)
        popular_names = {item["_id"] for item in popular_suggestions}
        
        # Mark popular suggestions and sort by priority + popularity
        for suggestion in suggestions:
            suggestion["is_popular"] = suggestion["name"] in popular_names
            suggestion["click_count"] = next(
                (item["click_count"] for item in popular_suggestions if item["_id"] == suggestion["name"]), 
                0
            )
        
        # Sort by popularity (click count) first, then priority
        suggestions.sort(key=lambda x: (x["click_count"], x["priority"]), reverse=True)
        
        return {
            "category": category,
            "suggestions": [CategorySuggestion(**s) for s in suggestions],
            "total_count": len(suggestions)
        }
        
    except Exception as e:
        logger.error(f"Category suggestions error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get category suggestions")

@api_router.post("/track-suggestion-click")
@limiter.limit("50/minute")
async def track_suggestion_click_endpoint(request: Request, analytics_data: ClickAnalyticsCreate, user_id: str = Depends(get_current_user)):
    """Track user clicks on category suggestions for analytics"""
    try:
        analytics_dict = analytics_data.dict()
        analytics_dict["user_id"] = user_id
        
        await create_click_analytics(analytics_dict)
        return {"message": "Click tracked successfully"}
        
    except Exception as e:
        logger.error(f"Click tracking error: {str(e)}")
        # Don't raise exception for analytics failures
        return {"message": "Click tracking failed but request continues"}

@api_router.get("/emergency/types")
@limiter.limit("20/minute")
async def get_emergency_types_endpoint(request: Request, user_id: str = Depends(get_current_user)):
    """Get all emergency types for Emergency Fund category"""
    try:
        emergency_types = await get_emergency_types()
        return {
            "emergency_types": [EmergencyType(**et) for et in emergency_types]
        }
        
    except Exception as e:
        logger.error(f"Emergency types error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get emergency types")

@api_router.get("/emergency/hospitals")
@limiter.limit("10/minute")
async def get_emergency_hospitals_endpoint(
    request: Request, 
    user_id: str = Depends(get_current_user),
    city: str = None,
    state: str = None,
    latitude: float = None,
    longitude: float = None,
    emergency_type: str = None,
    limit: int = 10
):
    """Get nearby hospitals and top-rated hospitals based on location"""
    try:
        hospitals = []
        
        # If coordinates provided, get nearby hospitals
        if latitude is not None and longitude is not None:
            nearby_hospitals = await get_nearby_hospitals(latitude, longitude, limit=limit//2)
            hospitals.extend(nearby_hospitals)
        
        # Get hospitals by city/state (top-rated hospitals)
        if city:
            city_hospitals = await get_hospitals_by_location(city, state, limit=limit//2)
            hospitals.extend(city_hospitals)
        elif not hospitals:
            # If no location provided, get some default top hospitals
            default_hospitals = await get_hospitals_by_location("Mumbai", "Maharashtra", limit=limit)
            hospitals.extend(default_hospitals)
        
        # Remove duplicates and limit results
        unique_hospitals = {}
        for hospital in hospitals:
            hospital_id = hospital.get("id", hospital.get("name"))
            if hospital_id not in unique_hospitals:
                unique_hospitals[hospital_id] = hospital
        
        final_hospitals = list(unique_hospitals.values())[:limit]
        
        return {
            "hospitals": [Hospital(**h) for h in final_hospitals],
            "total_count": len(final_hospitals),
            "search_criteria": {
                "city": city,
                "state": state,
                "coordinates": f"{latitude}, {longitude}" if latitude and longitude else None,
                "emergency_type": emergency_type
            }
        }
        
    except Exception as e:
        logger.error(f"Emergency hospitals error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get emergency hospitals")

@api_router.get("/price-comparison")
@limiter.limit("10/minute")
async def get_price_comparison_endpoint(
    request: Request, 
    query_data: PriceComparisonQuery = Depends(), 
    user_id: str = Depends(get_current_user)
):
    """Get price comparison suggestions for shopping category"""
    try:
        # For now, return static platform suggestions with search URLs
        # In future, this could integrate with actual price comparison APIs
        
        platforms = [
            {
                "name": "Amazon",
                "url": f"https://amazon.in/s?k={query_data.product_name.replace(' ', '+')}",
                "logo_url": "https://logo.clearbit.com/amazon.in",
                "description": "Wide selection with fast delivery",
                "pros": ["Fast delivery", "Wide selection", "Prime benefits"],
                "estimated_delivery": "1-2 days"
            },
            {
                "name": "Flipkart",
                "url": f"https://flipkart.com/search?q={query_data.product_name.replace(' ', '+')}",
                "logo_url": "https://logo.clearbit.com/flipkart.com",
                "description": "Indian e-commerce leader",
                "pros": ["Local brand", "Good customer service", "Competitive prices"],
                "estimated_delivery": "2-3 days"
            },
            {
                "name": "Meesho",
                "url": f"https://meesho.com/search?query={query_data.product_name.replace(' ', '+')}",
                "logo_url": "https://logo.clearbit.com/meesho.com",
                "description": "Best prices from local suppliers",
                "pros": ["Lowest prices", "Local suppliers", "No minimum order"],
                "estimated_delivery": "3-7 days"
            },
            {
                "name": "Myntra",
                "url": f"https://myntra.com/{query_data.product_name.replace(' ', '-')}",
                "logo_url": "https://logo.clearbit.com/myntra.com",
                "description": "Fashion and lifestyle specialist",
                "pros": ["Fashion focus", "Brand authenticity", "Easy returns"],
                "estimated_delivery": "2-4 days"
            },
            {
                "name": "Ajio",
                "url": f"https://ajio.com/search/{query_data.product_name.replace(' ', '-')}",
                "logo_url": "https://logo.clearbit.com/ajio.com",
                "description": "Trendy fashion destination",
                "pros": ["Trendy items", "Reliance brand", "Good quality"],
                "estimated_delivery": "3-5 days"
            }
        ]
        
        return {
            "product_name": query_data.product_name,
            "category": query_data.category,
            "platforms": platforms,
            "comparison_tips": [
                "Check customer reviews and ratings",
                "Compare delivery times and charges",
                "Look for ongoing offers and discounts",
                "Verify seller ratings and return policies",
                "Consider total cost including delivery"
            ],
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Price comparison error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get price comparison")

@api_router.get("/categories/all-suggestions")
@limiter.limit("20/minute")
async def get_all_category_suggestions_endpoint(request: Request, user_id: str = Depends(get_current_user)):
    """Get suggestions for all categories - useful for the dedicated recommendations page"""
    try:
        # Get all unique categories
        categories = ["Movies", "Transportation", "Shopping", "Food", "Groceries", "Entertainment", "Books"]
        
        all_suggestions = {}
        for category in categories:
            suggestions = await get_category_suggestions(category)
            popular = await get_popular_suggestions(category, days=30)
            popular_names = {item["_id"] for item in popular}
            
            # Add popularity info
            for suggestion in suggestions:
                suggestion["is_popular"] = suggestion["name"] in popular_names
                suggestion["click_count"] = next(
                    (item["click_count"] for item in popular if item["_id"] == suggestion["name"]), 
                    0
                )
            
            # Sort by popularity and priority
            suggestions.sort(key=lambda x: (x["click_count"], x["priority"]), reverse=True)
            all_suggestions[category] = suggestions[:5]  # Limit to top 5 per category
        
        return {
            "categories": all_suggestions,
            "total_categories": len(categories)
        }
        
    except Exception as e:
        logger.error(f"All category suggestions error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get all category suggestions")

@api_router.get("/app-suggestions/{category}")
@limiter.limit("30/minute")
async def get_app_suggestions_endpoint(request: Request, category: str, user_id: str = Depends(get_current_user)):
    """Get app/website suggestions for expense categories"""
    try:
        # Comprehensive app suggestions for each category
        app_suggestions = {
            "movies": [
                {"name": "BookMyShow", "url": "https://bookmyshow.com", "type": "booking", "logo": "https://logos-world.net/wp-content/uploads/2021/02/BookMyShow-Logo.png", "description": "Movie tickets & events"},
                {"name": "PVR Cinemas", "url": "https://pvrcinemas.com", "type": "booking", "logo": "https://logos-world.net/wp-content/uploads/2021/08/PVR-Cinemas-Logo.png", "description": "Premium movie experience"},
                {"name": "INOX Movies", "url": "https://inoxmovies.com", "type": "booking", "logo": "https://seeklogo.com/images/I/inox-logo-B8B666FB4B-seeklogo.com.png", "description": "Latest movies & snacks"},
                {"name": "Cinepolis", "url": "https://cinepolis.co.in", "type": "booking", "logo": "https://seeklogo.com/images/C/cinepolis-logo-57FF8C69CC-seeklogo.com.png", "description": "Luxury cinema experience"}
            ],
            "transportation": [
                {"name": "Uber", "url": "https://uber.com", "type": "ride", "logo": "https://logoeps.com/wp-content/uploads/2013/03/uber-vector-logo.png", "description": "Quick rides anywhere"},
                {"name": "Rapido", "url": "https://rapido.bike", "type": "ride", "logo": "https://seeklogo.com/images/R/rapido-logo-C5BBF01CB1-seeklogo.com.png", "description": "Bike taxis & deliveries"},
                {"name": "Ola", "url": "https://olacabs.com", "type": "ride", "logo": "https://seeklogo.com/images/O/ola-logo-99C0E4C53B-seeklogo.com.png", "description": "Affordable cab service"},
                {"name": "RedBus", "url": "https://redbus.in", "type": "booking", "logo": "https://seeklogo.com/images/R/redbus-logo-66D9D961BA-seeklogo.com.png", "description": "Bus tickets online"},
                {"name": "Namma Yatri", "url": "https://nammayatri.in", "type": "ride", "logo": "https://play-lh.googleusercontent.com/QObQO8wKDjc7kPgGXUs3X1LlErhBX8zBV_eQxZM4XwRF8VD5V_KdKJ7NOWwq5F9h5Q", "description": "Open mobility platform"},
                {"name": "IRCTC", "url": "https://irctc.co.in", "type": "booking", "logo": "https://seeklogo.com/images/I/irctc-logo-585A936C9F-seeklogo.com.png", "description": "Train tickets & bookings"}
            ],
            "shopping": [
                {"name": "Amazon", "url": "https://amazon.in", "type": "marketplace", "logo": "https://seeklogo.com/images/A/amazon-logo-51B59C4C8F-seeklogo.com.png", "description": "Everything store", "price_comparison": True},
                {"name": "Flipkart", "url": "https://flipkart.com", "type": "marketplace", "logo": "https://seeklogo.com/images/F/flipkart-logo-3F33927DAA-seeklogo.com.png", "description": "India's own store", "price_comparison": True},
                {"name": "Meesho", "url": "https://meesho.com", "type": "marketplace", "logo": "https://seeklogo.com/images/M/meesho-logo-93B8E245A6-seeklogo.com.png", "description": "Affordable fashion", "price_comparison": True},
                {"name": "Ajio", "url": "https://ajio.com", "type": "fashion", "logo": "https://seeklogo.com/images/A/ajio-logo-AB11A0691E-seeklogo.com.png", "description": "Fashion & lifestyle", "price_comparison": True},
                {"name": "Myntra", "url": "https://myntra.com", "type": "fashion", "logo": "https://seeklogo.com/images/M/myntra-logo-6C2EF51AC5-seeklogo.com.png", "description": "Fashion & beauty", "price_comparison": True},
                {"name": "Nykaa", "url": "https://nykaa.com", "type": "beauty", "logo": "https://seeklogo.com/images/N/nykaa-logo-131120B8C0-seeklogo.com.png", "description": "Beauty & cosmetics"}
            ],
            "food": [
                {"name": "Zomato", "url": "https://zomato.com", "type": "delivery", "logo": "https://seeklogo.com/images/Z/zomato-logo-52A799BCDD-seeklogo.com.png", "description": "Food delivery & dining"},
                {"name": "Swiggy", "url": "https://swiggy.com", "type": "delivery", "logo": "https://seeklogo.com/images/S/swiggy-logo-64F54A0C1D-seeklogo.com.png", "description": "Food & grocery delivery"},
                {"name": "Domino's", "url": "https://dominos.co.in", "type": "restaurant", "logo": "https://seeklogo.com/images/D/dominos-pizza-logo-2A55B03F71-seeklogo.com.png", "description": "30-min pizza delivery"},
                {"name": "McDonald's", "url": "https://mcdonalds.co.in", "type": "restaurant", "logo": "https://seeklogo.com/images/M/mcdonalds-logo-255A021C36-seeklogo.com.png", "description": "I'm lovin' it"},
                {"name": "KFC", "url": "https://kfc.co.in", "type": "restaurant", "logo": "https://seeklogo.com/images/K/kfc-logo-F490D0DB72-seeklogo.com.png", "description": "Finger lickin' good"},
                {"name": "Dunzo", "url": "https://dunzo.com", "type": "delivery", "logo": "https://seeklogo.com/images/D/dunzo-logo-606F0B1181-seeklogo.com.png", "description": "Instant delivery service"}
            ],
            "groceries": [
                {"name": "Swiggy Instamart", "url": "https://swiggy.com/instamart", "type": "grocery", "logo": "https://seeklogo.com/images/S/swiggy-logo-64F54A0C1D-seeklogo.com.png", "description": "10-min grocery delivery"},
                {"name": "Blinkit", "url": "https://blinkit.com", "type": "grocery", "logo": "https://seeklogo.com/images/B/blinkit-logo-568D32C8EC-seeklogo.com.png", "description": "Instant grocery delivery"},
                {"name": "BigBasket", "url": "https://bigbasket.com", "type": "grocery", "logo": "https://seeklogo.com/images/B/bigbasket-logo-141BB91926-seeklogo.com.png", "description": "India's largest grocery"},
                {"name": "Zepto", "url": "https://zepto.com", "type": "grocery", "logo": "https://seeklogo.com/images/Z/zepto-logo-E59B0F18F1-seeklogo.com.png", "description": "10-minute delivery"},
                {"name": "Amazon Fresh", "url": "https://amazon.in/fresh", "type": "grocery", "logo": "https://seeklogo.com/images/A/amazon-logo-51B59C4C8F-seeklogo.com.png", "description": "Fresh groceries online"},
                {"name": "JioMart", "url": "https://jiomart.com", "type": "grocery", "logo": "https://seeklogo.com/images/J/jiomart-logo-478C6D5B40-seeklogo.com.png", "description": "Digital commerce platform"}
            ],
            "entertainment": [
                {"name": "Netflix", "url": "https://netflix.com", "type": "streaming", "logo": "https://seeklogo.com/images/N/netflix-logo-6A5D357DF8-seeklogo.com.png", "description": "Movies & TV shows"},
                {"name": "Amazon Prime", "url": "https://primevideo.com", "type": "streaming", "logo": "https://seeklogo.com/images/A/amazon-prime-video-logo-D924A4BF70-seeklogo.com.png", "description": "Prime Video streaming"},
                {"name": "Disney+ Hotstar", "url": "https://hotstar.com", "type": "streaming", "logo": "https://seeklogo.com/images/D/disney-hotstar-logo-6B8EE553E9-seeklogo.com.png", "description": "Sports & entertainment"},
                {"name": "Sony LIV", "url": "https://sonyliv.com", "type": "streaming", "logo": "https://seeklogo.com/images/S/sony-liv-logo-7F05B9BF2A-seeklogo.com.png", "description": "Live TV & movies"},
                {"name": "Zee5", "url": "https://zee5.com", "type": "streaming", "logo": "https://seeklogo.com/images/Z/zee5-logo-8D25C0B31F-seeklogo.com.png", "description": "Regional content hub"},
                {"name": "Spotify", "url": "https://spotify.com", "type": "music", "logo": "https://seeklogo.com/images/S/spotify-logo-31719C2137-seeklogo.com.png", "description": "Music streaming"}
            ],
            "books": [
                {"name": "Amazon Kindle", "url": "https://amazon.in/kindle", "type": "ebooks", "logo": "https://seeklogo.com/images/A/amazon-kindle-logo-10AA2173F6-seeklogo.com.png", "description": "Digital books & reading"},
                {"name": "Audible", "url": "https://audible.in", "type": "audiobooks", "logo": "https://seeklogo.com/images/A/audible-logo-164884CA24-seeklogo.com.png", "description": "Audiobooks & podcasts"},
                {"name": "Google Books", "url": "https://books.google.com", "type": "ebooks", "logo": "https://seeklogo.com/images/G/google-play-books-logo-0A8BC4D92D-seeklogo.com.png", "description": "Digital library"},
                {"name": "Flipkart Books", "url": "https://flipkart.com/books", "type": "physical", "logo": "https://seeklogo.com/images/F/flipkart-logo-3F33927DAA-seeklogo.com.png", "description": "Physical & digital books"},
                {"name": "Scribd", "url": "https://scribd.com", "type": "subscription", "logo": "https://seeklogo.com/images/S/scribd-logo-89EEC4F12C-seeklogo.com.png", "description": "Unlimited reading"},
                {"name": "Byju's", "url": "https://byjus.com", "type": "educational", "logo": "https://seeklogo.com/images/B/byjus-logo-8D737CCDC0-seeklogo.com.png", "description": "Learning platform"}
            ],
            "rent": [
                {"name": "PayTM", "url": "https://paytm.com", "type": "payment", "logo": "https://seeklogo.com/images/P/paytm-logo-6F43E73431-seeklogo.com.png", "description": "Digital payments"},
                {"name": "PhonePe", "url": "https://phonepe.com", "type": "payment", "logo": "https://seeklogo.com/images/P/phonepe-logo-E8D775029B-seeklogo.com.png", "description": "UPI payments"},
                {"name": "Google Pay", "url": "https://pay.google.com", "type": "payment", "logo": "https://seeklogo.com/images/G/google-pay-logo-6E7B8F62AC-seeklogo.com.png", "description": "Quick payments"},
                {"name": "CRED", "url": "https://cred.club", "type": "bills", "logo": "https://seeklogo.com/images/C/cred-logo-849FDDC745-seeklogo.com.png", "description": "Credit card bills"}
            ],
            "utilities": [
                {"name": "PayTM Bills", "url": "https://paytm.com/electricity-bill-payment", "type": "bills", "logo": "https://seeklogo.com/images/P/paytm-logo-6F43E73431-seeklogo.com.png", "description": "Utility bill payments"},
                {"name": "PhonePe Bills", "url": "https://phonepe.com/bill-payments", "type": "bills", "logo": "https://seeklogo.com/images/P/phonepe-logo-E8D775029B-seeklogo.com.png", "description": "All bill payments"},
                {"name": "CRED Bills", "url": "https://cred.club", "type": "bills", "logo": "https://seeklogo.com/images/C/cred-logo-849FDDC745-seeklogo.com.png", "description": "Earn rewards on bills"},
                {"name": "Freecharge", "url": "https://freecharge.in", "type": "bills", "logo": "https://seeklogo.com/images/F/freecharge-logo-8E183DF5F3-seeklogo.com.png", "description": "Mobile & utility bills"}
            ],
            "subscriptions": [
                {"name": "Truecaller", "url": "https://truecaller.com", "type": "utility", "logo": "https://seeklogo.com/images/T/truecaller-logo-4E5DAC2C62-seeklogo.com.png", "description": "Premium caller ID"},
                {"name": "Spotify Premium", "url": "https://spotify.com/premium", "type": "music", "logo": "https://seeklogo.com/images/S/spotify-logo-31719C2137-seeklogo.com.png", "description": "Ad-free music"},
                {"name": "YouTube Premium", "url": "https://youtube.com/premium", "type": "video", "logo": "https://seeklogo.com/images/Y/youtube-logo-BD65E75679-seeklogo.com.png", "description": "Ad-free videos"},
                {"name": "Adobe Creative", "url": "https://adobe.com", "type": "creative", "logo": "https://seeklogo.com/images/A/adobe-creative-cloud-logo-563433F734-seeklogo.com.png", "description": "Design software"},
                {"name": "Microsoft 365", "url": "https://office.com", "type": "productivity", "logo": "https://seeklogo.com/images/M/microsoft-365-logo-A73DB007D4-seeklogo.com.png", "description": "Office suite"}
            ]
        }
        
        category_lower = category.lower()
        suggestions = app_suggestions.get(category_lower, [])
        
        if not suggestions:
            return {"apps": [], "message": f"No specific app suggestions for {category}"}
        
        return {
            "apps": suggestions,
            "category": category,
            "has_price_comparison": any(app.get("price_comparison", False) for app in suggestions)
        }
        
    except Exception as e:
        logger.error(f"App suggestions error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get app suggestions")

@api_router.get("/emergency-types")
@limiter.limit("20/minute") 
async def get_emergency_types_endpoint(request: Request, user_id: str = Depends(get_current_user)):
    """Get available emergency types for Emergency Fund category"""
    try:
        emergency_types = [
            {"id": "medical", "name": "Medical Emergency", "icon": "🏥", "description": "Health issues, accidents, surgery"},
            {"id": "family", "name": "Family Emergency", "icon": "👨‍👩‍👧‍👦", "description": "Family crisis, urgent travel"},
            {"id": "job_loss", "name": "Job Loss", "icon": "💼", "description": "Unemployment, income loss"},
            {"id": "education", "name": "Education Emergency", "icon": "🎓", "description": "Fees, exam expenses, course materials"},
            {"id": "travel", "name": "Emergency Travel", "icon": "✈️", "description": "Urgent travel for family/work"},
            {"id": "legal", "name": "Legal Emergency", "icon": "⚖️", "description": "Legal issues, court cases"},
            {"id": "vehicle", "name": "Vehicle Emergency", "icon": "🚗", "description": "Car breakdown, accident repairs"},
            {"id": "home", "name": "Home Emergency", "icon": "🏠", "description": "Repairs, maintenance, utilities"},
            {"id": "technology", "name": "Technology Emergency", "icon": "💻", "description": "Device repairs, urgent tech needs"},
            {"id": "other", "name": "Other Emergency", "icon": "🚨", "description": "Any other urgent situation"}
        ]
        
        return {"emergency_types": emergency_types}
        
    except Exception as e:
        logger.error(f"Emergency types error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get emergency types")

@api_router.post("/emergency-services")
@limiter.limit("10/minute")
async def get_emergency_services_endpoint(
    request: Request,
    location_data: dict,
    user_id: str = Depends(get_current_user)
):
    """Get comprehensive emergency services based on user location"""
    try:
        latitude = location_data.get("latitude")
        longitude = location_data.get("longitude")
        
        if not latitude or not longitude:
            raise HTTPException(status_code=400, detail="Location coordinates required")
        
        # Reverse geocoding to get area information (simplified)
        area_info = await get_area_info_from_coordinates(latitude, longitude)
        
        # Get comprehensive emergency services
        emergency_services = {
            "hospitals": await get_nearby_emergency_hospitals(latitude, longitude),
            "police_stations": await get_nearby_police_stations(latitude, longitude),
            "atms_banks": await get_nearby_atms_banks(latitude, longitude),
            "pharmacies": await get_nearby_pharmacies(latitude, longitude),
            "gas_stations": await get_nearby_gas_stations(latitude, longitude),
            "fire_stations": await get_nearby_fire_stations(latitude, longitude),
            "emergency_shelters": await get_nearby_emergency_shelters(latitude, longitude),
            "emergency_contacts": await get_local_emergency_contacts(area_info.get("city", "Bangalore"))
        }
        
        return {
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "area": area_info.get("area", "Unknown Area"),
                "city": area_info.get("city", "Unknown City"),
                "state": area_info.get("state", "Unknown State")
            },
            "emergency_services": emergency_services,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Emergency services error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get emergency services")

async def fetch_karnataka_hospitals(latitude, longitude, emergency_type, specialty_info):
    """Fetch hospitals from Karnataka approved hospital database with accurate location-based filtering"""
    import math
    
    # Helper function to calculate distance between two coordinates
    def calculate_distance(lat1, lon1, lat2, lon2):
        R = 6371  # Radius of Earth in km
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = (math.sin(dLat/2) * math.sin(dLat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dLon/2) * math.sin(dLon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    # Comprehensive Karnataka Approved Hospital Database with ACCURATE coordinates
    karnataka_hospitals = [
        # Tumkur District - Should show for Tumkur users
        {"name": "Chetana Hospital", "address": "Behind Allamaji Complex, B.H Road, Tiptur, Tumkur", "phone": "08134-252964", "emergency_phone": "108", "district": "Tumakuru", "specialties": ["General Medicine", "Emergency Medicine", "Surgery"], "coordinates": [13.2568, 76.4784]},
        {"name": "Mookambika Modi Eye Hospital", "address": "3rd Main, Shankarapuram, Behind Doddamane Nursing Home, B H Road, Tumkur", "phone": "0816-2254400", "emergency_phone": "108", "district": "Tumakuru", "specialties": ["Ophthalmology", "Eye Surgery"], "coordinates": [13.3379, 77.1017]},
        {"name": "Raghavendra Hospital", "address": "Madhugiri, near Tumkur toll gate, Tumkur", "phone": "08137-282342", "emergency_phone": "108", "district": "Tumakuru", "specialties": ["Multi-specialty", "Emergency Medicine"], "coordinates": [13.6580, 77.2094]},
        {"name": "Sri Swamy Vivekananda Rural Health Center", "address": "Pavagada, Tumkur", "phone": "08136-244030", "emergency_phone": "108", "district": "Tumakuru", "specialties": ["Rural Healthcare", "General Medicine"], "coordinates": [14.0980, 77.2773]},
        
        # Bengaluru District - Close to Tumkur
        {"name": "Narayana Netralaya", "address": "#121/C, Chord Road, 1st R Block, Rajajinagar, Bangalore", "phone": "080-66121312", "emergency_phone": "108", "district": "Bengaluru", "specialties": ["Ophthalmology", "Eye Surgery", "Retinal Surgery"], "coordinates": [12.9716, 77.5946]},
        {"name": "Jayadeva Institute of Cardiology", "address": "Bannerghatta Road, Bangalore", "phone": "080-22977229", "emergency_phone": "108", "district": "Bengaluru", "specialties": ["Cardiology", "Cardiac Surgery", "Interventional Cardiology"], "coordinates": [12.9141, 77.6093]},
        {"name": "M.S. Ramaiah Hospital", "address": "M.S.R Nagar M.S.R.I.T. Post, Bangalore-560034", "phone": "23609999", "emergency_phone": "108", "district": "Bengaluru", "specialties": ["Multi-specialty", "Emergency Medicine", "Trauma Surgery"], "coordinates": [13.0219, 77.5671]},
        {"name": "Sparsh Hospital", "address": "#146, Infantry Road, Bengaluru-560001", "phone": "9341386853", "emergency_phone": "108", "district": "Bengaluru", "specialties": ["Advanced Surgery", "Orthopedics", "Neurosurgery"], "coordinates": [12.9716, 77.5946]},
        {"name": "Trinity Hospital & Heart Foundation", "address": "Near R.V Teacher's College Circle, Basavangudi, Bangalore", "phone": "080-41503434", "emergency_phone": "108", "district": "Bengaluru", "specialties": ["Cardiology", "Cardiac Surgery", "Emergency Medicine"], "coordinates": [12.9451, 77.5644]},
        {"name": "Sanjay Gandhi Orthopedic Center", "address": "Sanitorium, Hosur Road, Bangalore", "phone": "26564516", "emergency_phone": "108", "district": "Bengaluru", "specialties": ["Orthopedics", "Trauma Surgery", "Emergency Medicine"], "coordinates": [12.9141, 77.6482]},
        
        # Hassan District - Nearby to Tumkur
        {"name": "Hemavathi Hospital", "address": "Hemavathi Hospital Road, Northern Extension, Hassan", "phone": "08172-267656", "emergency_phone": "108", "district": "Hassan", "specialties": ["Multi-specialty", "Emergency Medicine"], "coordinates": [13.0033, 76.0952]},
        {"name": "Shree Chamarajendra Medical College (HIMS)", "address": "Hassan", "phone": "08172-233677", "emergency_phone": "108", "district": "Hassan", "specialties": ["Medical College", "All Specialties", "Emergency Medicine"], "coordinates": [13.0033, 76.0952]},
        {"name": "Janapriya Indiana Heart Lifeline", "address": "4th Floor, 2nd Cross, Shankarmutt Road, K R Puram, Hassan", "phone": "08172-232789", "emergency_phone": "108", "district": "Hassan", "specialties": ["Cardiology", "Cardiac Surgery", "Emergency Medicine"], "coordinates": [13.0033, 76.0952]},
        
        # Chitradurga District - Nearby to Tumkur  
        {"name": "Basaveshwara Medical College", "address": "SJM Campus, Chitradurga-577502", "phone": "08194-234710", "emergency_phone": "108", "district": "Chitradurga", "specialties": ["Medical College", "All Specialties"], "coordinates": [14.2251, 76.3980]},
        {"name": "Akshay Global Hospital", "address": "Opp. Sri Rama Kalyana Mantap, Challakere Road, Chitradurga", "phone": "8970320990", "emergency_phone": "108", "district": "Chitradurga", "specialties": ["Multi-specialty", "Emergency Medicine"], "coordinates": [14.2251, 76.3980]},
        
        # Mandya District - Nearby to Tumkur
        {"name": "Adichunchanagiri Hospital", "address": "Balagangadharanatha Nagar, Nagamangala Taluk, Mandya", "phone": "08234-287575", "emergency_phone": "108", "district": "Mandya", "specialties": ["Medical College", "All Specialties"], "coordinates": [12.8236, 76.6747]},
        {"name": "Hemavathi Hospital", "address": "Ashok Nagara, Mandya", "phone": "08232-224092", "emergency_phone": "108", "district": "Mandya", "specialties": ["Multi-specialty", "Emergency Medicine"], "coordinates": [12.5266, 76.8956]},
        
        # Add more major hospitals across Karnataka for comprehensive coverage
        {"name": "Apollo Hospital", "address": "Bannerghatta Road, Bangalore", "phone": "+91-80-26304050", "emergency_phone": "108", "district": "Bengaluru", "specialties": ["Multi-specialty", "Cardiology", "Neurology", "Oncology", "Emergency Medicine"], "coordinates": [12.9141, 77.6093]},
        {"name": "Fortis Hospital", "address": "Cunningham Road, Bangalore", "phone": "+91-80-66214444", "emergency_phone": "108", "district": "Bengaluru", "specialties": ["Multi-specialty", "Cardiology", "Neurology", "Orthopedics", "Emergency Medicine"], "coordinates": [12.9719, 77.5937]},
        {"name": "Manipal Hospital", "address": "HAL Airport Road, Bangalore", "phone": "+91-80-25024444", "emergency_phone": "108", "district": "Bengaluru", "specialties": ["Multi-specialty", "Emergency Medicine", "Trauma Surgery"], "coordinates": [12.9605, 77.6492]},
        
        # Other major districts (but farther from Tumkur - should appear only if no nearby hospitals)
        {"name": "KLE Hospital", "address": "Nehrunagar, Belgaum-590010", "phone": "08312473777", "emergency_phone": "108", "district": "Belagavi", "specialties": ["Multi-specialty", "Emergency Medicine", "Trauma Surgery"], "coordinates": [15.8497, 74.4977]},
        {"name": "Karnataka Institute of Medical Sciences", "address": "Hubli, Dharwad", "phone": "0836-2373348", "emergency_phone": "108", "district": "Dharwad", "specialties": ["Multi-specialty", "Medical Education", "Emergency Medicine"], "coordinates": [15.3647, 75.1240]},
        
        # Bagalkot hospitals should only show for Bagalkot area users
        {"name": "Shri Abhinav Surgical Hospital", "address": "Jamkhandi, Bagalkot", "phone": "08353-223245", "emergency_phone": "108", "district": "Bagalkot", "specialties": ["General Surgery", "Emergency Medicine"], "coordinates": [16.5062, 75.2184]},
        {"name": "Drishti Super Speciality Eye Hospital", "address": "Near Durga Vihar, Bagalkot", "phone": "9739193657", "emergency_phone": "108", "district": "Bagalkot", "specialties": ["Ophthalmology", "Eye Surgery"], "coordinates": [16.1848, 75.6961]},
    ]
    
    # Calculate distance for all hospitals and sort by distance
    hospitals_with_distance = []
    for hospital in karnataka_hospitals:
        if hospital.get("coordinates"):
            h_lat, h_lon = hospital["coordinates"]
            distance = calculate_distance(latitude, longitude, h_lat, h_lon)
            hospital_data = hospital.copy()
            hospital_data["calculated_distance"] = distance
            hospitals_with_distance.append(hospital_data)
    
    # Sort by distance (closest first)
    hospitals_with_distance.sort(key=lambda x: x["calculated_distance"])
    
    # Filter hospitals based on distance and emergency type - STRICT 25km limit
    relevant_hospitals = []
    max_radius = 25  # STRICT 25km limit as requested by user
    
    # Get hospitals within 25km ONLY - do not extend beyond this limit
    for hospital in hospitals_with_distance:
        distance = hospital["calculated_distance"]
        
        # ONLY include hospitals within 25km radius
        if distance <= max_radius:
            # Calculate specialty match score
            specialty_match_score = 0
            matched_specialties = []
            
            if specialty_info and hospital.get("specialties"):
                primary_specialties = specialty_info.get("primary_specialties", [])
                secondary_specialties = specialty_info.get("secondary_specialties", [])
                
                for spec in hospital["specialties"]:
                    if spec in primary_specialties:
                        specialty_match_score += 3
                        matched_specialties.append(spec)
                    elif spec in secondary_specialties:
                        specialty_match_score += 1
                        matched_specialties.append(spec)
            
            # Format hospital data
            hospital_data = {
                "name": hospital["name"],
                "address": hospital["address"],
                "phone": hospital["phone"],
                "emergency_phone": hospital.get("emergency_phone", "108"),
                "distance": f"{distance:.1f} km",
                "rating": hospital.get("rating", 4.3),
                "specialties": hospital.get("specialties", []),
                "matched_specialties": matched_specialties,
                "specialty_match_score": specialty_match_score,
                "features": hospital.get("features", ["Emergency Services", "Government Approved"]),
                "estimated_time": f"{int(distance * 2.5)}-{int(distance * 3.5)} minutes",
                "hospital_type": "Government Approved Hospital",
                "data_source": "karnataka_approved",
                "district": hospital.get("district", "Karnataka")
            }
            relevant_hospitals.append(hospital_data)
    
    # Sort by specialty match score first, then by distance
    relevant_hospitals.sort(key=lambda x: (-x["specialty_match_score"], float(x["distance"].split()[0])))
    
    logger.info(f"Returning {len(relevant_hospitals)} hospitals for location {latitude}, {longitude}")
    return relevant_hospitals

async def fetch_enhanced_hospitals(latitude, longitude, emergency_type, specialty_info):
    """Enhanced hospital fetch with caching and fallback systems for 24/7 reliability"""
    import asyncio
    import aiohttp
    import math
    
    # Helper function to calculate distance between two coordinates
    def calculate_distance(lat1, lon1, lat2, lon2):
        R = 6371  # Radius of Earth in km
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = (math.sin(dLat/2) * math.sin(dLat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dLon/2) * math.sin(dLon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    # Helper functions for OSM data processing
    def format_address(tags):
        if not tags:
            return "Address not available"
        
        parts = []
        if tags.get('addr:housenumber') and tags.get('addr:street'):
            parts.append(f"{tags['addr:housenumber']} {tags['addr:street']}")
        elif tags.get('addr:street'):
            parts.append(tags['addr:street'])
        
        if tags.get('addr:city'):
            parts.append(tags['addr:city'])
        if tags.get('addr:state'):
            parts.append(tags['addr:state'])
        if tags.get('addr:postcode'):
            parts.append(tags['addr:postcode'])
        
        return ', '.join(parts) if parts else "Address not available"
    
    def extract_specialties(tags):
        specialties = []
        
        if tags.get('healthcare:speciality'):
            osm_specialties = tags['healthcare:speciality'].split(';')
            for spec in osm_specialties:
                spec = spec.strip().title()
                specialty_mapping = {
                    'Cardiology': 'Cardiology', 'Emergency': 'Emergency Medicine',
                    'General': 'General Medicine', 'Trauma': 'Trauma Surgery',
                    'Orthopaedics': 'Orthopedics', 'Orthopedics': 'Orthopedics',
                    'Neurology': 'Neurology', 'Paediatrics': 'Pediatrics',
                    'Pediatrics': 'Pediatrics', 'Psychiatry': 'Psychiatry',
                    'Obstetrics': 'Obstetrics', 'Gynaecology': 'Gynecology',
                    'Gynecology': 'Gynecology'
                }
                
                mapped_spec = specialty_mapping.get(spec, spec)
                if mapped_spec not in specialties:
                    specialties.append(mapped_spec)
        
        if tags.get('emergency') == 'yes':
            if 'Emergency Medicine' not in specialties:
                specialties.append('Emergency Medicine')
        
        if not specialties:
            specialties = ['Emergency Medicine', 'General Medicine']
        
        return specialties
    
    def extract_features(tags):
        features = []
        
        if tags.get('emergency') == 'yes':
            features.append('24/7 Emergency')
        if tags.get('ambulance') == 'yes':
            features.append('Ambulance Service')
        if 'icu' in str(tags.get('healthcare:speciality', '')).lower():
            features.append('ICU')
        if 'trauma' in str(tags.get('healthcare:speciality', '')).lower():
            features.append('Trauma Center')
        if tags.get('wheelchair') == 'yes':
            features.append('Wheelchair Accessible')
        if tags.get('pharmacy') == 'yes':
            features.append('Pharmacy')
        
        return features
    
    try:
        # Step 1: Check Cache First
        logger.info(f"🔍 Checking cache for {emergency_type} hospitals near {latitude}, {longitude}")
        cached_hospitals = await cache_service.get_cached_hospitals(latitude, longitude, emergency_type)
        
        if cached_hospitals:
            logger.info(f"✅ Cache HIT: Returning {len(cached_hospitals)} cached hospitals")
            return cached_hospitals
        
        # Step 2: Check API Rate Limiting
        can_call_api, current_calls = await cache_service.check_api_rate_limit("overpass")
        
        if can_call_api:
            # Step 3: Try OpenStreetMap API
            try:
                logger.info(f"🌐 Making Overpass API call ({current_calls + 1}/500 in 10min window)")
                await cache_service.increment_api_calls("overpass")
                
                radius = 25  # Fixed 25km radius
                overpass_query = f'''
                [out:json][timeout:30];
                (
                  node["amenity"="hospital"](around:{radius * 1000},{latitude},{longitude});
                  way["amenity"="hospital"](around:{radius * 1000},{latitude},{longitude});
                  relation["amenity"="hospital"](around:{radius * 1000},{latitude},{longitude});
                  node["amenity"="clinic"](around:{radius * 1000},{latitude},{longitude});
                  way["amenity"="clinic"](around:{radius * 1000},{latitude},{longitude});
                  relation["amenity"="clinic"](around:{radius * 1000},{latitude},{longitude});
                  node["healthcare"="hospital"](around:{radius * 1000},{latitude},{longitude});
                  way["healthcare"="hospital"](around:{radius * 1000},{latitude},{longitude});
                  relation["healthcare"="hospital"](around:{radius * 1000},{latitude},{longitude});
                  node["healthcare"="clinic"](around:{radius * 1000},{latitude},{longitude});
                  way["healthcare"="clinic"](around:{radius * 1000},{latitude},{longitude});
                  relation["healthcare"="clinic"](around:{radius * 1000},{latitude},{longitude});
                );
                out center meta;
                '''
                
                timeout = aiohttp.ClientTimeout(total=30)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(
                        'https://overpass-api.de/api/interpreter',
                        data=overpass_query,
                        headers={'Content-Type': 'application/x-www-form-urlencoded'}
                    ) as response:
                        
                        if response.status != 200:
                            logger.warning(f"⚠️  Overpass API returned status {response.status}")
                            raise Exception(f"Overpass API error: {response.status}")
                        
                        data = await response.json()
                        
                        if not data.get('elements'):
                            logger.info(f"ℹ️  No hospitals found in OSM data")
                            raise Exception("No hospitals found in OpenStreetMap")
                        
                        hospitals = []
                        for element in data['elements']:
                            # Get coordinates
                            lat = element.get('lat') or (element.get('center') and element['center'].get('lat'))
                            lon = element.get('lon') or (element.get('center') and element['center'].get('lon'))
                            
                            if not lat or not lon:
                                continue
                            
                            tags = element.get('tags', {})
                            hospital_name = tags.get('name', 'Hospital')
                            
                            if not hospital_name or hospital_name == 'Hospital':
                                continue
                            
                            distance = calculate_distance(latitude, longitude, lat, lon)
                            if distance > 25:  # Strict 25km limit
                                continue
                            
                            specialties = extract_specialties(tags)
                            features = extract_features(tags)
                            
                            hospital_data = {
                                "name": hospital_name,
                                "address": format_address(tags),
                                "phone": tags.get('phone') or tags.get('contact:phone') or "Contact hospital directly",
                                "emergency_phone": "108",
                                "distance": f"{distance:.1f} km",
                                "rating": 4.0,
                                "specialties": specialties,
                                "features": features,
                                "estimated_time": f"{int(distance * 3)}-{int(distance * 4)} minutes",
                                "hospital_type": "Hospital" if tags.get('amenity') == 'hospital' else "Clinic"
                            }
                            hospitals.append(hospital_data)
                
                if hospitals:
                    # Score and sort hospitals
                    scored_hospitals = []
                    for hospital in hospitals:
                        match_score = 0
                        hospital_specialties = set(hospital["specialties"])
                        
                        for specialty in specialty_info["primary_specialties"]:
                            if specialty in hospital_specialties:
                                match_score += 3
                        
                        for specialty in specialty_info["secondary_specialties"]:
                            if specialty in hospital_specialties:
                                match_score += 1
                        
                        if match_score > 0 or "Emergency Medicine" in hospital_specialties:
                            hospital_copy = hospital.copy()
                            hospital_copy["specialty_match_score"] = match_score
                            hospital_copy["speciality"] = specialty_info["description"]
                            hospital_copy["matched_specialties"] = [
                                s for s in specialty_info["primary_specialties"] + specialty_info["secondary_specialties"] 
                                if s in hospital_specialties
                            ]
                            scored_hospitals.append(hospital_copy)
                    
                    # Sort by specialty match score first, then by distance
                    scored_hospitals.sort(key=lambda x: (-x["specialty_match_score"], float(x["distance"].split()[0])))
                    
                    # Cache the results
                    await cache_service.cache_hospitals(latitude, longitude, emergency_type, scored_hospitals)
                    
                    logger.info(f"✅ OSM API SUCCESS: Found {len(scored_hospitals)} hospitals, cached for future use")
                    return scored_hospitals
                
            except Exception as api_error:
                logger.warning(f"🚫 OpenStreetMap API failed: {str(api_error)}")
        else:
            logger.warning(f"🚫 API Rate limit reached ({current_calls}/500), using fallback")
        
        # Step 4: Use Fallback Database
        logger.info(f"🔄 Falling back to comprehensive hospital database")
        fallback_hospitals = fallback_db.get_nearby_hospitals(latitude, longitude, emergency_type, 25)
        
        if fallback_hospitals:
            # Cache fallback results (shorter TTL)
            await cache_service.cache_hospitals(latitude, longitude, emergency_type, fallback_hospitals[:15])
            logger.info(f"✅ FALLBACK SUCCESS: Found {len(fallback_hospitals)} hospitals from database")
            return fallback_hospitals[:15]  # Limit to 15 results
        
        # Final fallback - return basic emergency info
        logger.warning(f"⚠️  No hospitals found in any source - returning emergency guidance")
        return [{
            "name": "Emergency Services",
            "address": "Call emergency helpline for immediate assistance",
            "phone": "108",
            "emergency_phone": "108",
            "distance": "N/A",
            "rating": 0,
            "specialties": ["Emergency Services"],
            "features": ["24/7 Emergency Helpline"],
            "estimated_time": "Immediate",
            "hospital_type": "Emergency Services",
            "specialty_match_score": 1,
            "speciality": "Emergency assistance and ambulance dispatch",
            "matched_specialties": ["Emergency Services"]
        }]
                
    except Exception as e:
        logger.error(f"❌ Enhanced hospital fetch error: {str(e)}")
        
        # Last resort - fallback database
        try:
            fallback_hospitals = fallback_db.get_nearby_hospitals(latitude, longitude, emergency_type, 25)
            if fallback_hospitals:
                return fallback_hospitals[:10]
        except:
            pass
        
        raise Exception(f"Hospital search failed: {str(e)}")

@api_router.get("/cache/stats")
@limiter.limit("10/minute") 
async def get_cache_statistics(request: Request, user_id: str = Depends(get_current_user)):
    """Get cache statistics and performance metrics"""
    try:
        cache_stats = await cache_service.get_cache_stats()
        fallback_stats = fallback_db.get_database_stats()
        
        return {
            "cache": cache_stats,
            "fallback_database": fallback_stats,
            "system_status": {
                "cache_enabled": cache_service.cache_enabled,
                "redis_connected": cache_service.connected,
                "total_fallback_hospitals": fallback_stats["total_hospitals"],
                "cities_covered": fallback_stats["cities_covered"]
            },
            "performance_info": {
                "cache_hit_improves_response_time": "~10x faster than API calls",
                "fallback_reliability": "24/7 availability during API outages",
                "api_rate_limit_protection": "500 calls per 10 minutes"
            }
        }
    except Exception as e:
        logger.error(f"Cache stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Cache statistics unavailable")

@api_router.post("/cache/warm/{city}")
@limiter.limit("5/minute")
async def warm_city_cache(request: Request, city: str, user_id: str = Depends(get_current_user)):
    """Warm cache for a specific city (admin function)"""
    try:
        # Get hospitals from fallback database for the city
        city_hospitals = fallback_db.get_hospitals_by_city(city, "general")
        
        if city_hospitals:
            # Cache the city data
            success = await cache_service.cache_popular_location(city, city_hospitals)
            if success:
                return {
                    "message": f"Cache warmed for {city}",
                    "hospitals_cached": len(city_hospitals),
                    "city": city
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to cache city data")
        else:
            raise HTTPException(status_code=404, detail=f"No hospitals found for {city}")
            
    except Exception as e:
        logger.error(f"Cache warming error for {city}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cache warming failed: {str(e)}")

@api_router.get("/hospitals/fallback/cities")
@limiter.limit("20/minute")
async def get_available_cities(request: Request):
    """Get list of cities available in fallback database"""
    try:
        cities = fallback_db.get_all_cities()
        stats = fallback_db.get_database_stats()
        
        return {
            "cities": cities,
            "total_cities": len(cities),
            "total_hospitals": stats["total_hospitals"],
            "emergency_hospitals": stats["emergency_hospitals"],
            "message": "Cities with comprehensive hospital data in fallback database"
        }
    except Exception as e:
        logger.error(f"Cities lookup error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get cities list")

@api_router.get("/hospitals/fallback/{city}")
@limiter.limit("15/minute")
async def get_city_hospitals_fallback(
    request: Request, 
    city: str,
    emergency_type: str = "general",
    user_id: str = Depends(get_current_user)
):
    """Get hospitals for a specific city from fallback database"""
    try:
        hospitals = fallback_db.get_hospitals_by_city(city, emergency_type)
        
        if not hospitals:
            raise HTTPException(status_code=404, detail=f"No hospitals found in {city}")
        
        return {
            "hospitals": hospitals,
            "city": city,
            "emergency_type": emergency_type,
            "total_hospitals": len(hospitals),
            "data_source": "fallback_database",
            "message": f"Found {len(hospitals)} hospitals in {city} for {emergency_type}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"City hospitals error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get hospitals for {city}")

# Add startup event to initialize cache warming
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting EarnNest with enhanced hospital system...")
    
    # Initialize cache warming for popular cities (background task)
    try:
        await cache_service.warm_popular_locations()
        logger.info("✅ Cache warming initiated for popular cities")
    except Exception as e:
        logger.warning(f"⚠️  Cache warming failed: {str(e)}")
    
    logger.info("✅ EarnNest startup complete with hospital cache system")
@limiter.limit("15/minute")
async def get_emergency_hospitals_endpoint(
    request: Request, 
    location_data: dict,
    emergency_type: str,
    user_id: str = Depends(get_current_user)
):
    """Get nearby hospitals dynamically based on location and emergency type with enhanced specialty matching"""
    try:
        latitude = location_data.get("latitude")
        longitude = location_data.get("longitude")
        
        if not latitude or not longitude:
            raise HTTPException(status_code=400, detail="Location coordinates required")
        
        # Enhanced specialty mapping for different accident and medical emergency types
        accident_specialty_mapping = {
            "road accident": {
                "primary_specialties": ["Trauma Surgery", "Orthopedics", "Neurosurgery"],
                "secondary_specialties": ["Emergency Medicine", "Plastic Surgery", "ICU"],
                "description": "Trauma centers specialized in road accident injuries"
            },
            "workplace accident": {
                "primary_specialties": ["Occupational Medicine", "Trauma Surgery", "Orthopedics"],
                "secondary_specialties": ["Emergency Medicine", "Rehabilitation"],
                "description": "Hospitals with occupational injury expertise"
            },
            "sports injury": {
                "primary_specialties": ["Sports Medicine", "Orthopedics", "Physiotherapy"],
                "secondary_specialties": ["Emergency Medicine", "Rehabilitation"],
                "description": "Sports medicine and orthopedic specialists"
            },
            "fall injury": {
                "primary_specialties": ["Orthopedics", "Trauma Surgery", "Neurology"],
                "secondary_specialties": ["Emergency Medicine", "Geriatrics"],
                "description": "Specialists for fall-related injuries"
            }
        }
        
        medical_specialty_mapping = {
            "cardiac": {
                "primary_specialties": ["Cardiology", "Cardiac Surgery", "Interventional Cardiology"],
                "secondary_specialties": ["Emergency Medicine", "ICU", "Anesthesiology"],
                "description": "Cardiac emergency specialists and interventional care"
            },
            "pediatric": {
                "primary_specialties": ["Pediatrics", "Pediatric Emergency", "NICU"],
                "secondary_specialties": ["Pediatric Surgery", "Child Psychology"],
                "description": "Specialized pediatric emergency and child care"
            },
            "orthopedic": {
                "primary_specialties": ["Orthopedics", "Orthopedic Surgery", "Sports Medicine"],
                "secondary_specialties": ["Emergency Medicine", "Physiotherapy"],
                "description": "Bone, joint and musculoskeletal specialists"
            },
            "neurological": {
                "primary_specialties": ["Neurology", "Neurosurgery", "Stroke Care"],
                "secondary_specialties": ["Emergency Medicine", "ICU", "Rehabilitation"],
                "description": "Brain and nervous system emergency specialists"
            },
            "respiratory": {
                "primary_specialties": ["Pulmonology", "Respiratory Medicine", "Critical Care"],
                "secondary_specialties": ["Emergency Medicine", "ICU", "Anesthesiology"],
                "description": "Respiratory and lung emergency specialists"
            },
            "gastroenterology": {
                "primary_specialties": ["Gastroenterology", "GI Surgery", "Hepatology"],
                "secondary_specialties": ["Emergency Medicine", "Endoscopy"],
                "description": "Digestive system and liver emergency care"
            },
            "psychiatric": {
                "primary_specialties": ["Psychiatry", "Mental Health", "Crisis Intervention"],
                "secondary_specialties": ["Emergency Medicine", "Psychology"],
                "description": "Mental health crisis and psychiatric emergency care"
            },
            "obstetric": {
                "primary_specialties": ["Obstetrics", "Gynecology", "Maternity Care"],
                "secondary_specialties": ["Emergency Medicine", "NICU", "Anesthesiology"],
                "description": "Pregnancy and childbirth emergency specialists"
            },
            "general": {
                "primary_specialties": ["Emergency Medicine", "General Medicine", "Internal Medicine"],
                "secondary_specialties": ["ICU", "General Surgery"],
                "description": "General emergency care and multi-specialty treatment"
            },
            "trauma": {
                "primary_specialties": ["Trauma Surgery", "Emergency Medicine", "Critical Care"],
                "secondary_specialties": ["Orthopedics", "Neurosurgery", "ICU"],
                "description": "Comprehensive trauma and critical care centers"
            }
        }
        
        # Determine the appropriate specialty mapping based on emergency type
        specialty_info = None
        if emergency_type in accident_specialty_mapping:
            specialty_info = accident_specialty_mapping[emergency_type]
        elif emergency_type in medical_specialty_mapping:
            specialty_info = medical_specialty_mapping[emergency_type]
        else:
            # Default for unknown types
            specialty_info = medical_specialty_mapping["general"]

        # Check if location is in Karnataka for enhanced hospital database
        def is_in_karnataka(lat, lng):
            # Karnataka approximate bounding box
            # North: 18.45, South: 11.31, East: 78.59, West: 74.05
            return (11.31 <= lat <= 18.45) and (74.05 <= lng <= 78.59)
        
        all_hospitals = []
        
        # If in Karnataka, fetch from approved hospital database first
        if is_in_karnataka(latitude, longitude):
            try:
                karnataka_hospitals = await fetch_karnataka_hospitals(latitude, longitude, emergency_type, specialty_info)
                if karnataka_hospitals:
                    all_hospitals.extend(karnataka_hospitals)
                    logger.info(f"Found {len(karnataka_hospitals)} hospitals from Karnataka approved database")
            except Exception as e:
                logger.warning(f"Karnataka hospital fetch failed: {str(e)}")
        
        # Also try to fetch dynamic hospitals from OpenStreetMap for comprehensive coverage
        try:
            enhanced_hospitals = await fetch_enhanced_hospitals(latitude, longitude, emergency_type, specialty_info)
            if enhanced_hospitals:
                # Merge enhanced hospitals with Karnataka data (avoid duplicates)
                existing_names = {h["name"].lower() for h in all_hospitals}
                for hospital in enhanced_hospitals:
                    if hospital["name"].lower() not in existing_names:
                        all_hospitals.append(hospital)
                logger.info(f"Added {len(enhanced_hospitals)} hospitals from enhanced system")
        except Exception as e:
            logger.warning(f"Enhanced hospital fetch failed: {str(e)}")
        
        # Ensure we have hospitals and sort them properly
        if all_hospitals:
            # Sort all hospitals by specialty match score and distance
            all_hospitals.sort(key=lambda x: (-x.get("specialty_match_score", 0), float(x["distance"].split()[0])))
            
            # Return hospitals within 25km only - limit to 15 for performance
            result_hospitals = all_hospitals[:15]
            
            return {
                "hospitals": result_hospitals,
                "emergency_type": emergency_type,
                "location": {"latitude": latitude, "longitude": longitude},
                "emergency_helpline": "108",
                "message": f"Found {len(result_hospitals)} hospitals within 25km for {emergency_type} emergency" + 
                          (" (Karnataka approved + live data)" if is_in_karnataka(latitude, longitude) else " (live data)"),
                "data_source": "enhanced" if is_in_karnataka(latitude, longitude) else "dynamic"
            }
        
        # Enhanced static hospital database with comprehensive coverage across India
        static_hospital_database = [
            # Major Multi-specialty Hospitals
            {
                "name": "Apollo Hospital",
                "address": "Multiple locations across India",
                "phone": "+91-80-26304050",
                "emergency_phone": "108",
                "distance": "2.3 km",
                "rating": 4.5,
                "specialties": ["Cardiology", "Cardiac Surgery", "Neurology", "Trauma Surgery", "Emergency Medicine", "ICU", "Interventional Cardiology", "Orthopedics"],
                "features": ["24/7 Emergency", "Cardiac Cath Lab", "Trauma Center", "ICU", "Ambulance Service", "Multi-specialty"],
                "estimated_time": "8-12 minutes",
                "hospital_type": "Multi-specialty Tertiary Care"
            },
            {
                "name": "Fortis Healthcare",
                "address": "Multiple locations across India", 
                "phone": "+91-80-66214444",
                "emergency_phone": "108",
                "distance": "3.7 km",
                "rating": 4.4,
                "specialties": ["Cardiac Surgery", "Neurosurgery", "Trauma Surgery", "Emergency Medicine", "Critical Care", "Orthopedics", "Oncology", "Nephrology"],
                "features": ["Trauma Center", "Heart Institute", "Emergency Surgery", "Blood Bank", "24/7 ICU", "Cancer Care"],
                "estimated_time": "10-18 minutes",
                "hospital_type": "Super Specialty Hospital"
            },
            {
                "name": "Max Healthcare",
                "address": "Multiple locations in North India",
                "phone": "+91-11-26925858",
                "emergency_phone": "108",
                "distance": "4.2 km",
                "rating": 4.3,
                "specialties": ["Emergency Medicine", "Cardiology", "Neurology", "Orthopedics", "Pediatrics", "Obstetrics", "Gastroenterology"],
                "features": ["24/7 Emergency", "Advanced ICU", "Pediatric Care", "Maternity Services", "Diagnostic Center"],
                "estimated_time": "12-16 minutes",
                "hospital_type": "Multi-specialty Hospital"
            },
            {
                "name": "Manipal Hospitals",
                "address": "Multiple locations across India",
                "phone": "+91-80-25024444",
                "emergency_phone": "108", 
                "distance": "3.1 km",
                "rating": 4.3,
                "specialties": ["Orthopedics", "Neurology", "Pediatrics", "Emergency Medicine", "Sports Medicine", "Rehabilitation", "Nephrology", "Urology"],
                "features": ["Emergency Ward", "Pediatric ICU", "Orthopedic Surgery", "Neuro Care", "Rehabilitation Center"],
                "estimated_time": "10-15 minutes",
                "hospital_type": "Multi-specialty Hospital"
            },
            {
                "name": "Narayana Health",
                "address": "Multiple locations in South India",
                "phone": "+91-80-71222222",
                "emergency_phone": "108",
                "distance": "5.2 km", 
                "rating": 4.2,
                "specialties": ["Emergency Medicine", "General Medicine", "Pediatrics", "Obstetrics", "Gynecology", "Internal Medicine", "Cardiology", "Neurology"],
                "features": ["24/7 Emergency", "Maternity Care", "Pediatric Ward", "Ambulance", "Pharmacy", "Affordable Care"],
                "estimated_time": "15-20 minutes",
                "hospital_type": "General Hospital"
            },
            
            # Government and Teaching Hospitals
            {
                "name": "AIIMS (All India Institute of Medical Sciences)",
                "address": "Multiple locations across India",
                "phone": "+91-11-26588700",
                "emergency_phone": "108",
                "distance": "6.5 km",
                "rating": 4.6,
                "specialties": ["Trauma Surgery", "Emergency Medicine", "Neurosurgery", "Cardiac Surgery", "Critical Care", "All Specialties"],
                "features": ["Government Hospital", "Teaching Hospital", "Advanced Trauma Center", "All Specialties", "Research Center"],
                "estimated_time": "18-25 minutes",
                "hospital_type": "Premier Government Medical Institute"
            },
            {
                "name": "King Edward Memorial Hospital",
                "address": "Government Hospital Network",
                "phone": "+91-22-24133651",
                "emergency_phone": "108",
                "distance": "7.2 km",
                "rating": 4.0,
                "specialties": ["Trauma Surgery", "Emergency Medicine", "General Surgery", "Orthopedics", "General Medicine", "Obstetrics"],
                "features": ["Government Hospital", "Trauma Center", "24/7 Emergency", "Affordable Care", "Teaching Hospital"],
                "estimated_time": "20-25 minutes",
                "hospital_type": "Government Medical College"
            },
            
            # Specialty Emergency Centers
            {
                "name": "Medanta - The Medicity",
                "address": "Multi-location Super Specialty",
                "phone": "+91-124-4141414",
                "emergency_phone": "108",
                "distance": "8.3 km",
                "rating": 4.4,
                "specialties": ["Trauma Surgery", "Emergency Medicine", "Cardiac Surgery", "Neurosurgery", "Critical Care", "Multi-organ Transplant"],
                "features": ["Level 1 Trauma Center", "Heart Institute", "24/7 Emergency", "Air Ambulance", "Critical Care"],
                "estimated_time": "22-30 minutes",
                "hospital_type": "Super Specialty Medical City"
            },
            {
                "name": "Kokilaben Dhirubhai Ambani Hospital",
                "address": "Mumbai and Multi-city Network",
                "phone": "+91-22-42696969",
                "emergency_phone": "108",
                "distance": "5.8 km",
                "rating": 4.5,
                "specialties": ["Emergency Medicine", "Cardiology", "Neurology", "Oncology", "Pediatrics", "Trauma Surgery", "Orthopedics"],
                "features": ["24/7 Emergency", "Advanced ICU", "Trauma Center", "Cancer Care", "Pediatric Emergency"],
                "estimated_time": "16-22 minutes",
                "hospital_type": "Multi-specialty Tertiary Care"
            },
            
            # Regional Major Hospitals
            {
                "name": "Christian Medical College (CMC)",
                "address": "Vellore, Tamil Nadu",
                "phone": "+91-416-228101",
                "emergency_phone": "108",
                "distance": "4.8 km",
                "rating": 4.7,
                "specialties": ["Emergency Medicine", "All Medical Specialties", "Trauma Surgery", "Cardiac Surgery", "Neurosurgery"],
                "features": ["World-class Emergency", "Teaching Hospital", "All Specialties", "Advanced ICU", "Research Center"],
                "estimated_time": "14-20 minutes",
                "hospital_type": "Premier Medical College & Hospital"
            },
            {
                "name": "Tata Memorial Hospital",
                "address": "Mumbai, Maharashtra",
                "phone": "+91-22-24177000",
                "emergency_phone": "108",
                "distance": "6.2 km",
                "rating": 4.6,
                "specialties": ["Oncology", "Emergency Medicine", "Critical Care", "Surgical Oncology", "Radiation Oncology"],
                "features": ["Cancer Emergency", "24/7 Oncology Emergency", "Critical Care", "Advanced Surgery"],
                "estimated_time": "18-24 minutes",
                "hospital_type": "Specialty Cancer Hospital"
            },
            {
                "name": "St. Martha's Hospital",
                "address": "Multi-city Mental Health Network",
                "phone": "+91-80-25598000",
                "emergency_phone": "108",
                "distance": "5.8 km",
                "rating": 4.1,
                "specialties": ["Psychiatry", "Mental Health", "Crisis Intervention", "Emergency Medicine", "Psychology", "De-addiction"],
                "features": ["Mental Health Emergency", "Crisis Intervention", "24/7 Psychiatric Emergency", "Counseling", "De-addiction Center"],
                "estimated_time": "16-22 minutes",
                "hospital_type": "Specialty Mental Health Hospital"
            },
            
            # Women & Children Specialist Hospitals
            {
                "name": "Fernandez Hospital",
                "address": "Multi-location Women & Children",
                "phone": "+91-40-29885533",
                "emergency_phone": "108",
                "distance": "4.5 km",
                "rating": 4.4,
                "specialties": ["Obstetrics", "Gynecology", "Pediatrics", "Neonatology", "Emergency Medicine", "Maternity Care"],
                "features": ["24/7 Maternity Emergency", "NICU", "Pediatric ICU", "Advanced Labor Room", "Women's Health"],
                "estimated_time": "12-18 minutes",
                "hospital_type": "Women & Children Specialty Hospital"
            },
            {
                "name": "Rainbow Children's Hospital",
                "address": "Multi-location Pediatric Network",
                "phone": "+91-40-35057777",
                "emergency_phone": "108",
                "distance": "3.9 km",
                "rating": 4.3,
                "specialties": ["Pediatrics", "Pediatric Emergency", "NICU", "Pediatric Surgery", "Child Psychology"],
                "features": ["24/7 Pediatric Emergency", "NICU", "PICU", "Child Psychology", "Pediatric Surgery"],
                "estimated_time": "11-17 minutes",
                "hospital_type": "Children's Specialty Hospital"
            },
            
            # Eye & ENT Specialty Centers  
            {
                "name": "L V Prasad Eye Institute",
                "address": "Multi-location Eye Care Network",
                "phone": "+91-40-30612345",
                "emergency_phone": "108",
                "distance": "7.1 km",
                "rating": 4.6,
                "specialties": ["Ophthalmology", "Eye Emergency", "Trauma Surgery", "Emergency Medicine"],
                "features": ["24/7 Eye Emergency", "Trauma Eye Care", "Advanced Eye Surgery", "Emergency Vision Care"],
                "estimated_time": "19-25 minutes",
                "hospital_type": "Specialty Eye Hospital"
            }
        ]
        
        # Score and filter hospitals based on specialty match
        scored_hospitals = []
        for hospital in hospital_database:
            match_score = 0
            hospital_specialties = set(hospital["specialties"])
            
            # Calculate match score based on primary and secondary specialties
            for specialty in specialty_info["primary_specialties"]:
                if specialty in hospital_specialties:
                    match_score += 3  # High weight for primary specialties
            
            for specialty in specialty_info["secondary_specialties"]:
                if specialty in hospital_specialties:
                    match_score += 1  # Lower weight for secondary specialties
            
            # Always include hospitals with at least some emergency care capability
            if match_score > 0 or "Emergency Medicine" in hospital_specialties:
                hospital_copy = hospital.copy()
                hospital_copy["specialty_match_score"] = match_score
                hospital_copy["speciality"] = specialty_info["description"]
                hospital_copy["matched_specialties"] = [s for s in specialty_info["primary_specialties"] + specialty_info["secondary_specialties"] if s in hospital_specialties]
                scored_hospitals.append(hospital_copy)
        
        # Sort by specialty match score first, then by rating
        scored_hospitals.sort(key=lambda x: (x["specialty_match_score"], x["rating"]), reverse=True)
        
        # Return top 5 most relevant hospitals
        sample_hospitals = scored_hospitals[:5]
        
        return {
            "hospitals": sample_hospitals,
            "emergency_type": emergency_type,
            "location": {"latitude": latitude, "longitude": longitude},
            "emergency_helpline": "108",
            "message": f"Found {len(sample_hospitals)} hospitals for {emergency_type} emergency (static fallback data)",
            "data_source": "static"
        }
        
    except Exception as e:
        logger.error(f"Emergency hospitals error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get emergency hospitals")

# Advanced Income Tracking System - Auto Import Routes
@api_router.post("/auto-import/parse-content")
@limiter.limit("20/minute")
async def parse_content_endpoint(
    request: Request, 
    parse_request: ContentParseRequest, 
    user_id: str = Depends(get_current_user)
):
    """Parse SMS/Email content using AI to extract transaction information"""
    try:
        from auto_import_service import auto_import_service
        
        # Parse content using AI
        parsed_data = await auto_import_service.parse_content(
            content=parse_request.content,
            content_type=parse_request.content_type,
            user_id=user_id
        )
        
        # Store parsed transaction
        parsed_transaction_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "original_content": parse_request.content,
            "parsed_data": parsed_data,
            "confidence_score": parsed_data.get("confidence_score", 0.0)
        }
        
        await create_parsed_transaction(parsed_transaction_data)
        
        # Check for potential duplicates
        duplicates = await auto_import_service.detect_duplicates(user_id, parsed_data)
        
        # Create transaction suggestion
        suggestion_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "parsed_transaction_id": parsed_transaction_data["id"],
            "suggested_type": parsed_data.get("transaction_type", "unknown"),
            "suggested_amount": parsed_data.get("amount", 0.0),
            "suggested_category": parsed_data.get("category", "Other"),
            "suggested_description": parsed_data.get("description", "Auto-imported transaction"),
            "suggested_source": parsed_data.get("income_source") if parsed_data.get("transaction_type") == "income" else None,
            "confidence_score": parsed_data.get("confidence_score", 0.0),
            "status": "pending"
        }
        
        await create_transaction_suggestion(suggestion_data)
        
        # Get categorization suggestions
        categorization_suggestions = await auto_import_service.get_categorization_suggestions(parsed_data)
        
        return {
            "success": True,
            "parsed_data": parsed_data,
            "suggestion_id": suggestion_data["id"],
            "potential_duplicates": duplicates,
            "categorization_suggestions": categorization_suggestions,
            "message": "Content parsed successfully. Review the suggestion before approving."
        }
        
    except Exception as e:
        logger.error(f"Content parsing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to parse content: {str(e)}")

@api_router.get("/auto-import/suggestions")
@limiter.limit("30/minute")
async def get_pending_suggestions_endpoint(
    request: Request,
    user_id: str = Depends(get_current_user),
    limit: int = 20
):
    """Get user's pending transaction suggestions"""
    try:
        suggestions = await get_user_pending_suggestions(user_id, limit)
        
        # Enrich suggestions with parsed transaction data
        enriched_suggestions = []
        for suggestion in suggestions:
            parsed_transaction = await get_parsed_transaction(suggestion["parsed_transaction_id"])
            suggestion["original_content"] = parsed_transaction["original_content"] if parsed_transaction else None
            suggestion["parsed_data"] = parsed_transaction["parsed_data"] if parsed_transaction else None
            enriched_suggestions.append(suggestion)
        
        return {
            "suggestions": enriched_suggestions,
            "count": len(enriched_suggestions)
        }
        
    except Exception as e:
        logger.error(f"Get suggestions error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get suggestions")

@api_router.post("/auto-import/approve-suggestion")  
@limiter.limit("30/minute")
async def approve_suggestion_endpoint(
    request: Request,
    approval_request: SuggestionApprovalRequest,
    user_id: str = Depends(get_current_user)
):
    """Approve or reject a transaction suggestion"""
    try:
        # Get the suggestion
        suggestion = await get_suggestion_by_id(approval_request.suggestion_id)
        if not suggestion:
            raise HTTPException(status_code=404, detail="Suggestion not found")
        
        if suggestion["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if approval_request.approved:
            # Create actual transaction
            transaction_data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "type": suggestion["suggested_type"],
                "amount": suggestion["suggested_amount"],
                "category": suggestion["suggested_category"],
                "description": suggestion["suggested_description"],
                "source": suggestion["suggested_source"],
                "is_hustle_related": False
            }
            
            # Apply corrections if provided
            if approval_request.corrections:
                transaction_data.update(approval_request.corrections)
            
            # Validate expense against budget if it's an expense
            if transaction_data["type"] == "expense":
                budget = await get_user_budget_by_category(user_id, transaction_data["category"])
                if budget:
                    remaining = budget["allocated_amount"] - budget["spent_amount"]
                    if transaction_data["amount"] > remaining:
                        raise HTTPException(
                            status_code=400, 
                            detail=f"No money, you reached the limit! Remaining budget: ₹{remaining:.2f}"
                        )
            
            # Create the transaction
            await create_transaction(transaction_data)
            
            # Update budget if expense
            if transaction_data["type"] == "expense":
                budget = await get_user_budget_by_category(user_id, transaction_data["category"])
                if budget:
                    new_spent = budget["spent_amount"] + transaction_data["amount"]
                    await update_user_budget(budget["id"], {"spent_amount": new_spent})
            
            # Update suggestion status
            await update_suggestion_status(
                approval_request.suggestion_id, 
                "approved", 
                datetime.now(timezone.utc)
            )
            
            # Store learning feedback
            feedback_data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "suggestion_id": approval_request.suggestion_id,
                "original_suggestion": {
                    "type": suggestion["suggested_type"],
                    "amount": suggestion["suggested_amount"],
                    "category": suggestion["suggested_category"],
                    "description": suggestion["suggested_description"],
                    "source": suggestion["suggested_source"]
                },
                "user_correction": approval_request.corrections or {},
                "feedback_type": "correction" if approval_request.corrections else "approval"
            }
            
            await create_learning_feedback(feedback_data)
            
            return {
                "success": True,
                "transaction_id": transaction_data["id"],
                "message": "Transaction approved and created successfully"
            }
        
        else:
            # Reject the suggestion
            await update_suggestion_status(approval_request.suggestion_id, "rejected")
            
            # Store rejection feedback
            feedback_data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "suggestion_id": approval_request.suggestion_id,
                "original_suggestion": {
                    "type": suggestion["suggested_type"],
                    "amount": suggestion["suggested_amount"],
                    "category": suggestion["suggested_category"],
                    "description": suggestion["suggested_description"],
                    "source": suggestion["suggested_source"]
                },
                "user_correction": {},
                "feedback_type": "rejection"
            }
            
            await create_learning_feedback(feedback_data)
            
            return {
                "success": True,
                "message": "Suggestion rejected successfully"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Approve suggestion error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process suggestion")

@api_router.post("/auto-import/configure-source")
@limiter.limit("10/minute") 
async def configure_source_endpoint(
    request: Request,
    source_config: AutoImportSourceCreate,
    user_id: str = Depends(get_current_user)
):
    """Configure a new auto-import source"""
    try:
        source_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "source_type": source_config.source_type,
            "provider": source_config.provider,
            "source_name": source_config.source_name,
            "is_active": True,
            "last_sync": None
        }
        
        await create_auto_import_source(source_data)
        
        return {
            "success": True,
            "source_id": source_data["id"],
            "message": f"{source_config.source_type.title()} source configured successfully"
        }
        
    except Exception as e:
        logger.error(f"Configure source error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to configure source")

@api_router.get("/auto-import/sources")
@limiter.limit("30/minute")
async def get_sources_endpoint(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get user's configured auto-import sources"""
    try:
        sources = await get_user_auto_import_sources(user_id)
        return {
            "sources": sources,
            "count": len(sources)
        }
        
    except Exception as e:
        logger.error(f"Get sources error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get sources")

@api_router.get("/auto-import/learning-feedback")
@limiter.limit("20/minute")
async def get_learning_feedback_endpoint(
    request: Request,
    user_id: str = Depends(get_current_user),
    limit: int = 50
):
    """Get user's learning feedback for AI improvement"""
    try:
        feedback = await get_user_learning_feedback(user_id, limit)
        
        # Analyze feedback patterns
        total_feedback = len(feedback)
        corrections = sum(1 for f in feedback if f["feedback_type"] == "correction")
        approvals = sum(1 for f in feedback if f["feedback_type"] == "approval") 
        rejections = sum(1 for f in feedback if f["feedback_type"] == "rejection")
        
        return {
            "feedback": feedback,
            "stats": {
                "total_feedback": total_feedback,
                "corrections": corrections,
                "approvals": approvals,
                "rejections": rejections,
                "accuracy_rate": (approvals / total_feedback * 100) if total_feedback > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Get learning feedback error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get learning feedback")

# Include the router in the main app (after all endpoints are defined)
app.include_router(api_router)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_database()
    logger.info("EarnNest Production Server started successfully")

@app.on_event("shutdown")
async def shutdown_db_client():
    """Close database connection on shutdown"""
    client.close()
    logger.info("Database connection closed")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

