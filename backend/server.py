from fastapi import FastAPI, APIRouter, HTTPException, Depends, File, UploadFile, Request, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from dotenv import load_dotenv
from pathlib import Path
import os
import logging
import shutil
import uuid
import json
import asyncio
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
from gamification_service import get_gamification_service
from admin_verification_service import admin_workflow_manager, email_verifier, document_verifier
from websocket_service import connection_manager, get_notification_service

# Performance optimization imports
from performance_cache import advanced_cache, cache_result
from database_optimization import db_optimizer
from api_optimization import api_optimizer, PerformanceTrackingMiddleware
from background_tasks import background_processor, TaskPriority, cache_warming_task, database_maintenance_task
try:
    from social_sharing_service import get_social_sharing_service
    SOCIAL_SHARING_AVAILABLE = True
except ImportError as e:
    print(f"Social sharing service unavailable due to missing dependencies: {e}")
    SOCIAL_SHARING_AVAILABLE = False
    
    def get_social_sharing_service():
        return None

try:
    from push_notification_service import get_push_service
    PUSH_NOTIFICATION_AVAILABLE = True
except ImportError as e:
    print(f"Push notification service unavailable due to missing dependencies: {e}")
    PUSH_NOTIFICATION_AVAILABLE = False
    
    def get_push_service():
        return None

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Get frontend URL from environment (for referral links, etc.)
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

# Get backend URL for file downloads (same as frontend URL by default)
BACKEND_URL = os.environ.get('BACKEND_URL', FRONTEND_URL)

# Ensure uploads directory exists
UPLOADS_DIR = ROOT_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# OpenAPI Tags for better API documentation organization
tags_metadata = [
    {"name": "Authentication", "description": "User authentication, registration, and password management"},
    {"name": "User Profile", "description": "User profile management and settings"},
    {"name": "Transactions", "description": "Income and expense transaction management"},
    {"name": "Budgets", "description": "Budget creation, tracking, and management"},
    {"name": "Financial Goals", "description": "Financial goal setting and progress tracking"},
    {"name": "Side Hustles", "description": "Side hustle recommendations and applications"},
    {"name": "Analytics", "description": "Financial insights and analytics"},
    {"name": "Gamification", "description": "Points, badges, streaks, and leaderboards"},
    {"name": "Referrals", "description": "Referral system and friend management"},
    {"name": "Emergency Services", "description": "Emergency hospital recommendations"},
    {"name": "Campus Admin", "description": "Campus administrator management"},
    {"name": "Club Admin", "description": "Club administrator operations"},
    {"name": "Super Admin", "description": "Super administrator operations"},
    {"name": "Competitions", "description": "Inter-college and prize challenges"},
    {"name": "Group Challenges", "description": "Group savings challenges"},
    {"name": "Notifications", "description": "Real-time notifications and WebSocket"},
    {"name": "Timeline", "description": "User activity timeline and feed"},
    {"name": "Social Sharing", "description": "Social media sharing functionality"},
]

# Create the main app with enhanced API documentation
app = FastAPI(
    title="EarnAura - Student Finance & Side Hustle Platform",
    description="""
## 🎓 Campus-Focused Financial Platform for Students

EarnAura is a comprehensive platform designed for college students to:
- 📊 **Manage Finances**: Track income, expenses, and budgets
- 💰 **Set Financial Goals**: Emergency funds, monthly income targets, graduation goals
- 🚀 **Discover Side Hustles**: AI-powered recommendations based on skills
- 🏆 **Compete & Earn**: Campus competitions, challenges, and leaderboards
- 🤝 **Connect**: Friend referrals and social features
- 🚨 **Emergency Support**: Location-based hospital recommendations

### Features
- Real-time WebSocket notifications
- Gamification with points, badges, and streaks
- Multi-level admin system (Super Admin → Campus Admin → Club Admin)
- Inter-college competitions and prize challenges
- AI-powered financial insights and recommendations

### Authentication
All endpoints (except registration/login) require JWT authentication via Bearer token.
""",
    version="2.0.0",
    openapi_tags=tags_metadata,
    docs_url="/api/docs" if os.environ.get("ENVIRONMENT") != "production" else None,
    redoc_url="/api/redoc" if os.environ.get("ENVIRONMENT") != "production" else None,
    contact={
        "name": "EarnAura Support",
        "email": "support@earnaura.com"
    },
    license_info={
        "name": "Proprietary",
    }
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
api_router.state = {}
api_router.state['limiter'] = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ============================================================================
# VALIDATION ERROR HANDLERS - Consistent Error Responses
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors with consistent format
    Returns detailed field-level error messages
    """
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation Error",
            "errors": errors,
            "message": "Please check your input and try again"
        }
    )

@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """
    Handle direct Pydantic validation errors
    """
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation Error",
            "errors": errors,
            "message": "Invalid data provided"
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions with consistent format
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions
    """
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )

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

# Add performance tracking middleware
app.add_middleware(PerformanceTrackingMiddleware)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add comprehensive security headers to all responses"""
    response = await call_next(request)
    
    # Strict-Transport-Security (HSTS) - Force HTTPS
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    
    # X-Content-Type-Options - Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # X-Frame-Options - Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # Content-Security-Policy - Prevent XSS and injection attacks
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: https: blob:; "
        "connect-src 'self' https: wss:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    
    # X-XSS-Protection - Legacy XSS protection (still useful for older browsers)
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Referrer-Policy - Control referrer information
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Permissions-Policy - Control browser features
    response.headers["Permissions-Policy"] = (
        "geolocation=(self), "
        "microphone=(), "
        "camera=(), "
        "payment=(), "
        "usb=()"
    )
    
    return response

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
    """Enhanced global exception handler with production-safe error messages"""
    import traceback
    
    # Log full error details for debugging (server-side only)
    logger.error(f"Global exception on {request.method} {request.url.path}: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Determine if we're in production
    is_production = os.environ.get("ENVIRONMENT") == "production"
    
    # Return safe error message (no stack trace in production)
    if is_production:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error. Please try again later.",
                "error_id": str(uuid.uuid4())[:8]  # For support reference
            }
        )
    else:
        # In development, provide more details
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error. Please try again later.",
                "error_type": type(exc).__name__,
                "error_message": str(exc) if len(str(exc)) < 200 else str(exc)[:200] + "...",
                "path": request.url.path
            }
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

async def get_current_user_dict(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current authenticated user as dictionary object"""
    user_id = verify_jwt_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Check if user exists and is active
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Account deactivated")
    
    # Convert MongoDB document to clean dictionary
    if user:
        if "_id" in user:
            del user["_id"]  # Remove MongoDB _id field
    
    return user

async def get_current_admin(user_id: str = Depends(get_current_user)) -> str:
    """Get current authenticated admin user (backward compatibility)"""
    user = await get_user_by_id(user_id)
    if not user or not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id

async def get_current_super_admin(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current authenticated super admin user"""
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Check both new super_admin flag and legacy is_admin flag
    is_super = user.get("is_super_admin", False) or (user.get("admin_level") == "super_admin") or user.get("is_admin", False)
    
    if not is_super:
        raise HTTPException(status_code=403, detail="Super admin privileges required")
    
    # Return user with proper user_id field for consistency
    user_dict = dict(user) if user else {}
    user_dict["user_id"] = user.get("id", user_id)
    return user_dict

async def get_current_campus_admin(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current authenticated campus admin with privileges"""
    db = await get_database()
    
    # Check if user is a campus admin
    campus_admin = await db.campus_admins.find_one({
        "user_id": user_id,
        "status": "active"
    })
    
    if not campus_admin:
        raise HTTPException(status_code=403, detail="Campus admin privileges required")
    
    return campus_admin


async def get_current_club_admin(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current authenticated club admin with privileges"""
    db = await get_database()
    
    # Check if user is a club admin
    club_admin = await db.campus_admins.find_one({
        "user_id": user_id,
        "status": "active",
        "admin_type": "club_admin"
    })
    
    if not club_admin:
        raise HTTPException(status_code=403, detail="Club admin privileges required")
    
    return club_admin


async def get_current_admin_with_challenge_permissions(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current authenticated admin (campus or club) with challenge creation privileges"""
    db = await get_database()
    
    # Check if user is system admin first
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    is_system_admin = user.get("is_admin", False) or user.get("is_super_admin", False)
    if is_system_admin:
        return {
            "user_id": user_id,
            "admin_type": "system_admin",
            "is_system_admin": True,
            "can_create_challenges": True,
            "max_challenges_per_month": float('inf')
        }
    
    # Check if user is campus admin OR club admin
    admin = await db.campus_admins.find_one({
        "user_id": user_id,
        "status": "active",
        "admin_type": {"$in": ["campus_admin", "club_admin"]}
    })
    
    if not admin:
        raise HTTPException(
            status_code=403, 
            detail="Challenge creation requires system admin, campus admin, or club admin privileges"
        )
    
    return admin


async def create_audit_log(
    db: Any,
    admin_user_id: str,
    action_type: str,
    action_description: str,
    target_type: str,
    target_id: Optional[str] = None,
    affected_entities: List[Dict] = [],
    before_state: Optional[Dict] = None,
    after_state: Optional[Dict] = None,
    severity: str = "info",
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    admin_level: Optional[str] = None,
    college_name: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    alert_sent: bool = False
):
    """Helper function to create comprehensive audit logs"""
    from models import AdminAuditLog
    
    audit_log = AdminAuditLog(
        admin_user_id=admin_user_id,
        action_type=action_type,
        action_description=action_description,
        target_type=target_type,
        target_id=target_id,
        affected_entities=affected_entities,
        before_state=before_state,
        after_state=after_state,
        severity=severity,
        ip_address=ip_address,
        user_agent=user_agent,
        admin_level=admin_level,
        college_name=college_name,
        success=success,
        error_message=error_message,
        alert_sent=alert_sent
    )
    
    await db.admin_audit_logs.insert_one(audit_log.dict())
    
    # Send real-time alert if severity is critical or warning
    if severity in ["critical", "warning"] and not alert_sent:
        await send_admin_alert(db, audit_log)

async def send_admin_alert(db: Any, audit_log: Any):
    """Send real-time alert to super admins"""
    from models import AdminAlert
    
    alert = AdminAlert(
        alert_type="high_priority_action" if audit_log.severity == "critical" else "suspicious_activity",
        severity=audit_log.severity,
        title=f"Admin Action: {audit_log.action_type}",
        message=audit_log.action_description,
        admin_user_id=audit_log.admin_user_id,
        admin_level=audit_log.admin_level,
        related_entity_type=audit_log.target_type,
        related_entity_id=audit_log.target_id,
        requires_action=audit_log.severity == "critical"
    )
    
    await db.admin_alerts.insert_one(alert.dict())
    
    # Here you could also send WebSocket notification to connected super admins
    # or send email notification for critical alerts

async def track_admin_session(
    db: Any,
    admin_user_id: str,
    admin_level: str,
    session_id: str,
    ip_address: str,
    user_agent: str
):
    """Track admin login session for security monitoring"""
    from models import AdminSessionTracker
    
    session = AdminSessionTracker(
        admin_user_id=admin_user_id,
        admin_level=admin_level,
        session_id=session_id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    await db.admin_sessions.insert_one(session.dict())

async def update_admin_activity(db: Any, admin_id: str):
    """Update last activity timestamp for admin"""
    await db.campus_admins.update_one(
        {"id": admin_id},
        {
            "$set": {"last_activity": datetime.now(timezone.utc)},
            "$inc": {"days_active": 0}  # Will be calculated by background job
        }
    )

    
    if not campus_admin:
        raise HTTPException(status_code=403, detail="Campus admin privileges required")
    
    # Check if admin privileges have expired
    if campus_admin.get("expires_at") and campus_admin["expires_at"] < datetime.now(timezone.utc):
        await db.campus_admins.update_one(
            {"id": campus_admin["id"]},
            {"$set": {"status": "expired"}}
        )
        raise HTTPException(status_code=403, detail="Campus admin privileges have expired")
    
    return campus_admin

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
        is_completed = monthly_income >= monthly_goal["target_amount"]
        previous_amount = monthly_goal.get("current_amount", 0)
        
        await db.financial_goals.update_one(
            {"_id": monthly_goal["_id"]},
            {
                "$set": {
                    "current_amount": monthly_income,
                    "updated_at": datetime.now(timezone.utc),
                    "is_completed": is_completed
                }
            }
        )
        
        # 🔥 REAL-TIME NOTIFICATIONS: Send goal progress updates
        try:
            notification_service = await get_notification_service()
            progress_percentage = (monthly_income / monthly_goal["target_amount"] * 100) if monthly_goal["target_amount"] > 0 else 0
            
            # Send progress update notification
            if monthly_income != previous_amount:
                await notification_service.create_and_notify_in_app_notification(user_id, {
                    "type": "goal_progress",
                    "title": f"📈 Goal Progress Updated!",
                    "message": f"Monthly income goal: ₹{monthly_income:.0f}/₹{monthly_goal['target_amount']:.0f} ({progress_percentage:.1f}% complete)",
                    "priority": "medium",
                    "data": {
                        "goal_id": str(monthly_goal["_id"]),
                        "goal_category": "monthly_income",
                        "current_amount": monthly_income,
                        "target_amount": monthly_goal["target_amount"],
                        "progress_percentage": progress_percentage,
                        "is_completed": is_completed
                    }
                })
            
            # Send goal completion notification
            if is_completed and not monthly_goal.get("is_completed", False):
                await notification_service.create_and_notify_in_app_notification(user_id, {
                    "type": "goal_completed",
                    "title": f"🎉 Goal Completed!",
                    "message": f"Congratulations! You've reached your monthly income goal of ₹{monthly_goal['target_amount']:.0f}!",
                    "priority": "high",
                    "data": {
                        "goal_id": str(monthly_goal["_id"]),
                        "goal_category": "monthly_income",
                        "completed_amount": monthly_income,
                        "target_amount": monthly_goal["target_amount"],
                        "achievement_type": "goal_completion"
                    }
                })
        except Exception as e:
            logger.error(f"Failed to send goal progress notification: {str(e)}")
        
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
    """Get nearby emergency hospitals using real OpenStreetMap data"""
    try:
        # Use the enhanced hospital fetch system with real API integration
        hospitals = await fetch_enhanced_hospitals(latitude, longitude, "general", {
            "emergency_types": ["medical", "trauma", "cardiac"],
            "specialties": ["Emergency Medicine", "General Surgery", "Internal Medicine"]
        })
        
        # Convert to expected format for emergency services endpoint
        formatted_hospitals = []
        for hospital in hospitals:
            formatted_hospitals.append({
                "name": hospital.get("name", "Hospital"),
                "address": hospital.get("address", "Address not available"),
                "phone": hospital.get("phone", "108"),
                "distance": f"{hospital.get('distance', 0):.1f} km",
                "emergency_services": hospital.get("features", ["Emergency Care"]),
                "rating": hospital.get("rating", 4.0)
            })
        
        return formatted_hospitals[:5]  # Return top 5 hospitals
        
    except Exception as e:
        logger.error(f"Real hospital fetch failed: {str(e)}")
        # Fallback to static hospitals if API fails
        return [
            {
                "name": "Emergency Hospital 108",
                "address": "Nearest Government Hospital",
                "phone": "108",
                "distance": "Variable",
                "emergency_services": ["24/7 Emergency", "Ambulance"],
                "rating": 4.0
            }
        ]

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
# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@api_router.get(
    "/auth/trending-skills",
    tags=["Authentication"],
    summary="Get trending skills for registration",
    description="Returns list of trending skills with categories and icons for user selection during registration"
)
@cache_result("trending_skills", 3600)  # Cache for 1 hour
async def get_trending_skills():
    """Get trending skills for registration and profile updates"""
    # Check cache first
    cached_skills = await advanced_cache.get("trending_skills")
    if cached_skills:
        return api_optimizer.optimize_json_response({"trending_skills": cached_skills})
    
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
    
    # Cache the result
    await advanced_cache.set("trending_skills", trending_skills)
    return api_optimizer.optimize_json_response({"trending_skills": trending_skills})

# Avatar selection endpoint removed

@api_router.post(
    "/auth/register",
    tags=["Authentication"],
    summary="Register new user",
    description="Register a new user account with mandatory fields: email, password, name, role, location, skills, and avatar",
    response_model=Dict[str, Any],
    responses={
        200: {"description": "User registered successfully with JWT token"},
        422: {"description": "Validation error - missing or invalid fields"},
        400: {"description": "Email already registered or referral code invalid"},
        429: {"description": "Rate limit exceeded - 5 registrations per minute"}
    }
)
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
        # ENHANCED SECURITY: Validate password strength (12+ chars, uppercase, lowercase, number, special)
        password_check = check_password_strength(user_data.password)
        if not password_check.get("valid", False):
            raise HTTPException(
                status_code=400, 
                detail=f"Password does not meet security requirements: {', '.join(password_check.get('feedback', []))}"
            )
        
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
        
        # Initialize gamification profile for new user
        gamification = await get_gamification_service()
        await gamification.update_user_streak(user_doc["id"])  # Start with day 1 streak
        await gamification.update_leaderboards(user_doc["id"])  # Add to leaderboards
        
        # Give welcome achievement and check for first-time badges
        await gamification.create_milestone_achievement(user_doc["id"], "welcome", {
            "registration_date": datetime.now(timezone.utc).isoformat(),
            "university": user_dict.get("university")
        })
        
        # Get database connection for referral processing
        db = await get_database()
        
        # Check if user was referred (extract from query params if present)
        referral_code = request.query_params.get("ref")
        if referral_code:
            try:
                # Process referral signup directly
                
                # Find referrer
                referrer = await db.referral_programs.find_one({"referral_code": referral_code})
                if referrer:
                    # Create referred user record
                    referred_user = {
                        "referrer_id": referrer["referrer_id"],
                        "referred_user_id": user_doc["id"],
                        "referral_code": referral_code,
                        "status": "pending",  # Will become "completed" after 30 days of activity
                        "signed_up_at": datetime.now(timezone.utc),
                        "earnings_awarded": 0.0
                    }
                    await db.referred_users.insert_one(referred_user)
                    
                    # Update referrer stats
                    await db.referral_programs.update_one(
                        {"referrer_id": referrer["referrer_id"]},
                        {"$inc": {"total_referrals": 1, "successful_referrals": 1}}
                    )
                    
                    # **NEW: Update invitation stats for Friends & Referrals section**
                    await db.user_invitation_stats.update_one(
                        {"user_id": referrer["referrer_id"]},
                        {
                            "$inc": {
                                "total_successful_invites": 1,
                                "invitation_bonus_points": 50  # Referral signup bonus
                            }
                        },
                        upsert=True
                    )
                    
                    # Add referral info to user document
                    await db.users.update_one(
                        {"id": user_doc["id"]},
                        {
                            "$set": {"referred_by": referrer["referrer_id"]},
                            "$inc": {"experience_points": 50}  # Welcome bonus for referred users
                        }
                    )
                    
                    # Create ₹50 signup bonus for referrer
                    signup_earning = {
                        "referrer_id": referrer["referrer_id"],
                        "referred_user_id": user_doc["id"],
                        "earning_type": "signup_bonus",
                        "amount": 50.0,
                        "description": f"Signup bonus for referring {user_dict['full_name']}",
                        "status": "confirmed",  # Instant reward
                        "created_at": datetime.now(timezone.utc),
                        "confirmed_at": datetime.now(timezone.utc)
                    }
                    await db.referral_earnings.insert_one(signup_earning)
                    
                    # Update referrer's earnings
                    await db.referral_programs.update_one(
                        {"referrer_id": referrer["referrer_id"]},
                        {"$inc": {"total_earnings": 50.0}}
                    )
                    
                    # **NEW: AUTOMATIC FRIENDSHIP CREATION**
                    # Create instant mutual friendship when someone registers via referral code
                    try:
                        # Check if friendship already exists (safety check)
                        existing_friendship = await db.friendships.find_one({
                            "$or": [
                                {"user1_id": referrer["referrer_id"], "user2_id": user_doc["id"]},
                                {"user1_id": user_doc["id"], "user2_id": referrer["referrer_id"]}
                            ]
                        })
                        
                        if not existing_friendship:
                            # Create automatic friendship
                            friendship = {
                                "id": str(uuid.uuid4()),
                                "user1_id": referrer["referrer_id"],
                                "user2_id": user_doc["id"],
                                "status": "active",
                                "created_at": datetime.now(timezone.utc),
                                "connection_type": "referral_signup",  # Track how they connected
                                "automatic": True  # Mark as automatically created
                            }
                            await db.friendships.insert_one(friendship)
                            
                            # Award additional friendship bonus points
                            friendship_bonus_points = 25
                            await db.users.update_one(
                                {"id": referrer["referrer_id"]},
                                {"$inc": {"experience_points": friendship_bonus_points, "achievement_points": friendship_bonus_points}}
                            )
                            
                            await db.users.update_one(
                                {"id": user_doc["id"]},
                                {"$inc": {"experience_points": friendship_bonus_points, "achievement_points": friendship_bonus_points}}
                            )
                            
                            # Get referrer user data for notifications
                            referrer_user = await db.users.find_one({"id": referrer["referrer_id"]})
                            
                            # Create real-time notifications for both users
                            await create_notification(
                                referrer["referrer_id"],
                                "friend_joined",
                                f"🎉 {user_dict['full_name']} joined via your referral!",
                                f"You're now friends and both earned {friendship_bonus_points} bonus points!",
                                related_id=friendship["id"]
                            )
                            
                            await create_notification(
                                user_doc["id"], 
                                "friend_joined",
                                f"🤝 Welcome! You're now friends with {referrer_user['full_name']}",
                                f"You both earned {friendship_bonus_points} friendship points!",
                                related_id=friendship["id"]
                            )
                            
                            # Check for friendship milestone badges
                            gamification = await get_gamification_service()
                            await gamification.check_and_award_badges(referrer["referrer_id"], "friend_invited", {
                                "successful_invites": 1,  # This counts as a successful invite
                                "automatic_friendship": True
                            })
                            
                            logger.info(f"Automatic friendship created: {referrer['referrer_id']} <-> {user_doc['id']}")
                        
                    except Exception as friendship_error:
                        logger.warning(f"Automatic friendship creation failed: {str(friendship_error)}")
                        # Don't fail registration if friendship creation fails
                    
                    logger.info(f"Referral processed successfully: {referral_code} -> {user_doc['id']}")
                else:
                    logger.warning(f"Invalid referral code: {referral_code}")
            except Exception as e:
                logger.warning(f"Referral processing failed: {str(e)}")
                # Don't fail registration if referral processing fails
        
        # Create referral program for new user
        try:
            referral_data = {
                "referrer_id": user_doc["id"],
                "referral_code": user_doc["id"][:8] + str(int(datetime.now().timestamp()))[-6:],  # Unique code
                "total_referrals": 0,
                "successful_referrals": 0,
                "total_earnings": 0.0,
                "pending_earnings": 0.0,
                "created_at": datetime.now(timezone.utc)
            }
            await db.referral_programs.insert_one(referral_data)
            logger.info(f"Referral program created for user {user_doc['id']}")
        except Exception as e:
            logger.warning(f"Failed to create referral program: {str(e)}")
            # Don't fail registration if referral program creation fails
        
        # Create JWT token immediately - no email verification needed
        token = create_jwt_token(user_doc["id"])
        
        # Remove password hash from response
        del user_doc["password_hash"]
        user = User(**user_doc)
        
        return {
            "message": "Registration successful! Welcome to EarnAura - Your journey to financial success starts now!",
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

@api_router.post(
    "/auth/login",
    tags=["Authentication"],
    summary="User login",
    description="Authenticate user with email and password, returns JWT token for subsequent API calls",
    responses={
        200: {"description": "Login successful with JWT token and user details"},
        401: {"description": "Invalid credentials"},
        404: {"description": "User not found"},
        429: {"description": "Rate limit exceeded - 5 login attempts per minute"}
    }
)
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


@api_router.post("/auth/refresh-token")
@limiter.limit("20/minute")
async def refresh_token(request: Request, current_user_id: str = Depends(get_current_user)):
    """
    Refresh JWT token before expiry (silent token refresh)
    
    This endpoint allows clients to refresh their JWT tokens without requiring login credentials.
    Used for seamless authentication when tokens are about to expire.
    """
    try:
        # Get user to verify they still exist and are active
        user_doc = await get_user_by_id(current_user_id)
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if account is still active
        if not user_doc.get("is_active", True):
            raise HTTPException(status_code=401, detail="Account deactivated")
        
        # Create new JWT token with fresh expiry
        new_token = create_jwt_token(current_user_id)
        
        logger.info(f"Token refreshed for user: {current_user_id}")
        
        return {
            "token": new_token,
            "message": "Token refreshed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(status_code=500, detail="Token refresh failed")

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
        if "phone" in update_data:
            update_data["phone"] = sanitize_input(update_data["phone"])
        
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
            # Use the transaction's date to determine the budget month (not current month)
            transaction_date = transaction_dict.get("date", datetime.now(timezone.utc))
            if isinstance(transaction_date, str):
                transaction_date = datetime.fromisoformat(transaction_date.replace('Z', '+00:00'))
            transaction_month = transaction_date.strftime("%Y-%m")
            
            # Find the budget for this category and transaction month
            budget = await db.budgets.find_one({
                "user_id": user_id,
                "category": transaction_dict["category"],
                "month": transaction_month
            })
            
            # If no budget found for transaction month, try to find current month's budget
            if not budget:
                current_month = datetime.now(timezone.utc).strftime("%Y-%m")
                budget = await db.budgets.find_one({
                    "user_id": user_id,
                    "category": transaction_dict["category"],
                    "month": current_month
                })
            
            # If still no budget, try to find any budget for this category
            if not budget:
                budget = await db.budgets.find_one({
                    "user_id": user_id,
                    "category": transaction_dict["category"]
                })
            
            # Debug logging for budget lookup
            if not budget:
                # Check if any budgets exist for this user and category
                all_user_budgets = await db.budgets.find({"user_id": user_id}).to_list(None)
                category_budgets = await db.budgets.find({"user_id": user_id, "category": transaction_dict["category"]}).to_list(None)
                
                logger.error(f"Budget lookup failed - user_id: {user_id}, category: '{transaction_dict['category']}', transaction_month: '{transaction_month}'")
                logger.error(f"All user budgets: {len(all_user_budgets)}, Category budgets: {len(category_budgets)}")
                
                if category_budgets:
                    logger.error(f"Category budget months: {[b.get('month') for b in category_budgets]}")
                
                raise HTTPException(
                    status_code=400, 
                    detail=f"No budget allocated for '{transaction_dict['category']}' category for {transaction_month}. Please allocate budget first."
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
            
            # Update challenge progress for savings challenges
            await update_user_challenge_progress(user_id)
            
            # Update group challenge progress
            await update_group_challenge_progress(user_id)
            
            # 🔥 UPDATE PRIZE CHALLENGE PROGRESS
            # Get all active prize challenges the user is participating in
            try:
                prize_participations = await db.prize_challenge_participations.find({
                    "user_id": user_id,
                    "participation_status": "active"
                }).to_list(None)
                
                for participation in prize_participations:
                    await update_single_prize_challenge_progress(participation["challenge_id"])
            except Exception as e:
                logger.error(f"Failed to update prize challenge progress: {e}")
            
            # 🔥 UPDATE INTER-COLLEGE COMPETITION PROGRESS
            # Get all active competitions the user is participating in
            try:
                competition_participations = await db.campus_competition_participations.find({
                    "user_id": user_id,
                    "registration_status": {"$in": ["registered", "active"]}
                }).to_list(None)
                
                for participation in competition_participations:
                    await update_single_competition_progress(participation["competition_id"])
            except Exception as e:
                logger.error(f"Failed to update competition progress: {e}")
            
            # Enhanced Gamification hooks for expense transactions - Phase 1
            gamification = await get_gamification_service()
            streak_result = await gamification.update_user_streak(user_id)
            
            # Check for milestone achievements and trigger notifications
            if streak_result and streak_result.get("milestone_reached"):
                milestone_data = streak_result["milestone_reached"]
                # Send push notification for milestone
                try:
                    if PUSH_NOTIFICATION_AVAILABLE:
                        push_service = await get_push_service()
                        await push_service.send_milestone_notification(user_id, milestone_data)
                except Exception as e:
                    logger.error(f"Failed to send milestone push notification: {e}")
            
            # Check and award badges
            newly_earned_badges = await gamification.check_and_award_badges(user_id, "expense_created", {
                "amount": transaction_data.amount,
                "category": transaction_dict["category"]
            })
            
            # Send notifications for new badges
            for badge in newly_earned_badges:
                try:
                    if PUSH_NOTIFICATION_AVAILABLE:
                        push_service = await get_push_service()
                        badge_milestone_data = {
                            "title": f"Badge Earned: {badge['name']}!",
                            "message": badge["description"],
                            "type": "badge",
                            "icon": badge["icon"],
                            "achievement_id": badge.get("achievement_id")
                        }
                        await push_service.send_milestone_notification(user_id, badge_milestone_data)
                except Exception as e:
                    logger.error(f"Failed to send badge push notification: {e}")
            
            await gamification.update_leaderboards(user_id)
            
        else:
            # For income transactions, no budget validation needed
            transaction = Transaction(**transaction_dict)
            await create_transaction(transaction.dict())
            
            # Update user's total earnings and net savings
            await db.users.update_one(
                {"id": user_id},
                {"$inc": {"total_earnings": transaction.amount, "net_savings": transaction.amount}}
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
            
            # Update challenge progress for savings challenges
            await update_user_challenge_progress(user_id)
            
            # Update group challenge progress
            await update_group_challenge_progress(user_id)
            
            # 🔥 UPDATE PRIZE CHALLENGE PROGRESS
            # Get all active prize challenges the user is participating in
            try:
                prize_participations = await db.prize_challenge_participations.find({
                    "user_id": user_id,
                    "participation_status": "active"
                }).to_list(None)
                
                for participation in prize_participations:
                    await update_single_prize_challenge_progress(participation["challenge_id"])
            except Exception as e:
                logger.error(f"Failed to update prize challenge progress: {e}")
            
            # 🔥 UPDATE INTER-COLLEGE COMPETITION PROGRESS
            # Get all active competitions the user is participating in
            try:
                competition_participations = await db.campus_competition_participations.find({
                    "user_id": user_id,
                    "registration_status": {"$in": ["registered", "active"]}
                }).to_list(None)
                
                for participation in competition_participations:
                    await update_single_competition_progress(participation["competition_id"])
            except Exception as e:
                logger.error(f"Failed to update competition progress: {e}")
            
            # Enhanced Gamification hooks for income transactions - Phase 1
            gamification = await get_gamification_service()
            streak_result = await gamification.update_user_streak(user_id)
            
            # Check for milestone achievements and trigger notifications
            if streak_result and streak_result.get("milestone_reached"):
                milestone_data = streak_result["milestone_reached"]
                # Send push notification for milestone
                try:
                    if PUSH_NOTIFICATION_AVAILABLE:
                        push_service = await get_push_service()
                        await push_service.send_milestone_notification(user_id, milestone_data)
                except Exception as e:
                    logger.error(f"Failed to send milestone push notification: {e}")
            
            # Check and award badges
            newly_earned_badges = await gamification.check_and_award_badges(user_id, "income_created", {
                "amount": transaction.amount,
                "source": transaction_dict.get("source"),
                "total_earnings": user_doc.get("total_earnings", 0) + transaction.amount
            })
            
            # Send notifications for new badges
            for badge in newly_earned_badges:
                try:
                    if PUSH_NOTIFICATION_AVAILABLE:
                        push_service = await get_push_service()
                        badge_milestone_data = {
                            "title": f"Badge Earned: {badge['name']}!",
                            "message": badge["description"],
                            "type": "badge",
                            "icon": badge["icon"],
                            "achievement_id": badge.get("achievement_id")
                        }
                        await push_service.send_milestone_notification(user_id, badge_milestone_data)
                except Exception as e:
                    logger.error(f"Failed to send badge push notification: {e}")
            
            await gamification.update_leaderboards(user_id)
            
            # Create milestone achievements for first transactions
            if len(await get_user_transactions(user_id, limit=2)) == 1:  # First transaction
                await gamification.create_milestone_achievement(user_id, "first_transaction", {
                    "type": "income",
                    "amount": transaction.amount
                })
        
        # 🔥 REAL-TIME NOTIFICATIONS: Send WebSocket notifications for all transactions
        try:
            notification_service = await get_notification_service()
            
            if transaction_data.type == "expense":
                # Send expense notification with budget info
                budget = await db.budgets.find_one({
                    "user_id": user_id,
                    "category": transaction_dict["category"],
                    "month": datetime.now(timezone.utc).strftime("%Y-%m")
                })
                remaining_budget = budget["allocated_amount"] - budget["spent_amount"] if budget else 0
                
                await notification_service.create_and_notify_in_app_notification(user_id, {
                    "type": "transaction_expense",
                    "title": f"💸 Expense Added: ₹{transaction.amount}",
                    "message": f"Spent ₹{transaction.amount} on {transaction.category}. Remaining budget: ₹{remaining_budget:.2f}",
                    "priority": "high" if remaining_budget < (budget["allocated_amount"] * 0.1) else "medium",
                    "data": {
                        "transaction_id": transaction.id,
                        "category": transaction.category,
                        "amount": transaction.amount,
                        "remaining_budget": remaining_budget,
                        "budget_alert": remaining_budget < (budget["allocated_amount"] * 0.2) if budget else False
                    }
                })
                
                # Send budget alert if low budget
                if budget and remaining_budget < (budget["allocated_amount"] * 0.2):
                    await notification_service.create_and_notify_in_app_notification(user_id, {
                        "type": "budget_alert",
                        "title": "⚠️ Budget Alert!",
                        "message": f"Only ₹{remaining_budget:.2f} left in {transaction.category} budget this month",
                        "priority": "high",
                        "data": {
                            "category": transaction.category,
                            "remaining_budget": remaining_budget,
                            "allocated_amount": budget["allocated_amount"]
                        }
                    })
            
            else:  # Income transaction
                # Get updated user stats
                user_doc = await get_user_by_id(user_id)
                total_earnings = user_doc.get("total_earnings", 0)
                
                await notification_service.create_and_notify_in_app_notification(user_id, {
                    "type": "transaction_income",
                    "title": f"💰 Income Added: ₹{transaction.amount}",
                    "message": f"Great! You've earned ₹{transaction.amount}. Total earnings: ₹{total_earnings:.2f}",
                    "priority": "medium",
                    "data": {
                        "transaction_id": transaction.id,
                        "amount": transaction.amount,
                        "total_earnings": total_earnings,
                        "income_streak": user_doc.get("current_streak", 0)
                    }
                })
                
                # Send streak milestone notification if applicable
                current_streak = user_doc.get("current_streak", 0)
                if current_streak > 0 and current_streak % 5 == 0:  # Every 5 days
                    await notification_service.create_and_notify_in_app_notification(user_id, {
                        "type": "streak_milestone",
                        "title": f"🔥 {current_streak}-Day Income Streak!",
                        "message": f"Amazing! You're on a {current_streak}-day income streak. Keep it up!",
                        "priority": "high",
                        "data": {
                            "streak_days": current_streak,
                            "milestone_type": "income_streak"
                        }
                    })
            
        except Exception as e:
            logger.error(f"Failed to send transaction notification: {str(e)}")
        
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
        hustle_dict["contact_info"] = hustle_data.application_link or "admin@earnaura.app"
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
    
    # Gamification hooks for budget creation
    gamification = await get_gamification_service()
    user_budgets = await get_user_budgets(user_id)
    if len(user_budgets) == 1:  # First budget
        await gamification.create_milestone_achievement(user_id, "first_budget", {
            "category": budget_dict["category"],
            "amount": budget_data.allocated_amount
        })
    
    await gamification.check_and_award_badges(user_id, "budget_created", {
        "budget_count": len(user_budgets),
        "category": budget_dict["category"]
    })
    
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
        
        # Get database connection for all operations
        db = await get_database()
        
        # Check if goal is being marked as completed
        was_completed = False
        if "is_completed" in update_data and update_data["is_completed"]:
            # Get the goal before updating to check if it wasn't already completed
            existing_goal = await db.financial_goals.find_one({"id": goal_id, "user_id": user_id})
            if existing_goal and not existing_goal.get("is_completed", False):
                was_completed = True
        
        if update_data:
            await update_financial_goal(goal_id, user_id, update_data)
        
        # Update challenge progress for goal completion challenges
        if was_completed:
            await update_user_challenge_progress(user_id)
            
            # Update group challenge progress
            await update_group_challenge_progress(user_id)
            
        # Gamification hooks for goal completion
        if was_completed:
            gamification = await get_gamification_service()
            
            # Create goal completion achievement
            goal = await db.financial_goals.find_one({"id": goal_id, "user_id": user_id})
            if goal:
                achievement_id = await gamification.create_milestone_achievement(user_id, "goal_completed", {
                    "goal_name": goal["name"],
                    "goal_category": goal["category"],
                    "target_amount": goal["target_amount"],
                    "completion_date": datetime.now(timezone.utc).isoformat()
                })
            
            # Check for goal-related badges
            await gamification.check_and_award_badges(user_id, "goal_completed", {
                "completed_goals": await db.financial_goals.count_documents({
                    "user_id": user_id,
                    "is_completed": True
                })
            })
            
            await gamification.update_leaderboards(user_id)
        
        # 🔥 REAL-TIME NOTIFICATIONS: Send WebSocket notifications for goal updates
        try:
            notification_service = await get_notification_service()
            goal = await db.financial_goals.find_one({"id": goal_id, "user_id": user_id})
            
            if goal:
                if was_completed:
                    # Goal completion notification
                    await notification_service.create_and_notify_in_app_notification(user_id, {
                        "type": "goal_completed",
                        "title": f"🎉 Goal Completed!",
                        "message": f"Congratulations! You've completed your {goal['name']} goal of ₹{goal['target_amount']:,.0f}!",
                        "priority": "high",
                        "action_url": "/goals",
                        "data": {
                            "goal_id": goal_id,
                            "goal_name": goal["name"],
                            "goal_category": goal.get("category", "custom"),
                            "target_amount": goal["target_amount"],
                            "achievement_unlocked": True
                        }
                    })
                else:
                    # Goal progress update notification
                    current_amount = goal.get("current_amount", 0)
                    target_amount = goal.get("target_amount", 0)
                    progress_percentage = (current_amount / target_amount * 100) if target_amount > 0 else 0
                    
                    # Send notification if significant progress (every 25%)
                    milestones = [25, 50, 75, 90]
                    for milestone in milestones:
                        if abs(progress_percentage - milestone) < 5:  # Within 5% of milestone
                            await notification_service.create_and_notify_in_app_notification(user_id, {
                                "type": "goal_progress",
                                "title": f"📊 Goal Progress: {progress_percentage:.0f}%",
                                "message": f"You're {progress_percentage:.0f}% towards your {goal['name']} goal! Keep going!",
                                "priority": "medium",
                                "action_url": "/goals",
                                "data": {
                                    "goal_id": goal_id,
                                    "goal_name": goal["name"],
                                    "current_amount": current_amount,
                                    "target_amount": target_amount,
                                    "progress_percentage": progress_percentage
                                }
                            })
                            break
        except Exception as e:
            logger.error(f"Failed to send goal update notification: {str(e)}")
        
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

# Startup event to initialize all services
@app.on_event("startup")
async def startup_event():
    """Initialize all services on startup"""
    logger.info("🚀 Starting EarnAura with comprehensive initialization...")
    
    # Initialize database and seed data (including universities)
    try:
        await init_database()
        logger.info("✅ Database initialization complete with universities")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
    
    # Initialize cache warming for popular cities (background task)
    try:
        await cache_service.warm_popular_locations()
        logger.info("✅ Cache warming initiated for popular cities")
    except Exception as e:
        logger.warning(f"⚠️  Cache warming failed: {str(e)}")
    
    logger.info("✅ EarnAura startup complete with all systems initialized")
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

# ===== GAMIFICATION & VIRAL FEATURES ENDPOINTS =====

@api_router.get("/gamification/profile")
@limiter.limit("30/minute")
async def get_gamification_profile_endpoint(
    request: Request,
    enhanced: bool = False,
    user_id: str = Depends(get_current_user)
):
    """Get user's complete gamification profile - Enhanced for Phase 1"""
    try:
        gamification = await get_gamification_service()
        
        if enhanced:
            # Return enhanced profile with social proof and celebrations
            profile = await gamification.get_enhanced_gamification_profile(user_id)
        else:
            # Return standard profile for backward compatibility
            profile = await gamification.get_user_gamification_profile(user_id)
        
        return profile
        
    except Exception as e:
        logger.error(f"Get gamification profile error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get gamification profile")

@api_router.get("/gamification/badges")
@limiter.limit("30/minute") 
async def get_available_badges_endpoint(request: Request):
    """Get all available badges"""
    try:
        db = await get_database()
        badges = await db.badges.find({"is_active": True}).sort("requirement_value", 1).to_list(None)
        
        # Format badges by category
        categorized_badges = {}
        for badge in badges:
            category = badge["category"]
            if category not in categorized_badges:
                categorized_badges[category] = []
            
            categorized_badges[category].append({
                "id": str(badge["_id"]),
                "name": badge["name"],
                "description": badge["description"],
                "icon": badge["icon"],
                "rarity": badge["rarity"],
                "requirement_type": badge["requirement_type"],
                "requirement_value": badge["requirement_value"],
                "points_awarded": badge["points_awarded"]
            })
        
        return {
            "badges_by_category": categorized_badges,
            "total_badges": len(badges)
        }
        
    except Exception as e:
        logger.error(f"Get badges error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get badges")

@api_router.get("/gamification/leaderboards/{leaderboard_type}")
@limiter.limit("20/minute")
async def get_leaderboard_endpoint(
    request: Request,
    leaderboard_type: str,
    period: str = "all_time",
    university: Optional[str] = None,
    limit: int = 10,
    user_id: str = Depends(get_current_user)
):
    """Get leaderboard rankings"""
    try:
        gamification = await get_gamification_service()
        leaderboard = await gamification.get_leaderboard(leaderboard_type, period, university, limit)
        
        # Add current user's rank
        user_rank = await gamification.get_user_rank(user_id, leaderboard_type, period, university)
        leaderboard["user_rank"] = user_rank
        
        return leaderboard
        
    except Exception as e:
        logger.error(f"Get leaderboard error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get leaderboard")

@api_router.get("/gamification/achievements")
@limiter.limit("30/minute")
async def get_user_achievements_endpoint(
    request: Request,
    user_id: str = Depends(get_current_user),
    limit: int = 20,
    skip: int = 0
):
    """Get user's achievements"""
    try:
        db = await get_database()
        achievements = await db.achievements.find(
            {"user_id": user_id}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(None)
        
        # Format achievements
        formatted_achievements = []
        for achievement in achievements:
            formatted_achievements.append({
                "id": str(achievement["_id"]),
                "type": achievement["type"],
                "title": achievement["title"],
                "description": achievement["description"],
                "icon": achievement["icon"],
                "points_earned": achievement["points_earned"],
                "created_at": achievement["created_at"],
                "is_shared": achievement.get("is_shared", False),
                "reaction_count": achievement.get("reaction_count", 0),
                "achievement_data": achievement.get("achievement_data", {})
            })
        
        total_achievements = await db.achievements.count_documents({"user_id": user_id})
        
        return {
            "achievements": formatted_achievements,
            "total": total_achievements,
            "page": skip // limit + 1,
            "has_more": skip + limit < total_achievements
        }
        
    except Exception as e:
        logger.error(f"Get achievements error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get achievements")

@api_router.post("/gamification/achievements/{achievement_id}/share")
@limiter.limit("10/minute")
async def share_achievement_endpoint(
    request: Request,
    achievement_id: str,
    user_id: str = Depends(get_current_user)
):
    """Share an achievement to the community"""
    try:
        db = await get_database()
        
        # Verify achievement belongs to user
        achievement = await db.achievements.find_one({
            "_id": achievement_id,
            "user_id": user_id
        })
        
        if not achievement:
            raise HTTPException(status_code=404, detail="Achievement not found")
        
        # Mark achievement as shared
        await db.achievements.update_one(
            {"_id": achievement_id},
            {"$set": {"is_shared": True}}
        )
        
        # Update user's shared count
        await db.users.update_one(
            {"id": user_id},
            {"$inc": {"achievements_shared": 1}}
        )
        
        # Create community post
        community_post = {
            "user_id": user_id,
            "type": "achievement_share",
            "content": f"Just earned the '{achievement['title']}' badge! {achievement['description']}",
            "achievement_id": achievement_id,
            "created_at": datetime.now(timezone.utc),
            "like_count": 0,
            "comment_count": 0,
            "share_count": 0,
            "is_featured": False
        }
        
        result = await db.community_posts.insert_one(community_post)
        
        # Check for social badges
        gamification = await get_gamification_service()
        await gamification.check_and_award_badges(user_id, "achievement_shared", {
            "shared_count": await db.achievements.count_documents({
                "user_id": user_id,
                "is_shared": True
            })
        })
        
        return {
            "message": "Achievement shared successfully",
            "post_id": str(result.inserted_id),
            "shared": True
        }
        
    except Exception as e:
        logger.error(f"Share achievement error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to share achievement")

@api_router.get("/gamification/community/feed")
@limiter.limit("30/minute")
async def get_community_feed_endpoint(
    request: Request,
    user_id: str = Depends(get_current_user),
    limit: int = 20,
    skip: int = 0,
    university_only: bool = False
):
    """Get community activity feed"""
    try:
        db = await get_database()
        
        # Build query
        query = {}
        if university_only:
            user = await get_user_by_id(user_id)
            if user and user.get("university"):
                # Get posts from users in the same university
                university_users = await db.users.find(
                    {"university": user["university"]}
                ).to_list(None)
                university_user_ids = [u["id"] for u in university_users]
                query["user_id"] = {"$in": university_user_ids}
        
        # Get community posts
        posts = await db.community_posts.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(None)
        
        # Format posts with user details
        formatted_posts = []
        for post in posts:
            post_user = await get_user_by_id(post["user_id"])
            if post_user:
                formatted_post = {
                    "id": str(post["_id"]),
                    "type": post["type"],
                    "content": post["content"],
                    "created_at": post["created_at"],
                    "like_count": post["like_count"],
                    "comment_count": post["comment_count"],
                    "share_count": post["share_count"],
                    "is_featured": post["is_featured"],
                    "user": {
                        "id": post_user["id"],
                        "full_name": post_user["full_name"],
                        "avatar": post_user.get("avatar", "boy"),
                        "university": post_user.get("university"),
                        "level": post_user.get("level", 1),
                        "title": post_user.get("title", "Beginner")
                    }
                }
                
                # Add achievement details if it's an achievement share
                if post.get("achievement_id"):
                    achievement = await db.achievements.find_one({"_id": post["achievement_id"]})
                    if achievement:
                        formatted_post["achievement"] = {
                            "id": str(achievement["_id"]),
                            "title": achievement["title"],
                            "description": achievement["description"],
                            "icon": achievement["icon"],
                            "points_earned": achievement["points_earned"]
                        }
                
                formatted_posts.append(formatted_post)
        
        total_posts = await db.community_posts.count_documents(query)
        
        return {
            "posts": formatted_posts,
            "total": total_posts,
            "page": skip // limit + 1,
            "has_more": skip + limit < total_posts
        }
        
    except Exception as e:
        logger.error(f"Get community feed error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get community feed")

@api_router.post("/gamification/community/posts/{post_id}/like")
@limiter.limit("30/minute")
async def like_community_post_endpoint(
    request: Request,
    post_id: str,
    user_id: str = Depends(get_current_user)
):
    """Like a community post"""
    try:
        db = await get_database()
        
        # Check if post exists
        post = await db.community_posts.find_one({"_id": post_id})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Check if user already liked this post
        existing_like = await db.community_interactions.find_one({
            "user_id": user_id,
            "post_id": post_id,
            "interaction_type": "like"
        })
        
        if existing_like:
            # Unlike - remove the interaction and decrement count
            await db.community_interactions.delete_one({"_id": existing_like["_id"]})
            await db.community_posts.update_one(
                {"_id": post_id},
                {"$inc": {"like_count": -1}}
            )
            return {"liked": False, "message": "Post unliked"}
        else:
            # Like - create interaction and increment count
            interaction = {
                "user_id": user_id,
                "target_user_id": post["user_id"],
                "post_id": post_id,
                "interaction_type": "like",
                "created_at": datetime.now(timezone.utc)
            }
            
            await db.community_interactions.insert_one(interaction)
            await db.community_posts.update_one(
                {"_id": post_id},
                {"$inc": {"like_count": 1}}
            )
            
            return {"liked": True, "message": "Post liked"}
        
    except Exception as e:
        logger.error(f"Like post error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to like post")

@api_router.get("/gamification/universities")
@limiter.limit("30/minute")
async def get_universities_endpoint(request: Request):
    """Get list of universities for registration"""
    try:
        db = await get_database()
        universities = await db.universities.find().sort("name", 1).to_list(None)
        
        formatted_universities = []
        for uni in universities:
            formatted_universities.append({
                "id": str(uni["_id"]),
                "name": uni["name"],
                "short_name": uni["short_name"],
                "location": uni["location"],
                "type": uni["type"],
                "is_verified": uni["is_verified"],
                "student_count": uni["student_count"]
            })
        
        return {
            "universities": formatted_universities,
            "total": len(formatted_universities)
        }
        
    except Exception as e:
        logger.error(f"Get universities error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get universities")

@api_router.post("/gamification/universities")
@limiter.limit("5/minute")
async def create_university_endpoint(
    request: Request,
    university_data: UniversityCreate,
    user_id: str = Depends(get_current_user)
):
    """Create a new university (user-submitted)"""
    try:
        db = await get_database()
        
        # Check if university already exists
        existing = await db.universities.find_one({
            "$or": [
                {"name": university_data.name},
                {"short_name": university_data.short_name}
            ]
        })
        
        if existing:
            return {
                "id": str(existing["_id"]),
                "name": existing["name"],
                "message": "University already exists"
            }
        
        # Create new university
        university_dict = university_data.dict()
        university_dict["is_verified"] = False  # User-submitted universities need admin verification
        university_dict["student_count"] = 1  # Creator is the first student
        university_dict["created_at"] = datetime.now(timezone.utc)
        
        result = await db.universities.insert_one(university_dict)
        
        return {
            "id": str(result.inserted_id),
            "name": university_data.name,
            "message": "University created successfully (pending verification)"
        }
        
    except Exception as e:
        logger.error(f"Create university error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create university")

@api_router.get("/gamification/universities/suggestions")
@limiter.limit("30/minute")
async def get_university_suggestions_endpoint(
    request: Request,
    location: str,
    student_level: str,
    limit: int = 10
):
    """Get smart university suggestions based on user location and student level"""
    try:
        db = await get_database()
        
        # Parse user location
        location_parts = [part.strip().lower() for part in location.split(',')]
        city_query = location_parts[0] if location_parts else ""
        state_query = location_parts[-1] if len(location_parts) > 1 else location_parts[0] if location_parts else ""
        
        # Build query for location matching
        location_query = {
            "$or": [
                {"city": {"$regex": city_query, "$options": "i"}},
                {"state": {"$regex": state_query, "$options": "i"}},
                {"location": {"$regex": location, "$options": "i"}}
            ]
        }
        
        # Add student level filter
        level_query = {"student_levels": student_level}
        
        # Combine queries
        combined_query = {
            "$and": [location_query, level_query]
        }
        
        # Get matching universities sorted by ranking
        universities = await db.universities.find(combined_query).sort("ranking", 1).limit(limit).to_list(None)
        
        # If no exact matches, get broader results
        if len(universities) < 3:
            # Fallback: Get universities by state only
            state_fallback = await db.universities.find({
                "$and": [
                    {"state": {"$regex": state_query, "$options": "i"}},
                    {"student_levels": student_level}
                ]
            }).sort("ranking", 1).limit(limit - len(universities)).to_list(None)
            
            # Add fallback results if not already included
            for uni in state_fallback:
                if str(uni["_id"]) not in [str(u["_id"]) for u in universities]:
                    universities.append(uni)
        
        # If still not enough, get top universities for the student level
        if len(universities) < 3:
            top_universities = await db.universities.find({
                "student_levels": student_level,
                "ranking": {"$lte": 20}  # Top 20 institutions
            }).sort("ranking", 1).limit(limit - len(universities)).to_list(None)
            
            for uni in top_universities:
                if str(uni["_id"]) not in [str(u["_id"]) for u in universities]:
                    universities.append(uni)
        
        # Format response
        suggestions = []
        for uni in universities[:limit]:
            # Calculate relevance score
            relevance_score = 100
            if city_query in uni.get("city", "").lower():
                relevance_score += 50  # Same city bonus
            elif state_query in uni.get("state", "").lower():
                relevance_score += 25  # Same state bonus
            
            # Type bonus for student level
            if student_level == "graduate" and uni.get("type") in ["engineering_institute", "management_institute"]:
                relevance_score += 20
            elif student_level == "undergraduate" and uni.get("type") in ["state_university", "central_university"]:
                relevance_score += 15
            
            # Ranking bonus (lower ranking = higher score)
            relevance_score += max(0, 30 - uni.get("ranking", 30))
            
            suggestions.append({
                "id": str(uni["_id"]),
                "name": uni["name"],
                "short_name": uni["short_name"],
                "location": uni["location"],
                "city": uni["city"],
                "state": uni["state"],
                "type": uni["type"],
                "student_levels": uni["student_levels"],
                "categories": uni.get("categories", []),
                "ranking": uni.get("ranking", 999),
                "is_verified": uni["is_verified"],
                "student_count": uni["student_count"],
                "relevance_score": relevance_score,
                "distance_match": city_query in uni.get("city", "").lower(),
                "level_match": student_level in uni["student_levels"]
            })
        
        # Sort by relevance score
        suggestions.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return {
            "suggestions": suggestions,
            "total": len(suggestions),
            "user_location": location,
            "student_level": student_level,
            "query_info": {
                "city_searched": city_query,
                "state_searched": state_query,
                "exact_matches": len([s for s in suggestions if s["distance_match"]]),
                "same_state_matches": len([s for s in suggestions if s["state"].lower() == state_query.lower()])
            }
        }
        
    except Exception as e:
        logger.error(f"Get university suggestions error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get university suggestions")

# ===== PHASE 1 ENHANCED GAMIFICATION ENDPOINTS =====

@api_router.get("/gamification/social-proof")
@limiter.limit("20/minute")
async def get_social_proof_stats_endpoint(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get social proof statistics for enhanced gamification"""
    try:
        gamification = await get_gamification_service()
        stats = await gamification.get_social_proof_stats(user_id)
        return stats
        
    except Exception as e:
        logger.error(f"Get social proof stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get social proof statistics")

@api_router.get("/gamification/celebrations/pending")
@limiter.limit("10/minute")
async def get_pending_celebrations_endpoint(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get pending celebrations for user login"""
    try:
        gamification = await get_gamification_service()
        celebrations = await gamification.get_pending_celebrations(user_id)
        return {"celebrations": celebrations}
        
    except Exception as e:
        logger.error(f"Get pending celebrations error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get pending celebrations")

@api_router.post("/gamification/celebrations/queue")
@limiter.limit("10/minute")
async def queue_celebration_endpoint(
    request: Request,
    celebration_data: dict,
    user_id: str = Depends(get_current_user)
):
    """Queue celebration for offline users"""
    try:
        gamification = await get_gamification_service()
        await gamification.queue_celebration(user_id, celebration_data)
        return {"message": "Celebration queued successfully"}
        
    except Exception as e:
        logger.error(f"Queue celebration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to queue celebration")

# ===== PUSH NOTIFICATION ENDPOINTS =====

@api_router.post("/notifications/subscribe")
@limiter.limit("5/minute")
async def subscribe_to_push_notifications(
    request: Request,
    subscription_data: dict,
    user_id: str = Depends(get_current_user)
):
    """Subscribe user to push notifications"""
    try:
        db = await get_database()
        
        # Store user's push subscription
        subscription_doc = {
            "user_id": user_id,
            "subscription_data": subscription_data,
            "created_at": datetime.now(timezone.utc),
            "is_active": True,
            "notification_preferences": {
                "streak_reminders": True,
                "milestone_achievements": True,
                "friend_activities": True,
                "daily_reminders": True,
                "reminder_time": "19:00"  # 7 PM default
            }
        }
        
        # Update or insert subscription
        await db.push_subscriptions.update_one(
            {"user_id": user_id},
            {"$set": subscription_doc},
            upsert=True
        )
        
        return {"message": "Successfully subscribed to push notifications"}
        
    except Exception as e:
        logger.error(f"Push subscription error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to subscribe to push notifications")

@api_router.put("/notifications/preferences")
@limiter.limit("10/minute")
async def update_notification_preferences(
    request: Request,
    preferences: dict,
    user_id: str = Depends(get_current_user)
):
    """Update user's notification preferences"""
    try:
        db = await get_database()
        
        # Update notification preferences
        await db.push_subscriptions.update_one(
            {"user_id": user_id},
            {"$set": {"notification_preferences": preferences}},
            upsert=True
        )
        
        return {"message": "Notification preferences updated"}
        
    except Exception as e:
        logger.error(f"Update notification preferences error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update notification preferences")

@api_router.get("/notifications/preferences")
@limiter.limit("20/minute")
async def get_notification_preferences(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get user's notification preferences"""
    try:
        db = await get_database()
        
        subscription = await db.push_subscriptions.find_one({"user_id": user_id})
        
        if subscription:
            return subscription.get("notification_preferences", {
                "streak_reminders": True,
                "milestone_achievements": True,
                "friend_activities": True,
                "daily_reminders": True,
                "reminder_time": "19:00"
            })
        
        # Return default preferences if no subscription exists
        return {
            "streak_reminders": True,
            "milestone_achievements": True,
            "friend_activities": True,
            "daily_reminders": True,
            "reminder_time": "19:00"
        }
        
    except Exception as e:
        logger.error(f"Get notification preferences error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get notification preferences")

@api_router.post("/gamification/trigger-milestone-check")
@limiter.limit("30/minute")
async def trigger_milestone_check_endpoint(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Manually trigger milestone check for testing"""
    try:
        gamification = await get_gamification_service()
        result = await gamification.update_user_streak(user_id)
        return {"result": result}
        
    except Exception as e:
        logger.error(f"Trigger milestone check error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to trigger milestone check")

# ===== GAMIFICATION & COMMUNITY API ENDPOINTS =====

@api_router.get("/gamification/achievements")
@limiter.limit("10/minute")
async def get_user_achievements(request: Request, limit: int = 10, current_user: Dict[str, Any] = Depends(get_current_super_admin)):
    """Get user's recent achievements"""
    try:
        db = await get_database()
        achievements = await db.achievements.find(
            {"user_id": current_user["id"]}
        ).sort("created_at", -1).limit(limit).to_list(None)
        
        # Convert ObjectId to string for JSON serialization
        for achievement in achievements:
            achievement["id"] = str(achievement["_id"])
            del achievement["_id"]
        
        return {"achievements": achievements}
    except Exception as e:
        logger.error(f"Get achievements error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get achievements")

# Removed duplicate leaderboard endpoint

@api_router.post("/gamification/achievements/{achievement_id}/share")
@limiter.limit("5/minute")
async def share_achievement(request: Request, achievement_id: str, current_user: Dict[str, Any] = Depends(get_current_super_admin)):
    """Share an achievement to community feed"""
    try:
        db = await get_database()
        
        # Check if achievement belongs to user
        achievement = await db.achievements.find_one({
            "_id": achievement_id,
            "user_id": current_user["id"]
        })
        
        if not achievement:
            raise HTTPException(status_code=404, detail="Achievement not found")
        
        if achievement.get("is_shared", False):
            raise HTTPException(status_code=400, detail="Achievement already shared")
        
        # Mark as shared
        await db.achievements.update_one(
            {"_id": achievement_id},
            {
                "$set": {
                    "is_shared": True,
                    "shared_at": datetime.now(timezone.utc)
                }
            }
        )
        
        # Update user's achievements_shared count
        await db.users.update_one(
            {"_id": current_user["id"]},
            {"$inc": {"achievements_shared": 1}}
        )
        
        # Check for sharing-related badges
        gamification = await get_gamification_service()
        await gamification.check_and_award_badges(current_user["id"], "achievement_shared", {
            "achievement_id": achievement_id
        })
        
        return {"success": True, "message": "Achievement shared successfully"}
        
    except Exception as e:
        logger.error(f"Share achievement error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to share achievement")

@api_router.get("/gamification/community-feed")
@limiter.limit("10/minute")
async def get_community_feed(request: Request, limit: int = 20, current_user: Dict[str, Any] = Depends(get_current_super_admin)):
    """Get community achievements feed (Pan-India)"""
    try:
        db = await get_database()
        
        # Get shared achievements from all users
        pipeline = [
            {"$match": {"is_shared": True}},
            {"$sort": {"shared_at": -1}},
            {"$limit": limit},
            {"$lookup": {
                "from": "users",
                "localField": "user_id", 
                "foreignField": "_id",
                "as": "user_info"
            }},
            {"$unwind": "$user_info"},
            {"$project": {
                "_id": 1,
                "type": 1,
                "title": 1,
                "description": 1,
                "icon": 1,
                "points_earned": 1,
                "shared_at": 1,
                "reaction_count": 1,
                "user_name": "$user_info.full_name",
                "user_avatar": "$user_info.avatar",
                "user_level": "$user_info.level",
                "user_title": "$user_info.title",
                "university": "$user_info.university"
            }}
        ]
        
        feed = await db.achievements.aggregate(pipeline).to_list(None)
        
        # Convert ObjectId to string
        for item in feed:
            item["id"] = str(item["_id"])
            del item["_id"]
        
        return {"feed": feed}
        
    except Exception as e:
        logger.error(f"Get community feed error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get community feed")

@api_router.post("/gamification/achievements/{achievement_id}/react")
@limiter.limit("10/minute")
async def react_to_achievement(request: Request, achievement_id: str, current_user: Dict[str, Any] = Depends(get_current_super_admin)):
    """React to a shared achievement"""
    try:
        db = await get_database()
        
        # Check if user already reacted
        existing_reaction = await db.achievement_reactions.find_one({
            "achievement_id": achievement_id,
            "user_id": current_user["id"]
        })
        
        if existing_reaction:
            # Remove reaction
            await db.achievement_reactions.delete_one({
                "achievement_id": achievement_id,
                "user_id": current_user["id"]
            })
            await db.achievements.update_one(
                {"_id": achievement_id},
                {"$inc": {"reaction_count": -1}}
            )
            return {"reacted": False, "message": "Reaction removed"}
        else:
            # Add reaction
            await db.achievement_reactions.insert_one({
                "achievement_id": achievement_id,
                "user_id": current_user["id"],
                "created_at": datetime.now(timezone.utc)
            })
            await db.achievements.update_one(
                {"_id": achievement_id},
                {"$inc": {"reaction_count": 1}}
            )
            return {"reacted": True, "message": "Reaction added"}
            
    except Exception as e:
        logger.error(f"React to achievement error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to react to achievement")

# ===== SOCIAL SHARING SYSTEM =====

@api_router.post("/social/generate-achievement-image")
@limiter.limit("10/minute")
async def generate_achievement_image_endpoint(
    request: Request,
    achievement_type: str,
    milestone_text: str,
    amount: Optional[float] = None,
    user_id: str = Depends(get_current_user)
):
    """Generate branded achievement image for social sharing"""
    try:
        db = await get_database()
        user = await get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's badge info if achievement type is badge
        badge_info = None
        if achievement_type == "badge_earned":
            # Get user's latest badge
            latest_badge = await db.user_badges.find_one(
                {"user_id": user_id},
                sort=[("earned_at", -1)]
            )
            if latest_badge:
                badge = await db.badges.find_one({"_id": latest_badge["badge_id"]})
                if badge:
                    badge_info = {
                        "icon": badge.get("icon", "🏆"),
                        "name": badge.get("name", "Achievement"),
                        "rarity": badge.get("rarity", "bronze")
                    }
        
        # Generate achievement image
        social_service = await get_social_sharing_service()
        if not social_service:
            raise HTTPException(status_code=503, detail="Social sharing service unavailable")
        
        image_filename = social_service.generate_achievement_image(
            achievement_type=achievement_type,
            milestone_text=milestone_text,
            amount=amount,
            user_name=user.get("full_name", "User"),
            badge_info=badge_info
        )
        
        if not image_filename:
            raise HTTPException(status_code=500, detail="Failed to generate image")
        
        return {
            "image_filename": image_filename,
            "image_url": f"/uploads/achievements/{image_filename}",
            "achievement_type": achievement_type,
            "milestone_text": milestone_text
        }
        
    except Exception as e:
        logger.error(f"Generate achievement image error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate achievement image")

@api_router.post("/social/generate-milestone-image")
@limiter.limit("10/minute")
async def generate_milestone_image_endpoint(
    request: Request,
    milestone_type: str,
    achievement_text: str,
    stats: Dict[str, Any],
    user_id: str = Depends(get_current_user)
):
    """Generate milestone celebration image"""
    try:
        db = await get_database()
        user = await get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Generate milestone image
        social_service = await get_social_sharing_service()
        if not social_service:
            raise HTTPException(status_code=503, detail="Social sharing service unavailable")
        
        image_filename = social_service.generate_milestone_celebration_image(
            milestone_type=milestone_type,
            achievement_text=achievement_text,
            stats=stats,
            user_name=user.get("full_name", "User")
        )
        
        if not image_filename:
            raise HTTPException(status_code=500, detail="Failed to generate milestone image")
        
        return {
            "image_filename": image_filename,
            "image_url": f"/uploads/achievements/{image_filename}",
            "milestone_type": milestone_type,
            "achievement_text": achievement_text
        }
        
    except Exception as e:
        logger.error(f"Generate milestone image error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate milestone image")

@api_router.post("/social/share/{platform}")
@limiter.limit("20/minute")
async def social_share_endpoint(
    request: Request,
    platform: str,
    achievement_type: str,
    milestone_text: str,
    image_filename: str,
    amount: Optional[float] = None,
    user_id: str = Depends(get_current_user)
):
    """Generate platform-specific share content"""
    try:
        db = await get_database()
        user = await get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if platform not in ["instagram", "whatsapp"]:
            raise HTTPException(status_code=400, detail="Platform must be 'instagram' or 'whatsapp'")
        
        # Generate platform-specific content
        social_service = await get_social_sharing_service()
        if not social_service:
            raise HTTPException(status_code=503, detail="Social sharing service unavailable")
        
        share_content = social_service.generate_social_share_content(
            platform=platform,
            achievement_type=achievement_type,
            milestone_text=milestone_text,
            image_filename=image_filename,
            user_name=user.get("full_name", "User")
        )
        
        # Track sharing activity
        sharing_record = {
            "user_id": user_id,
            "platform": platform,
            "achievement_type": achievement_type,
            "milestone_text": milestone_text,
            "image_filename": image_filename,
            "shared_at": datetime.now(timezone.utc)
        }
        await db.social_shares.insert_one(sharing_record)
        
        # Update user achievements_shared count
        await db.users.update_one(
            {"id": user_id},
            {"$inc": {"achievements_shared": 1}}
        )
        
        # Check for social sharing badges
        gamification = await get_gamification_service()
        await gamification.check_and_award_badges(user_id, "achievement_shared", {
            "shared_count": user.get("achievements_shared", 0) + 1
        })
        
        return share_content
        
    except Exception as e:
        logger.error(f"Social share error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate share content")

@api_router.get("/social/share-stats")
@limiter.limit("10/minute") 
async def get_share_stats_endpoint(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get user's social sharing statistics"""
    try:
        db = await get_database()
        
        # Get total shares by platform
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": "$platform",
                "count": {"$sum": 1}
            }}
        ]
        
        platform_stats = await db.social_shares.aggregate(pipeline).to_list(None)
        
        # Get recent shares
        recent_shares = await db.social_shares.find(
            {"user_id": user_id}
        ).sort("shared_at", -1).limit(10).to_list(None)
        
        # Format results
        stats_by_platform = {}
        for stat in platform_stats:
            stats_by_platform[stat["_id"]] = stat["count"]
        
        return {
            "total_shares": sum(stats_by_platform.values()),
            "instagram_shares": stats_by_platform.get("instagram", 0),
            "whatsapp_shares": stats_by_platform.get("whatsapp", 0),
            "recent_shares": [
                {
                    "platform": share["platform"],
                    "achievement_type": share["achievement_type"],
                    "milestone_text": share["milestone_text"],
                    "shared_at": share["shared_at"]
                }
                for share in recent_shares
            ]
        }
        
    except Exception as e:
        logger.error(f"Get share stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get share statistics")

# ===== ENHANCED SOCIAL SHARING ENDPOINTS =====

@api_router.post("/social/multi-platform-share")
@limiter.limit("10/minute")
async def generate_multi_platform_content_endpoint(
    request: Request,
    share_request: AchievementImageRequest,
    user_id: str = Depends(get_current_user)
):
    """Generate content for multiple social media platforms"""
    try:
        if not SOCIAL_SHARING_AVAILABLE:
            raise HTTPException(status_code=503, detail="Social sharing service unavailable")
        
        social_service = get_social_sharing_service()
        
        # Generate achievement image first
        image_filename = social_service.generate_achievement_image(
            achievement_type=share_request.achievement_type,
            milestone_text=share_request.milestone_text,
            amount=share_request.amount,
            user_name="User"
        )
        
        if not image_filename:
            raise HTTPException(status_code=500, detail="Failed to generate achievement image")
        
        # Generate multi-platform content
        multi_content = social_service.generate_multi_platform_content(
            achievement_type=share_request.achievement_type,
            milestone_text=share_request.milestone_text,
            image_filename=image_filename,
            user_name="User",
            platforms=["instagram", "whatsapp", "linkedin", "twitter", "facebook"]
        )
        
        # Record the sharing preparation (not actual sharing yet)
        db = await get_database()
        
        # Create multi-platform share record
        share_record = {
            "user_id": user_id,
            "achievement_type": share_request.achievement_type,
            "milestone_text": share_request.milestone_text,
            "image_filename": image_filename,
            "platforms_prepared": ["instagram", "whatsapp", "linkedin", "twitter", "facebook"],
            "prepared_at": datetime.now(timezone.utc)
        }
        
        await db.multi_platform_shares.insert_one(share_record)
        
        return multi_content
        
    except Exception as e:
        logger.error(f"Multi-platform share error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate multi-platform content")

@api_router.post("/social/linkedin-post")
@limiter.limit("10/minute")
async def generate_linkedin_post_endpoint(
    request: Request,
    share_request: AchievementImageRequest,
    user_id: str = Depends(get_current_user)
):
    """Generate LinkedIn-optimized achievement post"""
    try:
        if not SOCIAL_SHARING_AVAILABLE:
            raise HTTPException(status_code=503, detail="Social sharing service unavailable")
        
        social_service = get_social_sharing_service()
        
        # Generate professional achievement image
        image_filename = social_service.generate_achievement_image(
            achievement_type=share_request.achievement_type,
            milestone_text=share_request.milestone_text,
            amount=share_request.amount,
            user_name="User"
        )
        
        if not image_filename:
            raise HTTPException(status_code=500, detail="Failed to generate achievement image")
        
        # Generate LinkedIn-specific content
        linkedin_content = social_service.generate_social_share_content(
            platform="linkedin",
            achievement_type=share_request.achievement_type,
            milestone_text=share_request.milestone_text,
            image_filename=image_filename,
            user_name="User"
        )
        
        # Record LinkedIn post creation
        db = await get_database()
        
        linkedin_post = {
            "user_id": user_id,
            "achievement_type": share_request.achievement_type,
            "milestone_text": share_request.milestone_text,
            "professional_content": linkedin_content["text"],
            "hashtags": linkedin_content.get("text", "").split("#")[1:] if "#" in linkedin_content.get("text", "") else [],
            "image_filename": image_filename,
            "created_at": datetime.now(timezone.utc),
            "shared_manually": True
        }
        
        await db.linkedin_posts.insert_one(linkedin_post)
        
        return {
            "linkedin_content": linkedin_content,
            "image_url": f"/uploads/achievements/{image_filename}",
            "post_id": linkedin_post.get("id", "generated")
        }
        
    except Exception as e:
        logger.error(f"LinkedIn post error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate LinkedIn post")

@api_router.post("/social/viral-referral-link")
@limiter.limit("5/minute")
async def create_viral_referral_link_endpoint(
    request: Request,
    platform_source: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """Create trackable viral referral link"""
    try:
        db = await get_database()
        
        # Get or create referral program
        referral_program = await db.referral_programs.find_one({"referrer_id": user_id})
        
        if not referral_program:
            # Create referral program
            referral_code = user_id[:8] + str(int(datetime.now().timestamp()))[-6:]
            referral_program = {
                "referrer_id": user_id,
                "referral_code": referral_code,
                "total_referrals": 0,
                "successful_referrals": 0,
                "total_earnings": 0.0,
                "pending_earnings": 0.0,
                "created_at": datetime.now(timezone.utc)
            }
            await db.referral_programs.insert_one(referral_program)
        
        # Create viral referral link with tracking
        base_url = FRONTEND_URL
        original_url = f"{base_url}/register?ref={referral_program['referral_code']}"
        
        # Generate shortened URL (simple implementation)
        short_id = str(uuid.uuid4())[:8]
        shortened_url = f"{base_url}/r/{short_id}"
        
        viral_link = {
            "user_id": user_id,
            "referral_code": referral_program["referral_code"],
            "shortened_url": shortened_url,
            "original_url": original_url,
            "click_count": 0,
            "conversion_count": 0,
            "platform_source": platform_source,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(days=30),  # 30-day expiry
            "is_active": True,
            "viral_coefficient": 0.0
        }
        
        result = await db.viral_referral_links.insert_one(viral_link)
        viral_link["id"] = str(result.inserted_id)
        
        return {
            "viral_link": shortened_url,
            "original_link": original_url,
            "referral_code": referral_program["referral_code"],
            "track_id": viral_link["id"],
            "expires_at": viral_link["expires_at"],
            "sharing_content": {
                "text": f"🚀 Join me on EarnAura - the smartest way to track your finances and achieve your goals! Get rewarded for good financial habits. {shortened_url}",
                "hashtags": "#FinancialGoals #EarnAura #SmartMoney #StudentFinance"
            }
        }
        
    except Exception as e:
        logger.error(f"Viral referral link error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create viral referral link")

@api_router.get("/social/referral-analytics")
@limiter.limit("10/minute")
async def get_referral_analytics_endpoint(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get comprehensive referral tracking analytics"""
    try:
        db = await get_database()
        
        # Get viral referral links
        viral_links = await db.viral_referral_links.find({"user_id": user_id}).to_list(None)
        
        # Get click analytics
        total_clicks = sum(link.get("click_count", 0) for link in viral_links)
        total_conversions = sum(link.get("conversion_count", 0) for link in viral_links)
        
        # Calculate viral coefficient
        viral_coefficient = total_conversions / total_clicks if total_clicks > 0 else 0.0
        
        # Get platform breakdown
        platform_stats = {}
        for link in viral_links:
            platform = link.get("platform_source", "unknown")
            if platform not in platform_stats:
                platform_stats[platform] = {"clicks": 0, "conversions": 0}
            
            platform_stats[platform]["clicks"] += link.get("click_count", 0)
            platform_stats[platform]["conversions"] += link.get("conversion_count", 0)
        
        # Get recent clicks
        recent_clicks = await db.referral_clicks.find(
            {"referral_link_id": {"$in": [link["id"] for link in viral_links if "id" in link]}}
        ).sort("clicked_at", -1).limit(20).to_list(None)
        
        return {
            "total_links_created": len(viral_links),
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "viral_coefficient": round(viral_coefficient, 4),
            "conversion_rate": round((total_conversions / total_clicks * 100), 2) if total_clicks > 0 else 0.0,
            "platform_breakdown": platform_stats,
            "active_links": len([link for link in viral_links if link.get("is_active", False)]),
            "recent_activity": [
                {
                    "type": "click",
                    "platform_source": click.get("platform_source", "unknown"),
                    "clicked_at": click["clicked_at"],
                    "converted": click.get("converted", False)
                }
                for click in recent_clicks
            ]
        }
        
    except Exception as e:
        logger.error(f"Referral analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get referral analytics")

# ===== EXPENSE RECEIPT UPLOAD & SHARING =====

@api_router.post("/expenses/upload-receipt")
@limiter.limit("10/minute")
async def upload_expense_receipt_endpoint(
    request: Request,
    file: UploadFile = File(...),
    transaction_id: Optional[str] = None,
    category: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """Upload expense receipt with OCR processing (max 5MB)"""
    try:
        # Validate file type
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload JPG, PNG, or PDF files.")
        
        # Validate file size (5MB limit)
        MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes
        content = await file.read()
        file_size = len(content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size ({file_size / (1024*1024):.2f}MB) exceeds maximum limit of 5MB"
            )
        
        # Create receipts directory if it doesn't exist
        receipts_dir = UPLOADS_DIR / "receipts"
        receipts_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        timestamp = int(datetime.now().timestamp())
        unique_filename = f"receipt_{user_id[:8]}_{timestamp}{file_extension}"
        file_path = receipts_dir / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Basic OCR processing (simple implementation)
        # In production, you'd use services like AWS Textract, Google Vision API, etc.
        ocr_text = await process_receipt_ocr(str(file_path))
        
        # Extract merchant name, amount, and date from OCR text
        extracted_data = extract_receipt_data(ocr_text)
        
        # Save receipt record
        db = await get_database()
        
        receipt_record = {
            "user_id": user_id,
            "transaction_id": transaction_id,
            "filename": unique_filename,
            "original_filename": file.filename,
            "merchant_name": extracted_data.get("merchant_name"),
            "amount": extracted_data.get("amount"),
            "category": category or extracted_data.get("category"),
            "date_extracted": extracted_data.get("date"),
            "ocr_text": ocr_text,
            "uploaded_at": datetime.now(timezone.utc),
            "shared_count": 0,
            "shared_platforms": []
        }
        
        result = await db.expense_receipts.insert_one(receipt_record)
        receipt_record["id"] = str(result.inserted_id)
        
        return {
            "receipt_id": receipt_record["id"],
            "filename": unique_filename,
            "file_url": f"/uploads/receipts/{unique_filename}",
            "extracted_data": extracted_data,
            "ocr_confidence": "medium",  # Would come from actual OCR service
            "suggestions": {
                "create_transaction": not transaction_id,
                "merchant_detected": bool(extracted_data.get("merchant_name")),
                "amount_detected": bool(extracted_data.get("amount"))
            }
        }
        
    except Exception as e:
        logger.error(f"Receipt upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload receipt")

@api_router.post("/expenses/share-receipt/{receipt_id}")
@limiter.limit("10/minute")
async def share_expense_receipt_endpoint(
    request: Request,
    receipt_id: str,
    platforms: List[str],
    caption: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """Share expense receipt on social platforms"""
    try:
        db = await get_database()
        
        # Get receipt
        receipt = await db.expense_receipts.find_one({"id": receipt_id, "user_id": user_id})
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        # Generate sharing content
        sharing_content = {}
        
        for platform in platforms:
            if platform == "instagram":
                content = {
                    "text": f"💰 Smart expense tracking with EarnAura!\n{caption or 'Keeping track of every expense helps reach my financial goals faster!'}\n\n#ExpenseTracking #FinancialGoals #EarnAura #SmartMoney",
                    "image_url": f"/uploads/receipts/{receipt['filename']}",
                    "instructions": "Share on Instagram Stories with expense tracking motivation"
                }
            elif platform == "twitter":
                content = {
                    "text": f"📊 Tracking expenses = reaching goals faster! {caption or ''} #ExpenseTracking #FinancialGoals #EarnAura",
                    "image_url": f"/uploads/receipts/{receipt['filename']}",
                    "instructions": "Tweet about smart expense tracking"
                }
            elif platform == "linkedin":
                content = {
                    "text": f"💼 Financial discipline in action! Tracking every expense helps build better money habits and reach professional goals faster.\n\n{caption or ''}\n\n#FinancialLiteracy #PersonalFinance #ProfessionalDevelopment #MoneyManagement",
                    "image_url": f"/uploads/receipts/{receipt['filename']}",
                    "instructions": "Share on LinkedIn as a professional finance tip"
                }
            else:
                content = {
                    "text": f"💰 Smart expense tracking! {caption or ''}",
                    "image_url": f"/uploads/receipts/{receipt['filename']}"
                }
            
            sharing_content[platform] = content
        
        # Update sharing statistics
        await db.expense_receipts.update_one(
            {"id": receipt_id},
            {
                "$inc": {"shared_count": len(platforms)},
                "$addToSet": {"shared_platforms": {"$each": platforms}}
            }
        )
        
        # Create sharing records for analytics
        for platform in platforms:
            share_record = {
                "user_id": user_id,
                "platform": platform,
                "achievement_type": "expense_receipt",
                "milestone_text": f"Receipt from {receipt.get('merchant_name', 'expense')}",
                "image_filename": receipt["filename"],
                "amount": receipt.get("amount"),
                "shared_at": datetime.now(timezone.utc),
                "engagement_count": 0,
                "click_count": 0,
                "conversion_count": 0,
                "viral_coefficient": 0.0
            }
            await db.social_shares.insert_one(share_record)
        
        return {
            "success": True,
            "shared_platforms": platforms,
            "sharing_content": sharing_content,
            "receipt_info": {
                "merchant": receipt.get("merchant_name"),
                "amount": receipt.get("amount"),
                "category": receipt.get("category")
            }
        }
        
    except Exception as e:
        logger.error(f"Share receipt error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to share receipt")

@api_router.get("/expenses/receipts")
@limiter.limit("30/minute")
async def get_user_receipts_endpoint(
    request: Request,
    limit: int = 20,
    user_id: str = Depends(get_current_user)
):
    """Get user's uploaded receipts"""
    try:
        db = await get_database()
        
        receipts = await db.expense_receipts.find(
            {"user_id": user_id}
        ).sort("uploaded_at", -1).limit(limit).to_list(None)
        
        # Format response
        formatted_receipts = []
        for receipt in receipts:
            formatted_receipts.append({
                "id": receipt.get("id"),
                "filename": receipt["filename"],
                "original_filename": receipt["original_filename"],
                "file_url": f"/uploads/receipts/{receipt['filename']}",
                "merchant_name": receipt.get("merchant_name"),
                "amount": receipt.get("amount"),
                "category": receipt.get("category"),
                "uploaded_at": receipt["uploaded_at"],
                "shared_count": receipt.get("shared_count", 0),
                "shared_platforms": receipt.get("shared_platforms", []),
                "has_transaction": bool(receipt.get("transaction_id"))
            })
        
        return {
            "receipts": formatted_receipts,
            "total_count": len(formatted_receipts)
        }
        
    except Exception as e:
        logger.error(f"Get receipts error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get receipts")

# Helper functions for receipt processing
async def process_receipt_ocr(file_path: str) -> str:
    """Basic OCR processing - in production use proper OCR service"""
    try:
        # This is a placeholder - in production you'd use:
        # - AWS Textract
        # - Google Cloud Vision API  
        # - Azure Computer Vision
        # - Tesseract OCR
        
        # Simulate OCR results based on common receipt patterns
        import random
        
        sample_merchants = ["Starbucks", "McDonald's", "Walmart", "Target", "Amazon", "Uber", "Gas Station"]
        sample_amounts = [15.67, 25.99, 45.32, 12.50, 89.95, 33.45, 67.89]
        
        return f"Receipt from {random.choice(sample_merchants)} - Amount: ${random.choice(sample_amounts):.2f} - Date: {datetime.now().strftime('%Y-%m-%d')}"
        
    except Exception as e:
        logger.error(f"OCR processing error: {str(e)}")
        return "Receipt text could not be processed"

def extract_receipt_data(ocr_text: str) -> Dict[str, Any]:
    """Extract structured data from OCR text"""
    import re
    
    extracted = {}
    
    # Extract merchant name (simple pattern matching)
    merchant_patterns = [
        r'Receipt from\s+([A-Za-z\s]+)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ]
    
    for pattern in merchant_patterns:
        match = re.search(pattern, ocr_text)
        if match:
            extracted["merchant_name"] = match.group(1).strip()
            break
    
    # Extract amount
    amount_pattern = r'\$?(\d+\.?\d{0,2})'
    amount_match = re.search(amount_pattern, ocr_text)
    if amount_match:
        try:
            extracted["amount"] = float(amount_match.group(1))
        except ValueError:
            pass
    
    # Extract date
    date_pattern = r'(\d{4}-\d{2}-\d{2})'
    date_match = re.search(date_pattern, ocr_text)
    if date_match:
        try:
            extracted["date"] = datetime.strptime(date_match.group(1), '%Y-%m-%d')
        except ValueError:
            pass
    
    # Guess category based on merchant
    merchant = extracted.get("merchant_name", "").lower()
    if any(food in merchant for food in ["starbucks", "mcdonald", "restaurant", "cafe"]):
        extracted["category"] = "Food"
    elif any(shop in merchant for shop in ["walmart", "target", "amazon"]):
        extracted["category"] = "Shopping"
    elif "gas" in merchant or "fuel" in merchant:
        extracted["category"] = "Transportation"
    else:
        extracted["category"] = "Other"
    
    return extracted

# ===== CAMPUS AMBASSADOR PROGRAM =====

@api_router.post("/campus/ambassador/apply")
@limiter.limit("3/day")  # Limited applications per day
async def apply_campus_ambassador_endpoint(
    request: Request,
    application_data: Dict[str, Any],
    user_id: str = Depends(get_current_user)
):
    """Apply to become a campus ambassador"""
    try:
        db = await get_database()
        
        # Get user info
        user = await get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user is a student with university
        if user.get("role") != "Student" or not user.get("university"):
            raise HTTPException(status_code=400, detail="Only students with university information can apply")
        
        # Check if already applied or is ambassador
        existing_ambassador = await db.campus_ambassadors.find_one({"user_id": user_id})
        if existing_ambassador:
            status = existing_ambassador.get("status")
            if status == "active":
                raise HTTPException(status_code=400, detail="You are already a campus ambassador")
            elif status == "pending":
                raise HTTPException(status_code=400, detail="Your application is pending review")
            elif status == "suspended":
                raise HTTPException(status_code=400, detail="You cannot apply at this time")
        
        # Create ambassador application
        ambassador_record = {
            "user_id": user_id,
            "university": user["university"],
            "status": "pending",
            "applied_at": datetime.now(timezone.utc),
            "total_referrals": 0,
            "monthly_referrals": 0,
            "performance_score": 0.0,
            "special_privileges": [],
            "application_data": {
                "motivation": application_data.get("motivation", ""),
                "social_media_experience": application_data.get("social_media_experience", ""),
                "current_followers": application_data.get("current_followers", 0),
                "leadership_experience": application_data.get("leadership_experience", ""),
                "availability_hours": application_data.get("availability_hours", 5)
            }
        }
        
        result = await db.campus_ambassadors.insert_one(ambassador_record)
        ambassador_record["id"] = str(result.inserted_id)
        
        return {
            "success": True,
            "application_id": ambassador_record["id"],
            "status": "pending",
            "message": "Your campus ambassador application has been submitted for review",
            "review_timeline": "Applications are typically reviewed within 3-5 business days",
            "next_steps": [
                "We'll review your application and social media presence",
                "You may be contacted for a brief interview",
                "Successful candidates will receive ambassador training materials"
            ]
        }
        
    except Exception as e:
        logger.error(f"Ambassador application error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit ambassador application")

@api_router.get("/campus/ambassador/dashboard")
@limiter.limit("30/minute")
async def get_ambassador_dashboard_endpoint(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get campus ambassador dashboard"""
    try:
        db = await get_database()
        
        # Check if user is an active ambassador
        ambassador = await db.campus_ambassadors.find_one({"user_id": user_id})
        if not ambassador or ambassador.get("status") != "active":
            raise HTTPException(status_code=403, detail="Access denied. Active ambassador status required.")
        
        # Get ambassador stats
        current_month = datetime.now(timezone.utc).replace(day=1)
        
        # Get referral stats
        referral_program = await db.referral_programs.find_one({"referrer_id": user_id})
        total_referrals = referral_program.get("total_referrals", 0) if referral_program else 0
        
        # Get monthly referrals
        monthly_referrals = await db.referred_users.count_documents({
            "referrer_id": user_id,
            "signed_up_at": {"$gte": current_month}
        })
        
        # Get university ranking
        university_ambassadors = await db.campus_ambassadors.find({
            "university": ambassador["university"],
            "status": "active"
        }).to_list(None)
        
        university_ranking = sorted(
            university_ambassadors, 
            key=lambda x: x.get("performance_score", 0), 
            reverse=True
        )
        
        user_rank = next((i+1 for i, amb in enumerate(university_ranking) if amb["user_id"] == user_id), len(university_ranking))
        
        # Calculate performance score
        performance_score = calculate_ambassador_performance_score(ambassador, total_referrals, monthly_referrals)
        
        # Update performance score in database
        await db.campus_ambassadors.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "performance_score": performance_score,
                    "total_referrals": total_referrals,
                    "monthly_referrals": monthly_referrals
                }
            }
        )
        
        return {
            "ambassador_info": {
                "status": ambassador["status"],
                "university": ambassador["university"],
                "member_since": ambassador.get("approved_at", ambassador["applied_at"]),
                "special_privileges": ambassador.get("special_privileges", [])
            },
            "performance": {
                "score": performance_score,
                "university_rank": user_rank,
                "total_ambassadors": len(university_ranking),
                "monthly_target": 10,  # Monthly referral target
                "monthly_progress": (monthly_referrals / 10) * 100
            },
            "referral_stats": {
                "total_referrals": total_referrals,
                "monthly_referrals": monthly_referrals,
                "conversion_rate": 85.0,  # Placeholder - would calculate from actual data
                "earnings_this_month": monthly_referrals * 50  # ₹50 per referral
            },
            "special_features": {
                "unlimited_invites": "unlimited_invites" in ambassador.get("special_privileges", []),
                "beta_access": "beta_access" in ambassador.get("special_privileges", []),
                "custom_rewards": "custom_rewards" in ambassador.get("special_privileges", []),
                "priority_support": True
            },
            "monthly_leaderboard": [
                {
                    "name": f"Ambassador {i+1}",
                    "referrals": amb.get("monthly_referrals", 0),
                    "score": amb.get("performance_score", 0),
                    "is_you": amb["user_id"] == user_id
                }
                for i, amb in enumerate(university_ranking[:10])
            ]
        }
        
    except Exception as e:
        logger.error(f"Ambassador dashboard error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get ambassador dashboard")

@api_router.get("/campus/ambassador/rewards")
@limiter.limit("20/minute")
async def get_ambassador_rewards_endpoint(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get available ambassador rewards and achievements"""
    try:
        db = await get_database()
        
        # Check ambassador status
        ambassador = await db.campus_ambassadors.find_one({"user_id": user_id})
        if not ambassador or ambassador.get("status") != "active":
            raise HTTPException(status_code=403, detail="Active ambassador status required")
        
        # Define reward tiers
        reward_tiers = [
            {
                "tier": "Bronze Ambassador",
                "requirement": "5 monthly referrals",
                "rewards": ["Unlimited monthly invites", "Ambassador badge"],
                "current_progress": ambassador.get("monthly_referrals", 0),
                "target": 5,
                "unlocked": ambassador.get("monthly_referrals", 0) >= 5
            },
            {
                "tier": "Silver Ambassador", 
                "requirement": "15 monthly referrals",
                "rewards": ["Beta feature access", "Custom referral rewards", "Priority support"],
                "current_progress": ambassador.get("monthly_referrals", 0),
                "target": 15,
                "unlocked": ambassador.get("monthly_referrals", 0) >= 15
            },
            {
                "tier": "Gold Ambassador",
                "requirement": "30 monthly referrals", 
                "rewards": ["Campus event planning", "Direct team contact", "Exclusive merchandise"],
                "current_progress": ambassador.get("monthly_referrals", 0),
                "target": 30,
                "unlocked": ambassador.get("monthly_referrals", 0) >= 30
            }
        ]
        
        # Get achievements
        achievements = []
        if ambassador.get("total_referrals", 0) >= 10:
            achievements.append("First 10 Referrals")
        if ambassador.get("total_referrals", 0) >= 50:
            achievements.append("50 Referral Milestone") 
        if ambassador.get("monthly_referrals", 0) >= 20:
            achievements.append("Monthly Superstar")
        if ambassador.get("performance_score", 0) >= 80:
            achievements.append("High Performance Ambassador")
        
        return {
            "current_tier": get_ambassador_tier(ambassador.get("monthly_referrals", 0)),
            "reward_tiers": reward_tiers,
            "achievements_earned": achievements,
            "special_privileges": ambassador.get("special_privileges", []),
            "next_reward": next((tier for tier in reward_tiers if not tier["unlocked"]), None)
        }
        
    except Exception as e:
        logger.error(f"Ambassador rewards error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get ambassador rewards")

# ===== GROUP EXPENSE SPLITTING =====

@api_router.post("/expenses/group/create")
@limiter.limit("10/minute")
async def create_group_expense_endpoint(
    request: Request,
    expense_data: Dict[str, Any],
    user_id: str = Depends(get_current_user)
):
    """Create a group expense for splitting with friends"""
    try:
        db = await get_database()
        
        # Validate expense data
        required_fields = ["title", "total_amount", "category", "participants"]
        for field in required_fields:
            if field not in expense_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Validate participants are friends
        participant_ids = [p["user_id"] for p in expense_data["participants"]]
        
        # Check friendships
        friendships = await db.friendships.find({
            "$or": [
                {"user1_id": user_id, "user2_id": {"$in": participant_ids}},
                {"user2_id": user_id, "user1_id": {"$in": participant_ids}}
            ]
        }).to_list(None)
        
        friend_ids = set()
        for friendship in friendships:
            if friendship["user1_id"] == user_id:
                friend_ids.add(friendship["user2_id"])
            else:
                friend_ids.add(friendship["user1_id"])
        
        # Ensure all participants are friends
        non_friends = [pid for pid in participant_ids if pid not in friend_ids and pid != user_id]
        if non_friends:
            raise HTTPException(status_code=400, detail="Some participants are not in your friend network")
        
        # Create group expense
        group_expense = {
            "creator_id": user_id,
            "title": expense_data["title"],
            "description": expense_data.get("description"),
            "total_amount": float(expense_data["total_amount"]),
            "category": expense_data["category"],
            "receipt_filename": expense_data.get("receipt_filename"),
            "participants": expense_data["participants"],
            "created_at": datetime.now(timezone.utc),
            "settled": False,
            "settlement_method": expense_data.get("settlement_method", "equal")
        }
        
        result = await db.group_expenses.insert_one(group_expense)
        group_expense["id"] = str(result.inserted_id)
        
        # Create settlement records for each participant
        settlements = []
        for participant in expense_data["participants"]:
            if participant["user_id"] != user_id:  # Creator doesn't owe themselves
                settlement = {
                    "group_expense_id": group_expense["id"],
                    "payer_id": user_id,  # Creator paid initially
                    "payee_id": participant["user_id"],
                    "amount": float(participant["amount"]),
                    "status": "pending",
                    "payment_method": None
                }
                
                settlement_result = await db.expense_settlements.insert_one(settlement)
                settlement["id"] = str(settlement_result.inserted_id)
                settlements.append(settlement)
        
        # Send notifications to participants
        for participant in expense_data["participants"]:
            if participant["user_id"] != user_id:
                notification = {
                    "user_id": participant["user_id"],
                    "type": "group_expense_created",
                    "title": "New Group Expense",
                    "message": f"{await get_user_name(user_id)} added you to a group expense: {expense_data['title']}",
                    "action_url": f"/expenses/group/{group_expense['id']}",
                    "related_id": group_expense["id"],
                    "created_at": datetime.now(timezone.utc),
                    "read": False
                }
                await db.notifications.insert_one(notification)
        
        return {
            "group_expense": group_expense,
            "settlements": settlements,
            "participants_notified": len(participant_ids) - 1,
            "message": f"Group expense '{expense_data['title']}' created successfully"
        }
        
    except Exception as e:
        logger.error(f"Create group expense error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create group expense")

@api_router.get("/expenses/group")
@limiter.limit("30/minute") 
async def get_user_group_expenses_endpoint(
    request: Request,
    limit: int = 20,
    user_id: str = Depends(get_current_user)
):
    """Get user's group expenses"""
    try:
        db = await get_database()
        
        # Get group expenses where user is creator or participant
        group_expenses = await db.group_expenses.find({
            "$or": [
                {"creator_id": user_id},
                {"participants.user_id": user_id}
            ]
        }).sort("created_at", -1).limit(limit).to_list(None)
        
        formatted_expenses = []
        for expense in group_expenses:
            # Get settlements for this expense
            settlements = await db.expense_settlements.find({
                "group_expense_id": expense.get("id", str(expense["_id"]))
            }).to_list(None)
            
            # Calculate user's involvement
            user_settlement = next((s for s in settlements if s["payee_id"] == user_id or s["payer_id"] == user_id), None)
            
            formatted_expense = {
                "id": expense.get("id", str(expense["_id"])),
                "title": expense["title"],
                "description": expense.get("description"),
                "total_amount": expense["total_amount"],
                "category": expense["category"],
                "created_at": expense["created_at"],
                "settled": expense["settled"],
                "is_creator": expense["creator_id"] == user_id,
                "participant_count": len(expense["participants"]),
                "user_amount": user_settlement["amount"] if user_settlement else 0.0,
                "user_status": user_settlement["status"] if user_settlement else "settled",
                "receipt_available": bool(expense.get("receipt_filename"))
            }
            
            formatted_expenses.append(formatted_expense)
        
        return {
            "group_expenses": formatted_expenses,
            "total_count": len(formatted_expenses)
        }
        
    except Exception as e:
        logger.error(f"Get group expenses error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get group expenses")

# Helper functions
def calculate_ambassador_performance_score(ambassador: Dict, total_referrals: int, monthly_referrals: int) -> float:
    """Calculate ambassador performance score based on various factors"""
    base_score = 0.0
    
    # Monthly referrals (40% weight)
    monthly_score = min(monthly_referrals / 20 * 40, 40)  # Max 40 points for 20+ referrals
    
    # Total referrals (30% weight)
    total_score = min(total_referrals / 100 * 30, 30)  # Max 30 points for 100+ referrals
    
    # Consistency (20% weight) - placeholder
    consistency_score = 15 if monthly_referrals > 0 else 0
    
    # Special achievements (10% weight)
    achievement_score = len(ambassador.get("special_privileges", [])) * 2.5
    
    return min(base_score + monthly_score + total_score + consistency_score + achievement_score, 100)

def get_ambassador_tier(monthly_referrals: int) -> str:
    """Get ambassador tier based on monthly referrals"""
    if monthly_referrals >= 30:
        return "Gold Ambassador"
    elif monthly_referrals >= 15:
        return "Silver Ambassador"
    elif monthly_referrals >= 5:
        return "Bronze Ambassador"
    else:
        return "New Ambassador"

async def get_user_name(user_id: str) -> str:
    """Get user name for notifications"""
    user = await get_user_by_id(user_id)
    return user.get("full_name", "Someone") if user else "Someone"

# ===== GROWTH MECHANICS =====

@api_router.get("/growth/invite-quota")
@limiter.limit("30/minute")
async def get_invite_quota_endpoint(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get user's invite quota and usage statistics"""
    try:
        db = await get_database()
        
        # Get current invite quota
        quota = await db.invite_quotas.find_one({"user_id": user_id})
        
        if not quota:
            # Create initial quota (5 invites per month)
            current_month = datetime.now(timezone.utc).replace(day=1)
            next_reset = current_month.replace(month=current_month.month % 12 + 1)
            
            quota = {
                "user_id": user_id,
                "monthly_limit": 5,
                "used_this_month": 0,
                "bonus_invites": 0,
                "reset_date": next_reset,
                "total_earned": 0
            }
            
            await db.invite_quotas.insert_one(quota)
        
        # Check if reset is needed
        if datetime.now(timezone.utc) >= quota["reset_date"]:
            # Reset monthly usage
            current_month = datetime.now(timezone.utc).replace(day=1)
            next_reset = current_month.replace(month=current_month.month % 12 + 1)
            
            await db.invite_quotas.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "used_this_month": 0,
                        "reset_date": next_reset
                    }
                }
            )
            quota["used_this_month"] = 0
            quota["reset_date"] = next_reset
        
        # Calculate available invites
        total_available = quota["monthly_limit"] + quota["bonus_invites"]
        remaining = max(0, total_available - quota["used_this_month"])
        
        # Get ways to earn more invites
        earning_opportunities = [
            {
                "action": "Refer 3 friends",
                "reward": "2 bonus invites",
                "progress": min(quota.get("successful_referrals", 0) // 3, 5),
                "max_progress": 5
            },
            {
                "action": "Complete 10 transactions",
                "reward": "1 bonus invite", 
                "progress": 0,  # Would calculate from actual transactions
                "max_progress": 10
            },
            {
                "action": "Maintain 7-day streak",
                "reward": "2 bonus invites",
                "progress": 0,  # Would calculate from user streak
                "max_progress": 7
            },
            {
                "action": "Join 2 group challenges",
                "reward": "3 bonus invites",
                "progress": 0,  # Would calculate from challenges
                "max_progress": 2
            }
        ]
        
        return {
            "quota_info": {
                "monthly_limit": quota["monthly_limit"],
                "bonus_invites": quota["bonus_invites"],
                "total_available": total_available,
                "used_this_month": quota["used_this_month"],
                "remaining": remaining,
                "reset_date": quota["reset_date"],
                "total_earned": quota["total_earned"]
            },
            "usage_status": {
                "can_invite": remaining > 0,
                "usage_percentage": (quota["used_this_month"] / total_available * 100) if total_available > 0 else 0,
                "urgency_level": "high" if remaining <= 1 else "medium" if remaining <= 3 else "low"
            },
            "earning_opportunities": earning_opportunities,
            "special_status": {
                "is_campus_ambassador": False,  # Would check from ambassador table
                "has_unlimited": False  # Would check special privileges
            }
        }
        
    except Exception as e:
        logger.error(f"Get invite quota error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get invite quota")

@api_router.post("/growth/earn-bonus-invites")
@limiter.limit("5/minute")
async def earn_bonus_invites_endpoint(
    request: Request,
    achievement_type: str,
    user_id: str = Depends(get_current_user)
):
    """Award bonus invites for achievements"""
    try:
        db = await get_database()
        
        # Define bonus invite awards
        bonus_awards = {
            "first_referral": 1,
            "three_referrals": 2,
            "five_referrals": 3,
            "seven_day_streak": 2,
            "first_transaction": 1,
            "ten_transactions": 1,
            "group_challenge_join": 1,
            "goal_completion": 2,
            "budget_success": 1
        }
        
        bonus_amount = bonus_awards.get(achievement_type, 0)
        if bonus_amount == 0:
            raise HTTPException(status_code=400, detail="Invalid achievement type")
        
        # Check if already earned this bonus (prevent duplicates)
        existing_bonus = await db.earned_invite_bonuses.find_one({
            "user_id": user_id,
            "achievement_type": achievement_type
        })
        
        if existing_bonus:
            raise HTTPException(status_code=400, detail="Bonus already earned for this achievement")
        
        # Award bonus invites
        await db.invite_quotas.update_one(
            {"user_id": user_id},
            {
                "$inc": {
                    "bonus_invites": bonus_amount,
                    "total_earned": bonus_amount
                }
            },
            upsert=True
        )
        
        # Record the bonus earning
        bonus_record = {
            "user_id": user_id,
            "achievement_type": achievement_type,
            "bonus_amount": bonus_amount,
            "earned_at": datetime.now(timezone.utc)
        }
        
        await db.earned_invite_bonuses.insert_one(bonus_record)
        
        # Create notification
        notification = {
            "user_id": user_id,
            "type": "bonus_invites_earned",
            "title": "Bonus Invites Earned!",
            "message": f"You earned {bonus_amount} bonus invite{'s' if bonus_amount > 1 else ''} for {achievement_type.replace('_', ' ')}!",
            "action_url": "/growth/invite-quota",
            "created_at": datetime.now(timezone.utc),
            "read": False
        }
        await db.notifications.insert_one(notification)
        
        return {
            "success": True,
            "bonus_earned": bonus_amount,
            "achievement": achievement_type,
            "message": f"Congratulations! You earned {bonus_amount} bonus invite{'s' if bonus_amount > 1 else ''}!"
        }
        
    except Exception as e:
        logger.error(f"Earn bonus invites error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to earn bonus invites")

@api_router.post("/growth/waitlist/join")
@limiter.limit("10/day")  # Limited to prevent spam
async def join_feature_waitlist_endpoint(
    request: Request,
    feature_name: str,
    user_id: str = Depends(get_current_user)
):
    """Join waitlist for exclusive features"""
    try:
        db = await get_database()
        
        # Available exclusive features
        exclusive_features = {
            "ai_financial_advisor": {
                "name": "AI Financial Advisor",
                "description": "Personal AI coach for financial decisions",
                "capacity": 100
            },
            "premium_analytics": {
                "name": "Premium Analytics Dashboard", 
                "description": "Advanced spending insights and predictions",
                "capacity": 200
            },
            "investment_tracker": {
                "name": "Investment Portfolio Tracker",
                "description": "Track stocks, mutual funds, and crypto",
                "capacity": 150
            },
            "group_goals": {
                "name": "Collaborative Financial Goals",
                "description": "Set and achieve goals with friends",
                "capacity": 300
            },
            "merchant_partnerships": {
                "name": "Exclusive Merchant Discounts",
                "description": "Special discounts at partner stores",
                "capacity": 500
            }
        }
        
        if feature_name not in exclusive_features:
            raise HTTPException(status_code=400, detail="Invalid feature name")
        
        # Check if already on waitlist
        existing_entry = await db.feature_waitlists.find_one({
            "user_id": user_id,
            "feature_name": feature_name
        })
        
        if existing_entry:
            if existing_entry.get("granted_access"):
                raise HTTPException(status_code=400, detail="You already have access to this feature")
            else:
                raise HTTPException(status_code=400, detail="You're already on the waitlist for this feature")
        
        # Calculate priority score based on user activity
        user = await get_user_by_id(user_id)
        priority_score = await calculate_waitlist_priority_score(user_id, user)
        
        # Count current waitlist position
        current_waitlist_size = await db.feature_waitlists.count_documents({
            "feature_name": feature_name,
            "granted_access": False
        })
        
        # Create waitlist entry
        waitlist_entry = {
            "user_id": user_id,
            "feature_name": feature_name,
            "priority_score": priority_score,
            "joined_at": datetime.now(timezone.utc),
            "granted_access": False,
            "position": current_waitlist_size + 1
        }
        
        await db.feature_waitlists.insert_one(waitlist_entry)
        
        # Check if immediate access should be granted (high priority users)
        feature_info = exclusive_features[feature_name]
        if priority_score >= 80 and current_waitlist_size < feature_info["capacity"] * 0.1:  # Top 10% get immediate access
            await grant_feature_access(user_id, feature_name)
            waitlist_entry["granted_access"] = True
            waitlist_entry["position"] = 0
        
        return {
            "success": True,
            "feature": feature_info,
            "waitlist_position": waitlist_entry["position"],
            "priority_score": priority_score,
            "immediate_access": waitlist_entry["granted_access"],
            "estimated_wait": calculate_estimated_wait_time(waitlist_entry["position"], feature_info["capacity"]),
            "boost_tips": [
                "Refer more friends to increase priority",
                "Maintain daily transaction streak",
                "Complete financial goals",
                "Become a campus ambassador"
            ]
        }
        
    except Exception as e:
        logger.error(f"Join waitlist error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to join feature waitlist")

@api_router.get("/growth/beta-access")
@limiter.limit("20/minute")
async def get_beta_feature_access_endpoint(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get user's beta feature access status"""
    try:
        db = await get_database()
        
        # Get user info for criteria checking
        user = await get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check various criteria for beta access
        criteria_met = []
        
        # 1. Top saver (top 10% by net savings)
        if user.get("net_savings", 0) >= 10000:  # ₹10,000+ savings
            criteria_met.append("top_saver")
        
        # 2. High referrals (10+ successful referrals)
        referral_program = await db.referral_programs.find_one({"referrer_id": user_id})
        if referral_program and referral_program.get("successful_referrals", 0) >= 10:
            criteria_met.append("high_referrals")
        
        # 3. Campus ambassador
        ambassador = await db.campus_ambassadors.find_one({"user_id": user_id, "status": "active"})
        if ambassador:
            criteria_met.append("campus_ambassador")
        
        # 4. Long streak (30+ days)
        if user.get("current_streak", 0) >= 30:
            criteria_met.append("long_streak")
        
        # 5. High engagement (100+ transactions)
        transaction_count = await db.transactions.count_documents({"user_id": user_id})
        if transaction_count >= 100:
            criteria_met.append("high_engagement")
        
        # 6. Goal achiever (completed 3+ goals)
        completed_goals = await db.financial_goals.count_documents({
            "user_id": user_id,
            "current_amount": {"$gte": "$target_amount"}  # This would need proper aggregation in real implementation
        })
        if completed_goals >= 3:
            criteria_met.append("goal_achiever")
        
        # Get current beta features
        beta_features = await db.beta_feature_accesses.find({"user_id": user_id}).to_list(None)
        
        # Available beta features
        available_features = {
            "ai_insights_v2": {
                "name": "AI Insights v2.0",
                "description": "Advanced AI-powered financial predictions",
                "required_criteria": ["top_saver", "high_engagement"],
                "expires_in_days": 30
            },
            "social_investing": {
                "name": "Social Investment Feed",
                "description": "See and follow friends' investment strategies",
                "required_criteria": ["high_referrals", "campus_ambassador"],
                "expires_in_days": 45
            },
            "premium_budgeting": {
                "name": "Smart Budget Automation",
                "description": "AI-powered automatic budget adjustments",
                "required_criteria": ["goal_achiever", "long_streak"],
                "expires_in_days": 60
            },
            "exclusive_challenges": {
                "name": "VIP Challenge Access",
                "description": "Access to exclusive high-reward challenges",
                "required_criteria": ["campus_ambassador"],
                "expires_in_days": 90
            }
        }
        
        # Check eligibility for each feature
        eligible_features = []
        for feature_id, feature_info in available_features.items():
            has_required_criteria = all(
                criterion in criteria_met 
                for criterion in feature_info["required_criteria"]
            )
            
            current_access = next((bf for bf in beta_features if bf["feature_name"] == feature_id), None)
            
            eligible_features.append({
                "feature_id": feature_id,
                "feature_info": feature_info,
                "eligible": has_required_criteria,
                "has_access": bool(current_access),
                "expires_at": current_access.get("expires_at") if current_access else None,
                "missing_criteria": [
                    criterion for criterion in feature_info["required_criteria"]
                    if criterion not in criteria_met
                ]
            })
        
        return {
            "criteria_met": criteria_met,
            "total_criteria": len(criteria_met),
            "beta_features": eligible_features,
            "current_access_count": len(beta_features),
            "qualification_tips": {
                "top_saver": "Save ₹10,000+ to qualify",
                "high_referrals": "Refer 10+ successful friends", 
                "campus_ambassador": "Apply to become campus ambassador",
                "long_streak": "Maintain 30+ day transaction streak",
                "high_engagement": "Complete 100+ transactions",
                "goal_achiever": "Complete 3+ financial goals"
            }
        }
        
    except Exception as e:
        logger.error(f"Get beta access error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get beta feature access")

@api_router.post("/growth/beta-access/request/{feature_id}")
@limiter.limit("5/minute")
async def request_beta_feature_access_endpoint(
    request: Request,
    feature_id: str,
    user_id: str = Depends(get_current_user)
):
    """Request access to a specific beta feature"""
    try:
        db = await get_database()
        
        # Check if user meets criteria (reuse logic from get_beta_feature_access_endpoint)
        beta_access_info = await get_beta_feature_access_endpoint(request, user_id)
        
        # Find the requested feature
        requested_feature = next(
            (f for f in beta_access_info["beta_features"] if f["feature_id"] == feature_id),
            None
        )
        
        if not requested_feature:
            raise HTTPException(status_code=404, detail="Feature not found")
        
        if requested_feature["has_access"]:
            raise HTTPException(status_code=400, detail="You already have access to this feature")
        
        if not requested_feature["eligible"]:
            missing = ", ".join(requested_feature["missing_criteria"])
            raise HTTPException(status_code=400, detail=f"Missing required criteria: {missing}")
        
        # Grant beta access
        expiry_date = datetime.now(timezone.utc) + timedelta(days=requested_feature["feature_info"]["expires_in_days"])
        
        beta_access = {
            "user_id": user_id,
            "feature_name": feature_id,
            "access_criteria_met": beta_access_info["criteria_met"],
            "granted_at": datetime.now(timezone.utc),
            "expires_at": expiry_date,
            "usage_count": 0
        }
        
        await db.beta_feature_accesses.insert_one(beta_access)
        
        # Create notification
        notification = {
            "user_id": user_id,
            "type": "beta_access_granted",
            "title": "Beta Access Granted!",
            "message": f"You now have access to {requested_feature['feature_info']['name']}!",
            "action_url": f"/beta/{feature_id}",
            "created_at": datetime.now(timezone.utc),
            "read": False
        }
        await db.notifications.insert_one(notification)
        
        return {
            "success": True,
            "feature": requested_feature["feature_info"],
            "access_granted": True,
            "expires_at": expiry_date,
            "message": f"Congratulations! You now have beta access to {requested_feature['feature_info']['name']}"
        }
        
    except Exception as e:
        logger.error(f"Request beta access error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to request beta feature access")

# ===== INTER-COLLEGE COMPETITION SYSTEM =====

@api_router.post("/inter-college/competitions")
@limiter.limit("3/day")  # Limited to prevent spam
async def create_inter_college_competition(
    request: Request,
    competition_data: InterCollegeCompetitionCreate,
    current_admin: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Create a new inter-college competition (Super Admin ONLY)"""
    try:
        db = await get_database()
        
        current_user = current_admin["user_id"]
        
        # Super admin only - no permission checks needed
        
        # Calculate duration
        duration_days = (competition_data.end_date - competition_data.start_date).days
        
        # Create competition
        competition_dict = competition_data.dict()
        competition_dict.update({
            "id": str(uuid.uuid4()),
            "duration_days": duration_days,
            "created_by": current_user,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })
        
        # Add admin metadata
        # Check if user is super admin
        user_obj = await get_user_by_id(current_user)
        is_system_admin = user_obj.get("is_super_admin", False)
        
        if is_system_admin:
            competition_dict.update({
                "created_by_system_admin": True,
                "created_by_campus_admin": False,
                "created_by_club_admin": False
            })
        else:
            competition_dict.update({
                "created_by_system_admin": False,
                "created_by_campus_admin": current_admin.get("admin_type") == "campus_admin",
                "created_by_club_admin": current_admin.get("admin_type") == "club_admin",
                "admin_id": current_admin.get("id"),
                "creator_college": current_admin.get("college_name"),
                "creator_admin_type": current_admin.get("admin_type")
            })
        
        competition = InterCollegeCompetition(**competition_dict)
        await db.inter_college_competitions.insert_one(competition.dict())
        
        # Update admin statistics if applicable (campus admin or club admin)
        if not is_system_admin:
            await db.campus_admins.update_one(
                {"id": current_admin["id"]},
                {
                    "$inc": {"competitions_created": 1},
                    "$set": {"last_activity": datetime.now(timezone.utc)}
                }
            )
        
        # Initialize campus leaderboards for eligible universities
        eligible_unis = competition_data.eligible_universities if competition_data.eligible_universities else []
        if not eligible_unis:
            # Get all universities if no specific list provided
            all_users = await db.users.distinct("university")
            eligible_unis = [uni for uni in all_users if uni]
        
        for university in eligible_unis:
            leaderboard = CampusLeaderboard(
                competition_id=competition.id,
                campus=university
            )
            await db.campus_leaderboards.insert_one(leaderboard.dict())
        
        # Create audit log
        creator_type = "system_admin" if is_system_admin else current_admin.get("admin_type", "campus_admin")
        audit_log = await admin_workflow_manager.create_audit_log(
            admin_user_id=current_user,
            action_type="create_inter_college_competition",
            action_description=f"Created inter-college competition: {competition_data.title}",
            target_type="competition",
            target_id=competition.id,
            affected_entities=[{"type": "competition", "id": competition.id, "name": competition_data.title}],
            severity="info",
            ip_address=request.client.host,
            is_system_generated=False
        )
        await db.admin_audit_logs.insert_one(audit_log)
        
        return {
            "success": True,
            "message": "Inter-college competition created successfully",
            "competition_id": competition.id,
            "creator_type": creator_type,
            "eligible_universities": eligible_unis,
            "registration_period": {
                "start": competition_data.registration_start,
                "end": competition_data.registration_end
            }
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Create inter-college competition error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create competition: {str(e)}")

@api_router.get("/inter-college/competitions")
@limiter.limit("20/minute")
async def get_inter_college_competitions(
    request: Request,
    status: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Get all inter-college competitions"""
    try:
        db = await get_database()
        
        # Build filter
        filter_query = {}
        if status:
            filter_query["status"] = status
        
        competitions = await db.inter_college_competitions.find(filter_query).sort("created_at", -1).to_list(None)
        
        # Enhance with user's participation status
        user_id = current_user.get("id")
        user_university = current_user.get("university")
        
        enhanced_competitions = []
        for competition in competitions:
            # Check if user's university is eligible
            eligible_unis = competition.get("eligible_universities", [])
            is_eligible = not eligible_unis or user_university in eligible_unis
            
            # Check if user is registered
            user_participation = await db.campus_competition_participations.find_one({
                "competition_id": competition["id"],
                "user_id": user_id
            })
            
            # Get campus leaderboard stats
            campus_stats = await db.campus_leaderboards.find_one({
                "competition_id": competition["id"],
                "campus": user_university
            }) if user_university else None
            
            # Calculate registration status
            now = datetime.now(timezone.utc)
            registration_start = competition.get("registration_start")
            registration_end = competition.get("registration_end")
            
            # Ensure timezone-aware datetime comparison
            if isinstance(registration_start, str):
                registration_start = datetime.fromisoformat(registration_start.replace('Z', '+00:00'))
            elif registration_start and registration_start.tzinfo is None:
                registration_start = registration_start.replace(tzinfo=timezone.utc)
                
            if isinstance(registration_end, str):
                registration_end = datetime.fromisoformat(registration_end.replace('Z', '+00:00'))
            elif registration_end and registration_end.tzinfo is None:
                registration_end = registration_end.replace(tzinfo=timezone.utc)
            
            # Check if registration is currently open
            registration_open = True
            if registration_start and registration_end:
                registration_open = registration_start <= now <= registration_end
            elif competition.get("status") in ["completed", "cancelled"]:
                registration_open = False

            enhanced_competition = {
                **competition,
                "is_eligible": is_eligible,
                "is_registered": bool(user_participation),
                "user_campus": user_university,
                "campus_rank": campus_stats.get("campus_rank", 0) if campus_stats else 0,
                "campus_participants": campus_stats.get("total_participants", 0) if campus_stats else 0,
                "registration_open": registration_open
            }
            enhanced_competitions.append(enhanced_competition)
        
        return {
            "competitions": clean_mongo_doc(enhanced_competitions),
            "user_university": user_university
        }
        
    except Exception as e:
        logger.error(f"Get inter-college competitions error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get competitions")

@api_router.post("/inter-college/competitions/{competition_id}/register")
@limiter.limit("10/minute")
async def register_for_inter_college_competition(
    request: Request,
    competition_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Register for an inter-college competition"""
    try:
        db = await get_database()
        user = await get_user_by_id(current_user["id"])
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_university = user.get("university")
        if not user_university:
            raise HTTPException(status_code=400, detail="University information required to participate")
        
        # Get competition
        competition = await db.inter_college_competitions.find_one({"id": competition_id})
        if not competition:
            raise HTTPException(status_code=404, detail="Competition not found")
        
        # Check if registration is open
        now = datetime.now(timezone.utc)
        reg_start = competition.get("registration_start")
        reg_end = competition.get("registration_end")
        
        # Convert to timezone-aware datetime if needed
        if reg_start:
            if isinstance(reg_start, str):
                reg_start = datetime.fromisoformat(reg_start.replace('Z', '+00:00'))
            elif not reg_start.tzinfo:
                reg_start = reg_start.replace(tzinfo=timezone.utc)
        
        if reg_end:
            if isinstance(reg_end, str):
                reg_end = datetime.fromisoformat(reg_end.replace('Z', '+00:00'))
            elif not reg_end.tzinfo:
                reg_end = reg_end.replace(tzinfo=timezone.utc)
        
        if reg_start and now < reg_start:
            raise HTTPException(status_code=400, detail="Registration has not started yet")
        if reg_end and now > reg_end:
            raise HTTPException(status_code=400, detail="Registration period has ended")
        
        # Check eligibility
        eligible_unis = competition.get("eligible_universities", [])
        if eligible_unis and user_university not in eligible_unis:
            raise HTTPException(status_code=400, detail="Your university is not eligible for this competition")
        
        # Check user level requirement
        min_level = competition.get("min_user_level", 1)
        user_level = user.get("level", 1)
        if user_level < min_level:
            raise HTTPException(status_code=400, detail=f"Minimum level {min_level} required")
        
        # Check if already registered
        existing_participation = await db.campus_competition_participations.find_one({
            "competition_id": competition_id,
            "user_id": current_user["id"]
        })
        
        if existing_participation:
            raise HTTPException(status_code=400, detail="Already registered for this competition")
        
        # Check campus participant limits
        campus_participants = await db.campus_competition_participations.count_documents({
            "competition_id": competition_id,
            "campus": user_university
        })
        
        max_per_campus = competition.get("max_participants_per_campus", 100)
        if campus_participants >= max_per_campus:
            raise HTTPException(status_code=400, detail=f"Campus has reached maximum participants ({max_per_campus})")
        
        min_per_campus = competition.get("min_participants_per_campus", 10)
        
        # Create participation record
        participation = CampusCompetitionParticipation(
            competition_id=competition_id,
            user_id=current_user["id"],
            campus=user_university
        )
        
        await db.campus_competition_participations.insert_one(participation.dict())
        
        # Update campus leaderboard
        await db.campus_leaderboards.update_one(
            {"competition_id": competition_id, "campus": user_university},
            {
                "$inc": {"total_participants": 1, "active_participants": 1},
                "$set": {"last_updated": datetime.now(timezone.utc)}
            },
            upsert=True
        )
        
        # Check if campus now meets minimum requirements
        new_campus_count = campus_participants + 1
        campus_qualified = new_campus_count >= min_per_campus
        
        # Award registration points
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$inc": {"experience_points": 25}}  # Registration bonus
        )
        
        # Update user leaderboards after registration
        try:
            from gamification_service import update_user_leaderboards
            await update_user_leaderboards(db, current_user["id"])
            logger.info(f"✅ Updated leaderboards for user {current_user['id']} after inter-college registration")
        except Exception as e:
            logger.error(f"Failed to update leaderboards after inter-college registration: {str(e)}")
        
        return {
            "message": "Successfully registered for inter-college competition",
            "competition_id": competition_id,
            "campus": user_university,
            "campus_participants": new_campus_count,
            "campus_qualified": campus_qualified,
            "min_required": min_per_campus,
            "points_earned": 25
        }
        
    except Exception as e:
        logger.error(f"Register for competition error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to register for competition")

@api_router.post("/inter-college/competitions/{competition_id}/team-register")
@limiter.limit("10/minute")
async def register_team_for_inter_college_competition(
    request: Request,
    competition_id: str,
    team_data: dict,
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Register a team for inter-college competition"""
    try:
        db = await get_database()
        user_id = current_user["id"]
        user = current_user
        
        # Extract team information
        team_name = team_data.get("team_name", "").strip()
        team_members = team_data.get("team_members", [])  # List of member details
        registration_type = team_data.get("registration_type", "team_leader")  # "team_leader" or "join_team"
        
        if not team_name:
            raise HTTPException(status_code=400, detail="Team name is required")
        
        user_university = user.get("university")
        if not user_university:
            raise HTTPException(status_code=400, detail="University information required to participate")
        
        # Get competition
        competition = await db.inter_college_competitions.find_one({"id": competition_id})
        if not competition:
            raise HTTPException(status_code=404, detail="Competition not found")
        
        # Check if registration is open
        now = datetime.now(timezone.utc)
        reg_start = competition.get("registration_start")
        reg_end = competition.get("registration_end")
        
        # Convert to timezone-aware datetime if needed
        if reg_start:
            if isinstance(reg_start, str):
                reg_start = datetime.fromisoformat(reg_start.replace('Z', '+00:00'))
            elif not reg_start.tzinfo:
                reg_start = reg_start.replace(tzinfo=timezone.utc)
        
        if reg_end:
            if isinstance(reg_end, str):
                reg_end = datetime.fromisoformat(reg_end.replace('Z', '+00:00'))
            elif not reg_end.tzinfo:
                reg_end = reg_end.replace(tzinfo=timezone.utc)
        
        if reg_start and now < reg_start:
            raise HTTPException(status_code=400, detail="Registration has not started yet")
        if reg_end and now > reg_end:
            raise HTTPException(status_code=400, detail="Registration period has ended")
        
        # Check eligibility
        eligible_unis = competition.get("eligible_universities", [])
        if eligible_unis and user_university not in eligible_unis:
            raise HTTPException(status_code=400, detail="Your university is not eligible for this competition")
        
        # Check if already registered
        existing_participation = await db.campus_competition_participations.find_one({
            "competition_id": competition_id,
            "user_id": user_id
        })
        
        if existing_participation:
            raise HTTPException(status_code=400, detail="Already registered for this competition")
        
        team_id = None
        
        if registration_type == "team_leader":
            # User is creating a new team and registering as team leader
            team_id = str(uuid.uuid4())
            
            # Validate team members
            if len(team_members) < 1 or len(team_members) > 5:
                raise HTTPException(status_code=400, detail="Team must have 1-5 members (including leader)")
            
            # Check if team name already exists for this competition
            existing_team = await db.competition_teams.find_one({
                "competition_id": competition_id,
                "team_name": team_name,
                "campus": user_university
            })
            
            if existing_team:
                raise HTTPException(status_code=400, detail="Team name already exists for your campus in this competition")
            
            # Create team record
            team_record = {
                "id": team_id,
                "competition_id": competition_id,
                "team_name": team_name,
                "campus": user_university,
                "team_leader_id": user_id,
                "team_members": [
                    {
                        "user_id": user_id,
                        "name": user.get("full_name", "Unknown"),
                        "email": user.get("email", ""),
                        "role": "team_leader",
                        "joined_at": datetime.now(timezone.utc)
                    }
                ],
                "member_details": team_members,  # Additional member info provided by leader
                "created_at": datetime.now(timezone.utc),
                "status": "active"
            }
            
            await db.competition_teams.insert_one(team_record)
            
        elif registration_type == "join_team":
            # User is joining an existing team by team name
            existing_team = await db.competition_teams.find_one({
                "competition_id": competition_id,
                "team_name": team_name,
                "campus": user_university
            })
            
            if not existing_team:
                raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found for your campus in this competition")
            
            team_id = existing_team["id"]
            
            # Check if team is full (max 5 members)
            current_members = len(existing_team.get("team_members", []))
            if current_members >= 5:
                raise HTTPException(status_code=400, detail="Team is full (maximum 5 members)")
            
            # Check if user is already in team
            user_in_team = any(member.get("user_id") == user_id for member in existing_team.get("team_members", []))
            if user_in_team:
                raise HTTPException(status_code=400, detail="You are already a member of this team")
            
            # Add user to team
            new_member = {
                "user_id": user_id,
                "name": user.get("full_name", "Unknown"),
                "email": user.get("email", ""),
                "role": "member",
                "joined_at": datetime.now(timezone.utc)
            }
            
            await db.competition_teams.update_one(
                {"id": team_id},
                {"$push": {"team_members": new_member}}
            )
        
        # Create individual participation record
        participation = {
            "id": str(uuid.uuid4()),
            "competition_id": competition_id,
            "user_id": user_id,
            "campus": user_university,
            "team_id": team_id,
            "team_name": team_name,
            "registration_type": registration_type,
            "individual_score": 0.0,
            "campus_contribution": 0.0,
            "registration_status": "active",
            "registered_at": datetime.now(timezone.utc),
            "last_updated": datetime.now(timezone.utc)
        }
        
        await db.campus_competition_participations.insert_one(participation)
        
        # Update campus leaderboard
        await db.campus_leaderboards.update_one(
            {"competition_id": competition_id, "campus": user_university},
            {
                "$inc": {"total_participants": 1, "active_participants": 1},
                "$set": {"last_updated": datetime.now(timezone.utc)}
            },
            upsert=True
        )
        
        # Award registration points
        await db.users.update_one(
            {"id": user_id},
            {"$inc": {"experience_points": 25}}  # Registration bonus
        )
        
        return {
            "message": f"Successfully registered for inter-college competition as {registration_type.replace('_', ' ')}",
            "competition_id": competition_id,
            "team_id": team_id,
            "team_name": team_name,
            "campus": user_university,
            "registration_type": registration_type,
            "points_earned": 25
        }
        
    except Exception as e:
        logger.error(f"Team register for competition error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to register team for competition")

@api_router.get("/inter-college/competitions/{competition_id}/teams")
@limiter.limit("20/minute")
async def get_competition_teams(
    request: Request,
    competition_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Get all teams for a specific inter-college competition"""
    try:
        db = await get_database()
        user_university = current_user.get("university")
        
        # Get competition
        competition = await db.inter_college_competitions.find_one({"id": competition_id})
        if not competition:
            raise HTTPException(status_code=404, detail="Competition not found")
        
        # Get teams (filter by user's university for privacy)
        teams_query = {
            "competition_id": competition_id,
            "status": "active"
        }
        
        # Only show teams from user's campus
        if user_university:
            teams_query["campus"] = user_university
        
        teams = await db.competition_teams.find(teams_query).sort("created_at", -1).to_list(None)
        
        # Enhance with member count and status
        enhanced_teams = []
        for team in teams:
            member_count = len(team.get("team_members", []))
            
            # Check if current user can join
            user_can_join = (
                member_count < 5 and  # Team not full
                not any(member.get("user_id") == current_user["id"] for member in team.get("team_members", []))  # User not already in team
            )
            
            enhanced_team = {
                "id": team["id"],
                "team_name": team["team_name"],
                "campus": team["campus"],
                "team_leader_id": team["team_leader_id"],
                "member_count": member_count,
                "max_members": 5,
                "created_at": team["created_at"],
                "can_join": user_can_join,
                "is_full": member_count >= 5,
                "members": [
                    {
                        "name": member.get("name"),
                        "role": member.get("role"),
                        "joined_at": member.get("joined_at")
                    } for member in team.get("team_members", [])
                ]
            }
            enhanced_teams.append(enhanced_team)
        
        return {
            "teams": enhanced_teams,
            "user_campus": user_university,
            "competition_title": competition.get("title", "Competition")
        }
        
    except Exception as e:
        logger.error(f"Get competition teams error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get competition teams")

@api_router.get("/inter-college/competitions/{competition_id}/leaderboard")
@limiter.limit("20/minute")
async def get_inter_college_leaderboard(
    request: Request,
    competition_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Get inter-college competition leaderboard (accessible to all authenticated users)"""
    try:
        db = await get_database()
        
        # Get competition details
        competition = await db.inter_college_competitions.find_one({"id": competition_id})
        if not competition:
            raise HTTPException(status_code=404, detail="Competition not found")
        
        # Get campus leaderboards
        campus_leaderboards = await db.campus_leaderboards.find({
            "competition_id": competition_id
        }).sort("campus_total_score", -1).to_list(None)
        
        # Get reputation rewards configuration from competition
        reputation_config = competition.get("campus_reputation_points", {
            "1": 100,  # 1st place
            "2": 70,   # 2nd place
            "3": 50,   # 3rd place
            "4-10": 30,  # 4th to 10th place
            "participation": 10  # Beyond 10th place
        })
        
        # Calculate max score for performance bonus calculation
        max_score = max([c.get("campus_total_score", 0) for c in campus_leaderboards], default=1)
        
        # Update ranks and calculate reputation points
        for idx, campus in enumerate(campus_leaderboards):
            rank = idx + 1
            
            # Determine base reputation points based on rank
            if rank == 1:
                base_points = int(reputation_config.get("1", 100))
            elif rank == 2:
                base_points = int(reputation_config.get("2", 70))
            elif rank == 3:
                base_points = int(reputation_config.get("3", 50))
            elif rank <= 10:
                base_points = int(reputation_config.get("4-10", 30))
            else:
                base_points = int(reputation_config.get("participation", 10))
            
            # Calculate participation multiplier (encourages higher participation)
            # Formula: 1 + (active_participants / 50) capped at 2x
            active_participants = campus.get("active_participants", 0)
            participation_multiplier = min(1 + (active_participants / 50), 2.0)
            
            # Calculate performance bonus (0-50 points based on score relative to max)
            campus_score = campus.get("campus_total_score", 0)
            performance_bonus = int((campus_score / max_score) * 50) if max_score > 0 else 0
            
            # Total campus reputation points
            campus_reputation_points = int((base_points * participation_multiplier) + performance_bonus)
            
            # Update database with rank and reputation points
            await db.campus_leaderboards.update_one(
                {"_id": campus["_id"]},
                {"$set": {
                    "campus_rank": rank,
                    "campus_reputation_points": campus_reputation_points
                }}
            )
            campus["campus_rank"] = rank
            campus["campus_reputation_points"] = campus_reputation_points
            # Remove MongoDB ObjectId to prevent serialization errors
            campus.pop("_id", None)
        
        # Get user's campus and individual stats
        user = await get_user_by_id(current_user["id"])
        user_campus = user.get("university") if user else None
        
        user_participation = None
        user_campus_rank = None
        
        if user_campus:
            user_participation = await db.campus_competition_participations.find_one({
                "competition_id": competition_id,
                "user_id": current_user["id"]
            })
            
            # Remove MongoDB ObjectId from user_participation
            if user_participation:
                user_participation.pop("_id", None)
            
            user_campus_stats = next((c for c in campus_leaderboards if c["campus"] == user_campus), None)
            user_campus_rank = user_campus_stats["campus_rank"] if user_campus_stats else None
        
        # Get top individual performers across all campuses
        top_individuals = await db.campus_competition_participations.find({
            "competition_id": competition_id
        }).sort("individual_score", -1).limit(20).to_list(None)
        
        # Enhance with user details and remove MongoDB _id
        enhanced_individuals = []
        for participant in top_individuals:
            # Remove MongoDB ObjectId
            participant.pop("_id", None)
            user_detail = await get_user_by_id(participant["user_id"])
            if user_detail:
                enhanced_individuals.append({
                    **participant,
                    "user_name": user_detail.get("full_name", "Unknown"),
                    "avatar": user_detail.get("avatar", "man"),
                    "user_level": user_detail.get("level", 1)
                })
        
        return {
            "competition": {
                "id": competition["id"],
                "title": competition["title"],
                "competition_type": competition["competition_type"],
                "target_metric": competition["target_metric"],
                "status": competition.get("status", "active"),
                "end_date": competition["end_date"]
            },
            "campus_leaderboard": campus_leaderboards,
            "top_individuals": enhanced_individuals,
            "user_stats": {
                "campus": user_campus,
                "campus_rank": user_campus_rank,
                "individual_participation": user_participation,
                "is_registered": bool(user_participation)
            },
            "prize_distribution": competition.get("prize_distribution", {}),
            "campus_reputation_rewards": competition.get("campus_reputation_points", {})
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Get inter-college leaderboard error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get leaderboard: {str(e)}")

@api_router.post("/inter-college/competitions/{competition_id}/complete")
@limiter.limit("5/minute")
async def complete_inter_college_competition(
    request: Request,
    competition_id: str,
    completion_data: Dict[str, Any],  # Contains final rankings and results
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Complete an inter-college competition and award reputation points (Admin only)"""
    try:
        db = await get_database()
        
        # Check if user is system admin OR campus admin
        user = await get_user_by_id(current_user)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        is_system_admin = user.get("is_admin", False) or user.get("is_super_admin", False)
        
        campus_admin = None
        if not is_system_admin:
            campus_admin = await db.campus_admins.find_one({
                "user_id": current_user["id"],
                "status": "active"
            })
            
            if not campus_admin:
                raise HTTPException(
                    status_code=403, 
                    detail="Competition completion requires system admin or campus admin privileges"
                )
        
        # Get competition
        competition = await db.inter_college_competitions.find_one({"id": competition_id})
        if not competition:
            raise HTTPException(status_code=404, detail="Competition not found")
        
        # Check if competition is already completed
        if competition.get("status") == "completed":
            raise HTTPException(status_code=400, detail="Competition is already completed")
        
        # Get all participants for automatic ranking if not provided
        participants = await db.inter_college_participations.find({
            "competition_id": competition_id
        }).to_list(None)
        
        if not participants:
            raise HTTPException(status_code=400, detail="No participants found for this competition")
        
        # Use provided rankings or generate automatic rankings based on points/metrics
        final_rankings = completion_data.get("final_rankings", [])
        
        if not final_rankings:
            # Generate rankings based on participant scores (if available)
            participants_with_scores = []
            for participant in participants:
                user_id = participant["user_id"]
                # Get participant's score from their profile or transactions
                participant_user = await get_user_by_id(user_id)
                if participant_user:
                    # Use experience points or custom metric as score
                    score = participant_user.get("experience_points", 0)
                    participants_with_scores.append({
                        "user_id": user_id,
                        "score": score,
                        "campus": participant_user.get("university", "Unknown")
                    })
            
            # Sort by score (highest first)
            participants_with_scores.sort(key=lambda x: x["score"], reverse=True)
            final_rankings = participants_with_scores
        
        # Award reputation points based on rankings
        await award_competition_reputation(competition_id, final_rankings)
        
        # Update competition status
        await db.inter_college_competitions.update_one(
            {"id": competition_id},
            {
                "$set": {
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc),
                    "completed_by": current_user,
                    "final_rankings": final_rankings[:10],  # Store top 10
                    "total_participants": len(participants),
                    "reputation_points_awarded": True
                }
            }
        )
        
        # Create audit log
        audit_log = {
            "id": str(uuid.uuid4()),
            "admin_user_id": current_user,
            "action_type": "complete_competition",
            "action_description": f"Completed inter-college competition: {competition['title']}",
            "target_type": "competition",
            "target_id": competition_id,
            "affected_entities": [{"type": "competition", "id": competition_id, "name": competition["title"]}],
            "ip_address": request.client.host,
            "severity": "info",
            "admin_level": "campus_admin" if campus_admin else "super_admin",
            "college_name": campus_admin.get("college_name") if campus_admin else "system",
            "success": True,
            "created_at": datetime.now(timezone.utc)
        }
        await db.admin_audit_logs.insert_one(audit_log)
        
        return {
            "message": "Competition completed successfully",
            "competition_id": competition_id,
            "total_participants": len(participants),
            "reputation_points_awarded": True,
            "final_rankings": final_rankings[:10],
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Complete competition error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to complete competition")

# ===== PRIZE-BASED CHALLENGE SYSTEM =====

@api_router.post("/prize-challenges")
@limiter.limit("5/day")  # Limited to prevent spam
async def create_prize_challenge(
    request: Request,
    challenge_data: PrizeChallengeCreate,
    current_admin: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Create a new prize-based challenge (Super Admin ONLY)"""
    try:
        db = await get_database()
        
        current_user = current_admin["user_id"]
        
        # Super admin only - no permission checks needed
        
        # Calculate duration hours if not provided
        if not challenge_data.duration_hours:
            duration_hours = int((challenge_data.end_date - challenge_data.start_date).total_seconds() / 3600)
            challenge_data.duration_hours = duration_hours
        
        # Create challenge
        challenge_dict = challenge_data.dict()
        challenge_dict.update({
            "id": str(uuid.uuid4()),
            "created_by": current_user,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })
        
        # Add admin metadata
        # Check if user is super admin
        user_obj = await get_user_by_id(current_user)
        is_system_admin = user_obj.get("is_super_admin", False)
        
        if is_system_admin:
            challenge_dict.update({
                "created_by_system_admin": True,
                "created_by_campus_admin": False,
                "created_by_club_admin": False
            })
        else:
            challenge_dict.update({
                "created_by_system_admin": False,
                "created_by_campus_admin": current_admin.get("admin_type") == "campus_admin",
                "created_by_club_admin": current_admin.get("admin_type") == "club_admin",
                "admin_id": current_admin.get("id"),
                "creator_college": current_admin.get("college_name"),
                "creator_admin_type": current_admin.get("admin_type")
            })
        
        challenge = PrizeChallenge(**challenge_dict)
        await db.prize_challenges.insert_one(challenge.dict())
        
        # Update admin statistics if applicable (campus admin or club admin)
        if not is_system_admin:
            await db.campus_admins.update_one(
                {"id": current_admin["id"]},
                {
                    "$inc": {"challenges_created": 1},
                    "$set": {"last_activity": datetime.now(timezone.utc)}
                }
            )
        
        # Create audit log
        creator_type = "system_admin" if is_system_admin else current_admin.get("admin_type", "campus_admin")
        audit_log = await admin_workflow_manager.create_audit_log(
            admin_user_id=current_user,
            action_type="create_prize_challenge",
            action_description=f"Created prize challenge: {challenge_data.title}",
            target_type="challenge",
            target_id=challenge.id,
            affected_entities=[{"type": "challenge", "id": challenge.id, "name": challenge_data.title}],
            severity="info",
            ip_address=request.client.host,
            is_system_generated=False
        )
        await db.admin_audit_logs.insert_one(audit_log)
        
        return {
            "success": True,
            "message": "Prize-based challenge created successfully",
            "challenge_id": challenge.id,
            "creator_type": creator_type,
            "challenge_type": challenge_data.challenge_type,
            "prize_type": challenge_data.prize_type,
            "total_prize_value": challenge_data.total_prize_value
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Create prize challenge error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create prize challenge: {str(e)}")

@api_router.get("/prize-challenges")
@limiter.limit("20/minute")
async def get_prize_challenges(
    request: Request,
    challenge_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Get all prize-based challenges"""
    try:
        db = await get_database()
        
        # Build filter
        filter_query = {}
        if challenge_type:
            filter_query["challenge_type"] = challenge_type
        if status:
            filter_query["status"] = status
        
        challenges = await db.prize_challenges.find(filter_query).sort("created_at", -1).to_list(None)
        
        # Enhance with user's participation status
        user = await get_user_by_id(current_user["id"])
        
        enhanced_challenges = []
        for challenge in challenges:
            # Check if user is participating
            user_participation = await db.prize_challenge_participations.find_one({
                "challenge_id": challenge["id"],
                "user_id": current_user["id"]
            })
            
            # Check entry requirements
            meets_requirements = True
            requirements_details = {}
            
            entry_reqs = challenge.get("entry_requirements", {})
            if entry_reqs.get("min_level"):
                user_level = user.get("level", 1)
                meets_requirements &= user_level >= entry_reqs["min_level"]
                requirements_details["level"] = {"required": entry_reqs["min_level"], "current": user_level}
            
            if entry_reqs.get("min_streak"):
                user_streak = user.get("current_streak", 0)
                meets_requirements &= user_streak >= entry_reqs["min_streak"]
                requirements_details["streak"] = {"required": entry_reqs["min_streak"], "current": user_streak}
            
            # Calculate time remaining
            now = datetime.now(timezone.utc)
            start_date = challenge.get("start_date")
            end_date = challenge.get("end_date")
            
            # Ensure timezone-aware datetime comparison
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            elif start_date and start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
                
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            elif end_date and end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)
            
            time_to_start = (start_date - now).total_seconds() if start_date and start_date > now else 0
            time_to_end = (end_date - now).total_seconds() if end_date and end_date > now else 0
            
            enhanced_challenge = {
                **challenge,
                "is_participating": bool(user_participation),
                "user_participation": user_participation,
                "meets_requirements": meets_requirements,
                "requirements_details": requirements_details,
                "time_to_start_seconds": max(0, time_to_start),
                "time_to_end_seconds": max(0, time_to_end),
                "is_active": challenge.get("status") == "active" and time_to_end > 0,
                "can_join": (
                    meets_requirements and 
                    not user_participation and 
                    time_to_start <= 0 and 
                    time_to_end > 0 and
                    (not challenge.get("max_participants") or challenge.get("current_participants", 0) < challenge.get("max_participants"))
                )
            }
            enhanced_challenges.append(enhanced_challenge)
        
        return {
            "challenges": clean_mongo_doc(enhanced_challenges),
            "user_level": user.get("level", 1),
            "user_streak": user.get("current_streak", 0)
        }
        
    except Exception as e:
        logger.error(f"Get prize challenges error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get prize challenges")

@api_router.post("/prize-challenges/{challenge_id}/join")
@limiter.limit("10/minute")
async def join_prize_challenge(
    request: Request,
    challenge_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Join a prize-based challenge"""
    try:
        db = await get_database()
        user = await get_user_by_id(current_user["id"])
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get challenge
        challenge = await db.prize_challenges.find_one({"id": challenge_id})
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        # Check if challenge is active and accepting participants
        now = datetime.now(timezone.utc)
        start_date = challenge.get("start_date")
        end_date = challenge.get("end_date")
        
        # Convert to timezone-aware datetime if needed
        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            elif not start_date.tzinfo:
                start_date = start_date.replace(tzinfo=timezone.utc)
        
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            elif not end_date.tzinfo:
                end_date = end_date.replace(tzinfo=timezone.utc)
        
        if start_date and now < start_date:
            raise HTTPException(status_code=400, detail="Challenge has not started yet")
        if end_date and now > end_date:
            raise HTTPException(status_code=400, detail="Challenge has ended")
        
        # Check entry requirements
        entry_reqs = challenge.get("entry_requirements", {})
        
        if entry_reqs.get("min_level", 0) > user.get("level", 1):
            raise HTTPException(status_code=400, detail=f"Minimum level {entry_reqs['min_level']} required")
        
        if entry_reqs.get("min_streak", 0) > user.get("current_streak", 0):
            raise HTTPException(status_code=400, detail=f"Minimum streak {entry_reqs['min_streak']} days required")
        
        # Check if already participating
        existing_participation = await db.prize_challenge_participations.find_one({
            "challenge_id": challenge_id,
            "user_id": current_user["id"]
        })
        
        if existing_participation:
            raise HTTPException(status_code=400, detail="Already participating in this challenge")
        
        # Check participant limit
        if challenge.get("max_participants"):
            current_participants = challenge.get("current_participants", 0)
            if current_participants >= challenge["max_participants"]:
                raise HTTPException(status_code=400, detail="Challenge is full")
        
        # Create participation record
        participation = PrizeChallengeParticipation(
            challenge_id=challenge_id,
            user_id=current_user["id"],
            target_progress=challenge["target_value"]
        )
        
        await db.prize_challenge_participations.insert_one(participation.dict())
        
        # Update challenge participant count
        await db.prize_challenges.update_one(
            {"id": challenge_id},
            {"$inc": {"current_participants": 1}}
        )
        
        # Award joining points
        join_points = 10
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$inc": {"experience_points": join_points}}
        )
        
        # Update user leaderboards after joining challenge
        try:
            from gamification_service import update_user_leaderboards
            await update_user_leaderboards(db, current_user["id"])
            logger.info(f"✅ Updated leaderboards for user {current_user['id']} after joining prize challenge")
        except Exception as e:
            logger.error(f"Failed to update leaderboards after joining prize challenge: {str(e)}")
        
        return {
            "message": "Successfully joined prize challenge",
            "challenge_id": challenge_id,
            "challenge_title": challenge["title"],
            "target_value": challenge["target_value"],
            "prize_type": challenge["prize_type"],
            "total_prize_value": challenge["total_prize_value"],
            "points_earned": join_points
        }
        
    except Exception as e:
        logger.error(f"Join prize challenge error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to join challenge")

@api_router.get("/prize-challenges/{challenge_id}/leaderboard")
@limiter.limit("20/minute")
async def get_prize_challenge_leaderboard(
    request: Request,
    challenge_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Get prize challenge leaderboard"""
    try:
        db = await get_database()
        
        # Get challenge details
        challenge = await db.prize_challenges.find_one({"id": challenge_id})
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        # Get all participants sorted by progress
        participants = await db.prize_challenge_participations.find({
            "challenge_id": challenge_id
        }).sort("current_progress", -1).to_list(None)
        
        # Update ranks and enhance with user details
        leaderboard = []
        for idx, participant in enumerate(participants):
            # Update participant rank
            rank = idx + 1
            await db.prize_challenge_participations.update_one(
                {"_id": participant["_id"]},
                {"$set": {"current_rank": rank}}
            )
            
            # Get user details
            user_detail = await get_user_by_id(participant["user_id"])
            if user_detail:
                # Calculate progress percentage
                progress_percentage = min(100, (participant["current_progress"] / challenge["target_value"]) * 100) if challenge["target_value"] > 0 else 0
                
                leaderboard_entry = {
                    "rank": rank,
                    "user_id": participant["user_id"],
                    "user_name": user_detail.get("full_name", "Unknown"),
                    "avatar": user_detail.get("avatar", "man"),
                    "campus": user_detail.get("university"),
                    "current_progress": participant["current_progress"],
                    "progress_percentage": progress_percentage,
                    "is_completed": participant.get("participation_status") == "completed",
                    "joined_at": participant["joined_at"],
                    "is_current_user": participant["user_id"] == current_user["id"]
                }
                leaderboard.append(leaderboard_entry)
        
        # Find user's position
        user_rank = None
        user_entry = None
        for entry in leaderboard:
            if entry["is_current_user"]:
                user_rank = entry["rank"]
                user_entry = entry
                break
        
        return {
            "challenge": {
                "id": challenge["id"],
                "title": challenge["title"],
                "description": challenge["description"],
                "challenge_type": challenge["challenge_type"],
                "target_value": challenge["target_value"],
                "target_metric": challenge["target_metric"],
                "prize_type": challenge["prize_type"],
                "total_prize_value": challenge["total_prize_value"],
                "end_date": challenge["end_date"],
                "status": challenge.get("status", "active")
            },
            "leaderboard": leaderboard[:50],  # Top 50
            "user_stats": {
                "rank": user_rank,
                "entry": user_entry,
                "is_participating": bool(user_entry)
            },
            "prize_structure": challenge.get("prize_structure", {}),
            "campus_reputation_rewards": challenge.get("campus_reputation_rewards", {}),
            "total_participants": len(participants)
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Get prize challenge leaderboard error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get leaderboard: {str(e)}")


# ===== CRUD OPERATIONS FOR COMPETITIONS =====

@api_router.put("/inter-college/competitions/{competition_id}")
@limiter.limit("10/minute")
async def update_inter_college_competition(
    request: Request,
    competition_id: str,
    update_data: InterCollegeCompetitionUpdate,
    current_admin: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Update an inter-college competition (Super Admin ONLY)"""
    try:
        db = await get_database()
        
        # Get existing competition
        competition = await db.inter_college_competitions.find_one({"id": competition_id})
        if not competition:
            raise HTTPException(status_code=404, detail="Competition not found")
        
        current_user_id = current_admin["user_id"]
        is_system_admin = current_admin.get("is_system_admin", False)
        
        # Check permissions: creator or super admin can edit
        if competition["created_by"] != current_user_id and not is_system_admin:
            raise HTTPException(status_code=403, detail="Only the creator or super admin can edit this competition")
        
        # Build update dict from provided fields
        update_dict = {k: v for k, v in update_data.dict(exclude_unset=True).items() if v is not None}
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_dict["updated_at"] = datetime.now(timezone.utc)
        
        # Update competition
        await db.inter_college_competitions.update_one(
            {"id": competition_id},
            {"$set": update_dict}
        )
        
        # Create audit log
        creator_type = "system_admin" if is_system_admin else current_admin.get("admin_type", "campus_admin")
        audit_log = await admin_workflow_manager.create_audit_log(
            admin_user_id=current_user_id,
            action_type="update_inter_college_competition",
            action_description=f"Updated inter-college competition: {competition['title']}",
            target_type="competition",
            target_id=competition_id,
            affected_entities=[{"type": "competition", "id": competition_id}],
            severity="info",
            ip_address=request.client.host
        )
        await db.admin_audit_logs.insert_one(audit_log)
        
        return {
            "message": "Competition updated successfully",
            "competition_id": competition_id,
            "updated_fields": list(update_dict.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update competition error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update competition")

@api_router.delete("/inter-college/competitions/{competition_id}")
@limiter.limit("10/minute")
async def delete_inter_college_competition(
    request: Request,
    competition_id: str,
    current_admin: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Delete an inter-college competition (Super Admin ONLY)"""
    try:
        db = await get_database()
        
        # Get existing competition
        competition = await db.inter_college_competitions.find_one({"id": competition_id})
        if not competition:
            raise HTTPException(status_code=404, detail="Competition not found")
        
        current_user_id = current_admin["user_id"]
        is_system_admin = current_admin.get("is_system_admin", False)
        
        # Check permissions
        if competition["created_by"] != current_user_id and not is_system_admin:
            raise HTTPException(status_code=403, detail="Only the creator or super admin can delete this competition")
        
        # Check if competition has participants - prevent deletion
        participant_count = await db.inter_college_registrations.count_documents({"competition_id": competition_id})
        if participant_count > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete competition with {participant_count} registered participant(s). Please cancel the competition instead."
            )
        
        # Don't allow deletion if competition is active
        if competition.get("status") == "active":
            raise HTTPException(status_code=400, detail="Cannot delete an active competition. Cancel it first.")
        
        # Delete competition and related data (only if no participants)
        await db.inter_college_competitions.delete_one({"id": competition_id})
        await db.campus_leaderboards.delete_many({"competition_id": competition_id})
        await db.competition_registrations.delete_many({"competition_id": competition_id})
        
        # Create audit log
        creator_type = "system_admin" if is_system_admin else current_admin.get("admin_type", "campus_admin")
        audit_log = await admin_workflow_manager.create_audit_log(
            admin_user_id=current_user_id,
            action_type="delete_inter_college_competition",
            action_description=f"Deleted inter-college competition: {competition['title']}",
            target_type="competition",
            target_id=competition_id,
            severity="warning",
            ip_address=request.client.host
        )
        await db.admin_audit_logs.insert_one(audit_log)
        
        return {
            "message": "Competition deleted successfully",
            "competition_id": competition_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete competition error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete competition")

# ===== CRUD OPERATIONS FOR PRIZE CHALLENGES =====

@api_router.put("/prize-challenges/{challenge_id}")
@limiter.limit("10/minute")
async def update_prize_challenge(
    request: Request,
    challenge_id: str,
    update_data: PrizeChallengeUpdate,
    current_admin: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Update a prize challenge (Super Admin ONLY)"""
    try:
        db = await get_database()
        
        # Get existing challenge
        challenge = await db.prize_challenges.find_one({"id": challenge_id})
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        current_user_id = current_admin["user_id"]
        is_system_admin = current_admin.get("is_system_admin", False)
        
        # Check permissions
        if challenge["created_by"] != current_user_id and not is_system_admin:
            raise HTTPException(status_code=403, detail="Only the creator or super admin can edit this challenge")
        
        # Build update dict
        update_dict = {k: v for k, v in update_data.dict(exclude_unset=True).items() if v is not None}
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_dict["updated_at"] = datetime.now(timezone.utc)
        
        # Update challenge
        await db.prize_challenges.update_one(
            {"id": challenge_id},
            {"$set": update_dict}
        )
        
        # Create audit log
        creator_type = "system_admin" if is_system_admin else current_admin.get("admin_type", "campus_admin")
        audit_log = await admin_workflow_manager.create_audit_log(
            admin_user_id=current_user_id,
            action_type="update_prize_challenge",
            action_description=f"Updated prize challenge: {challenge['title']}",
            target_type="challenge",
            target_id=challenge_id,
            severity="info",
            ip_address=request.client.host
        )
        await db.admin_audit_logs.insert_one(audit_log)
        
        return {
            "message": "Challenge updated successfully",
            "challenge_id": challenge_id,
            "updated_fields": list(update_dict.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update challenge error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update challenge")

@api_router.delete("/prize-challenges/{challenge_id}")
@limiter.limit("10/minute")
async def delete_prize_challenge(
    request: Request,
    challenge_id: str,
    current_admin: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Delete a prize challenge (Super Admin ONLY)"""
    try:
        db = await get_database()
        
        # Get existing challenge
        challenge = await db.prize_challenges.find_one({"id": challenge_id})
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        current_user_id = current_admin["user_id"]
        is_system_admin = current_admin.get("is_system_admin", False)
        
        # Check permissions
        if challenge["created_by"] != current_user_id and not is_system_admin:
            raise HTTPException(status_code=403, detail="Only the creator or super admin can delete this challenge")
        
        # Check if challenge has participants - prevent deletion
        participant_count = await db.prize_challenge_participations.count_documents({"challenge_id": challenge_id})
        if participant_count > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete challenge with {participant_count} registered participant(s). Please cancel the challenge instead."
            )
        
        # Don't allow deletion if challenge is active
        if challenge.get("status") == "active":
            raise HTTPException(status_code=400, detail="Cannot delete an active challenge. Cancel it first.")
        
        # Delete challenge and related data (only if no participants)
        await db.prize_challenges.delete_one({"id": challenge_id})
        await db.prize_challenge_participations.delete_many({"challenge_id": challenge_id})
        
        # Create audit log
        creator_type = "system_admin" if is_system_admin else current_admin.get("admin_type", "campus_admin")
        audit_log = await admin_workflow_manager.create_audit_log(
            admin_user_id=current_user_id,
            action_type="delete_prize_challenge",
            action_description=f"Deleted prize challenge: {challenge['title']}",
            target_type="challenge",
            target_id=challenge_id,
            severity="warning",
            ip_address=request.client.host
        )
        await db.admin_audit_logs.insert_one(audit_log)
        
        return {
            "message": "Challenge deleted successfully",
            "challenge_id": challenge_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete challenge error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete challenge")

# ===== COLLEGE EVENTS SYSTEM =====

@api_router.post("/college-events")
@limiter.limit("10/day")
async def create_college_event(
    request: Request,
    event_data: CollegeEventCreate,
    current_admin: Dict[str, Any] = Depends(get_current_admin_with_challenge_permissions)
):
    """Create a new college event (Club Admin, Campus Admin, or Super Admin)"""
    try:
        db = await get_database()
        
        current_user = current_admin["user_id"]
        is_system_admin = current_admin.get("is_system_admin", False)
        admin_type = "super_admin" if is_system_admin else current_admin.get("admin_type", "campus_admin")
        
        # Get user's college
        user_doc = await get_user_by_id(current_user)
        college_name = user_doc.get("university", "Unknown College")
        
        # Create event
        event_dict = event_data.dict()
        event_dict.update({
            "id": str(uuid.uuid4()),
            "college_name": college_name,
            "created_by": current_user,
            "created_by_admin_type": admin_type,
            "admin_id": current_admin.get("id") if not is_system_admin else None,
            "category": "technical",  # Fixed as per requirements
            "current_participants": 0,
            "status": "upcoming",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })
        
        event = CollegeEvent(**event_dict)
        await db.college_events.insert_one(event.dict())
        
        # Update admin statistics
        if not is_system_admin and current_admin.get("id"):
            await db.campus_admins.update_one(
                {"id": current_admin["id"]},
                {
                    "$inc": {"events_created": 1},
                    "$set": {"last_activity": datetime.now(timezone.utc)}
                }
            )
        
        return {
            "message": "College event created successfully",
            "event_id": event.id,
            "event_type": event.event_type,
            "visibility": event.visibility,
            "college_name": college_name
        }
        
    except Exception as e:
        logger.error(f"Create college event error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")

@api_router.get("/college-events")
@limiter.limit("30/minute")
async def get_college_events(
    request: Request,
    status: Optional[str] = None,
    event_type: Optional[str] = None,
    visibility: Optional[str] = None,
    club_name: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Get college events with filters"""
    try:
        db = await get_database()
        user_college = current_user.get("university", "")
        
        # Build filter
        filter_dict = {}
        
        if status:
            filter_dict["status"] = status
        if event_type:
            filter_dict["event_type"] = event_type
        if club_name:
            filter_dict["club_name"] = club_name
        
        # Visibility filter
        if visibility:
            filter_dict["visibility"] = visibility
        else:
            # Show events based on visibility rules
            filter_dict["$or"] = [
                {"visibility": "all_colleges"},
                {"visibility": "college_only", "college_name": user_college},
                {"visibility": "selected_colleges", "eligible_colleges": user_college}
            ]
        
        events = await db.college_events.find(filter_dict).sort("start_date", 1).to_list(None)
        
        # Enhance with creator details and registration info
        enhanced_events = []
        user_id = current_user["id"]
        
        for event in events:
            # Remove MongoDB _id field
            if "_id" in event:
                del event["_id"]
            
            creator = await get_user_by_id(event["created_by"])
            
            # Check if current user is registered for this event
            user_registration = await db.event_registrations.find_one({
                "event_id": event["id"],
                "user_id": user_id
            })
            is_registered = user_registration is not None
            
            # Get total registration count
            registration_count = await db.event_registrations.count_documents({
                "event_id": event["id"]
            })
            
            event_info = {
                **event,
                "creator_name": creator.get("full_name", "Unknown") if creator else "Unknown",
                "creator_email": creator.get("email") if creator else None,
                "is_registered": is_registered,
                "registered_count": registration_count,
                "current_participants": registration_count,  # For backward compatibility
                "registration_enabled": event.get("registration_required", True)  # Frontend compatibility
            }
            enhanced_events.append(event_info)
        
        return {
            "events": enhanced_events,
            "total": len(enhanced_events),
            "user_college": user_college
        }
        
    except Exception as e:
        logger.error(f"Get college events error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get events")

@api_router.get("/college-events/{event_id}")
@limiter.limit("30/minute")
async def get_college_event_details(
    request: Request,
    event_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Get detailed information about a specific event"""
    try:
        db = await get_database()
        
        event = await db.college_events.find_one({"id": event_id})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Remove MongoDB _id field
        if "_id" in event:
            del event["_id"]
        
        # Check if user has access based on visibility
        user_college = current_user.get("university", "")
        if event["visibility"] == "college_only" and event["college_name"] != user_college:
            raise HTTPException(status_code=403, detail="This event is only visible to students from the host college")
        elif event["visibility"] == "selected_colleges" and user_college not in event.get("eligible_colleges", []):
            raise HTTPException(status_code=403, detail="This event is not available for your college")
        
        # Get creator details
        creator = await get_user_by_id(event["created_by"])
        
        # Check if user is registered
        user_registration = await db.event_registrations.find_one({
            "event_id": event_id,
            "user_id": current_user["id"]
        })
        
        # Get registration count
        registration_count = await db.event_registrations.count_documents({"event_id": event_id})
        
        return {
            **event,
            "creator_name": creator.get("full_name", "Unknown") if creator else "Unknown",
            "is_registered": bool(user_registration),
            "registration_status": user_registration.get("status") if user_registration else None,
            "current_registrations": registration_count,
            "can_register": (
                event.get("registration_required", True) and
                not user_registration and
                event["status"] in ["upcoming", "registration_open"] and
                (not event.get("max_participants") or registration_count < event.get("max_participants", 0))
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get event details error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get event details")

@api_router.put("/college-events/{event_id}")
@limiter.limit("10/minute")
async def update_college_event(
    request: Request,
    event_id: str,
    update_data: CollegeEventUpdate,
    current_admin: Dict[str, Any] = Depends(get_current_admin_with_challenge_permissions)
):
    """Update a college event (creator or super admin only)"""
    try:
        db = await get_database()
        
        # Get existing event
        event = await db.college_events.find_one({"id": event_id})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        current_user_id = current_admin["user_id"]
        is_system_admin = current_admin.get("is_system_admin", False)
        
        # Check permissions
        if event["created_by"] != current_user_id and not is_system_admin:
            raise HTTPException(status_code=403, detail="Only the creator or super admin can edit this event")
        
        # Build update dict
        update_dict = {k: v for k, v in update_data.dict(exclude_unset=True).items() if v is not None}
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_dict["updated_at"] = datetime.now(timezone.utc)
        
        # Update event
        await db.college_events.update_one(
            {"id": event_id},
            {"$set": update_dict}
        )
        
        return {
            "message": "Event updated successfully",
            "event_id": event_id,
            "updated_fields": list(update_dict.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update event error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update event")

@api_router.delete("/college-events/{event_id}")
@limiter.limit("10/minute")
async def delete_college_event(
    request: Request,
    event_id: str,
    current_admin: Dict[str, Any] = Depends(get_current_admin_with_challenge_permissions)
):
    """Delete a college event (creator or super admin only)"""
    try:
        db = await get_database()
        
        # Get existing event
        event = await db.college_events.find_one({"id": event_id})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        current_user_id = current_admin["user_id"]
        is_system_admin = current_admin.get("is_system_admin", False)
        
        # Check permissions
        if event["created_by"] != current_user_id and not is_system_admin:
            raise HTTPException(status_code=403, detail="Only the creator or super admin can delete this event")
        
        # Don't allow deletion if event is ongoing
        if event.get("status") == "ongoing":
            raise HTTPException(status_code=400, detail="Cannot delete an ongoing event. Mark it as completed or cancelled first.")
        
        # Delete event and registrations
        await db.college_events.delete_one({"id": event_id})
        await db.event_registrations.delete_many({"event_id": event_id})
        
        return {
            "message": "Event deleted successfully",
            "event_id": event_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete event error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete event")

@api_router.post("/college-events/{event_id}/register")
@limiter.limit("10/minute")
async def register_for_event(
    request: Request,
    event_id: str,
    team_name: Optional[str] = None,
    team_members: List[Dict[str, str]] = [],
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Register for a college event"""
    try:
        db = await get_database()
        
        # Get event
        event = await db.college_events.find_one({"id": event_id})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Check if registration is required
        if not event.get("registration_required", True):
            raise HTTPException(status_code=400, detail="This event does not require registration")
        
        # Check event status
        if event["status"] not in ["upcoming", "registration_open"]:
            raise HTTPException(status_code=400, detail="Registration is not open for this event")
        
        # Check if already registered
        existing_registration = await db.event_registrations.find_one({
            "event_id": event_id,
            "user_id": current_user["id"]
        })
        
        if existing_registration:
            raise HTTPException(status_code=400, detail="You are already registered for this event")
        
        # Check participant limit
        if event.get("max_participants"):
            registration_count = await db.event_registrations.count_documents({"event_id": event_id})
            if registration_count >= event["max_participants"]:
                raise HTTPException(status_code=400, detail="Event is full")
        
        # Create registration
        registration = EventRegistration(
            event_id=event_id,
            user_id=current_user["id"],
            user_name=current_user.get("full_name", "Unknown"),
            user_email=current_user.get("email", ""),
            user_college=current_user.get("university", ""),
            team_name=team_name,
            team_members=team_members
        )
        
        await db.event_registrations.insert_one(registration.dict())
        
        # Update event participant count
        await db.college_events.update_one(
            {"id": event_id},
            {"$inc": {"current_participants": 1}}
        )
        
        # Get updated registration count
        updated_count = await db.event_registrations.count_documents({"event_id": event_id})
        
        return {
            "message": "Successfully registered for event",
            "registration_id": registration.id,
            "event_title": event["title"],
            "event_date": event["start_date"],
            "updated_count": updated_count,
            "is_registered": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Event registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to register for event")

@api_router.get("/college-events/{event_id}/participants")
@limiter.limit("20/minute")
async def get_event_participants(
    request: Request,
    event_id: str,
    current_admin: Dict[str, Any] = Depends(get_current_admin_with_challenge_permissions)
):
    """Get list of event participants (creator or super admin only)"""
    try:
        db = await get_database()
        
        # Get event
        event = await db.college_events.find_one({"id": event_id})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        current_user_id = current_admin["user_id"]
        is_system_admin = current_admin.get("is_system_admin", False)
        
        # Check permissions
        if event["created_by"] != current_user_id and not is_system_admin:
            raise HTTPException(status_code=403, detail="Only the creator or super admin can view participants")
        
        # Get all registrations
        registrations = await db.event_registrations.find({"event_id": event_id}).to_list(None)
        
        return {
            "event_id": event_id,
            "event_title": event["title"],
            "total_participants": len(registrations),
            "max_participants": event.get("max_participants"),
            "participants": registrations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get event participants error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get participants")

@api_router.get("/my-events")
@limiter.limit("20/minute")
async def get_my_created_events(
    request: Request,
    current_admin: Dict[str, Any] = Depends(get_current_admin_with_challenge_permissions)
):
    """Get all events created by the current admin"""
    try:
        db = await get_database()
        
        current_user_id = current_admin["user_id"]
        
        # Get all events created by user
        events = await db.college_events.find({"created_by": current_user_id}).sort("created_at", -1).to_list(None)
        
        # Enhance with registration counts
        enhanced_events = []
        for event in events:
            # Remove MongoDB _id field
            if "_id" in event:
                del event["_id"]
            
            registration_count = await db.event_registrations.count_documents({"event_id": event["id"]})
            event_info = {
                **event,
                "current_registrations": registration_count
            }
            enhanced_events.append(event_info)
        
        return {
            "events": enhanced_events,
            "total": len(enhanced_events)
        }
        
    except Exception as e:
        logger.error(f"Get my events error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get events")

# ===== CAMPUS REPUTATION SYSTEM =====
# REMOVED: Campus reputation system as per user request
# The following endpoints have been disabled:
# - GET /api/campus/reputation
# - GET /api/campus/reputation/{campus_name}
# - POST /api/campus-admin/reputation/update

# ===== HELPER FUNCTIONS FOR NEW SYSTEMS =====

async def update_competition_progress():
    """Background function to update competition progress for all active participants"""
    try:
        db = await get_database()
        
        # Get all active competitions
        active_competitions = await db.inter_college_competitions.find({
            "status": "active",
            "end_date": {"$gte": datetime.now(timezone.utc)}
        }).to_list(None)
        
        for competition in active_competitions:
            await update_single_competition_progress(competition["id"])
            
    except Exception as e:
        logger.error(f"Update competition progress error: {str(e)}")

async def update_single_competition_progress(competition_id: str):
    """Update progress for a single competition - matches prize challenge logic"""
    try:
        db = await get_database()
        
        competition = await db.inter_college_competitions.find_one({"id": competition_id})
        if not competition:
            return
        
        participants = await db.campus_competition_participations.find({
            "competition_id": competition_id,
            "registration_status": {"$in": ["registered", "active"]}
        }).to_list(None)
        
        competition_type = competition["competition_type"]
        target_metric = competition["target_metric"]
        target_value = competition.get("target_value", 0)
        
        # Calculate progress for all participants and sort by score
        participant_scores = []
        for participant in participants:
            user_id = participant["user_id"]
            
            # Calculate new score based on competition type (same logic as prize challenges)
            new_score = await calculate_competition_score(user_id, competition_type, target_metric, participant["registered_at"])
            
            # Calculate progress percentage
            progress_percentage = 0.0
            if target_value and target_value > 0:
                progress_percentage = min((new_score / target_value) * 100, 100.0)
            
            # Check if target is completed
            is_completed = new_score >= target_value if target_value else False
            
            participant_scores.append({
                "_id": participant["_id"],
                "user_id": user_id,
                "campus": participant["campus"],
                "score": new_score,
                "progress_percentage": progress_percentage,
                "is_completed": is_completed
            })
        
        # Sort by score descending to calculate ranks
        participant_scores.sort(key=lambda x: x["score"], reverse=True)
        
        # Update each participant with score, rank, and progress
        for rank, participant_data in enumerate(participant_scores, start=1):
            update_data = {
                "individual_score": participant_data["score"],
                "campus_contribution": participant_data["score"],
                "current_progress": participant_data["score"],
                "progress_percentage": participant_data["progress_percentage"],
                "current_rank": rank,
                "last_updated": datetime.now(timezone.utc)
            }
            
            # Mark as completed if target reached
            if participant_data["is_completed"]:
                # Only update status if not already completed
                existing = await db.campus_competition_participations.find_one({"_id": participant_data["_id"]})
                if existing and existing.get("registration_status") != "completed":
                    update_data["registration_status"] = "completed"
                    
                    # Award completion reward if applicable
                    await award_competition_completion(competition_id, participant_data["user_id"], rank)
            
            await db.campus_competition_participations.update_one(
                {"_id": participant_data["_id"]},
                {"$set": update_data}
            )
        
        # Update campus totals
        await update_campus_leaderboards(competition_id)
        
    except Exception as e:
        logger.error(f"Update single competition progress error: {str(e)}")

async def calculate_competition_score(user_id: str, competition_type: str, target_metric: str, start_date: datetime) -> float:
    """Calculate user's score for competition based on type - matches prize challenge logic"""
    try:
        db = await get_database()
        score = 0.0
        
        # Handle savings-based competitions (matches prize challenge logic)
        if competition_type in ["campus_savings", "savings", "individual", "savings_based"] or target_metric in ["total_savings", "amount_saved", "savings_amount", "savings_based"]:
            # Calculate savings progress (income - expenses since competition start)
            # Use 'date' field which is the actual field name in transactions
            income_pipeline = [
                {"$match": {"user_id": user_id, "type": "income", "date": {"$gte": start_date}}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]
            income_result = await db.transactions.aggregate(income_pipeline).to_list(None)
            total_income = income_result[0]["total"] if income_result else 0.0
            
            expense_pipeline = [
                {"$match": {"user_id": user_id, "type": "expense", "date": {"$gte": start_date}}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]
            expense_result = await db.transactions.aggregate(expense_pipeline).to_list(None)
            total_expenses = expense_result[0]["total"] if expense_result else 0.0
            
            score = max(0, total_income - total_expenses)
        
        elif competition_type in ["campus_streak", "streak"]:
            if target_metric in ["average_streak", "days_streak"]:
                user = await db.users.find_one({"id": user_id})
                score = float(user.get("current_streak", 0)) if user else 0.0
        
        elif competition_type in ["campus_referrals", "referrals"]:
            if target_metric in ["referral_count", "referrals_made"]:
                referral_program = await db.referral_programs.find_one({"referrer_id": user_id})
                if referral_program:
                    # Count successful referrals since competition start
                    recent_referrals = await db.referred_users.count_documents({
                        "referrer_id": user_id,
                        "status": "completed",
                        "completed_at": {"$gte": start_date}
                    })
                    score = float(recent_referrals)
        
        elif competition_type in ["campus_goals", "goals"]:
            if target_metric in ["goals_completed"]:
                completed_goals = await db.financial_goals.count_documents({
                    "user_id": user_id,
                    "is_completed": True,
                    "updated_at": {"$gte": start_date}
                })
                score = float(completed_goals)
        
        elif competition_type == "engagement":
            # Count transactions, logins, or other engagement metrics
            transaction_count = await db.transactions.count_documents({
                "user_id": user_id,
                "date": {"$gte": start_date}
            })
            score = float(transaction_count)
        
        return score
        
    except Exception as e:
        logger.error(f"Calculate competition score error: {str(e)}")
        return 0.0

async def update_campus_leaderboards(competition_id: str):
    """Update campus leaderboards for a competition"""
    try:
        db = await get_database()
        
        competition = await db.inter_college_competitions.find_one({"id": competition_id})
        if not competition:
            return
        
        scoring_method = competition.get("scoring_method", "total")
        
        # Get all campuses in this competition
        campuses = await db.campus_competition_participations.distinct("campus", {"competition_id": competition_id})
        
        campus_scores = []
        
        for campus in campuses:
            # Get all participants for this campus
            campus_participants = await db.campus_competition_participations.find({
                "competition_id": competition_id,
                "campus": campus,
                "registration_status": {"$in": ["registered", "active"]}
            }).to_list(None)
            
            if not campus_participants:
                continue
            
            # Calculate campus score based on method
            individual_scores = [p["individual_score"] for p in campus_participants]
            
            if scoring_method == "total":
                campus_score = sum(individual_scores)
            elif scoring_method == "average":
                campus_score = sum(individual_scores) / len(individual_scores)
            elif scoring_method == "top_performers":
                # Use top 10 or all if less than 10
                top_scores = sorted(individual_scores, reverse=True)[:10]
                campus_score = sum(top_scores)
            else:
                campus_score = sum(individual_scores)
            
            campus_scores.append({
                "campus": campus,
                "score": campus_score,
                "participants": len(campus_participants),
                "active_participants": len([p for p in campus_participants if p.get("registration_status") == "active"])
            })
        
        # Sort campuses by score
        campus_scores.sort(key=lambda x: x["score"], reverse=True)
        
        # Get reputation rewards configuration from competition
        reputation_config = competition.get("campus_reputation_points", {
            "1": 100, "2": 70, "3": 50, "4-10": 30, "participation": 10
        })
        
        # Calculate max score for performance bonus
        max_score = max([c["score"] for c in campus_scores], default=1)
        
        # Update leaderboards with reputation points
        for idx, campus_data in enumerate(campus_scores):
            rank = idx + 1
            
            # Determine base reputation points based on rank
            if rank == 1:
                base_points = int(reputation_config.get("1", 100))
            elif rank == 2:
                base_points = int(reputation_config.get("2", 70))
            elif rank == 3:
                base_points = int(reputation_config.get("3", 50))
            elif rank <= 10:
                base_points = int(reputation_config.get("4-10", 30))
            else:
                base_points = int(reputation_config.get("participation", 10))
            
            # Calculate participation multiplier
            active_participants = campus_data["active_participants"]
            participation_multiplier = min(1 + (active_participants / 50), 2.0)
            
            # Calculate performance bonus
            campus_score = campus_data["score"]
            performance_bonus = int((campus_score / max_score) * 50) if max_score > 0 else 0
            
            # Total campus reputation points
            campus_reputation_points = int((base_points * participation_multiplier) + performance_bonus)
            
            await db.campus_leaderboards.update_one(
                {"competition_id": competition_id, "campus": campus_data["campus"]},
                {
                    "$set": {
                        "campus_total_score": campus_data["score"],
                        "campus_average_score": campus_data["score"] / max(1, campus_data["participants"]),
                        "campus_rank": rank,
                        "campus_reputation_points": campus_reputation_points,
                        "total_participants": campus_data["participants"],
                        "active_participants": campus_data["active_participants"],
                        "last_updated": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
        
    except Exception as e:
        logger.error(f"Update campus leaderboards error: {str(e)}")

async def update_prize_challenge_progress():
    """Background function to update prize challenge progress"""
    try:
        db = await get_database()
        
        # Get all active prize challenges
        active_challenges = await db.prize_challenges.find({
            "status": "active",
            "end_date": {"$gte": datetime.now(timezone.utc)}
        }).to_list(None)
        
        for challenge in active_challenges:
            await update_single_prize_challenge_progress(challenge["id"])
            
    except Exception as e:
        logger.error(f"Update prize challenge progress error: {str(e)}")

async def update_single_prize_challenge_progress(challenge_id: str):
    """Update progress for a single prize challenge"""
    try:
        db = await get_database()
        
        challenge = await db.prize_challenges.find_one({"id": challenge_id})
        if not challenge:
            return
        
        participants = await db.prize_challenge_participations.find({
            "challenge_id": challenge_id,
            "participation_status": "active"
        }).to_list(None)
        
        challenge_category = challenge["challenge_category"]
        target_metric = challenge["target_metric"]
        
        for participant in participants:
            user_id = participant["user_id"]
            
            # Calculate new progress based on challenge category
            new_progress = await calculate_prize_challenge_progress(
                user_id, challenge_category, target_metric, participant["joined_at"]
            )
            
            # Update progress
            progress_percentage = min(100, (new_progress / challenge["target_value"]) * 100) if challenge["target_value"] > 0 else 0
            is_completed = new_progress >= challenge["target_value"]
            
            update_data = {
                "current_progress": new_progress,
                "progress_percentage": progress_percentage
            }
            
            # Mark as completed if target reached
            if is_completed and participant.get("participation_status") != "completed":
                update_data["participation_status"] = "completed"
                
                # Award completion reward
                await award_prize_challenge_completion(challenge_id, user_id, participant["current_rank"])
            
            await db.prize_challenge_participations.update_one(
                {"_id": participant["_id"]},
                {"$set": update_data}
            )
        
    except Exception as e:
        logger.error(f"Update single prize challenge progress error: {str(e)}")

async def calculate_prize_challenge_progress(user_id: str, challenge_category: str, target_metric: str, start_date: datetime) -> float:
    """Calculate user's progress for prize challenge"""
    try:
        db = await get_database()
        progress = 0.0
        
        # Handle both "savings" and "individual" with "savings_amount" or "savings_based" metrics
        if challenge_category in ["savings", "individual", "savings_based"] or target_metric in ["amount_saved", "savings_amount", "savings_based"]:
            # Calculate savings progress (income - expenses since challenge start)
            # Use 'date' field which is the actual field name in transactions
            income_pipeline = [
                {"$match": {"user_id": user_id, "type": "income", "date": {"$gte": start_date}}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]
            income_result = await db.transactions.aggregate(income_pipeline).to_list(None)
            total_income = income_result[0]["total"] if income_result else 0.0
            
            expense_pipeline = [
                {"$match": {"user_id": user_id, "type": "expense", "date": {"$gte": start_date}}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]
            expense_result = await db.transactions.aggregate(expense_pipeline).to_list(None)
            total_expenses = expense_result[0]["total"] if expense_result else 0.0
            
            progress = max(0, total_income - total_expenses)
        
        elif challenge_category == "streak":
            if target_metric == "days_streak":
                user = await db.users.find_one({"id": user_id})
                progress = float(user.get("current_streak", 0)) if user else 0.0
        
        elif challenge_category == "referrals":
            if target_metric == "referrals_made":
                referral_program = await db.referral_programs.find_one({"referrer_id": user_id})
                if referral_program:
                    # Count successful referrals since challenge start
                    recent_referrals = await db.referred_users.count_documents({
                        "referrer_id": user_id,
                        "status": "completed",
                        "completed_at": {"$gte": start_date}
                    })
                    progress = float(recent_referrals)
        
        elif challenge_category == "goals":
            if target_metric == "goals_completed":
                completed_goals = await db.financial_goals.count_documents({
                    "user_id": user_id,
                    "is_completed": True,
                    "updated_at": {"$gte": start_date}
                })
                progress = float(completed_goals)
        
        elif challenge_category == "engagement":
            # Count transactions, logins, or other engagement metrics
            transaction_count = await db.transactions.count_documents({
                "user_id": user_id,
                "timestamp": {"$gte": start_date}
            })
            progress = float(transaction_count)
        
        return progress
        
    except Exception as e:
        logger.error(f"Calculate prize challenge progress error: {str(e)}")
        return 0.0

async def award_prize_challenge_completion(challenge_id: str, user_id: str, rank: int):
    """Award prizes for challenge completion"""
    try:
        db = await get_database()
        
        challenge = await db.prize_challenges.find_one({"id": challenge_id})
        if not challenge:
            return
        
        prize_structure = challenge.get("prize_structure", {})
        
        # Determine prize based on rank
        prize_key = f"{rank}st" if rank == 1 else f"{rank}nd" if rank == 2 else f"{rank}rd" if rank == 3 else f"{rank}th"
        if prize_key not in prize_structure:
            # Check for participation prize
            prize_key = "participation"
        
        if prize_key not in prize_structure:
            return
        
        prize_info = prize_structure[prize_key]
        
        # Create reward record
        reward = ChallengeReward(
            challenge_id=challenge_id,
            user_id=user_id,
            reward_type=challenge["prize_type"],
            reward_value=prize_info.get("amount", prize_info.get("points", 0)),
            reward_rank=rank
        )
        
        if challenge["prize_type"] == "monetary":
            reward.amount_inr = float(prize_info.get("amount", 0))
        elif challenge["prize_type"] == "scholarship":
            reward.scholarship_info = challenge.get("scholarship_details", {})
        elif challenge["prize_type"] == "campus_reputation":
            user = await get_user_by_id(user_id)
            campus = user.get("university") if user else None
            if campus:
                points = int(prize_info.get("reputation_points", 0))
                await add_campus_reputation_points(campus, points, "prize_challenge", challenge_id, "prize_challenge", user_id)
                reward.campus_reputation_points = points
                reward.campus_affected = campus
        
        await db.challenge_rewards.insert_one(reward.dict())
        
        # Notify user
        await create_notification(
            user_id,
            "challenge_reward",
            f"🏆 Prize Challenge Reward!",
            f"You finished #{rank} in '{challenge['title']}' and earned a reward!",
            related_id=reward.id
        )
        
    except Exception as e:
        logger.error(f"Award prize challenge completion error: {str(e)}")

async def award_competition_completion(competition_id: str, user_id: str, rank: int):
    """Award prizes for inter-college competition completion - similar to prize challenges"""
    try:
        db = await get_database()
        
        competition = await db.inter_college_competitions.find_one({"id": competition_id})
        if not competition:
            return
        
        prize_distribution = competition.get("prize_distribution", {})
        participation_rewards = competition.get("participation_rewards", {})
        
        # Determine prize based on rank
        prize_key = f"{rank}st" if rank == 1 else f"{rank}nd" if rank == 2 else f"{rank}rd" if rank == 3 else f"{rank}th"
        
        # Check if this rank has a prize
        prize_amount = 0
        reward_type = "monetary"
        
        if prize_key in prize_distribution:
            prize_amount = float(prize_distribution[prize_key])
        elif str(rank) in prize_distribution:
            prize_amount = float(prize_distribution[str(rank)])
        elif "participation" in participation_rewards:
            # Award participation reward
            reward_info = participation_rewards["participation"]
            prize_amount = float(reward_info.get("amount", reward_info.get("points", 0)))
            reward_type = reward_info.get("type", "points")
        
        if prize_amount <= 0 and reward_type == "monetary":
            return
        
        # Get user details for campus reputation
        user = await get_user_by_id(user_id)
        campus = user.get("university") if user else None
        
        # Create reward record in individual_rewards array
        reward_record = {
            "id": str(uuid.uuid4()),
            "competition_id": competition_id,
            "user_id": user_id,
            "reward_type": reward_type,
            "reward_value": prize_amount,
            "reward_rank": rank,
            "awarded_at": datetime.now(timezone.utc),
            "status": "pending"
        }
        
        # Update participation record with reward
        await db.campus_competition_participations.update_one(
            {"competition_id": competition_id, "user_id": user_id},
            {
                "$push": {"individual_rewards": reward_record},
                "$set": {"reward_eligibility.completion": True}
            }
        )
        
        # Add campus reputation points if applicable
        if campus and "campus_reputation_points" in competition:
            rep_points = competition["campus_reputation_points"]
            rank_points = rep_points.get(prize_key, rep_points.get(str(rank), 0))
            if rank_points > 0:
                await add_campus_reputation_points(
                    campus, 
                    int(rank_points), 
                    "inter_college_competition", 
                    competition_id, 
                    "competition_completion", 
                    user_id
                )
        
        # Award achievement points to user
        if prize_amount > 0:
            await db.users.update_one(
                {"id": user_id},
                {"$inc": {"achievement_points": int(prize_amount / 10)}}  # 1 point per 10 INR
            )
        
        # Notify user
        notification_title = f"🏆 Competition Reward - Rank #{rank}!"
        notification_message = f"Congratulations! You finished #{rank} in '{competition['title']}' competition"
        
        if reward_type == "monetary":
            notification_message += f" and earned ₹{prize_amount:,.0f}!"
        elif reward_type == "points":
            notification_message += f" and earned {prize_amount:,.0f} points!"
        
        await notification_service.create_and_notify_in_app_notification(
            user_id=user_id,
            notification_type="competition_reward",
            title=notification_title,
            message=notification_message,
            priority="high",
            action_url="/campus/competitions",
            metadata={
                "competition_id": competition_id,
                "rank": rank,
                "reward_amount": prize_amount,
                "reward_type": reward_type
            }
        )
        
    except Exception as e:
        logger.error(f"Award competition completion error: {str(e)}")

# ===== INTER-COLLEGE COMPETITION AUTOMATION SYSTEM =====

async def update_inter_college_competitions_progress():
    """Background function to update inter-college competition progress - runs periodically"""
    try:
        db = await get_database()
        
        # Get all active inter-college competitions
        active_competitions = await db.inter_college_competitions.find({
            "status": "active",
            "start_date": {"$lte": datetime.now(timezone.utc)},
            "end_date": {"$gte": datetime.now(timezone.utc)}
        }).to_list(None)
        
        logger.info(f"📊 Updating progress for {len(active_competitions)} active inter-college competitions")
        
        for competition in active_competitions:
            await update_single_inter_college_progress(competition["id"])
            
    except Exception as e:
        logger.error(f"Update inter-college competitions progress error: {str(e)}")

async def update_single_inter_college_progress(competition_id: str):
    """Update progress for a single inter-college competition"""
    try:
        db = await get_database()
        
        competition = await db.inter_college_competitions.find_one({"id": competition_id})
        if not competition:
            return
        
        # Get all participants
        participants = await db.campus_competition_participations.find({
            "competition_id": competition_id
        }).to_list(None)
        
        if not participants:
            return
        
        competition_type = competition.get("competition_type", "savings")  # savings, streak, goals, engagement
        target_value = competition.get("target_value", 0)
        
        for participant in participants:
            user_id = participant["user_id"]
            
            # Calculate new progress based on competition type
            new_progress = await calculate_inter_college_progress(
                user_id, competition_type, participant.get("joined_at", competition["start_date"])
            )
            
            # Calculate progress percentage
            progress_percentage = min(100, (new_progress / target_value) * 100) if target_value > 0 else 0
            
            # Determine current rank among all participants
            current_rank = await calculate_participant_rank(competition_id, user_id, new_progress)
            
            update_data = {
                "current_progress": new_progress,
                "progress_percentage": progress_percentage,
                "current_rank": current_rank,
                "last_updated": datetime.now(timezone.utc)
            }
            
            # Update participation record
            await db.campus_competition_participations.update_one(
                {"_id": participant["_id"]},
                {"$set": update_data}
            )
        
        # Update campus leaderboard scores
        await update_campus_competition_leaderboard(competition_id)
        
        logger.info(f"✅ Updated progress for {len(participants)} participants in competition {competition_id}")
        
    except Exception as e:
        logger.error(f"Update single inter-college progress error: {str(e)}")

async def calculate_inter_college_progress(user_id: str, competition_type: str, start_date: datetime) -> float:
    """Calculate user's progress for inter-college competition based on competition type"""
    try:
        db = await get_database()
        progress = 0.0
        
        if competition_type == "savings":
            # Calculate savings progress (income - expenses since competition start)
            income_pipeline = [
                {"$match": {"user_id": user_id, "type": "income", "date": {"$gte": start_date}}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]
            income_result = await db.transactions.aggregate(income_pipeline).to_list(None)
            total_income = income_result[0]["total"] if income_result else 0.0
            
            expense_pipeline = [
                {"$match": {"user_id": user_id, "type": "expense", "date": {"$gte": start_date}}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]
            expense_result = await db.transactions.aggregate(expense_pipeline).to_list(None)
            total_expenses = expense_result[0]["total"] if expense_result else 0.0
            
            progress = max(0, total_income - total_expenses)
        
        elif competition_type == "streak":
            # Get current streak from user profile
            user = await db.users.find_one({"id": user_id})
            progress = float(user.get("current_streak", 0)) if user else 0.0
        
        elif competition_type == "goals":
            # Count goals completed since competition start
            completed_goals = await db.financial_goals.count_documents({
                "user_id": user_id,
                "is_completed": True,
                "updated_at": {"$gte": start_date}
            })
            progress = float(completed_goals)
        
        elif competition_type == "referrals":
            # Count successful referrals since competition start
            recent_referrals = await db.referred_users.count_documents({
                "referrer_id": user_id,
                "status": "completed",
                "completed_at": {"$gte": start_date}
            })
            progress = float(recent_referrals)
        
        elif competition_type == "engagement":
            # Count total transactions/activities since competition start
            transaction_count = await db.transactions.count_documents({
                "user_id": user_id,
                "date": {"$gte": start_date}
            })
            progress = float(transaction_count)
        
        elif competition_type == "income":
            # Total income earned since competition start
            income_pipeline = [
                {"$match": {"user_id": user_id, "type": "income", "date": {"$gte": start_date}}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]
            income_result = await db.transactions.aggregate(income_pipeline).to_list(None)
            progress = income_result[0]["total"] if income_result else 0.0
        
        return progress
        
    except Exception as e:
        logger.error(f"Calculate inter-college progress error: {str(e)}")
        return 0.0

async def calculate_participant_rank(competition_id: str, user_id: str, current_progress: float) -> int:
    """Calculate participant's current rank based on progress"""
    try:
        db = await get_database()
        
        # Count participants with higher progress
        higher_count = await db.campus_competition_participations.count_documents({
            "competition_id": competition_id,
            "current_progress": {"$gt": current_progress}
        })
        
        return higher_count + 1
        
    except Exception as e:
        logger.error(f"Calculate participant rank error: {str(e)}")
        return 0

async def update_campus_competition_leaderboard(competition_id: str):
    """Update campus-level leaderboard for competition"""
    try:
        db = await get_database()
        
        # Get all participants grouped by campus
        pipeline = [
            {"$match": {"competition_id": competition_id}},
            {"$group": {
                "_id": "$campus",
                "total_progress": {"$sum": "$current_progress"},
                "avg_progress": {"$avg": "$current_progress"},
                "participant_count": {"$sum": 1},
                "top_progress": {"$max": "$current_progress"}
            }},
            {"$sort": {"total_progress": -1}}
        ]
        
        campus_stats = await db.campus_competition_participations.aggregate(pipeline).to_list(None)
        
        # Update campus leaderboard
        for rank, campus_stat in enumerate(campus_stats, 1):
            await db.campus_leaderboards.update_one(
                {"competition_id": competition_id, "campus": campus_stat["_id"]},
                {
                    "$set": {
                        "total_progress": campus_stat["total_progress"],
                        "average_progress": campus_stat["avg_progress"],
                        "participant_count": campus_stat["participant_count"],
                        "top_individual_progress": campus_stat["top_progress"],
                        "current_rank": rank,
                        "last_updated": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
        
    except Exception as e:
        logger.error(f"Update campus competition leaderboard error: {str(e)}")

async def auto_complete_expired_competitions():
    """Automatically complete competitions that have ended"""
    try:
        db = await get_database()
        
        # Find competitions that ended but not completed
        expired_competitions = await db.inter_college_competitions.find({
            "status": "active",
            "end_date": {"$lt": datetime.now(timezone.utc)}
        }).to_list(None)
        
        logger.info(f"🏁 Auto-completing {len(expired_competitions)} expired competitions")
        
        for competition in expired_competitions:
            await auto_complete_competition(competition["id"])
            
    except Exception as e:
        logger.error(f"Auto complete expired competitions error: {str(e)}")

async def auto_complete_competition(competition_id: str):
    """Automatically complete a competition and award points"""
    try:
        db = await get_database()
        
        competition = await db.inter_college_competitions.find_one({"id": competition_id})
        if not competition or competition.get("status") == "completed":
            return
        
        # Get all participants sorted by progress
        participants = await db.campus_competition_participations.find({
            "competition_id": competition_id
        }).sort("current_progress", -1).to_list(None)
        
        if not participants:
            logger.warning(f"No participants found for competition {competition_id}")
            return
        
        # Build final rankings with user details
        final_rankings = []
        for participant in participants:
            user = await get_user_by_id(participant["user_id"])
            if user:
                final_rankings.append({
                    "user_id": participant["user_id"],
                    "campus": user.get("university", "Unknown"),
                    "score": participant.get("current_progress", 0),
                    "rank": len(final_rankings) + 1
                })
        
        # Award campus reputation points
        await award_competition_reputation(competition_id, final_rankings)
        
        # Award individual achievement points to participants
        await award_inter_college_individual_points(competition_id, final_rankings)
        
        # Update competition status
        await db.inter_college_competitions.update_one(
            {"id": competition_id},
            {
                "$set": {
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc),
                    "completed_by": {"auto_completion": True},
                    "final_rankings": final_rankings[:10],  # Store top 10
                    "total_participants": len(participants),
                    "reputation_points_awarded": True,
                    "individual_points_awarded": True
                }
            }
        )
        
        # Send completion notifications to all participants
        await send_competition_completion_notifications(competition_id, competition["title"], final_rankings)
        
        logger.info(f"✅ Auto-completed competition {competition_id} with {len(participants)} participants")
        
    except Exception as e:
        logger.error(f"Auto complete competition error: {str(e)}")

async def award_inter_college_individual_points(competition_id: str, participant_rankings: list):
    """Award individual achievement and experience points to competition participants"""
    try:
        db = await get_database()
        
        competition = await db.inter_college_competitions.find_one({"id": competition_id})
        if not competition:
            return
        
        # Point structure for individual rewards
        individual_points_structure = {
            1: 500,   # 1st place
            2: 300,   # 2nd place
            3: 200,   # 3rd place
            "top_10": 100,  # 4th-10th place
            "participation": 50  # All other participants
        }
        
        for participant in participant_rankings:
            user_id = participant["user_id"]
            rank = participant["rank"]
            
            # Determine points based on rank
            if rank == 1:
                points = individual_points_structure[1]
            elif rank == 2:
                points = individual_points_structure[2]
            elif rank == 3:
                points = individual_points_structure[3]
            elif rank <= 10:
                points = individual_points_structure["top_10"]
            else:
                points = individual_points_structure["participation"]
            
            # Award both achievement_points and experience_points
            await db.users.update_one(
                {"id": user_id},
                {
                    "$inc": {
                        "achievement_points": points,
                        "experience_points": points
                    }
                }
            )
            
            # Create reward record for tracking
            reward_record = {
                "id": str(uuid.uuid4()),
                "competition_id": competition_id,
                "competition_title": competition["title"],
                "user_id": user_id,
                "reward_type": "individual_points",
                "achievement_points": points,
                "experience_points": points,
                "rank": rank,
                "awarded_at": datetime.now(timezone.utc),
                "reason": f"Rank #{rank} in Inter-College Competition"
            }
            await db.competition_individual_rewards.insert_one(reward_record)
            
            # Send notification
            await create_notification(
                user_id,
                "competition_reward",
                f"🏆 Competition Completed!",
                f"You finished #{rank} in '{competition['title']}' and earned {points} points!",
                action_url="/competitions",
                related_id=competition_id
            )
        
        logger.info(f"✅ Awarded individual points to {len(participant_rankings)} participants in competition {competition_id}")
        
    except Exception as e:
        logger.error(f"Award inter-college individual points error: {str(e)}")

async def send_competition_completion_notifications(competition_id: str, competition_title: str, rankings: list):
    """Send completion notifications to all participants"""
    try:
        # Top 3 get special notifications
        for participant in rankings[:3]:
            rank = participant["rank"]
            emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉"
            await create_notification(
                participant["user_id"],
                "competition_complete",
                f"{emoji} Top {rank} Achievement!",
                f"Congratulations! You finished #{rank} in '{competition_title}'! Check your rewards.",
                action_url="/competitions",
                related_id=competition_id
            )
        
        # Others get general completion notification
        for participant in rankings[3:]:
            await create_notification(
                participant["user_id"],
                "competition_complete",
                f"Competition Completed!",
                f"'{competition_title}' has ended. You finished #{participant['rank']}. Great effort!",
                action_url="/competitions",
                related_id=competition_id
            )
        
    except Exception as e:
        logger.error(f"Send competition completion notifications error: {str(e)}")

async def add_campus_reputation_points(campus: str, points: int, category: str, source_id: str, source_type: str = "challenge", user_id: str = None, reason: str = None):
    """Add reputation points to a campus"""
    try:
        db = await get_database()
        
        # Update or create campus reputation record
        await db.campus_reputations.update_one(
            {"campus": campus},
            {
                "$inc": {
                    "total_reputation_points": points,
                    "monthly_reputation_points": points,
                    f"{category}_points": points
                },
                "$set": {"last_updated": datetime.now(timezone.utc)}
            },
            upsert=True
        )
        
        # Create reputation transaction record
        default_reason = f"{source_type.replace('_', ' ').title()} completion - {source_id}"
        transaction = ReputationTransaction(
            campus=campus,
            transaction_type="earned",
            points=points,
            reason=reason or default_reason,
            category=category,
            source_type=source_type,
            source_id=source_id,
            user_id=user_id
        )
        
        await db.reputation_transactions.insert_one(transaction.dict())
        
        # Update campus ranking after points change
        await update_campus_rankings()
        
        logger.info(f"Added {points} reputation points to {campus} for {category} ({source_type})")
        
    except Exception as e:
        logger.error(f"Add campus reputation points error: {str(e)}")

async def update_campus_rankings():
    """Update campus rankings based on total reputation points"""
    try:
        db = await get_database()
        
        # Get all campuses sorted by total reputation points
        campus_reputations = await db.campus_reputations.find({}).sort("total_reputation_points", -1).to_list(None)
        
        # Update ranks
        for idx, campus in enumerate(campus_reputations):
            new_rank = idx + 1
            if campus.get("current_rank") != new_rank:
                await db.campus_reputations.update_one(
                    {"_id": campus["_id"]},
                    {"$set": {"current_rank": new_rank, "previous_rank": campus.get("current_rank", new_rank)}}
                )
                
    except Exception as e:
        logger.error(f"Update campus rankings error: {str(e)}")

async def award_competition_reputation(competition_id: str, participant_rankings: list):
    """Award reputation points based on inter-college competition results"""
    try:
        db = await get_database()
        
        # Get competition details
        competition = await db.inter_college_competitions.find_one({"id": competition_id})
        if not competition:
            logger.error(f"Competition {competition_id} not found")
            return
        
        # Get campus reputation points configuration from competition
        reputation_rewards = competition.get("campus_reputation_points", {
            "1": 100,  # 1st place
            "2": 70,   # 2nd place
            "3": 50,   # 3rd place
            "participation": 20  # All other participants
        })
        
        # Award points based on rankings
        for rank, participant in enumerate(participant_rankings[:3], 1):  # Top 3
            user = await get_user_by_id(participant["user_id"])
            if user and user.get("university"):
                campus = user["university"]
                points = reputation_rewards.get(str(rank), 0)
                if points > 0:
                    await add_campus_reputation_points(
                        campus=campus,
                        points=points,
                        category="competition",
                        source_id=competition_id,
                        source_type="inter_college_competition",
                        user_id=participant["user_id"],
                        reason=f"Rank #{rank} in '{competition['title']}'"
                    )
        
        # Award participation points to all other participants
        participation_points = reputation_rewards.get("participation", 20)
        if participation_points > 0:
            for participant in participant_rankings[3:]:  # Participants beyond top 3
                user = await get_user_by_id(participant["user_id"])
                if user and user.get("university"):
                    campus = user["university"]
                    await add_campus_reputation_points(
                        campus=campus,
                        points=participation_points,
                        category="competition",
                        source_id=competition_id,
                        source_type="inter_college_competition",
                        user_id=participant["user_id"],
                        reason=f"Participated in '{competition['title']}'"
                    )
        
        logger.info(f"Awarded reputation points for competition {competition_id} to {len(participant_rankings)} participants")
        
    except Exception as e:
        logger.error(f"Award competition reputation error: {str(e)}")

# Helper function for creating notifications (reuse existing function)
async def create_notification(user_id: str, notification_type: str, title: str, message: str, action_url: str = None, related_id: str = None):
    """Create an in-app notification for user"""
    try:
        db = await get_database()
        
        notification = InAppNotification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            action_url=action_url,
            related_id=related_id
        )
        
        await db.notifications.insert_one(notification.dict())
        
    except Exception as e:
        logger.error(f"Create notification error: {str(e)}")

# Helper functions for growth mechanics
async def calculate_waitlist_priority_score(user_id: str, user: Dict[str, Any]) -> float:
    """Calculate priority score for waitlist positioning"""
    score = 0.0
    
    # Base user activity (30 points)
    score += min(user.get("current_streak", 0) * 2, 30)
    
    # Referral activity (25 points)  
    db = await get_database()
    referral_program = await db.referral_programs.find_one({"referrer_id": user_id})
    if referral_program:
        score += min(referral_program.get("successful_referrals", 0) * 5, 25)
    
    # Financial activity (20 points)
    score += min(user.get("net_savings", 0) / 1000, 20)  # ₹1000 = 1 point
    
    # Campus ambassador bonus (15 points)
    ambassador = await db.campus_ambassadors.find_one({"user_id": user_id, "status": "active"})
    if ambassador:
        score += 15
    
    # Account age bonus (10 points)
    if user.get("created_at"):
        days_old = (datetime.now(timezone.utc) - user["created_at"]).days
        score += min(days_old / 30, 10)  # 1 point per month, max 10
    
    return min(score, 100)

def calculate_estimated_wait_time(position: int, capacity: int) -> str:
    """Calculate estimated wait time for feature access"""
    if position <= capacity * 0.1:  # Top 10%
        return "Immediate access"
    elif position <= capacity * 0.3:  # Top 30%
        return "1-2 weeks"
    elif position <= capacity * 0.6:  # Top 60%
        return "3-4 weeks"
    else:
        return "1-2 months"

async def grant_feature_access(user_id: str, feature_name: str):
    """Grant immediate feature access"""
    db = await get_database()
    
    await db.feature_waitlists.update_one(
        {"user_id": user_id, "feature_name": feature_name},
        {
            "$set": {
                "granted_access": True,
                "granted_at": datetime.now(timezone.utc),
                "position": 0
            }
        }
    )

# ===== REFERRAL SYSTEM WITH MONETARY INCENTIVES =====

@api_router.get("/referrals/my-link")
@limiter.limit("5/minute")
async def get_referral_link(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dict)):
    """Get user's referral link for direct sharing"""
    try:
        db = await get_database()
        
        # Check if user already has a referral link
        referral = await db.referral_programs.find_one({"referrer_id": current_user["id"]})
        
        if not referral:
            # Create new referral record
            referral_data = {
                "referrer_id": current_user["id"],
                "referral_code": current_user["id"][:8] + str(int(datetime.now().timestamp()))[-6:],  # Unique code
                "total_referrals": 0,
                "successful_referrals": 0,
                "total_earnings": 0.0,
                "pending_earnings": 0.0,
                "created_at": datetime.now(timezone.utc)
            }
            await db.referral_programs.insert_one(referral_data)
            referral = referral_data
        
        # Generate shareable link
        base_url = FRONTEND_URL
        referral_link = f"{base_url}/register?ref={referral['referral_code']}"
        
        return {
            "referral_link": referral_link,
            "referral_code": referral["referral_code"],
            "total_referrals": referral["total_referrals"],
            "successful_referrals": referral["successful_referrals"],
            "total_earnings": referral["total_earnings"],
            "pending_earnings": referral["pending_earnings"]
        }
        
    except Exception as e:
        logger.error(f"Get referral link error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get referral link")

@api_router.get("/referrals/stats")
@limiter.limit("10/minute")
async def get_referral_stats(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dict)):
    """Get detailed referral statistics"""
    try:
        db = await get_database()
        
        # Get referral record
        referral = await db.referral_programs.find_one({"referrer_id": current_user["id"]})
        if not referral:
            return {
                "total_referrals": 0,
                "successful_referrals": 0,
                "conversion_rate": 0,
                "total_earnings": 0.0,
                "pending_earnings": 0.0,
                "recent_referrals": []
            }
        
        # Get recent successful referrals (all time)
        recent_referrals = await db.referred_users.find({
            "referrer_id": current_user["id"],
            "status": "completed"
        }).sort("completed_at", -1).limit(10).to_list(None)
        
        # Get this month's referrals
        from datetime import datetime, timezone, timedelta
        start_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        monthly_referrals = await db.referred_users.find({
            "referrer_id": current_user["id"],
            "signed_up_at": {"$gte": start_of_month}
        }).to_list(None)
        
        # Get user details for recent referrals
        referral_details = []
        for ref in recent_referrals:
            user = await get_user_by_id(ref["referred_user_id"])
            if user:
                referral_details.append({
                    "user_name": user.get("full_name", "Unknown"),
                    "joined_at": ref["completed_at"],
                    "earnings": ref.get("earnings_awarded", 0)
                })
        
        conversion_rate = (referral["successful_referrals"] / max(referral["total_referrals"], 1)) * 100
        
        return {
            "total_referrals": referral["total_referrals"],
            "successful_referrals": referral["successful_referrals"],
            "conversion_rate": round(conversion_rate, 1),
            "total_earnings": referral["total_earnings"],
            "pending_earnings": referral["pending_earnings"],
            "recent_referrals": referral_details,
            "monthly_referrals": len(monthly_referrals)
        }
        
    except Exception as e:
        logger.error(f"Get referral stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get referral stats")

@api_router.post("/referrals/process-signup")
@limiter.limit("10/minute")
async def process_referral_signup(request: Request, referral_code: str, new_user_id: str):
    """Process a new user signup through referral (called internally during registration)"""
    try:
        db = await get_database()
        
        # Find referrer
        referrer = await db.referral_programs.find_one({"referral_code": referral_code})
        if not referrer:
            return {"success": False, "message": "Invalid referral code"}
        
        # Create referred user record
        referred_user = {
            "referrer_id": referrer["referrer_id"],
            "referred_user_id": new_user_id,
            "referral_code": referral_code,
            "status": "pending",  # Will become "completed" after 30 days of activity
            "signed_up_at": datetime.now(timezone.utc),
            "earnings_awarded": 0.0
        }
        await db.referred_users.insert_one(referred_user)
        
        # Update referrer stats
        await db.referral_programs.update_one(
            {"referrer_id": referrer["referrer_id"]},
            {"$inc": {"total_referrals": 1}}
        )
        
        # Give welcome bonus to new user
        await db.users.update_one(
            {"_id": new_user_id},
            {
                "$set": {"referred_by": referrer["referrer_id"]},
                "$inc": {"experience_points": 50}  # Welcome bonus
            }
        )
        
        return {"success": True, "message": "Referral processed successfully"}
        
    except Exception as e:
        logger.error(f"Process referral signup error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process referral signup")

# ===== SOCIAL CHALLENGES SYSTEM =====

@api_router.get("/challenges")
@limiter.limit("20/minute")
async def get_active_challenges(request: Request, current_user: Dict[str, Any] = Depends(get_current_super_admin)):
    """Get all active challenges"""
    try:
        db = await get_database()
        
        # Get all active challenges
        challenges = await db.challenges.find({
            "is_active": True,
            "end_date": {"$gte": datetime.now(timezone.utc)}
        }).sort("created_at", -1).to_list(None)
        
        # Get user's participation status for each challenge
        for challenge in challenges:
            participant = await db.challenge_participants.find_one({
                "challenge_id": challenge["id"],
                "user_id": current_user["id"]
            })
            challenge["is_joined"] = participant is not None
            challenge["user_progress"] = participant["current_progress"] if participant else 0.0
            challenge["user_rank"] = participant["rank"] if participant else None
        
        return {"challenges": challenges}
        
    except Exception as e:
        logger.error(f"Get challenges error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get challenges")

@api_router.post("/challenges")
@limiter.limit("5/minute") 
async def create_challenge_standard(request: Request, challenge_data: ChallengeCreate, current_user: Dict[str, Any] = Depends(get_current_user_dict)):
    """Create a new challenge (standard REST endpoint)"""
    try:
        db = await get_database()
        
        # Check if user is admin
        user = await get_user_by_id(current_user)
        is_admin = user.get("role") == "admin" if user else False
        
        # Calculate end date
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=challenge_data.duration_days)
        
        challenge_dict = challenge_data.dict()
        challenge_dict.update({
            "id": str(uuid.uuid4()),
            "start_date": start_date,
            "end_date": end_date,
            "created_by": current_user,
            "created_at": start_date,
            "is_active": is_admin,  # Admin challenges are active immediately, user challenges need approval
            "is_approved": is_admin,
            "is_featured": is_admin,  # Only admin challenges can be featured
            "current_participants": 0,
            "total_prize_pool": challenge_data.prize_amount if hasattr(challenge_data, 'prize_amount') else 0.0,
            "moderation_status": "approved" if is_admin else "pending"
        })
        
        # Insert challenge
        await db.challenges.insert_one(challenge_dict)
        
        return {
            "message": "Challenge created successfully!" if is_admin else "Challenge submitted for approval!",
            "challenge_id": challenge_dict["id"],
            "is_approved": is_admin
        }
        
    except Exception as e:
        logger.error(f"Create challenge error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create challenge")

@api_router.post("/challenges/create")
@limiter.limit("5/minute") 
async def create_challenge(request: Request, challenge_data: ChallengeCreate, current_user: Dict[str, Any] = Depends(get_current_super_admin)):
    """Create a new challenge (admin can create featured challenges, users can create peer challenges)"""
    try:
        db = await get_database()
        
        # Check if user is admin
        user = await get_user_by_id(current_user)
        is_admin = user.get("role") == "admin" if user else False
        
        # Calculate end date
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=challenge_data.duration_days)
        
        challenge_dict = challenge_data.dict()
        challenge_dict.update({
            "id": str(uuid.uuid4()),
            "start_date": start_date,
            "end_date": end_date,
            "created_by": current_user,
            "created_at": start_date,
            "is_active": is_admin,  # Admin challenges are active immediately, user challenges need approval
            "participant_count": 0,
            "featured": is_admin  # Admin challenges are featured
        })
        
        challenge = Challenge(**challenge_dict)
        await db.challenges.insert_one(challenge.dict())
        
        # If user challenge, add to moderation queue
        if not is_admin:
            await db.challenge_moderation.insert_one({
                "challenge_id": challenge.id,
                "created_by": current_user,
                "status": "pending_review",
                "created_at": datetime.now(timezone.utc)
            })
        
        return {
            "challenge_id": challenge.id,
            "message": "Challenge created successfully" if is_admin else "Challenge submitted for review",
            "needs_approval": not is_admin
        }
        
    except Exception as e:
        logger.error(f"Create challenge error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create challenge")

@api_router.post("/challenges/{challenge_id}/join")
@limiter.limit("10/minute")
async def join_challenge(request: Request, challenge_id: str, current_user: Dict[str, Any] = Depends(get_current_super_admin)):
    """Join a challenge"""
    try:
        db = await get_database()
        
        # Check if challenge exists and is active
        challenge = await db.challenges.find_one({
            "id": challenge_id,
            "is_active": True,
            "end_date": {"$gte": datetime.now(timezone.utc)}
        })
        
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found or inactive")
        
        # Check if user already joined
        existing = await db.challenge_participants.find_one({
            "challenge_id": challenge_id,
            "user_id": current_user["id"]
        })
        
        if existing:
            raise HTTPException(status_code=400, detail="Already joined this challenge")
        
        # Check participant limit
        if challenge.get("max_participants"):
            participant_count = await db.challenge_participants.count_documents({
                "challenge_id": challenge_id
            })
            if participant_count >= challenge["max_participants"]:
                raise HTTPException(status_code=400, detail="Challenge is full")
        
        # Create participant record
        participant_data = {
            "id": str(uuid.uuid4()),
            "challenge_id": challenge_id,
            "user_id": current_user["id"],
            "joined_at": datetime.now(timezone.utc),
            "current_progress": 0.0,
            "is_completed": False
        }
        
        await db.challenge_participants.insert_one(participant_data)
        
        # Update challenge participant count
        await db.challenges.update_one(
            {"id": challenge_id},
            {"$inc": {"participant_count": 1}}
        )
        
        # Initialize progress based on challenge type
        await update_challenge_progress(challenge_id, current_user["id"])
        
        return {"message": "Successfully joined challenge", "challenge_id": challenge_id}
        
    except Exception as e:
        logger.error(f"Join challenge error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to join challenge")

@api_router.get("/challenges/{challenge_id}/leaderboard")
@limiter.limit("20/minute")
async def get_challenge_leaderboard(request: Request, challenge_id: str, current_user: Dict[str, Any] = Depends(get_current_super_admin)):
    """Get challenge leaderboard"""
    try:
        db = await get_database()
        
        # Get challenge details
        challenge = await db.challenges.find_one({"id": challenge_id})
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        # Get all participants with progress
        participants = await db.challenge_participants.find({
            "challenge_id": challenge_id
        }).sort("current_progress", -1).to_list(None)
        
        # Enrich with user data
        leaderboard = []
        for idx, participant in enumerate(participants):
            user = await get_user_by_id(participant["user_id"])
            if user:
                leaderboard.append({
                    "rank": idx + 1,
                    "user_id": participant["user_id"],
                    "user_name": user.get("full_name", "Unknown"),
                    "avatar": user.get("avatar", "man"),
                    "progress": participant["current_progress"],
                    "progress_percentage": min(100, (participant["current_progress"] / challenge["target_value"]) * 100) if challenge["target_value"] > 0 else 0,
                    "is_completed": participant["is_completed"],
                    "completion_date": participant.get("completion_date"),
                    "is_current_user": participant["user_id"] == current_user["id"]
                })
        
        # Find current user's rank
        user_rank = None
        for item in leaderboard:
            if item["is_current_user"]:
                user_rank = item["rank"]
                break
        
        return {
            "challenge": {
                "id": challenge["id"],
                "title": challenge["title"],
                "description": challenge["description"],
                "target_value": challenge["target_value"],
                "challenge_type": challenge["challenge_type"],
                "end_date": challenge["end_date"]
            },
            "leaderboard": leaderboard[:50],  # Top 50
            "user_rank": user_rank,
            "total_participants": len(participants)
        }
        
    except Exception as e:
        logger.error(f"Get challenge leaderboard error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get challenge leaderboard")

@api_router.get("/challenges/my-challenges")
@limiter.limit("20/minute")
async def get_my_challenges(request: Request, current_user: Dict[str, Any] = Depends(get_current_super_admin)):
    """Get user's active challenges with progress"""
    try:
        db = await get_database()
        
        # Get user's challenge participations
        participations = await db.challenge_participants.find({
            "user_id": current_user["id"]
        }).to_list(None)
        
        my_challenges = []
        for participation in participations:
            challenge = await db.challenges.find_one({"id": participation["challenge_id"]})
            if challenge and challenge.get("is_active", True):
                # Calculate progress percentage
                progress_percentage = min(100, (participation["current_progress"] / challenge["target_value"]) * 100) if challenge["target_value"] > 0 else 0
                
                # Get user's rank in this challenge
                better_participants = await db.challenge_participants.count_documents({
                    "challenge_id": challenge["id"],
                    "current_progress": {"$gt": participation["current_progress"]}
                })
                user_rank = better_participants + 1
                
                my_challenges.append({
                    "challenge": challenge,
                    "participation": participation,
                    "progress_percentage": progress_percentage,
                    "user_rank": user_rank,
                    "days_remaining": (challenge["end_date"] - datetime.now(timezone.utc)).days,
                    "is_expired": challenge["end_date"] < datetime.now(timezone.utc)
                })
        
        # Sort by remaining time
        my_challenges.sort(key=lambda x: x["days_remaining"])
        
        return {"my_challenges": my_challenges}
        
    except Exception as e:
        logger.error(f"Get my challenges error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user challenges")

@api_router.post("/challenges/{challenge_id}/share")
@limiter.limit("5/minute")
async def generate_challenge_share_content(request: Request, challenge_id: str, share_type: str, current_user: Dict[str, Any] = Depends(get_current_super_admin)):
    """Generate shareable content for social media platforms"""
    try:
        db = await get_database()
        
        # Get challenge and user participation
        challenge = await db.challenges.find_one({"id": challenge_id})
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
            
        participant = await db.challenge_participants.find_one({
            "challenge_id": challenge_id,
            "user_id": current_user["id"]
        })
        
        if not participant:
            raise HTTPException(status_code=400, detail="You must join the challenge first")
        
        user = await get_user_by_id(current_user["id"])
        user_name = user.get("full_name", "EarnAura User")
        
        # Calculate progress
        progress_percentage = min(100, (participant["current_progress"] / challenge["target_value"]) * 100) if challenge["target_value"] > 0 else 0
        
        # Get user rank
        better_participants = await db.challenge_participants.count_documents({
            "challenge_id": challenge_id,
            "current_progress": {"$gt": participant["current_progress"]}
        })
        user_rank = better_participants + 1
        
        # Generate platform-specific content
        base_url = "https://earnest.app"  # Replace with actual domain
        challenge_url = f"{base_url}/challenges/{challenge_id}"
        
        share_content = {}
        
        if share_type == "whatsapp":
            if participant["is_completed"]:
                message = f"🎉 I just completed the '{challenge['title']}' challenge on EarnAura! 💪\n\n"
                message += f"Target: ₹{challenge['target_value']:,.0f}\n"
                message += f"My Achievement: ₹{participant['current_progress']:,.0f}\n"
                message += f"Final Rank: #{user_rank}\n\n"
                message += f"Join me in building better financial habits! 📱\n{challenge_url}"
            else:
                message = f"🚀 I'm taking on the '{challenge['title']}' challenge on EarnAura!\n\n"
                message += f"Target: ₹{challenge['target_value']:,.0f}\n"
                message += f"Current Progress: {progress_percentage:.0f}% (₹{participant['current_progress']:,.0f})\n"
                message += f"Current Rank: #{user_rank}\n\n"
                message += f"Want to join me? Let's build better financial habits together! 💪\n{challenge_url}"
            
            encoded_message = message.replace(' ', '%20').replace('\n', '%0A')
            share_content["whatsapp"] = {
                "text": message,
                "url": f"https://wa.me/?text={encoded_message}"
            }
        
        elif share_type == "instagram":
            if participant["is_completed"]:
                story_text = f"Challenge Completed! 🎉\n{challenge['title']}\n₹{participant['current_progress']:,.0f} saved\nRank #{user_rank} 🏆\n#EarnAura #FinancialGoals #Savings"
            else:
                story_text = f"Challenge Progress 📊\n{challenge['title']}\n{progress_percentage:.0f}% Complete\n₹{participant['current_progress']:,.0f}/₹{challenge['target_value']:,.0f}\nRank #{user_rank} 💪\n#EarnAura #FinancialChallenge"
            
            share_content["instagram"] = {
                "story_text": story_text,
                "hashtags": ["EarnAura", "FinancialGoals", "Savings", "Challenge", "StudentFinance"]
            }
        
        elif share_type == "twitter":
            if participant["is_completed"]:
                tweet = f"🎉 Just completed the '{challenge['title']}' challenge! Saved ₹{participant['current_progress']:,.0f} and ranked #{user_rank}! 💪 Building better financial habits with @EarnAura 📱 {challenge_url} #FinancialGoals #Savings"
            else:
                tweet = f"🚀 {progress_percentage:.0f}% through the '{challenge['title']}' challenge! Currently at ₹{participant['current_progress']:,.0f}/₹{challenge['target_value']:,.0f} (Rank #{user_rank}) 📊 Join me on @EarnAura! 💪 {challenge_url} #FinancialChallenge"
            
            tweet_text = tweet[:280]  # Twitter character limit
            encoded_tweet = tweet_text.replace(' ', '%20').replace('\n', '%0A')
            share_content["twitter"] = {
                "text": tweet_text,
                "url": f"https://twitter.com/intent/tweet?text={encoded_tweet}"
            }
        
        elif share_type == "linkedin":
            if participant["is_completed"]:
                post = f"Excited to share that I just completed the '{challenge['title']}' financial challenge! 🎉\n\n"
                post += f"✅ Target: ₹{challenge['target_value']:,.0f}\n"
                post += f"✅ Achieved: ₹{participant['current_progress']:,.0f}\n"
                post += f"✅ Final Rank: #{user_rank}\n\n"
                post += f"Building disciplined financial habits is crucial for long-term success. Proud to be part of the EarnAura community that's making financial literacy accessible to students across India! 💪\n\n"
                post += f"#FinancialLiteracy #StudentFinance #PersonalFinance #Goals #EarnAura"
            else:
                post = f"Currently {progress_percentage:.0f}% through the '{challenge['title']}' financial challenge! 📊\n\n"
                post += f"Progress: ₹{participant['current_progress']:,.0f} / ₹{challenge['target_value']:,.0f}\n"
                post += f"Current Rank: #{user_rank}\n\n"
                post += f"Consistency in financial habits is key to building wealth. Every small step counts toward achieving bigger goals! 💪\n\n"
                post += f"Join the challenge: {challenge_url}\n\n"
                post += f"#FinancialGoals #PersonalFinance #Savings #StudentFinance #EarnAura"
            
            share_content["linkedin"] = {
                "text": post,
                "url": f"https://www.linkedin.com/sharing/share-offsite/?url={challenge_url}"
            }
        
        # Log sharing activity
        await db.challenge_shares.insert_one({
            "challenge_id": challenge_id,
            "user_id": current_user["id"],
            "platform": share_type,
            "shared_at": datetime.now(timezone.utc),
            "progress_at_share": participant["current_progress"]
        })
        
        # Award experience points for sharing
        await db.users.update_one(
            {"_id": current_user["id"]},
            {"$inc": {"experience_points": 10}}  # 10 points for sharing
        )
        
        return share_content
        
    except Exception as e:
        logger.error(f"Generate share content error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate share content")

@api_router.put("/challenges/{challenge_id}")
@limiter.limit("5/minute")
async def update_challenge(request: Request, challenge_id: str, challenge_data: ChallengeUpdate, current_user_id: str = Depends(get_current_user)):
    """Update a challenge (only creator or admin can edit)"""
    try:
        db = await get_database()
        
        # Get challenge to check permissions
        challenge = await db.challenges.find_one({"id": challenge_id})
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        # Check if user is creator or admin
        user = await get_user_by_id(current_user_id)
        is_creator = challenge["created_by"] == current_user_id
        is_admin = user.get("role") == "admin" if user else False
        
        if not (is_creator or is_admin):
            raise HTTPException(status_code=403, detail="You can only edit your own challenges")
        
        # Prepare update data (only non-None fields)
        update_data = {}
        for field, value in challenge_data.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Add updated timestamp
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        # Update challenge
        result = await db.challenges.update_one(
            {"id": challenge_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Challenge not found or no changes made")
        
        return {"message": "Challenge updated successfully", "challenge_id": challenge_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update challenge error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update challenge")

@api_router.delete("/challenges/{challenge_id}")
@limiter.limit("5/minute")
async def delete_challenge(request: Request, challenge_id: str, current_user_id: str = Depends(get_current_user)):
    """Delete a challenge (only creator or admin can delete)"""
    try:
        db = await get_database()
        
        # Get challenge to check permissions
        challenge = await db.challenges.find_one({"id": challenge_id})
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        # Check if user is creator or admin
        user = await get_user_by_id(current_user_id)
        is_creator = challenge["created_by"] == current_user_id
        is_admin = user.get("role") == "admin" if user else False
        
        if not (is_creator or is_admin):
            raise HTTPException(status_code=403, detail="You can only delete your own challenges")
        
        # Check if challenge has participants (prevent deletion if people have joined)
        participant_count = await db.challenge_participants.count_documents({"challenge_id": challenge_id})
        if participant_count > 0 and not is_admin:
            raise HTTPException(status_code=400, detail="Cannot delete challenge with participants (admin override required)")
        
        # Delete challenge and all related data
        await db.challenges.delete_one({"id": challenge_id})
        
        # Delete all participations
        await db.challenge_participants.delete_many({"challenge_id": challenge_id})
        
        # Delete moderation records if any
        await db.challenge_moderation.delete_many({"challenge_id": challenge_id})
        
        return {"message": "Challenge deleted successfully", "challenge_id": challenge_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete challenge error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete challenge")

@api_router.post("/challenges/admin/approve/{challenge_id}")
@limiter.limit("10/minute")
async def approve_challenge(request: Request, challenge_id: str, current_user: str = Depends(get_current_user)):
    """Admin endpoint to approve user-created challenges"""
    try:
        # Check if user is admin
        user = await get_user_by_id(current_user)
        if not user or user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        db = await get_database()
        
        # Update challenge status
        result = await db.challenges.update_one(
            {"id": challenge_id},
            {"$set": {"is_active": True, "approved_at": datetime.now(timezone.utc), "approved_by": current_user}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        # Update moderation record
        await db.challenge_moderation.update_one(
            {"challenge_id": challenge_id},
            {"$set": {"status": "approved", "reviewed_at": datetime.now(timezone.utc), "reviewed_by": current_user}}
        )
        
        return {"message": "Challenge approved successfully"}
        
    except Exception as e:
        logger.error(f"Approve challenge error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to approve challenge")

@api_router.post("/challenges/{challenge_id}/reject")
@limiter.limit("10/minute")
async def reject_challenge(request: Request, challenge_id: str, reject_data: ChallengeReject, current_user: Dict[str, Any] = Depends(get_current_super_admin)):
    """Admin endpoint to reject user-created challenges with reason"""
    try:
        # Check if user is admin
        user = await get_user_by_id(current_user)
        if not user or user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        rejection_reason = reject_data.rejection_reason.strip()
        
        db = await get_database()
        
        # Check if challenge exists and is not already approved
        challenge = await db.challenges.find_one({"id": challenge_id})
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
            
        if challenge.get("is_active", False):
            raise HTTPException(status_code=400, detail="Cannot reject an already approved challenge")
        
        # Update moderation record with rejection
        result = await db.challenge_moderation.update_one(
            {"challenge_id": challenge_id},
            {
                "$set": {
                    "status": "rejected",
                    "rejection_reason": rejection_reason,
                    "reviewed_at": datetime.now(timezone.utc),
                    "reviewed_by": current_user
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Challenge moderation record not found")
        
        return {"message": "Challenge rejected successfully", "rejection_reason": rejection_reason}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reject challenge error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reject challenge")

@api_router.get("/challenges/my-created")
@limiter.limit("20/minute")
async def get_my_created_challenges(request: Request, current_user: Dict[str, Any] = Depends(get_current_super_admin)):
    """Get challenges created by the current user with their moderation status"""
    try:
        db = await get_database()
        
        # Get challenges created by current user
        created_challenges = await db.challenges.find({
            "created_by": current_user
        }).sort("created_at", -1).to_list(None)
        
        challenges_with_status = []
        for challenge in created_challenges:
            # Get moderation status if exists
            moderation = await db.challenge_moderation.find_one({
                "challenge_id": challenge["id"]
            })
            
            # Determine status
            if challenge.get("is_active", False):
                status = "approved"
                rejection_reason = None
            elif moderation:
                status = moderation.get("status", "pending_review")
                rejection_reason = moderation.get("rejection_reason", None)
            else:
                status = "approved"  # Admin challenges are auto-approved
                rejection_reason = None
            
            # Calculate days remaining or days since ended
            now = datetime.now(timezone.utc)
            end_date = challenge.get("end_date")
            if end_date:
                if isinstance(end_date, str):
                    end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                days_remaining = (end_date - now).days
                is_expired = end_date < now
            else:
                days_remaining = 0
                is_expired = True
            
            # Get participant count
            participant_count = await db.challenge_participants.count_documents({
                "challenge_id": challenge["id"]
            })
            
            challenge_data = {
                "challenge": challenge,
                "status": status,
                "rejection_reason": rejection_reason,
                "days_remaining": days_remaining,
                "is_expired": is_expired,
                "participant_count": participant_count,
                "reviewed_at": moderation.get("reviewed_at") if moderation else None
            }
            
            challenges_with_status.append(challenge_data)
        
        return {"created_challenges": challenges_with_status}
        
    except Exception as e:
        logger.error(f"Get my created challenges error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get created challenges")

# Helper function to update all active challenges for a user
async def update_user_challenge_progress(user_id: str):
    """Update progress for all active challenges the user is participating in"""
    try:
        db = await get_database()
        
        # Get all active challenge participations for this user
        participations = await db.challenge_participants.find({
            "user_id": user_id,
            "is_completed": False
        }).to_list(None)
        
        for participation in participations:
            # Check if challenge is still active
            challenge = await db.challenges.find_one({
                "id": participation["challenge_id"],
                "is_active": True,
                "end_date": {"$gte": datetime.now(timezone.utc)}
            })
            
            if challenge:
                await update_challenge_progress(participation["challenge_id"], user_id)
                
    except Exception as e:
        logger.error(f"Update user challenge progress error: {str(e)}")

# Background function to update challenge progress
async def update_challenge_progress(challenge_id: str, user_id: str):
    """Update user's progress in a challenge based on their activity"""
    try:
        db = await get_database()
        
        challenge = await db.challenges.find_one({"id": challenge_id})
        if not challenge:
            return
        
        participant = await db.challenge_participants.find_one({
            "challenge_id": challenge_id,
            "user_id": user_id
        })
        
        if not participant:
            return
        
        new_progress = 0.0
        
        if challenge["challenge_type"] == "savings":
            # Calculate total savings (income - expenses) since challenge start
            start_date = participant["joined_at"]
            
            # Get income transactions
            income_pipeline = [
                {"$match": {
                    "user_id": user_id,
                    "type": "income",
                    "timestamp": {"$gte": start_date}
                }},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]
            income_result = await db.transactions.aggregate(income_pipeline).to_list(None)
            total_income = income_result[0]["total"] if income_result else 0.0
            
            # Get expense transactions
            expense_pipeline = [
                {"$match": {
                    "user_id": user_id,
                    "type": "expense",
                    "timestamp": {"$gte": start_date}
                }},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]
            expense_result = await db.transactions.aggregate(expense_pipeline).to_list(None)
            total_expenses = expense_result[0]["total"] if expense_result else 0.0
            
            new_progress = max(0, total_income - total_expenses)
            
        elif challenge["challenge_type"] == "goals":
            # Count completed financial goals since challenge start
            start_date = participant["joined_at"]
            completed_goals = await db.financial_goals.count_documents({
                "user_id": user_id,
                "is_completed": True,
                "updated_at": {"$gte": start_date}
            })
            new_progress = float(completed_goals)
        
        # Update progress
        is_completed = new_progress >= challenge["target_value"]
        completion_date = datetime.now(timezone.utc) if is_completed and not participant["is_completed"] else participant.get("completion_date")
        
        await db.challenge_participants.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            {
                "$set": {
                    "current_progress": new_progress,
                    "is_completed": is_completed,
                    "completion_date": completion_date
                }
            }
        )
        
        # Award completion rewards
        if is_completed and not participant["is_completed"]:
            await db.users.update_one(
                {"_id": user_id},
                {"$inc": {"experience_points": challenge["reward_points"]}}
            )
            
            # Create achievement for challenge completion
            gamification = await get_gamification_service()
            await gamification.create_milestone_achievement(user_id, "challenge_completed", {
                "challenge_id": challenge_id,
                "challenge_title": challenge["title"],
                "target_value": challenge["target_value"],
                "final_progress": new_progress
            })
        
    except Exception as e:
        logger.error(f"Update challenge progress error: {str(e)}")

# ===== FRIEND NETWORK & CAMPUS CHALLENGES SYSTEM =====

@api_router.post("/friends/invite")
@limiter.limit("10/hour")
async def invite_friend(request: Request, invite_data: FriendInviteRequest, current_user: Dict[str, Any] = Depends(get_current_user_dict)):
    """Send friend invitation via referral code"""
    try:
        db = await get_database()
        user = current_user
        user_id = current_user["id"]  # Fix: Extract user_id from current_user dict
        
        # Check invitation limits
        current_date = datetime.now(timezone.utc)
        current_month = current_date.month
        current_year = current_date.year
        
        # Get or create invitation stats
        invite_stats = await db.user_invitation_stats.find_one({"user_id": user_id})
        if not invite_stats:
            invite_stats = UserInvitationStats(user_id=user_id).dict()
            await db.user_invitation_stats.insert_one(invite_stats)
        
        # Reset monthly count if new month
        if invite_stats["current_month"] != current_month or invite_stats["current_year"] != current_year:
            await db.user_invitation_stats.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "monthly_invites_sent": 0,
                        "current_month": current_month,
                        "current_year": current_year,
                        "last_reset_date": current_date
                    }
                }
            )
            invite_stats["monthly_invites_sent"] = 0
        
        # Check if user has reached monthly limit
        if invite_stats["monthly_invites_sent"] >= invite_stats["monthly_invites_limit"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Monthly invitation limit reached ({invite_stats['monthly_invites_limit']} invites). Limit resets next month or unlock more through achievements."
            )
        
        # Generate unique referral code
        referral_code = f"EARN{user_id[:4].upper()}{uuid.uuid4().hex[:6].upper()}"
        
        # Create invitation record
        invitation = FriendInvitation(
            inviter_id=user_id,
            invitee_email=invite_data.email,
            invitee_phone=invite_data.phone,
            referral_code=referral_code,
            expires_at=current_date + timedelta(days=30)
        )
        
        await db.friend_invitations.insert_one(invitation.dict())
        
        # Update invitation stats
        await db.user_invitation_stats.update_one(
            {"user_id": user_id},
            {"$inc": {"monthly_invites_sent": 1}}
        )
        
        # Create notification for inviter
        await create_notification(
            user_id, 
            "friend_invited",
            f"Friend invitation sent!",
            f"You've sent an invitation using code {referral_code}. Share it to earn points when they join!",
            related_id=invitation.id
        )
        
        return {
            "message": "Friend invitation sent successfully",
            "referral_code": referral_code,
            "invites_left": invite_stats["monthly_invites_limit"] - invite_stats["monthly_invites_sent"] - 1
        }
        
    except Exception as e:
        logger.error(f"Invite friend error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send invitation")

@api_router.get("/friends")
@limiter.limit("20/minute")
async def get_friends(
    request: Request, 
    current_user: Dict[str, Any] = Depends(get_current_user_dict),
    skip: int = 0,
    limit: int = 50
):
    """
    Get user's friends list with pagination
    
    ENHANCED WITH:
    - Pagination support
    - Optimized N+1 query resolution (single aggregation query)
    - Gamification data included
    """
    try:
        db = await get_database()
        user_id = current_user["id"]
        
        # Use optimized aggregation query (fixes N+1 problem)
        # This replaces the loop that fetches each friend individually
        friends_optimized = await get_friends_with_details_optimized(user_id, limit=limit)
        
        # Transform data to match expected format
        friends_list = []
        for item in friends_optimized:
            friend_data = item.get("friend", {})
            gamification = item.get("gamification", {})
            
            friends_list.append({
                "friend_id": item.get("friend_id"),
                "full_name": friend_data.get("full_name", "Unknown"),
                "avatar": friend_data.get("avatar", "boy"),
                "university": friend_data.get("university"),
                "current_streak": gamification.get("current_streak", 0),
                "total_earnings": 0.0,  # Can be added to aggregation if needed
                "friendship_points": item.get("points_earned", 0),
                "friendship_created": item.get("created_at"),
                "level": gamification.get("level", 1),
                "badges_count": len(gamification.get("badges", []))
            })
        
        return {
            "friends": friends_list,
            "total_friends": len(friends_list)
        }
        
    except Exception as e:
        logger.error(f"Get friends error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get friends list")

@api_router.get("/friends/invitations")
@limiter.limit("20/minute")
async def get_invitations(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dict)):
    """Get sent and received invitations"""
    try:
        db = await get_database()
        user_id = current_user.get("id")
        
        # Get sent invitations
        sent_invitations = await db.friend_invitations.find({
            "inviter_id": user_id
        }).sort("invited_at", -1).to_list(None)
        
        # Get invitation stats
        invite_stats = await db.user_invitation_stats.find_one({"user_id": user_id})
        if not invite_stats:
            invite_stats = UserInvitationStats(user_id=user_id).dict()
            await db.user_invitation_stats.insert_one(invite_stats)
        
        return {
            "sent_invitations": sent_invitations,
            "invitation_stats": {
                "monthly_sent": invite_stats["monthly_invites_sent"],
                "monthly_limit": invite_stats["monthly_invites_limit"],
                "remaining": invite_stats["monthly_invites_limit"] - invite_stats["monthly_invites_sent"],
                "total_successful": invite_stats["total_successful_invites"],
                "bonus_points_earned": invite_stats["invitation_bonus_points"]
            }
        }
        
    except Exception as e:
        logger.error(f"Get invitations error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get invitations")

@api_router.post("/friends/accept-invitation")
@limiter.limit("5/minute")
async def accept_friend_invitation(request: Request, referral_code: str, current_user: Dict[str, Any] = Depends(get_current_user_dict)):
    """Accept friend invitation using referral code"""
    try:
        db = await get_database()
        user_id = current_user["id"]
        
        # First try to find formal invitation
        invitation = await db.friend_invitations.find_one({
            "referral_code": referral_code,
            "status": "pending"
        })
        
        inviter_id = None
        
        if invitation:
            # Check if invitation is expired
            if invitation.get("expires_at") and invitation["expires_at"] < datetime.now(timezone.utc):
                await db.friend_invitations.update_one(
                    {"_id": invitation["_id"]},
                    {"$set": {"status": "expired"}}
                )
                raise HTTPException(status_code=400, detail="Invitation has expired")
            
            inviter_id = invitation["inviter_id"]
        else:
            # If no formal invitation, check if it's a referral code from referral system
            referral_program = await db.referral_programs.find_one({"referral_code": referral_code})
            if referral_program:
                inviter_id = referral_program["referrer_id"]
            else:
                raise HTTPException(status_code=404, detail="Invalid referral code or invitation")
        
        # Check if they're not trying to add themselves
        if inviter_id == user_id:
            raise HTTPException(status_code=400, detail="Cannot send friend invitation to yourself")
        
        # Check if friendship already exists
        existing_friendship = await db.friendships.find_one({
            "$or": [
                {"user1_id": inviter_id, "user2_id": user_id},
                {"user1_id": user_id, "user2_id": inviter_id}
            ]
        })
        
        if existing_friendship:
            raise HTTPException(status_code=400, detail="You're already friends with this user")
        
        # Create friendship
        friendship = {
            "id": str(uuid.uuid4()),
            "user1_id": inviter_id,
            "user2_id": user_id,
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "connection_type": "manual_invitation",  # Different from automatic referral signup
            "automatic": False
        }
        await db.friendships.insert_one(friendship)
        
        # Update invitation status (only if it was a formal invitation)
        if invitation:
            await db.friend_invitations.update_one(
                {"_id": invitation["_id"]},
                {
                    "$set": {
                        "status": "accepted",
                        "accepted_at": datetime.now(timezone.utc)
                    }
                }
            )
        
        # Reward points to both users
        inviter_points = 50  # Points for successful referral
        invitee_points = 25  # Welcome bonus for new friend
        
        await db.users.update_one(
            {"id": inviter_id},
            {"$inc": {"experience_points": inviter_points, "achievement_points": inviter_points}}
        )
        
        await db.users.update_one(
            {"id": user_id},
            {"$inc": {"experience_points": invitee_points, "achievement_points": invitee_points}}
        )
        
        # Update inviter's successful invitations count
        await db.user_invitation_stats.update_one(
            {"user_id": inviter_id},
            {
                "$inc": {
                    "total_successful_invites": 1,
                    "invitation_bonus_points": inviter_points
                }
            }
        )
        
        # Create notifications
        inviter = await db.users.find_one({"id": inviter_id})
        await create_notification(
            inviter_id,
            "friend_joined",
            f"🎉 {current_user['full_name']} accepted your invitation!",
            f"You earned {inviter_points} points for successful referral.",
            related_id=friendship["id"]
        )
        
        await create_notification(
            user_id,
            "friend_joined",
            f"🤝 Welcome to EarnAura friends network!",
            f"You're now friends with {inviter['full_name']} and earned {invitee_points} welcome points!",
            related_id=friendship["id"]
        )
        
        # Check for friendship milestone badges
        gamification = await get_gamification_service()
        await gamification.check_and_award_badges(inviter_id, "friend_invited", {
            "successful_invites": (await db.user_invitation_stats.find_one({"user_id": inviter_id}))["total_successful_invites"]
        })
        
        return {
            "message": "Friend invitation accepted successfully",
            "friendship_id": friendship.id,
            "points_earned": invitee_points
        }
        
    except Exception as e:
        logger.error(f"Accept invitation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to accept invitation")

@api_router.get("/friends/suggestions")
@limiter.limit("20/minute")
async def get_friend_suggestions(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dict)):
    """Get campus-specific friend suggestions"""
    try:
        db = await get_database()
        user = current_user
        user_university = user.get("university")
        
        if not user_university:
            return {"suggestions": [], "message": "Add your university to get campus friend suggestions"}
        
        # Get existing friends to exclude them
        existing_friends = await db.friendships.find({
            "$or": [
                {"user1_id": user["id"]},
                {"user2_id": user["id"]}
            ]
        }).to_list(None)
        
        excluded_user_ids = [user["id"]]  # Exclude self
        for friendship in existing_friends:
            friend_id = friendship["user2_id"] if friendship["user1_id"] == user["id"] else friendship["user1_id"]
            excluded_user_ids.append(friend_id)
        
        # Get pending invitations to exclude them too
        pending_invites = await db.friend_invitations.find({
            "$or": [
                {"inviter_id": user["id"], "status": "pending"},
                {"email": user.get("email"), "status": "pending"},
                {"phone": user.get("phone"), "status": "pending"}
            ]
        }).to_list(None)
        
        for invite in pending_invites:
            if invite.get("invitee_user_id"):
                excluded_user_ids.append(invite["invitee_user_id"])
        
        # Find campus friends with similar activity
        suggestions = await db.users.find({
            "university": user_university,
            "id": {"$nin": excluded_user_ids},
            "is_active": True
        }).limit(10).to_list(None)
        
        # Enhance suggestions with user stats
        enhanced_suggestions = []
        for suggestion in suggestions:
            # Get user's gamification stats
            user_stats = await db.users.find_one({"id": suggestion["id"]})
            if user_stats:
                enhanced_suggestion = {
                    "id": suggestion["id"],
                    "full_name": suggestion.get("full_name", "User"),
                    "avatar": suggestion.get("avatar", "man"),
                    "university": suggestion.get("university"),
                    "skills": suggestion.get("skills", []),
                    "current_streak": user_stats.get("current_streak", 0),
                    "experience_points": user_stats.get("experience_points", 0),
                    "total_savings": user_stats.get("net_savings", 0),
                    "level": user_stats.get("level", 1),
                    "title": user_stats.get("title", "Beginner"),
                    "mutual_skills": len(set(user.get("skills", [])) & set(suggestion.get("skills", []))),
                    "suggestion_reason": f"Same university ({user_university})"
                }
                
                # Add suggestion reason based on similarities
                if enhanced_suggestion["mutual_skills"] > 0:
                    enhanced_suggestion["suggestion_reason"] += f" • {enhanced_suggestion['mutual_skills']} shared skills"
                
                if enhanced_suggestion["current_streak"] > 7:
                    enhanced_suggestion["suggestion_reason"] += f" • Active tracker ({enhanced_suggestion['current_streak']} day streak)"
                
                enhanced_suggestions.append(enhanced_suggestion)
        
        # Sort by relevance (mutual skills, then streak, then points)
        enhanced_suggestions.sort(key=lambda x: (
            x["mutual_skills"],
            x["current_streak"],
            x["experience_points"]
        ), reverse=True)
        
        return {
            "suggestions": enhanced_suggestions,
            "university": user_university,
            "total_campus_users": await db.users.count_documents({"university": user_university})
        }
        
    except Exception as e:
        logger.error(f"Get friend suggestions error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get friend suggestions")

# ===== REAL-TIME FRIEND ACTIVITY ENDPOINTS =====

@api_router.get("/friends/recent-activity")
@limiter.limit("30/minute")  
async def get_recent_friend_activity(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dict)):
    """Get recent activity from friends for real-time updates"""
    try:
        db = await get_database()
        user_id = current_user["id"]
        
        # Get user's friends
        friendships = await db.friendships.find({
            "$or": [
                {"user1_id": user_id, "status": "active"},
                {"user2_id": user_id, "status": "active"}
            ]
        }).to_list(None)
        
        friend_ids = []
        for friendship in friendships:
            friend_id = friendship["user2_id"] if friendship["user1_id"] == user_id else friendship["user1_id"]
            friend_ids.append(friend_id)
        
        if not friend_ids:
            return {
                "recent_activities": [],
                "friend_count": 0,
                "message": "No friends yet! Share your referral code to connect with friends."
            }
        
        # Get recent friend activities (last 7 days)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        
        # Get recent transactions from friends
        recent_activities = []
        
        # Friend milestone achievements
        milestones = await db.achievements.find({
            "user_id": {"$in": friend_ids},
            "created_at": {"$gte": seven_days_ago}
        }).sort("created_at", -1).limit(10).to_list(None)
        
        for milestone in milestones:
            friend = await db.users.find_one({"id": milestone["user_id"]})
            if friend:
                recent_activities.append({
                    "type": "milestone_achieved",
                    "friend_name": friend.get("full_name", "Friend"),
                    "friend_avatar": friend.get("avatar", "man"),
                    "friend_id": milestone["user_id"],
                    "activity": f"achieved {milestone.get('milestone_type', 'milestone')}",
                    "description": milestone.get("description", "New milestone unlocked!"),
                    "timestamp": milestone["created_at"],
                    "emoji": "🏆"
                })
        
        # Friend referral connections (new friends joining)
        new_friendships = await db.friendships.find({
            "$or": [
                {"user1_id": {"$in": friend_ids}, "created_at": {"$gte": seven_days_ago}},
                {"user2_id": {"$in": friend_ids}, "created_at": {"$gte": seven_days_ago}}
            ],
            "automatic": True  # Only show automatic referral-based friendships
        }).sort("created_at", -1).limit(5).to_list(None)
        
        for friendship in new_friendships:
            # Determine which friend this relates to
            friend_in_network_id = None
            new_friend_id = None
            
            if friendship["user1_id"] in friend_ids:
                friend_in_network_id = friendship["user1_id"]
                new_friend_id = friendship["user2_id"]
            elif friendship["user2_id"] in friend_ids:
                friend_in_network_id = friendship["user2_id"] 
                new_friend_id = friendship["user1_id"]
            
            if friend_in_network_id and new_friend_id != user_id:  # Don't show user's own connections
                friend = await db.users.find_one({"id": friend_in_network_id})
                new_friend = await db.users.find_one({"id": new_friend_id})
                
                if friend and new_friend:
                    recent_activities.append({
                        "type": "friend_referred",
                        "friend_name": friend.get("full_name", "Friend"),
                        "friend_avatar": friend.get("avatar", "man"), 
                        "friend_id": friend_in_network_id,
                        "activity": f"referred {new_friend.get('full_name', 'someone new')}",
                        "description": f"Growing the network! 🌟",
                        "timestamp": friendship["created_at"],
                        "emoji": "🤝"
                    })
        
        # Sort all activities by timestamp
        recent_activities.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Get friend stats for summary
        friend_stats = await db.users.find({
            "id": {"$in": friend_ids}
        }).to_list(None)
        
        total_friend_savings = sum(friend.get("net_savings", 0) for friend in friend_stats)
        avg_friend_streak = sum(friend.get("current_streak", 0) for friend in friend_stats) / len(friend_stats) if friend_stats else 0
        
        return {
            "recent_activities": recent_activities[:15],  # Limit to 15 most recent
            "friend_count": len(friend_ids),
            "network_stats": {
                "total_friends": len(friend_ids),
                "total_network_savings": total_friend_savings,
                "average_streak": round(avg_friend_streak, 1),
                "most_active_today": len([f for f in friend_stats if f.get("last_activity_date") and 
                                        f["last_activity_date"].date() == datetime.now().date()])
            },
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get recent friend activity error: {str(e)}")
        return {
            "recent_activities": [],
            "friend_count": 0,
            "error": "Unable to load friend activities"
        }

@api_router.get("/friends/live-stats")
@limiter.limit("60/minute")  # Higher limit for live data
async def get_live_friend_stats(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dict)):
    """Get live friend statistics for real-time dashboard updates"""
    try:
        db = await get_database()
        user_id = current_user["id"]
        
        # Get friends count
        friends_count = await db.friendships.count_documents({
            "$or": [
                {"user1_id": user_id, "status": "active"},
                {"user2_id": user_id, "status": "active"}
            ]
        })
        
        # Get pending invitations (sent by user)
        pending_invitations = await db.friend_invitations.count_documents({
            "inviter_id": user_id,
            "status": "pending"
        })
        
        # Get new friend requests (for user to accept)
        # This would be referral codes shared by others that user can accept
        
        # Get referral stats
        referral_stats = await db.referral_programs.find_one({"referrer_id": user_id})
        total_referrals = referral_stats.get("total_referrals", 0) if referral_stats else 0
        
        # Recent friend activity count (last 24 hours)
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        recent_activity_count = await db.achievements.count_documents({
            "user_id": {"$ne": user_id},  # Exclude user's own activities
            "created_at": {"$gte": yesterday}
        })
        
        return {
            "friends_count": friends_count,
            "pending_invitations": pending_invitations,
            "total_referrals": total_referrals,
            "recent_friend_activities": recent_activity_count,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get live friend stats error: {str(e)}")
        return {
            "friends_count": 0,
            "pending_invitations": 0,
            "total_referrals": 0,
            "recent_friend_activities": 0,
            "error": "Unable to load friend statistics"
        }

@api_router.post("/group-challenges")
@limiter.limit("5/hour")
async def create_group_challenge(request: Request, challenge_data: GroupChallengeCreateRequest, current_admin: Dict[str, Any] = Depends(get_current_admin_with_challenge_permissions)):
    """Create a new group savings challenge (System Admin, Campus Admin, or Club Admin)"""
    try:
        db = await get_database()
        
        current_user = current_admin["user_id"]
        is_system_admin = current_admin.get("is_system_admin", False)
        
        # Check monthly limit for non-system admins
        if not is_system_admin:
            current_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            challenges_this_month = await db.group_challenges.count_documents({
                "created_by": current_user,
                "created_at": {"$gte": current_month}
            })
            
            max_limit = current_admin.get("max_competitions_per_month", current_admin.get("max_challenges_per_month", 5))
            if challenges_this_month >= max_limit:
                raise HTTPException(
                    status_code=429,
                    detail=f"Monthly group challenge limit reached ({max_limit})"
                )
        
        # Get user details for university restriction
        user = await get_user_by_id(current_user)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Calculate dates
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=challenge_data.duration_days)
        
        # Set university restriction if requested
        university = user.get("university") if challenge_data.university_only else None
        
        # Calculate group target
        group_target = challenge_data.target_amount_per_person * challenge_data.max_participants
        
        # Create group challenge
        group_challenge = GroupChallenge(
            title=challenge_data.title,
            description=challenge_data.description,
            challenge_type=challenge_data.challenge_type,
            target_amount_per_person=challenge_data.target_amount_per_person,
            group_target_amount=group_target,
            duration_days=challenge_data.duration_days,
            max_participants=challenge_data.max_participants,
            university=university,
            created_by=current_user,
            start_date=start_date,
            end_date=end_date
        )
        
        await db.group_challenges.insert_one(group_challenge.dict())
        
        # Auto-join creator as first participant
        participant = GroupChallengeParticipant(
            group_challenge_id=group_challenge.id,
            user_id=current_user,
            individual_target=challenge_data.target_amount_per_person
        )
        await db.group_challenge_participants.insert_one(participant.dict())
        
        # Update participant count
        await db.group_challenges.update_one(
            {"id": group_challenge.id},
            {"$inc": {"current_participants": 1}}
        )
        
        # Update admin statistics if applicable (campus admin or club admin)
        if not is_system_admin:
            await db.campus_admins.update_one(
                {"id": current_admin["id"]},
                {
                    "$inc": {"challenges_created": 1},
                    "$set": {"last_activity": datetime.now(timezone.utc)}
                }
            )
        
        # Create notification
        await create_notification(
            current_user,
            "challenge_created",
            f"Group Challenge Created: {group_challenge.title}",
            f"You've created a {challenge_data.duration_days}-day group challenge. Invite friends to join!",
            action_url=f"/group-challenges/{group_challenge.id}",
            related_id=group_challenge.id
        )
        
        return {
            "message": "Group challenge created successfully",
            "group_challenge": group_challenge.dict(),
            "participant_id": participant.id
        }
        
    except Exception as e:
        logger.error(f"Create group challenge error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create group challenge")

@api_router.get("/group-challenges")
@limiter.limit("20/minute")
async def get_group_challenges(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dict)):
    """Get available group challenges (campus-specific and open)"""
    try:
        db = await get_database()
        user = current_user
        user_university = user.get("university")
        
        # Build query - include open challenges and user's campus challenges
        query = {
            "is_active": True,
            "end_date": {"$gte": datetime.now(timezone.utc)},
            "$or": [
                {"university": None},  # Open to all
                {"university": user_university}  # Campus specific
            ]
        }
        
        # Get all active group challenges
        challenges = await db.group_challenges.find(query).sort("created_at", -1).to_list(None)
        
        challenges_with_status = []
        for challenge in challenges:
            # Check if user has already joined
            participation = await db.group_challenge_participants.find_one({
                "group_challenge_id": challenge["id"],
                "user_id": user["id"]
            })
            
            # Get creator info
            creator = await db.users.find_one({"id": challenge["created_by"]})
            
            # Calculate progress percentage
            total_progress = 0
            participants = await db.group_challenge_participants.find({
                "group_challenge_id": challenge["id"]
            }).to_list(None)
            
            for participant in participants:
                total_progress += participant.get("current_progress", 0)
            
            progress_percentage = min(100, (total_progress / challenge["group_target_amount"]) * 100) if challenge["group_target_amount"] > 0 else 0
            
            challenge_info = {
                **challenge,
                "is_joined": participation is not None,
                "user_progress": participation["current_progress"] if participation else 0.0,
                "spots_remaining": challenge["max_participants"] - challenge["current_participants"],
                "progress_percentage": round(progress_percentage, 1),
                "total_progress_amount": total_progress,
                "creator_name": creator["full_name"] if creator else "Unknown",
                "creator_university": creator.get("university") if creator else None,
                "is_campus_only": challenge.get("university") is not None,
                "participants_count": len(participants)
            }
            
            challenges_with_status.append(challenge_info)
        
        return {
            "group_challenges": challenges_with_status,
            "user_university": user_university
        }
        
    except Exception as e:
        logger.error(f"Get group challenges error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get group challenges")

@api_router.post("/group-challenges/{challenge_id}/join")
@limiter.limit("10/minute")
async def join_group_challenge(request: Request, challenge_id: str, current_user: Dict[str, Any] = Depends(get_current_user_dict)):
    """Join a group challenge"""
    try:
        db = await get_database()
        user_id = current_user["id"]
        
        # Check if challenge exists and is active
        challenge = await db.group_challenges.find_one({
            "id": challenge_id,
            "is_active": True,
            "end_date": {"$gte": datetime.now(timezone.utc)}
        })
        
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found or expired")
        
        # Check if user already joined
        existing_participation = await db.group_challenge_participants.find_one({
            "group_challenge_id": challenge_id,
            "user_id": user_id
        })
        
        if existing_participation:
            raise HTTPException(status_code=400, detail="You've already joined this challenge")
        
        # Check if challenge is full
        if challenge["current_participants"] >= challenge["max_participants"]:
            raise HTTPException(status_code=400, detail="Challenge is full")
        
        # Check university restrictions
        if challenge.get("university") and current_user.get("university") != challenge["university"]:
            raise HTTPException(status_code=400, detail="This challenge is restricted to specific campus students")
        
        # Join the challenge
        participant = GroupChallengeParticipant(
            group_challenge_id=challenge_id,
            user_id=user_id,
            individual_target=challenge["target_amount_per_person"]
        )
        await db.group_challenge_participants.insert_one(participant.dict())
        
        # Update participant count
        await db.group_challenges.update_one(
            {"id": challenge_id},
            {"$inc": {"current_participants": 1}}
        )
        
        # Notify all participants about new member
        participants = await db.group_challenge_participants.find({
            "group_challenge_id": challenge_id
        }).to_list(None)
        
        for participant_doc in participants:
            if participant_doc["user_id"] != user_id:  # Don't notify the joiner
                await create_notification(
                    participant_doc["user_id"],
                    "group_progress",
                    f"New member joined {challenge['title']}!",
                    f"{current_user['full_name']} joined your group challenge. Group now has {challenge['current_participants'] + 1} members.",
                    action_url=f"/group-challenges/{challenge_id}",
                    related_id=challenge_id
                )
        
        # Notify the joiner
        await create_notification(
            user_id,
            "challenge_invite",
            f"Joined Group Challenge: {challenge['title']}",
            f"Successfully joined! Target: ₹{challenge['target_amount_per_person']} in {challenge['duration_days']} days.",
            action_url=f"/group-challenges/{challenge_id}",
            related_id=challenge_id
        )
        
        return {
            "message": "Successfully joined group challenge",
            "participant_id": participant.id,
            "individual_target": challenge["target_amount_per_person"],
            "group_size": challenge["current_participants"] + 1
        }
        
    except Exception as e:
        logger.error(f"Join group challenge error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to join group challenge")

@api_router.get("/group-challenges/{challenge_id}")
@limiter.limit("20/minute")
async def get_group_challenge_details(request: Request, challenge_id: str, current_user: Dict[str, Any] = Depends(get_current_user_dict)):
    """Get detailed information about a specific group challenge"""
    try:
        db = await get_database()
        
        # Get challenge details
        challenge = await db.group_challenges.find_one({"id": challenge_id})
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        # Get all participants
        participants = await db.group_challenge_participants.find({
            "group_challenge_id": challenge_id
        }).sort("current_progress", -1).to_list(None)
        
        # Get participant details
        participants_info = []
        total_group_progress = 0
        
        for participant in participants:
            user = await db.users.find_one({"id": participant["user_id"]})
            if user:
                progress_percentage = min(100, (participant["current_progress"] / participant["individual_target"]) * 100) if participant["individual_target"] > 0 else 0
                total_group_progress += participant["current_progress"]
                
                participants_info.append({
                    "user_id": participant["user_id"],
                    "full_name": user["full_name"],
                    "avatar": user.get("avatar", "boy"),
                    "university": user.get("university"),
                    "individual_target": participant["individual_target"],
                    "current_progress": participant["current_progress"],
                    "progress_percentage": round(progress_percentage, 1),
                    "is_completed": participant["is_completed"],
                    "joined_at": participant["joined_at"],
                    "points_earned": participant.get("points_earned", 0)
                })
        
        # Calculate overall progress
        group_progress_percentage = min(100, (total_group_progress / challenge["group_target_amount"]) * 100) if challenge["group_target_amount"] > 0 else 0
        
        # Get creator info
        creator = await db.users.find_one({"id": challenge["created_by"]})
        
        # Check if current user is participant
        user_participation = next((p for p in participants_info if p["user_id"] == current_user["id"]), None)
        
        return {
            "challenge": challenge,
            "participants": participants_info,
            "creator": {
                "full_name": creator["full_name"] if creator else "Unknown",
                "avatar": creator.get("avatar", "boy") if creator else "boy"
            },
            "progress": {
                "total_amount": total_group_progress,
                "target_amount": challenge["group_target_amount"],
                "percentage": round(group_progress_percentage, 1),
                "completed_count": sum(1 for p in participants_info if p["is_completed"]),
                "total_participants": len(participants_info)
            },
            "user_participation": user_participation,
            "spots_remaining": challenge["max_participants"] - challenge["current_participants"],
            "days_remaining": max(0, (challenge["end_date"] - datetime.now(timezone.utc)).days)
        }
        
    except Exception as e:
        logger.error(f"Get group challenge details error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get challenge details")

@api_router.get("/notifications")
@limiter.limit("30/minute")
async def get_notifications(
    request: Request, 
    current_user: Dict[str, Any] = Depends(get_current_user_dict),
    skip: int = 0,
    limit: int = 20,
    unread_only: bool = False
):
    """
    Get user's notifications with pagination
    
    ENHANCED WITH:
    - Pagination support (skip/limit)
    - Filter by unread notifications
    - Optimized N+1 query resolution
    """
    try:
        user_id = current_user.get("id")

        # Use optimized pagination function (fixes N+1 query problem)
        paginated_notifications = await get_notifications_paginated(
            user_id=user_id,
            skip=skip,
            limit=limit,
            unread_only=unread_only
        )

        
        # Get notifications with filter
        db = await get_database()
    
        unread_count = await db.notifications.count_documents({
            "user_id": user_id,
            "is_read": False
        })
        
        
        return {
            "notifications": paginated_notifications["data"],
            "unread_count": unread_count,
            "pagination": {
                "total": paginated_notifications["total"],
                "skip": skip,
                "limit": limit,
                "has_more": paginated_notifications["has_more"],
                "page": paginated_notifications["page"],
                "total_pages": paginated_notifications["total_pages"]
            }
        }
        
    except Exception as e:
        logger.error(f"Get notifications error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get notifications")

@api_router.put("/notifications/{notification_id}/read")
@limiter.limit("30/minute")
async def mark_notification_read(request: Request, notification_id: str, current_user: Dict[str, Any] = Depends(get_current_user_dict)):
    """Mark notification as read"""
    try:
        db = await get_database()
        user_id = current_user.get("id")
        
        # Update notification
        result = await db.notifications.update_one(
            {
                "id": notification_id,
                "user_id": user_id,
                "is_read": False
            },
            {
                "$set": {
                    "is_read": True,
                    "read_at": datetime.now(timezone.utc)
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found or already read")
        
        return {"message": "Notification marked as read"}
        
    except Exception as e:
        logger.error(f"Mark notification read error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark notification as read")

@api_router.put("/notifications/mark-all-read")
@limiter.limit("10/minute")
async def mark_all_notifications_read(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dict)):
    """Mark all notifications as read"""
    try:
        db = await get_database()
        user_id = current_user.get("id")
        
        # Update all unread notifications
        result = await db.notifications.update_many(
            {
                "user_id": user_id,
                "is_read": False
            },
            {
                "$set": {
                    "is_read": True,
                    "read_at": datetime.now(timezone.utc)
                }
            }
        )
        
        return {
            "message": "All notifications marked as read",
            "updated_count": result.modified_count
        }
        
    except Exception as e:
        logger.error(f"Mark all notifications read error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark all notifications as read")


@api_router.get("/leaderboards/campus/{leaderboard_type}")
@limiter.limit("20/minute")
async def get_campus_leaderboards(
    request: Request, 
    leaderboard_type: str, 
    period: str = "monthly",
    current_user: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Get campus-specific leaderboards with college vs college comparison"""
    try:
        db = await get_database()
        user_university = current_user.get("university")
        
        if not user_university:
            raise HTTPException(status_code=400, detail="User must select a university to view campus leaderboards")
        
        # Get gamification service
        gamification = await get_gamification_service()
        
        # Get campus-specific leaderboard
        campus_leaderboard = await gamification.get_leaderboard(leaderboard_type, period, university=user_university)
        
        # Get top universities for comparison
        university_comparison = await get_university_comparison(leaderboard_type, period)
        
        # Get user's campus rank
        user_campus_rank = await gamification.get_user_rank(current_user["id"], leaderboard_type, university=user_university)
        user_global_rank = await gamification.get_user_rank(current_user["id"], leaderboard_type)
        
        return {
            "campus_leaderboard": campus_leaderboard,
            "university_comparison": university_comparison,
            "user_campus_rank": user_campus_rank,
            "user_global_rank": user_global_rank,
            "user_university": user_university
        }
        
    except Exception as e:
        logger.error(f"Get campus leaderboards error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get campus leaderboards")

# Helper function to create notifications
async def create_notification(user_id: str, notification_type: str, title: str, message: str, action_url: str = None, related_id: str = None):
    """Helper function to create notifications"""
    try:
        db = await get_database()
        
        notification = InAppNotification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            action_url=action_url,
            related_id=related_id
        )
        
        await db.notifications.insert_one(notification.dict())
        return notification.id
        
    except Exception as e:
        logger.error(f"Create notification error: {str(e)}")
        return None

# Helper function to update group challenge progress
async def update_group_challenge_progress(user_id: str):
    """Update user's progress in all active group challenges"""
    try:
        db = await get_database()
        
        # Get user's active group challenge participations
        participations = await db.group_challenge_participants.find({
            "user_id": user_id,
            "is_completed": False
        }).to_list(None)
        
        for participation in participations:
            # Check if challenge is still active
            challenge = await db.group_challenges.find_one({
                "id": participation["group_challenge_id"],
                "is_active": True,
                "end_date": {"$gte": datetime.now(timezone.utc)}
            })
            
            if not challenge:
                continue
            
            # Calculate new progress based on challenge type
            new_progress = await calculate_group_challenge_progress(
                user_id, 
                challenge["challenge_type"], 
                challenge["start_date"]
            )
            
            # Check if individual target is completed
            is_completed = new_progress >= participation["individual_target"]
            completion_date = datetime.now(timezone.utc) if is_completed and not participation["is_completed"] else participation.get("completion_date")
            
            # Update progress
            await db.group_challenge_participants.update_one(
                {"_id": participation["_id"]},
                {
                    "$set": {
                        "current_progress": new_progress,
                        "is_completed": is_completed,
                        "completion_date": completion_date
                    }
                }
            )
            
            # Award points if just completed
            if is_completed and not participation["is_completed"]:
                await db.group_challenge_participants.update_one(
                    {"_id": participation["_id"]},
                    {"$inc": {"points_earned": challenge["reward_points_per_person"]}}
                )
                
                await db.users.update_one(
                    {"id": user_id},
                    {"$inc": {"experience_points": challenge["reward_points_per_person"]}}
                )
                
                # Notify group members
                await notify_group_members_of_completion(challenge["id"], user_id, participation["individual_target"])
                
                # 🔥 REAL-TIME NOTIFICATION: Send personal completion notification
                try:
                    notification_service = await get_notification_service()
                    await notification_service.create_and_notify_in_app_notification(user_id, {
                        "type": "group_challenge_completed",
                        "title": "🎉 Challenge Target Reached!",
                        "message": f"Congratulations! You completed your target of ₹{participation['individual_target']:,.0f} in '{challenge['title']}'! Earned {challenge['reward_points_per_person']} points!",
                        "priority": "high",
                        "action_url": f"/group-challenges/{challenge['id']}",
                        "data": {
                            "challenge_id": challenge["id"],
                            "challenge_title": challenge["title"],
                            "target_amount": participation["individual_target"],
                            "points_earned": challenge["reward_points_per_person"]
                        }
                    })
                except Exception as e:
                    logger.error(f"Failed to send group challenge completion notification: {str(e)}")
            
            # 🔥 REAL-TIME NOTIFICATION: Send progress update for significant milestones
            elif not is_completed:
                try:
                    progress_percentage = (new_progress / participation["individual_target"] * 100) if participation["individual_target"] > 0 else 0
                    previous_progress = participation.get("current_progress", 0)
                    previous_percentage = (previous_progress / participation["individual_target"] * 100) if participation["individual_target"] > 0 else 0
                    
                    # Send notification for 25%, 50%, 75% milestones
                    milestones = [25, 50, 75]
                    for milestone in milestones:
                        if previous_percentage < milestone <= progress_percentage:
                            notification_service = await get_notification_service()
                            await notification_service.create_and_notify_in_app_notification(user_id, {
                                "type": "group_challenge_progress",
                                "title": f"📊 Challenge Progress: {milestone}%",
                                "message": f"You're {milestone}% towards your target in '{challenge['title']}'! Keep it up!",
                                "priority": "medium",
                                "action_url": f"/group-challenges/{challenge['id']}",
                                "data": {
                                    "challenge_id": challenge["id"],
                                    "challenge_title": challenge["title"],
                                    "current_progress": new_progress,
                                    "target_amount": participation["individual_target"],
                                    "progress_percentage": progress_percentage
                                }
                            })
                            break
                except Exception as e:
                    logger.error(f"Failed to send group challenge progress notification: {str(e)}")
        
    except Exception as e:
        logger.error(f"Update group challenge progress error: {str(e)}")

async def calculate_group_challenge_progress(user_id: str, challenge_type: str, start_date: datetime) -> float:
    """Calculate user's progress for group challenge based on type"""
    try:
        db = await get_database()
        
        if challenge_type == "group_savings":
            # Calculate total income since challenge start
            income_result = await db.transactions.aggregate([
                {
                    "$match": {
                        "user_id": user_id,
                        "type": "income",
                        "date": {"$gte": start_date}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_income": {"$sum": "$amount"}
                    }
                }
            ]).to_list(None)
            
            return income_result[0]["total_income"] if income_result else 0.0
            
        elif challenge_type == "group_streak":
            # Use current user streak (simplified)
            user = await db.users.find_one({"id": user_id})
            return user.get("current_streak", 0)
            
        elif challenge_type == "group_goals":
            # Count completed goals since challenge start
            goals_count = await db.financial_goals.count_documents({
                "user_id": user_id,
                "is_completed": True,
                "updated_at": {"$gte": start_date}
            })
            return float(goals_count)
        
        return 0.0
        
    except Exception as e:
        logger.error(f"Calculate group challenge progress error: {str(e)}")
        return 0.0

async def notify_group_members_of_completion(group_challenge_id: str, completed_user_id: str, target_amount: float):
    """Notify group members when someone completes their target"""
    try:
        db = await get_database()
        
        # Get challenge details
        challenge = await db.group_challenges.find_one({"id": group_challenge_id})
        if not challenge:
            return
            
        # Get completed user details
        completed_user = await db.users.find_one({"id": completed_user_id})
        if not completed_user:
            return
        
        # Get all other participants
        participants = await db.group_challenge_participants.find({
            "group_challenge_id": group_challenge_id,
            "user_id": {"$ne": completed_user_id}
        }).to_list(None)
        
        # Notify each participant with WebSocket notification
        notification_service = await get_notification_service()
        for participant in participants:
            try:
                await notification_service.create_and_notify_in_app_notification(
                    participant["user_id"], {
                        "type": "group_member_completed",
                        "title": f"🎉 Team Member Success!",
                        "message": f"{completed_user['full_name']} reached ₹{target_amount:,.0f} in '{challenge['title']}'! Keep going!",
                        "priority": "medium",
                        "action_url": f"/group-challenges/{group_challenge_id}",
                        "data": {
                            "challenge_id": group_challenge_id,
                            "challenge_title": challenge["title"],
                            "completed_user_name": completed_user["full_name"],
                            "target_amount": target_amount
                        }
                    }
                )
            except Exception as e:
                logger.error(f"Failed to send group member completion notification: {str(e)}")
        
    except Exception as e:
        logger.error(f"Notify group members error: {str(e)}")

async def get_university_comparison(leaderboard_type: str, period: str, limit: int = 10):
    """Get university comparison for campus leaderboards"""
    try:
        db = await get_database()
        
        # Get aggregated university data based on leaderboard type
        if leaderboard_type == "points":
            pipeline = [
                {"$match": {"university": {"$ne": None}}},
                {"$group": {
                    "_id": "$university",
                    "total_points": {"$sum": "$experience_points"},
                    "student_count": {"$sum": 1},
                    "avg_points": {"$avg": "$experience_points"}
                }}
            ]
        elif leaderboard_type == "savings":
            pipeline = [
                {"$match": {"university": {"$ne": None}}},
                {"$group": {
                    "_id": "$university",
                    "total_savings": {"$sum": "$net_savings"},
                    "student_count": {"$sum": 1},
                    "avg_savings": {"$avg": "$net_savings"}
                }}
            ]
        elif leaderboard_type == "streak":
            pipeline = [
                {"$match": {"university": {"$ne": None}}},
                {"$group": {
                    "_id": "$university",
                    "max_streak": {"$max": "$current_streak"},
                    "avg_streak": {"$avg": "$current_streak"},
                    "student_count": {"$sum": 1}
                }}
            ]
        else:
            return []
        
        # Execute aggregation
        results = await db.users.aggregate(pipeline).to_list(None)
        
        # Sort and format results
        if leaderboard_type == "points":
            results.sort(key=lambda x: x["total_points"], reverse=True)
        elif leaderboard_type == "savings":
            results.sort(key=lambda x: x["total_savings"], reverse=True)
        elif leaderboard_type == "streak":
            results.sort(key=lambda x: x["max_streak"], reverse=True)
        
        # Format and limit results
        formatted_results = []
        for i, result in enumerate(results[:limit]):
            formatted_results.append({
                "rank": i + 1,
                "university": result["_id"],
                "student_count": result["student_count"],
                **{k: v for k, v in result.items() if k not in ["_id", "student_count"]}
            })
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"Get university comparison error: {str(e)}")
        return []

# Helper functions for feature unlocks and calculations
async def get_user_total_income(user_id: str) -> float:
    """Calculate user's total income"""
    try:
        income_transactions = await db.transactions.find({
            "user_id": user_id,
            "type": "income"
        }).to_list(None)
        return sum(tx["amount"] for tx in income_transactions)
    except:
        return 0

async def get_user_total_savings(user_id: str) -> float:
    """Calculate user's total savings (income - expenses)"""
    try:
        income = await get_user_total_income(user_id)
        expense_transactions = await db.transactions.find({
            "user_id": user_id,
            "type": "expense"
        }).to_list(None)
        expenses = sum(tx["amount"] for tx in expense_transactions)
        return income - expenses
    except:
        return 0

# ================================================================================================
# PHASE 1: SOCIAL FEATURES IMPLEMENTATION
# ================================================================================================

# Real-time friend activity feed
@api_router.get("/social/friend-activity-feed")
@limiter.limit("30/minute")
async def get_friend_activity_feed(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    user_id: str = Depends(get_current_user)
):
    """Get real-time activity feed from friends"""
    try:
        # Get user's friends
        friends = await db.friends.find({
            "$or": [
                {"user_id": user_id},
                {"friend_id": user_id}
            ],
            "status": "accepted"
        }).to_list(None)
        
        friend_ids = []
        for friend in friends:
            friend_id = friend["friend_id"] if friend["user_id"] == user_id else friend["user_id"]
            friend_ids.append(friend_id)
        
        if not friend_ids:
            return {"activities": [], "total": 0}
        
        # Get recent activities from friends
        activities = []
        
        # Recent transactions
        recent_transactions = await db.transactions.find({
            "user_id": {"$in": friend_ids},
            "created_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=7)}
        }).sort("created_at", -1).limit(50).to_list(None)
        
        for tx in recent_transactions:
            user_info = await db.users.find_one({"user_id": tx["user_id"]})
            activities.append({
                "type": "transaction",
                "user_name": user_info.get("name", "Friend"),
                "user_avatar": user_info.get("avatar", "man"),
                "action": f"{'earned' if tx['type'] == 'income' else 'spent'} ₹{tx['amount']}",
                "details": f"on {tx['category']}",
                "timestamp": tx["created_at"],
                "amount": tx["amount"],
                "category": tx["category"]
            })
        
        # Recent achievements
        recent_achievements = await db.user_achievements.find({
            "user_id": {"$in": friend_ids},
            "earned_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=7)}
        }).sort("earned_at", -1).limit(30).to_list(None)
        
        for ach in recent_achievements:
            user_info = await db.users.find_one({"user_id": ach["user_id"]})
            activities.append({
                "type": "achievement",
                "user_name": user_info.get("name", "Friend"),
                "user_avatar": user_info.get("avatar", "man"),
                "action": f"unlocked achievement",
                "details": ach["achievement_name"],
                "timestamp": ach["earned_at"],
                "badge_icon": "🏆"
            })
        
        # Recent milestones
        recent_milestones = await db.user_milestones.find({
            "user_id": {"$in": friend_ids},
            "achieved_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=7)}
        }).sort("achieved_at", -1).limit(20).to_list(None)
        
        for milestone in recent_milestones:
            user_info = await db.users.find_one({"user_id": milestone["user_id"]})
            activities.append({
                "type": "milestone",
                "user_name": user_info.get("name", "Friend"),
                "user_avatar": user_info.get("avatar", "man"),
                "action": f"reached milestone",
                "details": f"{milestone['milestone_type']} of ₹{milestone.get('amount', 0)}",
                "timestamp": milestone["achieved_at"],
                "milestone_icon": "🎯"
            })
        
        # Sort by timestamp and paginate
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        paginated_activities = activities[offset:offset + limit]
        
        return {
            "activities": paginated_activities,
            "total": len(activities),
            "has_more": offset + limit < len(activities)
        }
        
    except Exception as e:
        logger.error(f"Friend activity feed error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get friend activity feed")

# Challenge friends to individual savings goals
@api_router.post("/social/challenge-friend")
@limiter.limit("10/minute")
async def challenge_friend_to_goal(
    request: Request,
    challenge_data: dict,
    user_id: str = Depends(get_current_user)
):
    """Challenge a friend to an individual savings goal"""
    try:
        friend_id = challenge_data.get("friend_id")
        goal_amount = challenge_data.get("goal_amount")
        goal_title = challenge_data.get("goal_title")
        duration_days = challenge_data.get("duration_days", 30)
        
        # Verify friendship
        friendship = await db.friends.find_one({
            "$or": [
                {"user_id": user_id, "friend_id": friend_id},
                {"user_id": friend_id, "friend_id": user_id}
            ],
            "status": "accepted"
        })
        
        if not friendship:
            raise HTTPException(status_code=400, detail="You are not friends with this user")
        
        # Create challenge
        challenge = {
            "challenge_id": str(uuid.uuid4()),
            "challenger_id": user_id,
            "challenged_id": friend_id,
            "goal_title": goal_title,
            "goal_amount": goal_amount,
            "duration_days": duration_days,
            "start_date": datetime.now(timezone.utc),
            "end_date": datetime.now(timezone.utc) + timedelta(days=duration_days),
            "status": "pending",
            "challenger_progress": 0,
            "challenged_progress": 0,
            "created_at": datetime.now(timezone.utc)
        }
        
        await db.friend_challenges.insert_one(challenge)
        
        # Create notification for challenged friend
        notification = {
            "notification_id": str(uuid.uuid4()),
            "user_id": friend_id,
            "type": "friend_challenge",
            "title": "New Savings Challenge!",
            "message": f"Your friend challenged you to save ₹{goal_amount} in {duration_days} days!",
            "data": {"challenge_id": challenge["challenge_id"]},
            "is_read": False,
            "created_at": datetime.now(timezone.utc)
        }
        
        await db.notifications.insert_one(notification)
        
        return {"success": True, "challenge_id": challenge["challenge_id"]}
        
    except Exception as e:
        logger.error(f"Challenge friend error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create friend challenge")

async def generate_enhanced_peer_comparison(user_savings_rate: float, peer_savings_rates: list, university: str, role: str, user_id: str):
    """Generate enhanced peer comparison with detailed messaging and social pressure"""
    try:
        if not peer_savings_rates:
            return {
                "user_savings_rate": round(user_savings_rate, 1),
                "peer_average_rate": 0,
                "comparison_message": "No peer data available for comparison",
                "detailed_message": "Be the first in your university to start tracking finances!",
                "status": "no_data",
                "peer_count": 0,
                "university": university,
                "role": role,
                "motivation_level": "neutral",
                "social_pressure": 0,
                "actionable_tips": ["Start saving to compare with future peers"]
            }
        
        avg_peer_rate = sum(peer_savings_rates) / len(peer_savings_rates)
        comparison_percentage = ((user_savings_rate - avg_peer_rate) / avg_peer_rate * 100) if avg_peer_rate > 0 else 0
        
        # Calculate percentile ranking
        better_than_count = sum(1 for rate in peer_savings_rates if user_savings_rate > rate)
        percentile = (better_than_count / len(peer_savings_rates)) * 100
        
        # Get additional context
        top_10_percent = sorted(peer_savings_rates, reverse=True)[:max(1, len(peer_savings_rates)//10)]
        top_performer_rate = max(peer_savings_rates) if peer_savings_rates else 0
        
        # Generate detailed comparison messaging
        if comparison_percentage > 20:
            status = "top_performer"
            motivation_level = "excellent"
            social_pressure = 8
            primary_message = f"🏆 Outstanding! You save {comparison_percentage:.1f}% more than peers!"
            detailed_message = f"You're in the top {100-percentile:.0f}% of {role.lower()}s at {university}. Your {user_savings_rate:.1f}% savings rate puts you ahead of {better_than_count} out of {len(peer_savings_rates)} peers. Keep this momentum going!"
            
            actionable_tips = [
                "Share your success story with friends",
                "Consider mentoring peers with lower savings rates",
                f"Challenge: Can you reach the top performer's {top_performer_rate:.1f}% rate?"
            ]
            
        elif comparison_percentage > 5:
            status = "above_average" 
            motivation_level = "good"
            social_pressure = 6
            primary_message = f"✨ Great job! You save {comparison_percentage:.1f}% more than similar students"
            detailed_message = f"You're doing better than {percentile:.0f}% of your peers at {university}. Your {user_savings_rate:.1f}% savings rate beats the average of {avg_peer_rate:.1f}%. You're on the right track!"
            
            actionable_tips = [
                f"You're only {top_performer_rate - user_savings_rate:.1f}% away from the top performer",
                "Invite friends to join and compete together",
                "Try the 50/30/20 rule to optimize further"
            ]
            
        elif comparison_percentage >= -5:
            status = "average"
            motivation_level = "okay"
            social_pressure = 5
            primary_message = f"📊 You're close to average - {user_savings_rate:.1f}% vs {avg_peer_rate:.1f}%"
            detailed_message = f"You're performing similarly to most {role.lower()}s at {university}. Your savings rate is within 5% of the average. Small improvements can make a big difference!"
            
            actionable_tips = [
                f"Increase savings by just 2% to beat {len([r for r in peer_savings_rates if r < user_savings_rate + 2]):.0f} more peers",
                "Track expenses for 1 week to find saving opportunities", 
                "Join a group challenge for motivation"
            ]
            
        elif comparison_percentage >= -15:
            status = "below_average"
            motivation_level = "needs_improvement"
            social_pressure = 7
            primary_message = f"💪 You can improve! Currently {abs(comparison_percentage):.1f}% behind peers"
            detailed_message = f"Your {user_savings_rate:.1f}% savings rate is below the {university} average of {avg_peer_rate:.1f}%. But don't worry - {len([r for r in peer_savings_rates if r < avg_peer_rate]):.0f} other students are also working to improve!"
            
            actionable_tips = [
                f"Save just ₹{((avg_peer_rate - user_savings_rate) * 1000 / 100):.0f} more monthly to reach average",
                "Use the 'Cook at Home' tip - save ₹200-400 daily",
                f"Join friends who are already saving well - peer motivation works!"
            ]
            
        else:  # More than 15% below
            status = "needs_attention"
            motivation_level = "urgent"
            social_pressure = 9
            primary_message = f"🚨 Action needed: {abs(comparison_percentage):.1f}% behind peers"
            detailed_message = f"Your {user_savings_rate:.1f}% savings rate is significantly below your {university} peers' {avg_peer_rate:.1f}% average. Time to take action! Remember, small changes lead to big results."
            
            # Get user's recent expenses for personalized tips
            recent_expenses = await db.transactions.find({
                "user_id": user_id,
                "type": "expense", 
                "created_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=7)}
            }).to_list(None)
            
            top_expense_categories = {}
            for expense in recent_expenses:
                category = expense.get("category", "Other")
                top_expense_categories[category] = top_expense_categories.get(category, 0) + expense["amount"]
            
            top_category = max(top_expense_categories.items(), key=lambda x: x[1])[0] if top_expense_categories else "Food"
            
            actionable_tips = [
                f"Focus on {top_category} expenses - your biggest spending area",
                "Start with the 50/30/20 rule: 20% savings minimum",
                f"Challenge a friend - social accountability helps!",
                f"Quick win: Cook at home for 1 week, save ₹1,400+"
            ]
        
        # Add university-specific insights
        university_context = ""
        if university:
            if "IIT" in university or "NIT" in university:
                university_context = f"Tech students at {university} typically excel at systematic saving!"
            elif "Delhi" in university or "Mumbai" in university:
                university_context = f"Metro city students face higher costs - great job tracking expenses!"
            else:
                university_context = f"{university} students are building strong financial habits together!"
        
        return {
            "user_savings_rate": round(user_savings_rate, 1),
            "peer_average_rate": round(avg_peer_rate, 1),
            "comparison_message": primary_message,
            "detailed_message": detailed_message,
            "status": status,
            "peer_count": len(peer_savings_rates),
            "university": university,
            "role": role,
            "percentile": round(percentile, 1),
            "motivation_level": motivation_level,
            "social_pressure": social_pressure,
            "actionable_tips": actionable_tips,
            "university_context": university_context,
            "top_performer_rate": round(top_performer_rate, 1),
            "gap_to_top": round(max(0, top_performer_rate - user_savings_rate), 1),
            "peers_behind": better_than_count,
            "peers_ahead": len(peer_savings_rates) - better_than_count
        }
        
    except Exception as e:
        logger.error(f"Enhanced peer comparison generation error: {str(e)}")
        return {
            "user_savings_rate": round(user_savings_rate, 1),
            "peer_average_rate": 0,
            "comparison_message": "Error generating comparison",
            "status": "error",
            "peer_count": 0
        }

# Peer comparison features
@api_router.get("/social/peer-comparison")
@limiter.limit("10/minute")
async def get_peer_comparison(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get peer comparison data for social pressure"""
    try:
        # Get current user data
        current_user = await db.users.find_one({"user_id": user_id})
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        university = current_user.get("university", "")
        role = current_user.get("role", "Student")
        
        # Get user's savings rate (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        user_transactions = await db.transactions.find({
            "user_id": user_id,
            "created_at": {"$gte": thirty_days_ago}
        }).to_list(None)
        
        user_income = sum(tx["amount"] for tx in user_transactions if tx["type"] == "income")
        user_savings = user_income - sum(tx["amount"] for tx in user_transactions if tx["type"] == "expense")
        user_savings_rate = (user_savings / user_income * 100) if user_income > 0 else 0
        
        # Get peer data (same university and role)
        peer_users = await db.users.find({
            "university": university,
            "role": role,
            "user_id": {"$ne": user_id}
        }).to_list(None)
        
        peer_savings_rates = []
        for peer in peer_users[:50]:  # Limit to 50 peers for performance
            peer_transactions = await db.transactions.find({
                "user_id": peer["user_id"],
                "created_at": {"$gte": thirty_days_ago}
            }).to_list(None)
            
            peer_income = sum(tx["amount"] for tx in peer_transactions if tx["type"] == "income")
            peer_savings = peer_income - sum(tx["amount"] for tx in peer_transactions if tx["type"] == "expense")
            peer_rate = (peer_savings / peer_income * 100) if peer_income > 0 else 0
            peer_savings_rates.append(peer_rate)
        
        enhanced_comparison = await generate_enhanced_peer_comparison(
            user_savings_rate, peer_savings_rates, university, role, user_id
        )
        
        return enhanced_comparison
        
    except Exception as e:
        logger.error(f"Peer comparison error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get peer comparison")

# Enhanced peer messaging with social pressure and motivation
@api_router.get("/social/peer-messages") 
@limiter.limit("10/minute")
async def get_peer_motivation_messages(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get personalized peer comparison messages and social pressure alerts"""
    try:
        current_user = await db.users.find_one({"user_id": user_id})
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        university = current_user.get("university", "")
        role = current_user.get("role", "Student")
        
        # Get recent peer activities for social pressure
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        
        # Friends' recent achievements
        friends = await db.friends.find({
            "$or": [{"user_id": user_id}, {"friend_id": user_id}],
            "status": "accepted"
        }).to_list(None)
        
        friend_ids = []
        for friend in friends:
            friend_id = friend["friend_id"] if friend["user_id"] == user_id else friend["user_id"] 
            friend_ids.append(friend_id)
        
        peer_messages = []
        
        if friend_ids:
            # Friends who saved more this week
            friend_savings = []
            for friend_id in friend_ids[:10]:  # Limit to 10 friends for performance
                friend_transactions = await db.transactions.find({
                    "user_id": friend_id,
                    "created_at": {"$gte": week_ago}
                }).to_list(None)
                
                friend_income = sum(tx["amount"] for tx in friend_transactions if tx["type"] == "income")
                friend_expenses = sum(tx["amount"] for tx in friend_transactions if tx["type"] == "expense")
                net_savings = friend_income - friend_expenses
                
                if net_savings > 0:
                    friend_user = await db.users.find_one({"user_id": friend_id})
                    friend_savings.append({
                        "friend_id": friend_id,
                        "name": friend_user.get("name", "Friend"),
                        "avatar": friend_user.get("avatar", "boy"),
                        "net_savings": net_savings
                    })
            
            # Sort friends by savings
            friend_savings.sort(key=lambda x: x["net_savings"], reverse=True)
            
            # Create social pressure messages
            if friend_savings:
                top_friend = friend_savings[0]
                peer_messages.append({
                    "type": "friend_outperforming",
                    "urgency": "high",
                    "title": f"🚀 {top_friend['name']} saved ₹{top_friend['net_savings']:.0f} this week!",
                    "message": f"Your friend is on fire! They're ahead of you this week. Can you catch up?",
                    "call_to_action": "Add income or reduce expenses",
                    "action_url": "/transactions/new",
                    "social_pressure": 8,
                    "friend_avatar": top_friend['avatar']
                })
                
                if len(friend_savings) >= 3:
                    peer_messages.append({
                        "type": "multiple_friends_saving",
                        "urgency": "medium", 
                        "title": f"💰 {len(friend_savings)} friends are actively saving!",
                        "message": f"Don't get left behind! Your network is building wealth together.",
                        "call_to_action": "Join the savings streak",
                        "action_url": "/friends",
                        "social_pressure": 6
                    })
        
        # University peer pressure
        university_active_users = await db.transactions.count_documents({
            "created_at": {"$gte": week_ago}
        })
        
        if university_active_users > 0:
            peer_messages.append({
                "type": "university_activity",
                "urgency": "medium",
                "title": f"📊 {university_active_users} students tracked money this week",
                "message": f"Your {university} peers are getting ahead financially. Stay competitive!",
                "call_to_action": "Track your expenses",
                "action_url": "/analytics",
                "social_pressure": 5
            })
        
        # Challenge pressure - active challenges with friends
        friend_challenges = await db.group_challenges.find({
            "status": "active",
            "participants": {"$in": friend_ids}
        }).to_list(None)
        
        if friend_challenges:
            peer_messages.append({
                "type": "friends_in_challenges", 
                "urgency": "high",
                "title": f"⚡ Your friends are in {len(friend_challenges)} active challenges!",
                "message": "They're earning points and badges while you're missing out!",
                "call_to_action": "Join a challenge",
                "action_url": "/group-challenges",
                "social_pressure": 9
            })
        
        # Personal performance decline
        user_last_week = await db.transactions.find({
            "user_id": user_id,
            "created_at": {"$gte": week_ago - timedelta(days=7), "$lt": week_ago}
        }).to_list(None)
        
        user_this_week = await db.transactions.find({
            "user_id": user_id,
            "created_at": {"$gte": week_ago}
        }).to_list(None)
        
        if len(user_last_week) > len(user_this_week) and len(user_last_week) > 3:
            peer_messages.append({
                "type": "personal_decline",
                "urgency": "high",
                "title": "📉 Your financial tracking declined this week",
                "message": f"You tracked {len(user_last_week)} transactions last week vs {len(user_this_week)} this week. Your peers are staying consistent!",
                "call_to_action": "Get back on track",
                "action_url": "/transactions",
                "social_pressure": 7
            })
        
        # Streak pressure
        current_streak = current_user.get("current_streak", 0)
        if current_streak == 0:
            # Check friends' streaks
            friend_streaks = []
            for friend_id in friend_ids[:5]:
                friend = await db.users.find_one({"user_id": friend_id})
                if friend and friend.get("current_streak", 0) > 0:
                    friend_streaks.append({
                        "name": friend.get("name", "Friend"),
                        "streak": friend.get("current_streak", 0)
                    })
            
            if friend_streaks:
                max_streak_friend = max(friend_streaks, key=lambda x: x["streak"])
                peer_messages.append({
                    "type": "streak_pressure",
                    "urgency": "critical",
                    "title": f"🔥 {max_streak_friend['name']} has a {max_streak_friend['streak']}-day streak!",
                    "message": "Your friends are building habits while you're at 0 days. Start now!",
                    "call_to_action": "Start your streak",
                    "action_url": "/transactions/quick",
                    "social_pressure": 10
                })
        
        # Sort by social pressure (urgency)
        urgency_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        peer_messages.sort(key=lambda x: urgency_order.get(x["urgency"], 0), reverse=True)
        
        return {
            "peer_messages": peer_messages[:5],  # Limit to top 5 most urgent
            "total_pressure_score": sum(msg.get("social_pressure", 0) for msg in peer_messages),
            "friends_count": len(friend_ids),
            "active_friends": len(friend_savings) if 'friend_savings' in locals() else 0,
            "urgency_distribution": {
                "critical": len([m for m in peer_messages if m["urgency"] == "critical"]),
                "high": len([m for m in peer_messages if m["urgency"] == "high"]),
                "medium": len([m for m in peer_messages if m["urgency"] == "medium"])
            }
        }
        
    except Exception as e:
        logger.error(f"Peer motivation messages error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get peer messages")

# Social proof notifications
@api_router.get("/social/social-proof")
@limiter.limit("20/minute")
async def get_social_proof_notifications(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get social proof notifications to encourage engagement"""
    try:
        notifications = []
        
        # Friends joined this week
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        new_friends_count = await db.friends.count_documents({
            "$or": [{"user_id": user_id}, {"friend_id": user_id}],
            "created_at": {"$gte": week_ago}
        })
        
        if new_friends_count > 0:
            notifications.append({
                "type": "friends_joined",
                "message": f"{new_friends_count} friends joined this week!",
                "icon": "👥",
                "action_text": "Invite more friends",
                "action_url": "/friends"
            })
        
        # Users in same university saving money
        current_user = await db.users.find_one({"user_id": user_id})
        university_savers = await db.transactions.count_documents({
            "type": "income",
            "created_at": {"$gte": week_ago}
        })
        
        if university_savers > 0:
            notifications.append({
                "type": "university_activity",
                "message": f"{university_savers} students earned money this week!",
                "icon": "💰",
                "action_text": "Join the earning streak",
                "action_url": "/hustles"
            })
        
        # Challenge participation
        active_challenges = await db.group_challenges.count_documents({
            "status": "active",
            "spots_remaining": {"$gt": 0}
        })
        
        if active_challenges > 0:
            notifications.append({
                "type": "challenges_available",
                "message": f"{active_challenges} active challenges with spots available!",
                "icon": "🏆",
                "action_text": "Join challenge",
                "action_url": "/group-challenges"
            })
        
        # Recent achievements by friends
        friends = await db.friends.find({
            "$or": [{"user_id": user_id}, {"friend_id": user_id}],
            "status": "accepted"
        }).to_list(None)
        
        friend_ids = []
        for friend in friends:
            friend_id = friend["friend_id"] if friend["user_id"] == user_id else friend["user_id"]
            friend_ids.append(friend_id)
        
        if friend_ids:
            friend_achievements = await db.user_achievements.count_documents({
                "user_id": {"$in": friend_ids},
                "earned_at": {"$gte": week_ago}
            })
            
            if friend_achievements > 0:
                notifications.append({
                    "type": "friend_achievements",
                    "message": f"Your friends earned {friend_achievements} achievements this week!",
                    "icon": "🎯",
                    "action_text": "See achievements",
                    "action_url": "/gamification"
                })
        
        return {"notifications": notifications, "count": len(notifications)}
        
    except Exception as e:
        logger.error(f"Social proof notifications error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get social proof notifications")

# ================================================================================================
# INDIVIDUAL FRIEND CHALLENGES SYSTEM (1-on-1 Challenges)
# ================================================================================================

@api_router.post("/individual-challenges/create")
@limiter.limit("10/minute")
async def create_individual_friend_challenge(
    request: Request,
    challenge_data: dict,
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Create a 1-on-1 challenge with a specific friend"""
    try:
        db = await get_database()
        user_id = current_user["id"]
        
        friend_id = challenge_data.get("friend_id")
        challenge_type = challenge_data.get("challenge_type")  # "savings_race", "streak_battle", "expense_limit"
        target_amount = challenge_data.get("target_amount", 0)
        duration_days = challenge_data.get("duration_days", 7)
        title = challenge_data.get("title", "")
        description = challenge_data.get("description", "")
        
        # Validate friendship
        friendship = await db.friendships.find_one({
            "$or": [
                {"user1_id": user_id, "user2_id": friend_id},
                {"user1_id": friend_id, "user2_id": user_id}
            ],
            "status": "active"
        })
        
        if not friendship:
            raise HTTPException(status_code=400, detail="You can only challenge accepted friends")
        
        # Create individual challenge
        challenge_id = str(uuid.uuid4())
        end_date = datetime.now(timezone.utc) + timedelta(days=duration_days)
        
        individual_challenge = {
            "challenge_id": challenge_id,
            "challenger_id": user_id,
            "challenged_id": friend_id,
            "challenge_type": challenge_type,
            "title": title,
            "description": description,
            "target_amount": target_amount,
            "duration_days": duration_days,
            "start_date": datetime.now(timezone.utc),
            "end_date": end_date,
            "status": "pending",  # pending, active, completed, declined
            "challenger_progress": 0,
            "challenged_progress": 0,
            "winner": None,
            "created_at": datetime.now(timezone.utc),
            "stakes": challenge_data.get("stakes", "Bragging rights!")
        }
        
        await db.individual_challenges.insert_one(individual_challenge)
        
        # Create notification for challenged friend
        notification = {
            "notification_id": str(uuid.uuid4()),
            "user_id": friend_id,
            "notification_type": "individual_challenge_invite",
            "title": f"🥊 Challenge from {user_id}!",
            "message": f"You've been challenged to: {title}",
            "action_url": f"/individual-challenges/{challenge_id}",
            "related_id": challenge_id,
            "is_read": False,
            "created_at": datetime.now(timezone.utc)
        }
        
        await db.in_app_notifications.insert_one(notification)
        
        return {
            "success": True,
            "challenge_id": challenge_id,
            "message": "Challenge sent to your friend!",
            "challenge_details": individual_challenge
        }
        
    except Exception as e:
        logger.error(f"Individual challenge creation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create individual challenge")

@api_router.post("/individual-challenges/{challenge_id}/respond")
@limiter.limit("10/minute") 
async def respond_to_individual_challenge(
    request: Request,
    challenge_id: str,
    response_data: dict,
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Accept or decline an individual challenge"""
    try:
        db = await get_database()
        user_id = current_user["id"]
        action = response_data.get("action")  # "accept" or "decline"
        
        # Find the challenge
        challenge = await db.individual_challenges.find_one({"challenge_id": challenge_id})
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        # Verify user is the challenged person
        if challenge["challenged_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to respond to this challenge")
        
        # Check if challenge is still pending
        if challenge["status"] != "pending":
            raise HTTPException(status_code=400, detail="Challenge is no longer pending")
        
        if action == "accept":
            # Accept the challenge
            await db.individual_challenges.update_one(
                {"challenge_id": challenge_id},
                {
                    "$set": {
                        "status": "active",
                        "start_date": datetime.now(timezone.utc),
                        "end_date": datetime.now(timezone.utc) + timedelta(days=challenge["duration_days"])
                    }
                }
            )
            
            # Notify challenger
            notification = {
                "notification_id": str(uuid.uuid4()),
                "user_id": challenge["challenger_id"],
                "notification_type": "challenge_accepted",
                "title": "🔥 Challenge Accepted!",
                "message": f"Your friend accepted your challenge: {challenge['title']}",
                "action_url": f"/individual-challenges/{challenge_id}",
                "related_id": challenge_id,
                "is_read": False,
                "created_at": datetime.now(timezone.utc)
            }
            
            await db.in_app_notifications.insert_one(notification)
            
            return {"success": True, "message": "Challenge accepted! Let the battle begin!", "status": "active"}
            
        elif action == "decline":
            # Decline the challenge
            await db.individual_challenges.update_one(
                {"challenge_id": challenge_id},
                {"$set": {"status": "declined"}}
            )
            
            # Notify challenger
            notification = {
                "notification_id": str(uuid.uuid4()),
                "user_id": challenge["challenger_id"],
                "notification_type": "challenge_declined",
                "title": "💔 Challenge Declined",
                "message": f"Your friend declined the challenge: {challenge['title']}",
                "action_url": "/individual-challenges",
                "related_id": challenge_id,
                "is_read": False,
                "created_at": datetime.now(timezone.utc)
            }
            
            await db.in_app_notifications.insert_one(notification)
            
            return {"success": True, "message": "Challenge declined", "status": "declined"}
        
    except Exception as e:
        logger.error(f"Individual challenge response error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to respond to challenge")

@api_router.get("/individual-challenges")
@limiter.limit("20/minute")
async def get_individual_challenges(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get user's individual challenges (both created and received)"""
    try:
        # Get challenges where user is either challenger or challenged
        challenges = await db.individual_challenges.find({
            "$or": [
                {"challenger_id": user_id},
                {"challenged_id": user_id}
            ]
        }).sort("created_at", -1).to_list(None)
        
        # Get friend details for each challenge
        for challenge in challenges:
            friend_id = challenge["challenged_id"] if challenge["challenger_id"] == user_id else challenge["challenger_id"]
            friend = await db.users.find_one({"user_id": friend_id})
            
            challenge["friend_info"] = {
                "friend_id": friend_id,
                "name": friend.get("name", "Unknown"),
                "avatar": friend.get("avatar", "boy"),
                "university": friend.get("university", "")
            }
            
            challenge["user_role"] = "challenger" if challenge["challenger_id"] == user_id else "challenged"
            
            # Calculate progress
            await update_individual_challenge_progress(challenge["challenge_id"])
        
        # Refresh challenge data after progress update
        challenges = await db.individual_challenges.find({
            "$or": [
                {"challenger_id": user_id},
                {"challenged_id": user_id}
            ]
        }).sort("created_at", -1).to_list(None)
        
        return {
            "challenges": challenges,
            "total": len(challenges),
            "active_count": len([c for c in challenges if c["status"] == "active"]),
            "pending_count": len([c for c in challenges if c["status"] == "pending"])
        }
        
    except Exception as e:
        logger.error(f"Get individual challenges error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get individual challenges")

@api_router.get("/individual-challenges/{challenge_id}")
@limiter.limit("20/minute")
async def get_individual_challenge_details(
    request: Request,
    challenge_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get detailed information about a specific individual challenge"""
    try:
        challenge = await db.individual_challenges.find_one({"challenge_id": challenge_id})
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        # Verify user is part of this challenge
        if challenge["challenger_id"] != user_id and challenge["challenged_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this challenge")
        
        # Update progress
        await update_individual_challenge_progress(challenge_id)
        
        # Get updated challenge data
        challenge = await db.individual_challenges.find_one({"challenge_id": challenge_id})
        
        # Get both users' info
        challenger = await db.users.find_one({"user_id": challenge["challenger_id"]})
        challenged = await db.users.find_one({"user_id": challenge["challenged_id"]})
        
        challenge["challenger_info"] = {
            "name": challenger.get("name", "Unknown"),
            "avatar": challenger.get("avatar", "boy"),
            "university": challenger.get("university", "")
        }
        
        challenge["challenged_info"] = {
            "name": challenged.get("name", "Unknown"),
            "avatar": challenged.get("avatar", "girl"),
            "university": challenged.get("university", "")
        }
        
        # Calculate time remaining
        if challenge["status"] == "active":
            time_remaining = challenge["end_date"] - datetime.now(timezone.utc)
            challenge["hours_remaining"] = max(0, int(time_remaining.total_seconds() // 3600))
            challenge["days_remaining"] = max(0, time_remaining.days)
        
        return challenge
        
    except Exception as e:
        logger.error(f"Get individual challenge details error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get challenge details")

async def update_individual_challenge_progress(challenge_id: str):
    """Update progress for an individual challenge"""
    try:
        challenge = await db.individual_challenges.find_one({"challenge_id": challenge_id})
        if not challenge or challenge["status"] != "active":
            return
        
        challenge_type = challenge["challenge_type"]
        start_date = challenge["start_date"]
        end_date = challenge["end_date"]
        now = datetime.now(timezone.utc)
        
        # Calculate challenger progress
        challenger_progress = await calculate_individual_challenge_progress(
            challenge["challenger_id"], challenge_type, start_date
        )
        
        # Calculate challenged progress  
        challenged_progress = await calculate_individual_challenge_progress(
            challenge["challenged_id"], challenge_type, start_date
        )
        
        # Update challenge with new progress
        update_data = {
            "challenger_progress": challenger_progress,
            "challenged_progress": challenged_progress
        }
        
        # Check if challenge is completed
        if now >= end_date:
            # Determine winner based on challenge type and progress
            if challenge_type == "savings_race":
                if challenger_progress > challenged_progress:
                    winner = challenge["challenger_id"]
                elif challenged_progress > challenger_progress:
                    winner = challenge["challenged_id"]
                else:
                    winner = "tie"
            elif challenge_type == "streak_battle":
                if challenger_progress > challenged_progress:
                    winner = challenge["challenger_id"]
                elif challenged_progress > challenger_progress:
                    winner = challenge["challenged_id"]
                else:
                    winner = "tie"
            else:
                winner = "tie"
            
            update_data["status"] = "completed"
            update_data["winner"] = winner
            
            # Send completion notifications
            await send_challenge_completion_notifications(challenge_id, winner)
        
        await db.individual_challenges.update_one(
            {"challenge_id": challenge_id},
            {"$set": update_data}
        )
        
    except Exception as e:
        logger.error(f"Update individual challenge progress error: {str(e)}")

async def calculate_individual_challenge_progress(user_id: str, challenge_type: str, start_date: datetime) -> float:
    """Calculate user's progress for individual challenge"""
    try:
        if challenge_type == "savings_race":
            # Calculate income since challenge start
            income_result = await db.transactions.aggregate([
                {
                    "$match": {
                        "user_id": user_id,
                        "type": "income",
                        "created_at": {"$gte": start_date}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_income": {"$sum": "$amount"}
                    }
                }
            ]).to_list(None)
            
            return income_result[0]["total_income"] if income_result else 0.0
            
        elif challenge_type == "streak_battle":
            # Get current streak
            user = await db.users.find_one({"user_id": user_id})
            return user.get("current_streak", 0)
            
        elif challenge_type == "expense_limit":
            # Calculate expenses since challenge start
            expense_result = await db.transactions.aggregate([
                {
                    "$match": {
                        "user_id": user_id,
                        "type": "expense",
                        "created_at": {"$gte": start_date}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_expenses": {"$sum": "$amount"}
                    }
                }
            ]).to_list(None)
            
            # For expense limit, lower is better (return negative to make comparison work)
            return -(expense_result[0]["total_expenses"] if expense_result else 0.0)
        
        return 0.0
        
    except Exception as e:
        logger.error(f"Calculate individual challenge progress error: {str(e)}")
        return 0.0

async def send_challenge_completion_notifications(challenge_id: str, winner: str):
    """Send notifications when individual challenge completes"""
    try:
        challenge = await db.individual_challenges.find_one({"challenge_id": challenge_id})
        if not challenge:
            return
        
        challenger_id = challenge["challenger_id"]
        challenged_id = challenge["challenged_id"]
        
        # Notification for challenger
        challenger_notification = {
            "notification_id": str(uuid.uuid4()),
            "user_id": challenger_id,
            "notification_type": "challenge_completed",
            "title": "🏁 Challenge Complete!",
            "message": "",
            "action_url": f"/individual-challenges/{challenge_id}",
            "related_id": challenge_id,
            "is_read": False,
            "created_at": datetime.now(timezone.utc)
        }
        
        # Notification for challenged
        challenged_notification = {
            "notification_id": str(uuid.uuid4()),
            "user_id": challenged_id,
            "notification_type": "challenge_completed", 
            "title": "🏁 Challenge Complete!",
            "message": "",
            "action_url": f"/individual-challenges/{challenge_id}",
            "related_id": challenge_id,
            "is_read": False,
            "created_at": datetime.now(timezone.utc)
        }
        
        if winner == challenger_id:
            challenger_notification["message"] = f"🎉 You won the challenge: {challenge['title']}!"
            challenger_notification["title"] = "🏆 You Won!"
            challenged_notification["message"] = f"😔 You lost the challenge: {challenge['title']}"
            challenged_notification["title"] = "😔 Challenge Lost"
        elif winner == challenged_id:
            challenger_notification["message"] = f"😔 You lost the challenge: {challenge['title']}"
            challenger_notification["title"] = "😔 Challenge Lost"
            challenged_notification["message"] = f"🎉 You won the challenge: {challenge['title']}!"
            challenged_notification["title"] = "🏆 You Won!"
        else:
            challenger_notification["message"] = f"🤝 Tie! Great effort on: {challenge['title']}"
            challenger_notification["title"] = "🤝 It's a Tie!"
            challenged_notification["message"] = f"🤝 Tie! Great effort on: {challenge['title']}"
            challenged_notification["title"] = "🤝 It's a Tie!"
        
        await db.in_app_notifications.insert_many([challenger_notification, challenged_notification])
        
    except Exception as e:
        logger.error(f"Send challenge completion notifications error: {str(e)}")

# ================================================================================================
# PHASE 2: ENGAGEMENT FEATURES IMPLEMENTATION
# ================================================================================================

# Push notifications for friend activities (backend notification creation)
@api_router.post("/engagement/create-friend-notification")
@limiter.limit("100/minute")  # Higher limit for system-generated notifications
async def create_friend_activity_notification(
    request: Request,
    notification_data: dict,
    user_id: str = Depends(get_current_user)
):
    """Create notifications for friend activities"""
    try:
        activity_type = notification_data.get("activity_type")
        target_friend_id = notification_data.get("friend_id")
        details = notification_data.get("details", {})
        
        # Verify friendship
        friendship = await db.friends.find_one({
            "$or": [
                {"user_id": user_id, "friend_id": target_friend_id},
                {"user_id": target_friend_id, "friend_id": user_id}
            ],
            "status": "accepted"
        })
        
        if not friendship:
            return {"success": False, "message": "Not friends"}
        
        # Get user info for notification
        user_info = await db.users.find_one({"user_id": user_id})
        user_name = user_info.get("name", "Your friend")
        
        # Generate notification based on activity type
        notifications_to_create = []
        
        if activity_type == "achievement":
            notifications_to_create.append({
                "user_id": target_friend_id,
                "type": "friend_achievement",
                "title": "Friend Achievement!",
                "message": f"{user_name} unlocked a new achievement!",
                "data": details
            })
        elif activity_type == "milestone":
            notifications_to_create.append({
                "user_id": target_friend_id,
                "type": "friend_milestone",
                "title": "Friend Milestone!",
                "message": f"{user_name} reached a new savings milestone!",
                "data": details
            })
        elif activity_type == "big_transaction":
            amount = details.get("amount", 0)
            notifications_to_create.append({
                "user_id": target_friend_id,
                "type": "friend_activity",
                "title": "Friend Activity!",
                "message": f"{user_name} just earned ₹{amount}!",
                "data": details
            })
        
        # Create notifications
        created_count = 0
        for notif_data in notifications_to_create:
            notification = {
                "notification_id": str(uuid.uuid4()),
                "is_read": False,
                "created_at": datetime.now(timezone.utc),
                **notif_data
            }
            await db.notifications.insert_one(notification)
            created_count += 1
        
        return {"success": True, "notifications_created": created_count}
        
    except Exception as e:
        logger.error(f"Friend notification creation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create friend notification")

# Daily savings tips/financial quotes
@api_router.get("/engagement/daily-tip")
@limiter.limit("10/minute")
async def get_daily_financial_tip(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get daily savings tip or financial quote"""
    try:
        # Get current date for consistent daily tips
        today = datetime.now(timezone.utc).date()
        tip_index = hash(str(today) + user_id) % 50  # Rotate through tips
        
        tips_and_quotes = [
            {
                "type": "tip",
                "title": "50/30/20 Rule",
                "content": "Allocate 50% of income to needs, 30% to wants, and 20% to savings and debt repayment.",
                "icon": "💡"
            },
            {
                "type": "quote",
                "title": "Warren Buffett",
                "content": "Do not save what is left after spending, but spend what is left after saving.",
                "icon": "💭"
            },
            {
                "type": "tip",
                "title": "Track Small Expenses",
                "content": "Small daily expenses like chai and snacks can add up to ₹3,000+ monthly. Track them!",
                "icon": "☕"
            },
            {
                "type": "quote",
                "title": "Benjamin Franklin",
                "content": "An investment in knowledge pays the best interest.",
                "icon": "📚"
            },
            {
                "type": "tip",
                "title": "Emergency Fund Priority",
                "content": "Build an emergency fund of 3-6 months expenses before investing elsewhere.",
                "icon": "🚨"
            },
            {
                "type": "tip",
                "title": "Student Discounts",
                "content": "Always ask for student discounts - many businesses offer 10-20% off for students!",
                "icon": "🎓"
            },
            {
                "type": "quote",
                "title": "Robert Kiyosaki",
                "content": "It's not how much money you make, but how much money you keep.",
                "icon": "💰"
            },
            {
                "type": "tip",
                "title": "Cook at Home",
                "content": "Cooking meals at home can save ₹200-400 per day compared to ordering food.",
                "icon": "🍳"
            },
            {
                "type": "tip",
                "title": "Bulk Purchases",
                "content": "Buy non-perishables in bulk with friends to get wholesale prices and split costs.",
                "icon": "🛒"
            },
            {
                "type": "quote",
                "title": "Dave Ramsey",
                "content": "A budget is telling your money where to go instead of wondering where it went.",
                "icon": "📊"
            }
        ]
        
        # Add more tips to reach 50
        additional_tips = [
            {"type": "tip", "title": "Public Transport", "content": "Use student bus passes and metro cards for maximum savings on transport.", "icon": "🚌"},
            {"type": "tip", "title": "Library Resources", "content": "Use college library for books, internet, and study space instead of paid alternatives.", "icon": "📖"},
            {"type": "tip", "title": "Group Studies", "content": "Share textbook costs with classmates and form study groups to split tuition fees.", "icon": "👥"},
            {"type": "tip", "title": "Side Hustles", "content": "Start freelancing or tutoring to earn ₹5,000-15,000 monthly during studies.", "icon": "💼"},
            {"type": "tip", "title": "Water Bottle", "content": "Carry a water bottle to avoid buying ₹20 bottles - save ₹600+ monthly.", "icon": "💧"},
            {"type": "tip", "title": "Generic Brands", "content": "Choose generic/store brands for basic items - same quality, 30-40% cheaper.", "icon": "🏷️"},
            {"type": "tip", "title": "Cashback Apps", "content": "Use cashback apps for online shopping to get 2-10% money back.", "icon": "💳"},
            {"type": "tip", "title": "Movie Discounts", "content": "Watch movies on weekdays or matinee shows for 40-50% discount.", "icon": "🎬"},
            {"type": "tip", "title": "Subscription Audit", "content": "Review monthly subscriptions and cancel unused ones - save ₹500-1500 monthly.", "icon": "📱"},
            {"type": "tip", "title": "Energy Saving", "content": "Unplug devices when not in use to reduce electricity bills by 10-15%.", "icon": "⚡"}
        ]
        
        all_tips = tips_and_quotes + additional_tips
        selected_tip = all_tips[tip_index % len(all_tips)]
        
        # Check if user has already seen today's tip
        today_tip_seen = await db.daily_tips_seen.find_one({
            "user_id": user_id,
            "date": today.isoformat()
        })
        
        if not today_tip_seen:
            # Mark as seen
            await db.daily_tips_seen.insert_one({
                "user_id": user_id,
                "date": today.isoformat(),
                "tip_content": selected_tip["content"],
                "seen_at": datetime.now(timezone.utc)
            })
            
            # Award points for checking daily tip
            gamification_service = get_gamification_service()
            if gamification_service:
                try:
                    await gamification_service.add_experience_points(user_id, 5, "daily_tip_viewed")
                except:
                    pass
        
        return {
            "tip": selected_tip,
            "date": today.isoformat(),
            "is_new": not bool(today_tip_seen),
            "streak_info": "Check daily for bonus points!"
        }
        
    except Exception as e:
        logger.error(f"Daily tip error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get daily tip")

# Enhanced daily tips with push notification scheduling
@api_router.post("/engagement/schedule-daily-tips")
@limiter.limit("5/minute")
async def schedule_daily_tip_notifications(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Schedule daily tip push notifications for user"""
    try:
        # Check if user has active push subscription
        subscription = await db.push_subscriptions.find_one({
            "user_id": user_id,
            "is_active": True
        })
        
        if not subscription:
            return {
                "success": False,
                "message": "Please enable push notifications first to receive daily tips"
            }
        
        # Check current preferences
        preferences = subscription.get("notification_preferences", {})
        if not preferences.get("daily_tips", True):
            return {
                "success": False,
                "message": "Daily tip notifications are disabled in your preferences"
            }
        
        # Create daily tip schedule
        schedule_entry = {
            "user_id": user_id,
            "notification_type": "daily_tip",
            "scheduled_time": "09:00",  # 9 AM daily
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "last_sent": None,
            "timezone": "Asia/Kolkata"  # Default to Indian timezone
        }
        
        # Upsert schedule (update if exists, create if not)
        await db.notification_schedules.update_one(
            {
                "user_id": user_id,
                "notification_type": "daily_tip"
            },
            {"$set": schedule_entry},
            upsert=True
        )
        
        return {
            "success": True,
            "message": "Daily tip notifications scheduled for 9:00 AM",
            "scheduled_time": "09:00"
        }
        
    except Exception as e:
        logger.error(f"Daily tip scheduling error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to schedule daily tips")

# Send daily tip push notification (called by scheduler)
async def send_daily_tip_push_notification(user_id: str):
    """Send daily tip as push notification"""
    try:
        if not PUSH_NOTIFICATION_AVAILABLE:
            return False
        
        push_service = get_push_service()
        if not push_service:
            return False
        
        # Get today's tip
        today = datetime.now(timezone.utc).date()
        tip_index = hash(str(today) + user_id) % 50
        
        # Reduced tip set for notifications (most impactful ones)
        notification_tips = [
            {"title": "💡 50/30/20 Rule", "content": "Allocate 50% to needs, 30% to wants, 20% to savings!", "icon": "💡"},
            {"title": "☕ Track Small Expenses", "content": "Daily chai & snacks add up to ₹3,000+ monthly. Track them!", "icon": "☕"},
            {"title": "🚨 Emergency Fund", "content": "Build 3-6 months expenses emergency fund before investing.", "icon": "🚨"},
            {"title": "🍳 Cook at Home", "content": "Save ₹200-400 daily by cooking instead of ordering food.", "icon": "🍳"},
            {"title": "🎓 Student Discounts", "content": "Always ask for student discounts - get 10-20% off!", "icon": "🎓"},
            {"title": "🚌 Public Transport", "content": "Use student passes for maximum transport savings.", "icon": "🚌"},
            {"title": "💧 Water Bottle", "content": "Carry water bottle - save ₹600+ monthly on bottles.", "icon": "💧"},
            {"title": "💼 Side Hustles", "content": "Start freelancing - earn ₹5,000-15,000 monthly!", "icon": "💼"},
            {"title": "📱 Subscription Audit", "content": "Cancel unused subscriptions - save ₹500-1500 monthly.", "icon": "📱"},
            {"title": "⚡ Energy Saving", "content": "Unplug devices when not in use - reduce bills by 10-15%.", "icon": "⚡"}
        ]
        
        selected_tip = notification_tips[tip_index % len(notification_tips)]
        
        # Create notification payload
        notification_data = {
            "title": f"💰 Daily Financial Tip",
            "message": f"{selected_tip['title']}: {selected_tip['content']}",
            "icon": selected_tip["icon"],
            "type": "daily_tip",
            "action_url": "/dashboard"
        }
        
        # Send push notification
        success = await push_service.send_milestone_notification(user_id, notification_data)
        
        if success:
            # Mark as sent in schedule
            await db.notification_schedules.update_one(
                {
                    "user_id": user_id,
                    "notification_type": "daily_tip"
                },
                {
                    "$set": {
                        "last_sent": datetime.now(timezone.utc)
                    }
                }
            )
            
            # Track engagement
            await db.daily_tips_sent.insert_one({
                "user_id": user_id,
                "date": today.isoformat(),
                "tip_content": selected_tip["content"],
                "sent_at": datetime.now(timezone.utc),
                "notification_method": "push"
            })
        
        return success
        
    except Exception as e:
        logger.error(f"Daily tip push notification error: {str(e)}")
        return False

# ================================================================================================
# PHASE 3: RETENTION MECHANICS IMPLEMENTATION  
# ================================================================================================

# Daily check-in rewards/bonuses
@api_router.post("/retention/daily-checkin")
@limiter.limit("5/minute")
async def daily_checkin_reward(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Handle daily check-in and rewards"""
    try:
        today = datetime.now(timezone.utc).date()
        
        # Check if already checked in today
        existing_checkin = await db.daily_checkins.find_one({
            "user_id": user_id,
            "date": today.isoformat()
        })
        
        if existing_checkin:
            return {
                "success": False, 
                "message": "Already checked in today!",
                "next_checkin": (today + timedelta(days=1)).isoformat()
            }
        
        # Get consecutive check-in streak
        yesterday = today - timedelta(days=1)
        yesterday_checkin = await db.daily_checkins.find_one({
            "user_id": user_id,
            "date": yesterday.isoformat()
        })
        
        # Calculate streak
        if yesterday_checkin:
            current_streak = yesterday_checkin.get("streak", 0) + 1
        else:
            current_streak = 1
        
        # Enhanced reward calculation system
        base_points = 10
        
        # Progressive streak bonus (increases over time)
        if current_streak <= 7:
            streak_bonus = current_streak * 3  # 3-21 points for first week
        elif current_streak <= 30:
            streak_bonus = 21 + ((current_streak - 7) * 5)  # Higher bonus for weeks 2-4
        else:
            streak_bonus = min(21 + (23 * 5) + ((current_streak - 30) * 7), 200)  # Max 200 bonus
        
        # Weekly streak multiplier bonus (2x points for 7-day streaks)
        weekly_multiplier_bonus = 0
        if current_streak % 7 == 0 and current_streak >= 7:
            weekly_multiplier_bonus = (base_points + streak_bonus)  # Double the current points
            
        total_points = base_points + streak_bonus + weekly_multiplier_bonus
        
        # Enhanced milestone rewards with better progression
        milestone_bonus = 0
        milestone_message = ""
        milestone_type = ""
        
        if current_streak == 3:
            milestone_bonus = 25
            milestone_message = "3-day starter bonus! You're building a habit! 🌱"
            milestone_type = "starter"
        elif current_streak == 7:
            milestone_bonus = 150  # Increased from 100
            milestone_message = "Weekly warrior! 7-day streak bonus! 🎉"
            milestone_type = "weekly"
        elif current_streak == 14:
            milestone_bonus = 300
            milestone_message = "Two weeks strong! Consistency champion! ⚡"
            milestone_type = "biweekly"
        elif current_streak == 30:
            milestone_bonus = 1000  # Increased from 500
            milestone_message = "Monthly master! 30-day streak! Amazing! 🏆"
            milestone_type = "monthly"
        elif current_streak == 60:
            milestone_bonus = 2500
            milestone_message = "Two months of dedication! Incredible! 💎"
            milestone_type = "bimonthly"
        elif current_streak == 100:
            milestone_bonus = 5000  # Increased from 2000
            milestone_message = "Centurion status! 100-day legend! 👑"
            milestone_type = "centurion"
        elif current_streak == 365:
            milestone_bonus = 25000
            milestone_message = "Annual achievement! You're unstoppable! 🌟"
            milestone_type = "annual"
        elif current_streak % 50 == 0 and current_streak > 100:
            milestone_bonus = current_streak * 25
            milestone_message = f"{current_streak}-day milestone! Legendary dedication! 🚀"
            milestone_type = "legendary"
        
        total_points += milestone_bonus
        
        # Create enhanced check-in record
        checkin_record = {
            "user_id": user_id,
            "date": today.isoformat(),
            "streak": current_streak,
            "points_earned": total_points,
            "base_points": base_points,
            "streak_bonus": streak_bonus,
            "weekly_multiplier_bonus": weekly_multiplier_bonus,
            "milestone_bonus": milestone_bonus,
            "milestone_type": milestone_type,
            "checked_in_at": datetime.now(timezone.utc)
        }
        
        await db.daily_checkins.insert_one(checkin_record)
        
        # Award points through gamification system
        gamification_service = get_gamification_service()
        if gamification_service:
            try:
                await gamification_service.add_experience_points(user_id, total_points, "daily_checkin")
                
                # Check for streak achievements
                if current_streak in [7, 30, 100]:
                    await gamification_service.award_achievement(
                        user_id, 
                        f"check_in_streak_{current_streak}",
                        f"{current_streak}-Day Check-in Champion"
                    )
            except Exception as e:
                logger.error(f"Gamification error during check-in: {e}")
        
        return {
            "success": True,
            "streak": current_streak,
            "points_earned": total_points,
            "base_points": base_points,
            "streak_bonus": streak_bonus,
            "weekly_multiplier_bonus": weekly_multiplier_bonus,
            "milestone_bonus": milestone_bonus,
            "milestone_message": milestone_message,
            "milestone_type": milestone_type,
            "is_weekly_multiplier": current_streak % 7 == 0 and current_streak >= 7,
            "total_lifetime_points": "Check profile for total",
            "next_checkin": (today + timedelta(days=1)).isoformat(),
            "streak_tier": "legend" if current_streak >= 100 else "champion" if current_streak >= 30 else "warrior" if current_streak >= 7 else "starter"
        }
        
    except Exception as e:
        logger.error(f"Daily check-in error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process daily check-in")

# Progressive unlock system
@api_router.get("/retention/unlock-status")
@limiter.limit("20/minute")
async def get_feature_unlock_status(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get user's feature unlock status based on usage"""
    try:
        # Get user stats
        user_stats = await db.user_stats.find_one({"user_id": user_id})
        if not user_stats:
            # Initialize user stats if not exists
            user_stats = {
                "user_id": user_id,
                "transactions_count": 0,
                "days_active": 0,
                "features_unlocked": [],
                "created_at": datetime.now(timezone.utc)
            }
            await db.user_stats.insert_one(user_stats)
        
        # Get transaction count
        transaction_count = await db.transactions.count_documents({"user_id": user_id})
        
        # Get active days (days with any activity)
        active_days = await db.transactions.distinct("created_at", {"user_id": user_id})
        days_active = len(set(day.date() for day in active_days))
        
        # Get friend count for social feature unlocks
        friend_count = await db.friendships.count_documents({
            "$or": [
                {"user_id": user_id, "status": "active"},
                {"friend_id": user_id, "status": "active"}
            ]
        })
        
        # Define enhanced unlock requirements with social features based on friend count
        unlock_requirements = [
            {
                "feature": "advanced_analytics",
                "name": "Advanced Analytics Dashboard",
                "requirement": "5 transactions",
                "requirement_met": transaction_count >= 5,
                "description": "Detailed spending patterns and insights",
                "icon": "📊",
                "category": "analytics"
            },
            {
                "feature": "friend_invitations",
                "name": "Friend Invitations",
                "requirement": "Complete profile setup",
                "requirement_met": True,  # Always unlocked
                "description": "Invite friends to join your financial journey",
                "icon": "👋",
                "category": "social"
            },
            {
                "feature": "social_sharing",
                "name": "Achievement Sharing",
                "requirement": "1 friend connected",
                "requirement_met": friend_count >= 1,
                "description": "Share your financial achievements with friends",
                "icon": "📱",
                "category": "social"
            },
            {
                "feature": "group_challenges",
                "name": "Group Challenges",
                "requirement": "3 friends connected",
                "requirement_met": friend_count >= 3,
                "description": "Create and join savings challenges with friends",
                "icon": "👥",
                "category": "social"
            },
            {
                "feature": "friend_leaderboards",
                "name": "Friend Leaderboards",
                "requirement": "5 friends connected",
                "requirement_met": friend_count >= 5,
                "description": "Compete with friends on savings leaderboards",
                "icon": "🏆",
                "category": "social"
            },
            {
                "feature": "social_feed",
                "name": "Social Activity Feed",
                "requirement": "7 friends connected",
                "requirement_met": friend_count >= 7,
                "description": "See your friends' achievements and milestones",
                "icon": "📰",
                "category": "social"
            },
            {
                "feature": "peer_insights",
                "name": "Peer Performance Insights",
                "requirement": "10 friends connected",
                "requirement_met": friend_count >= 10,
                "description": "Compare your progress with friend averages",
                "icon": "📊",
                "category": "social"
            },
            {
                "feature": "ai_insights",
                "name": "AI Financial Advisor",
                "requirement": "7 days active",
                "requirement_met": days_active >= 7,
                "description": "Personalized AI-powered financial recommendations",
                "icon": "🤖",
                "category": "ai"
            },
            {
                "feature": "premium_hustles",
                "name": "Premium Side Hustles",
                "requirement": "₹5000 total income",
                "requirement_met": await get_user_total_income(user_id) >= 5000,
                "description": "Access to exclusive high-paying opportunities",
                "icon": "💎",
                "category": "premium"
            },
            {
                "feature": "investment_tracker",
                "name": "Investment Portfolio Tracker",
                "requirement": "30 days active + ₹10000 savings",
                "requirement_met": days_active >= 30 and await get_user_total_savings(user_id) >= 10000,
                "description": "Track and analyze your investment portfolio",
                "icon": "📈",
                "category": "premium"
            }
        ]
        
        # Update user stats
        await db.user_stats.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "transactions_count": transaction_count,
                    "days_active": days_active,
                    "updated_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        
        # Categorize features by unlock status
        unlocked_features = [f for f in unlock_requirements if f["requirement_met"]]
        locked_features = [f for f in unlock_requirements if not f["requirement_met"]]
        
        return {
            "user_stats": {
                "transactions": transaction_count,
                "days_active": days_active,
                "friend_count": friend_count,
                "total_income": await get_user_total_income(user_id),
                "total_savings": await get_user_total_savings(user_id)
            },
            "features": unlock_requirements,
            "unlocked_features": unlocked_features,
            "locked_features": locked_features,
            "unlocked_count": len(unlocked_features),
            "total_features": len(unlock_requirements),
            "social_progress": {
                "current_friends": friend_count,
                "next_unlock_at": next(
                    (f["requirement"] for f in locked_features 
                     if f["category"] == "social" and "friends" in f["requirement"]),
                    None
                )
            }
        }
        
    except Exception as e:
        logger.error(f"Feature unlock status error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get unlock status")

# Dynamic personalized goals based on university leaderboards
@api_router.get("/retention/personalized-goals")
@limiter.limit("10/minute")
async def get_personalized_goals(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get dynamic personalized goals based on peer performance"""
    try:
        # Get user info
        user_doc = await get_user_by_id(user_id)
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_university = user_doc.get("university", "")
        
        # Get user's current performance
        user_total_savings = await get_user_total_savings(user_id)
        user_monthly_income = await get_user_monthly_income(user_id)
        user_transaction_count = await db.transactions.count_documents({"user_id": user_id})
        
        # Get university peer performance averages
        university_users = await db.users.find({"university": user_university}).to_list(None)
        peer_user_ids = [str(u["_id"]) for u in university_users if str(u["_id"]) != user_id]
        
        # Calculate peer averages
        peer_savings = []
        peer_monthly_incomes = []
        peer_transaction_counts = []
        
        for peer_id in peer_user_ids[:50]:  # Limit for performance
            peer_savings.append(await get_user_total_savings(peer_id))
            peer_monthly_incomes.append(await get_user_monthly_income(peer_id))
            peer_count = await db.transactions.count_documents({"user_id": peer_id})
            peer_transaction_counts.append(peer_count)
        
        # Calculate statistics
        avg_peer_savings = sum(peer_savings) / len(peer_savings) if peer_savings else 0
        avg_peer_monthly_income = sum(peer_monthly_incomes) / len(peer_monthly_incomes) if peer_monthly_incomes else 0
        avg_peer_transactions = sum(peer_transaction_counts) / len(peer_transaction_counts) if peer_transaction_counts else 0
        
        # Calculate percentiles
        peer_savings.sort()
        peer_monthly_incomes.sort()
        peer_transaction_counts.sort()
        
        def get_percentile(sorted_list, value):
            if not sorted_list:
                return 50
            position = sum(1 for x in sorted_list if x < value)
            return min(100, max(0, int((position / len(sorted_list)) * 100)))
        
        user_savings_percentile = get_percentile(peer_savings, user_total_savings)
        user_income_percentile = get_percentile(peer_monthly_incomes, user_monthly_income)
        user_activity_percentile = get_percentile(peer_transaction_counts, user_transaction_count)
        
        # Generate dynamic goals based on peer performance
        personalized_goals = []
        
        # Savings goal
        if user_savings_percentile < 75:
            target_savings = max(avg_peer_savings * 1.2, user_total_savings + 2000)
            if avg_peer_savings > 0:
                personalized_goals.append({
                    "type": "savings_catch_up",
                    "title": f"Match Your {user_university} Peers",
                    "description": f"Your campus average is ₹{avg_peer_savings:,.0f} in savings. You're at ₹{user_total_savings:,.0f}",
                    "target_amount": target_savings,
                    "current_amount": user_total_savings,
                    "progress": min(100, (user_total_savings / target_savings) * 100),
                    "peer_context": f"You're in the {user_savings_percentile}th percentile at {user_university}",
                    "motivation": "🎯 Beat the campus average and climb the leaderboard!",
                    "category": "peer_comparison",
                    "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                    "reward_points": 500
                })
        else:
            # User is already above average, set stretch goal
            top_10_threshold = peer_savings[int(len(peer_savings) * 0.9):] if peer_savings else [user_total_savings * 1.5]
            target_savings = max(top_10_threshold) if top_10_threshold else user_total_savings * 1.3
            
            personalized_goals.append({
                "type": "excellence_goal",
                "title": f"Join {user_university} Top 10%",
                "description": f"You're doing great! Aim for top 10% savings at {user_university}",
                "target_amount": target_savings,
                "current_amount": user_total_savings,
                "progress": min(100, (user_total_savings / target_savings) * 100),
                "peer_context": f"You're in the {user_savings_percentile}th percentile - excellent!",
                "motivation": "👑 Become a campus savings leader!",
                "category": "excellence",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=45)).isoformat(),
                "reward_points": 1000
            })
        
        # Activity goal
        if user_activity_percentile < 60:
            target_transactions = max(avg_peer_transactions * 1.1, user_transaction_count + 10)
            personalized_goals.append({
                "type": "activity_boost",
                "title": "Increase Financial Activity",
                "description": f"Your peers track {avg_peer_transactions:.0f} transactions on average",
                "target_amount": target_transactions,
                "current_amount": user_transaction_count,
                "progress": min(100, (user_transaction_count / target_transactions) * 100),
                "peer_context": f"More tracking leads to better insights and results",
                "motivation": "📊 Track more, save more!",
                "category": "activity",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
                "reward_points": 200
            })
        
        # Income goal
        if avg_peer_monthly_income > user_monthly_income and avg_peer_monthly_income > 1000:
            target_income = avg_peer_monthly_income * 1.1
            personalized_goals.append({
                "type": "income_growth",
                "title": "Boost Your Monthly Income",
                "description": f"Your campus peers earn ₹{avg_peer_monthly_income:,.0f}/month on average",
                "target_amount": target_income,
                "current_amount": user_monthly_income,
                "progress": min(100, (user_monthly_income / target_income) * 100),
                "peer_context": f"Explore side hustles and opportunities",
                "motivation": "💰 Increase your earning potential!",
                "category": "income",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=60)).isoformat(),
                "reward_points": 750
            })
        
        return {
            "user_performance": {
                "savings": user_total_savings,
                "monthly_income": user_monthly_income,
                "transaction_count": user_transaction_count
            },
            "peer_benchmarks": {
                "university": user_university,
                "avg_savings": avg_peer_savings,
                "avg_monthly_income": avg_peer_monthly_income,
                "avg_transactions": avg_peer_transactions,
                "peer_count": len(peer_user_ids)
            },
            "percentiles": {
                "savings": user_savings_percentile,
                "income": user_income_percentile,
                "activity": user_activity_percentile
            },
            "personalized_goals": personalized_goals,
            "overall_ranking": f"Top {100 - max(user_savings_percentile, user_income_percentile)}% at {user_university}"
        }
        
    except Exception as e:
        logger.error(f"Personalized goals error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate personalized goals")

# Helper function for monthly income calculation
async def get_user_monthly_income(user_id: str) -> float:
    """Calculate user's average monthly income"""
    try:
        # Get income transactions from last 3 months
        three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)
        
        income_transactions = await db.transactions.find({
            "user_id": user_id,
            "type": "income",
            "created_at": {"$gte": three_months_ago}
        }).to_list(None)
        
        if not income_transactions:
            return 0.0
        
        # Calculate monthly average
        total_income = sum(t.get("amount", 0) for t in income_transactions)
        months = min(3, max(1, len(income_transactions) / 10))  # Estimate months based on transactions
        
        return total_income / months
        
    except Exception as e:
        logger.error(f"Monthly income calculation error: {e}")
        return 0.0

# Habit tracking with social pressure
@api_router.get("/retention/habit-tracking")
@limiter.limit("20/minute")
async def get_habit_tracking_status(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get habit tracking status with social pressure elements"""
    try:
        # Get user info
        user_doc = await get_user_by_id(user_id)
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Define core financial habits to track
        today = datetime.now(timezone.utc).date()
        
        # Get user's activity for last 30 days
        thirty_days_ago = today - timedelta(days=30)
        
        # Track daily check-ins
        checkin_days = await db.daily_checkins.find({
            "user_id": user_id,
            "date": {"$gte": thirty_days_ago.isoformat()}
        }).to_list(None)
        
        checkin_dates = set(c["date"] for c in checkin_days)
        
        # Track transaction logging days
        transaction_days = await db.transactions.distinct("created_at", {
            "user_id": user_id,
            "created_at": {"$gte": datetime.combine(thirty_days_ago, datetime.min.time())}
        })
        transaction_dates = set(d.date().isoformat() for d in transaction_days)
        
        # Track budget adherence days
        budget_check_days = await db.transactions.find({
            "user_id": user_id,
            "type": "expense",
            "created_at": {"$gte": datetime.combine(thirty_days_ago, datetime.min.time())}
        }).to_list(None)
        
        budget_adherence_dates = set()
        for transaction in budget_check_days:
            # Check if expense was within budget (simplified check)
            date_str = transaction["created_at"].date().isoformat()
            budget_adherence_dates.add(date_str)
        
        # Get friends for social pressure
        friends = await db.friendships.find({
            "$or": [
                {"user_id": user_id, "status": "active"},
                {"friend_id": user_id, "status": "active"}
            ]
        }).to_list(None)
        
        friend_ids = []
        for friendship in friends:
            friend_id = friendship["friend_id"] if friendship["user_id"] == user_id else friendship["user_id"]
            friend_ids.append(friend_id)
        
        # Get friends' habit performance for social comparison
        friends_performance = []
        for friend_id in friend_ids[:10]:  # Limit for performance
            friend_checkins = await db.daily_checkins.count_documents({
                "user_id": friend_id,
                "date": {"$gte": thirty_days_ago.isoformat()}
            })
            
            friend_transactions = await db.transactions.distinct("created_at", {
                "user_id": friend_id,
                "created_at": {"$gte": datetime.combine(thirty_days_ago, datetime.min.time())}
            })
            friend_transaction_days = len(set(d.date() for d in friend_transactions))
            
            friend_doc = await get_user_by_id(friend_id)
            friends_performance.append({
                "friend_id": friend_id,
                "name": friend_doc.get("name", "Friend") if friend_doc else "Friend",
                "avatar": friend_doc.get("avatar", "man") if friend_doc else "man",
                "checkin_days": friend_checkins,
                "transaction_days": friend_transaction_days,
                "total_habit_score": friend_checkins + friend_transaction_days
            })
        
        # Calculate user's habit scores
        user_checkin_days = len(checkin_dates)
        user_transaction_days = len(transaction_dates)
        user_budget_days = len(budget_adherence_dates)
        user_total_score = user_checkin_days + user_transaction_days + user_budget_days
        
        # Calculate habit streaks
        def calculate_habit_streak(date_set, habit_name):
            """Calculate current streak for a habit"""
            streak = 0
            current_date = today
            
            while current_date >= thirty_days_ago:
                if current_date.isoformat() in date_set:
                    streak += 1
                    current_date -= timedelta(days=1)
                else:
                    break
            
            return streak
        
        checkin_streak = calculate_habit_streak(checkin_dates, "check-in")
        transaction_streak = calculate_habit_streak(transaction_dates, "transaction")
        
        # Generate social pressure messages
        friends_performance.sort(key=lambda x: x["total_habit_score"], reverse=True)
        
        social_pressure_messages = []
        
        if friends_performance:
            top_performer = friends_performance[0]
            if top_performer["total_habit_score"] > user_total_score:
                social_pressure_messages.append({
                    "type": "competition",
                    "message": f"{top_performer['name']} is leading with {top_performer['total_habit_score']} habit points this month!",
                    "action": "Catch up by checking in daily and tracking expenses",
                    "urgency": "high" if top_performer["total_habit_score"] - user_total_score > 10 else "medium"
                })
            
            avg_friend_score = sum(f["total_habit_score"] for f in friends_performance) / len(friends_performance)
            if user_total_score < avg_friend_score:
                social_pressure_messages.append({
                    "type": "peer_pressure",
                    "message": f"Your friends average {avg_friend_score:.1f} habit points. You have {user_total_score}",
                    "action": "Stay consistent with your financial habits",
                    "urgency": "medium"
                })
        
        # Habit tracking goals with social elements
        habits = [
            {
                "name": "Daily Check-in",
                "description": "Check in daily to earn points and maintain streaks",
                "current_streak": checkin_streak,
                "days_this_month": user_checkin_days,
                "target_days": 25,  # Target 25 out of 30 days
                "progress": min(100, (user_checkin_days / 25) * 100),
                "icon": "✅",
                "social_ranking": sum(1 for f in friends_performance if f["checkin_days"] < user_checkin_days) + 1,
                "total_friends": len(friends_performance) + 1
            },
            {
                "name": "Transaction Tracking",
                "description": "Log your income and expenses regularly",
                "current_streak": transaction_streak,
                "days_this_month": user_transaction_days,
                "target_days": 20,  # Target 20 days of activity
                "progress": min(100, (user_transaction_days / 20) * 100),
                "icon": "💰",
                "social_ranking": sum(1 for f in friends_performance if f["transaction_days"] < user_transaction_days) + 1,
                "total_friends": len(friends_performance) + 1
            },
            {
                "name": "Budget Awareness",
                "description": "Stay mindful of your spending limits",
                "current_streak": len(budget_adherence_dates),
                "days_this_month": user_budget_days,
                "target_days": 15,  # Target mindful spending
                "progress": min(100, (user_budget_days / 15) * 100),
                "icon": "📊",
                "social_ranking": "N/A",  # Not compared with friends
                "total_friends": "N/A"
            }
        ]
        
        return {
            "user_habit_score": user_total_score,
            "habits": habits,
            "social_comparison": {
                "friends_performance": friends_performance[:5],  # Top 5 friends
                "user_ranking": sum(1 for f in friends_performance if f["total_habit_score"] < user_total_score) + 1,
                "total_participants": len(friends_performance) + 1
            },
            "social_pressure_messages": social_pressure_messages,
            "monthly_summary": {
                "check_in_days": user_checkin_days,
                "transaction_days": user_transaction_days,
                "budget_awareness_days": user_budget_days,
                "total_score": user_total_score,
                "month_target": 60,  # Combined target score
                "progress": min(100, (user_total_score / 60) * 100)
            }
        }
        
    except Exception as e:
        logger.error(f"Habit tracking error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get habit tracking status")

# Weekly recap with social comparison elements  
@api_router.get("/retention/weekly-recap")
@limiter.limit("10/minute")
async def get_weekly_recap(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get weekly recap with social comparison elements"""
    try:
        # Get user info
        user_doc = await get_user_by_id(user_id)
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Calculate this week's date range
        today = datetime.now(timezone.utc).date()
        week_start = today - timedelta(days=today.weekday())  # Monday
        week_end = week_start + timedelta(days=6)  # Sunday
        
        # Get this week's user activity
        week_start_dt = datetime.combine(week_start, datetime.min.time()).replace(tzinfo=timezone.utc)
        week_end_dt = datetime.combine(week_end, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        # User's weekly stats
        weekly_transactions = await db.transactions.find({
            "user_id": user_id,
            "created_at": {"$gte": week_start_dt, "$lte": week_end_dt}
        }).to_list(None)
        
        weekly_checkins = await db.daily_checkins.count_documents({
            "user_id": user_id,
            "date": {"$gte": week_start.isoformat(), "$lte": week_end.isoformat()}
        })
        
        # Calculate user metrics
        weekly_income = sum(t.get("amount", 0) for t in weekly_transactions if t["type"] == "income")
        weekly_expenses = sum(t.get("amount", 0) for t in weekly_transactions if t["type"] == "expense")
        weekly_savings = weekly_income - weekly_expenses
        
        # Get friends for comparison
        friends = await db.friendships.find({
            "$or": [
                {"user_id": user_id, "status": "active"},
                {"friend_id": user_id, "status": "active"}
            ]
        }).to_list(None)
        
        friend_ids = []
        for friendship in friends:
            friend_id = friendship["friend_id"] if friendship["user_id"] == user_id else friendship["user_id"]
            friend_ids.append(friend_id)
        
        # Get friends' weekly performance
        friends_weekly_stats = []
        
        for friend_id in friend_ids[:20]:  # Limit for performance
            friend_transactions = await db.transactions.find({
                "user_id": friend_id,
                "created_at": {"$gte": week_start_dt, "$lte": week_end_dt}
            }).to_list(None)
            
            friend_checkins = await db.daily_checkins.count_documents({
                "user_id": friend_id,
                "date": {"$gte": week_start.isoformat(), "$lte": week_end.isoformat()}
            })
            
            friend_income = sum(t.get("amount", 0) for t in friend_transactions if t["type"] == "income")
            friend_expenses = sum(t.get("amount", 0) for t in friend_transactions if t["type"] == "expense")
            friend_savings = friend_income - friend_expenses
            
            friend_doc = await get_user_by_id(friend_id)
            
            friends_weekly_stats.append({
                "friend_id": friend_id,
                "name": friend_doc.get("name", "Friend") if friend_doc else "Friend",
                "avatar": friend_doc.get("avatar", "man") if friend_doc else "man",
                "savings": friend_savings,
                "checkins": friend_checkins,
                "transactions": len(friend_transactions),
                "activity_score": friend_checkins + len(friend_transactions)
            })
        
        # Calculate comparative metrics
        if friends_weekly_stats:
            avg_friend_savings = sum(f["savings"] for f in friends_weekly_stats) / len(friends_weekly_stats)
            avg_friend_checkins = sum(f["checkins"] for f in friends_weekly_stats) / len(friends_weekly_stats)
            avg_friend_transactions = sum(f["transactions"] for f in friends_weekly_stats) / len(friends_weekly_stats)
            
            # Rankings
            friends_by_savings = sorted(friends_weekly_stats, key=lambda x: x["savings"], reverse=True)
            friends_by_activity = sorted(friends_weekly_stats, key=lambda x: x["activity_score"], reverse=True)
            
            user_savings_rank = sum(1 for f in friends_weekly_stats if f["savings"] < weekly_savings) + 1
            user_activity_rank = sum(1 for f in friends_weekly_stats if f["activity_score"] < weekly_checkins + len(weekly_transactions)) + 1
        else:
            avg_friend_savings = 0
            avg_friend_checkins = 0
            avg_friend_transactions = 0
            friends_by_savings = []
            friends_by_activity = []
            user_savings_rank = 1
            user_activity_rank = 1
        
        # Generate achievements and insights
        weekly_achievements = []
        
        if weekly_checkins >= 6:
            weekly_achievements.append({
                "type": "consistency",
                "title": "Consistency Champion",
                "description": f"Checked in {weekly_checkins}/7 days this week!",
                "icon": "🎯"
            })
        
        if weekly_savings > 0:
            weekly_achievements.append({
                "type": "savings",
                "title": "Positive Saver",
                "description": f"Saved ₹{weekly_savings:.0f} this week!",
                "icon": "💰"
            })
        
        if weekly_savings > avg_friend_savings and friends_weekly_stats:
            weekly_achievements.append({
                "type": "social",
                "title": "Savings Leader",
                "description": "You out-saved your friend group this week!",
                "icon": "🏆"
            })
        
        # Social comparison insights
        comparison_insights = []
        
        if friends_weekly_stats:
            if weekly_savings > avg_friend_savings:
                comparison_insights.append({
                    "type": "positive",
                    "message": f"You saved ₹{weekly_savings - avg_friend_savings:.0f} more than your friends' average",
                    "icon": "📈"
                })
            elif avg_friend_savings > weekly_savings:
                comparison_insights.append({
                    "type": "motivational",
                    "message": f"Your friends averaged ₹{avg_friend_savings:.0f} in savings. You can catch up!",
                    "icon": "🎯"
                })
            
            if weekly_checkins > avg_friend_checkins:
                comparison_insights.append({
                    "type": "positive",
                    "message": f"You checked in more consistently than {len([f for f in friends_weekly_stats if f['checkins'] < weekly_checkins])} friends",
                    "icon": "✅"
                })
        
        return {
            "week_period": {
                "start": week_start.isoformat(),
                "end": week_end.isoformat(),
                "week_number": week_start.isocalendar()[1]
            },
            "user_stats": {
                "income": weekly_income,
                "expenses": weekly_expenses,
                "savings": weekly_savings,
                "checkins": weekly_checkins,
                "transactions": len(weekly_transactions),
                "activity_score": weekly_checkins + len(weekly_transactions)
            },
            "social_comparison": {
                "friend_averages": {
                    "savings": avg_friend_savings,
                    "checkins": avg_friend_checkins,
                    "transactions": avg_friend_transactions
                },
                "rankings": {
                    "savings_rank": user_savings_rank,
                    "activity_rank": user_activity_rank,
                    "total_participants": len(friends_weekly_stats) + 1
                },
                "top_performers": {
                    "savings": friends_by_savings[:3],
                    "activity": friends_by_activity[:3]
                }
            },
            "achievements": weekly_achievements,
            "insights": comparison_insights,
            "next_week_goals": [
                {
                    "type": "consistency",
                    "title": "Perfect Week Challenge",
                    "description": "Check in all 7 days next week",
                    "target": 7,
                    "reward_points": 200
                },
                {
                    "type": "savings",
                    "title": "Beat This Week",
                    "description": f"Save more than ₹{weekly_savings:.0f} next week",
                    "target": weekly_savings + 500,
                    "reward_points": 300
                },
                {
                    "type": "social",
                    "title": "Friend Challenge",
                    "description": "Outperform your friend group average",
                    "target": avg_friend_savings,
                    "reward_points": 400
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Weekly recap error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate weekly recap")

# ================================================================================================
# PHASE 4: SHARING TOOLS IMPLEMENTATION
# ================================================================================================

# LinkedIn achievement posts
@api_router.post("/sharing/linkedin-post")
@limiter.limit("10/minute")
async def generate_linkedin_achievement_post(
    request: Request,
    post_data: dict,
    user_id: str = Depends(get_current_user)
):
    """Generate LinkedIn-ready achievement post content"""
    try:
        achievement_type = post_data.get("achievement_type")
        achievement_details = post_data.get("details", {})
        
        # Get user info
        user_info = await db.users.find_one({"user_id": user_id})
        user_name = user_info.get("name", "")
        university = user_info.get("university", "")
        
        # Generate LinkedIn post templates
        linkedin_templates = {
            "savings_milestone": {
                "text": f"🎯 Excited to share that I've reached my savings milestone of ₹{achievement_details.get('amount', 0)}! \n\n💡 Using EarnAura has helped me develop better financial habits as a {university} student. The gamification and peer comparison features keep me motivated to save consistently.\n\n#FinancialLiteracy #StudentLife #SavingsGoals #EarnAura #PersonalFinance #StudentSuccess",
                "hashtags": ["#FinancialLiteracy", "#StudentLife", "#SavingsGoals", "#EarnAura", "#PersonalFinance"],
                "suggested_image": "achievement_badge"
            },
            "streak_achievement": {
                "text": f"🔥 {achievement_details.get('days', 0)}-day financial tracking streak achieved! \n\n📊 Consistency in money management has been a game-changer. Every day of tracking my expenses and income brings me closer to my financial goals.\n\n💪 To fellow students: small daily habits lead to big financial wins!\n\n#FinancialHabits #ConsistencyMatters #StudentFinance #MoneyManagement #EarnAura #FinancialGoals",
                "hashtags": ["#FinancialHabits", "#ConsistencyMatters", "#StudentFinance"],
                "suggested_image": "streak_badge"
            },
            "income_milestone": {
                "text": f"💰 Just earned my first ₹{achievement_details.get('amount', 0)} through side hustles! \n\n🚀 EarnAura's opportunity matching helped me find legitimate freelancing gigs that fit my schedule as a student.\n\n📈 Proof that with the right tools and mindset, students can build multiple income streams while studying.\n\n#SideHustle #StudentEntrepreneur #FinancialIndependence #EarnAura #FreelanceLife #StudentSuccess",
                "hashtags": ["#SideHustle", "#StudentEntrepreneur", "#FinancialIndependence"],
                "suggested_image": "income_achievement"
            }
        }
        
        template = linkedin_templates.get(achievement_type, {
            "text": f"🎉 Achieved a new financial milestone with EarnAura! \n\n📱 The app's gamification and social features make money management engaging and fun. Highly recommend to fellow students!\n\n#FinancialLiteracy #StudentLife #EarnAura",
            "hashtags": ["#FinancialLiteracy", "#StudentLife", "#EarnAura"],
            "suggested_image": "general_achievement"
        })
        
        # Track sharing for analytics
        sharing_record = {
            "user_id": user_id,
            "platform": "linkedin",
            "achievement_type": achievement_type,
            "shared_at": datetime.now(timezone.utc),
            "content_preview": template["text"][:100] + "..."
        }
        await db.social_shares.insert_one(sharing_record)
        
        return {
            "platform": "linkedin",
            "post_content": template["text"],
            "hashtags": template["hashtags"],
            "suggested_image": template["suggested_image"],
            "copy_instructions": "Copy this text and paste it as your LinkedIn post. Add the suggested image for better engagement!",
            "engagement_tip": "Post between 8-10 AM or 12-2 PM for maximum visibility"
        }
        
    except Exception as e:
        logger.error(f"LinkedIn post generation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate LinkedIn post")

# One-click sharing to multiple platforms
@api_router.post("/sharing/multi-platform")
@limiter.limit("15/minute")
async def share_to_multiple_platforms(
    request: Request,
    share_data: dict,
    user_id: str = Depends(get_current_user)
):
    """Generate sharing content for multiple platforms simultaneously"""
    try:
        achievement_data = share_data.get("achievement", {})
        platforms = share_data.get("platforms", ["instagram", "whatsapp", "twitter"])
        
        sharing_content = {}
        
        for platform in platforms:
            if platform == "instagram":
                sharing_content["instagram"] = {
                    "caption": f"🎯 New milestone unlocked! 💰\n\n#{achievement_data.get('type', 'achievement')} #StudentLife #FinancialGoals #EarnAura #MoneyManagement #StudentSuccess #FinancialLiteracy",
                    "story_text": f"Just hit my savings goal! 🎉\n₹{achievement_data.get('amount', 0)} milestone reached",
                    "share_url": f"https://instagram.com/stories/new",
                    "instructions": "Share to your Instagram story with the generated image"
                }
            
            elif platform == "whatsapp":
                sharing_content["whatsapp"] = {
                    "message": f"🎉 Just achieved a financial milestone! Saved ₹{achievement_data.get('amount', 0)} using EarnAura app 💰\n\nIt's amazing how gamification makes saving money fun! 📊\n\nDownload: https://earnaura.app",
                    "share_url": f"https://wa.me/?text={achievement_data.get('message', '').replace(' ', '%20')}",
                    "instructions": "Click to share on WhatsApp Status or send to friends"
                }
            
            elif platform == "twitter":
                tweet_text = f"🎯 Financial milestone achieved! ₹{achievement_data.get('amount', 0)} saved with @EarnAura 💰\n\nGamefication + Social features = Consistent savings habits 📈\n\n#FinTech #StudentLife #SavingsGoals"
                sharing_content["twitter"] = {
                    "tweet": tweet_text,
                    "share_url": f"https://twitter.com/intent/tweet?text={tweet_text.replace(' ', '%20')}",
                    "instructions": "Click to post this tweet"
                }
            
            elif platform == "facebook":
                sharing_content["facebook"] = {
                    "post": f"Excited to share my latest financial achievement! 🎯\n\nReached my ₹{achievement_data.get('amount', 0)} savings goal using EarnAura. The app's social features and gamification make money management actually enjoyable!\n\nHighly recommend to students looking to build better financial habits. 📊💪\n\n#FinancialLiteracy #StudentLife #MoneyManagement",
                    "share_url": f"https://www.facebook.com/sharer/sharer.php?u=https://earnaura.app",
                    "instructions": "Share this post on your Facebook timeline"
                }
        
        # Track multi-platform sharing
        for platform in platforms:
            sharing_record = {
                "user_id": user_id,
                "platform": platform,
                "achievement_type": achievement_data.get("type"),
                "shared_at": datetime.now(timezone.utc),
                "is_multi_platform": True
            }
            await db.social_shares.insert_one(sharing_record)
        
        return {
            "platforms": sharing_content,
            "total_platforms": len(platforms),
            "sharing_tip": "Posting across multiple platforms increases your reach and can inspire friends to join!",
            "bonus_points": len(platforms) * 10  # Bonus points for multi-platform sharing
        }
        
    except Exception as e:
        logger.error(f"Multi-platform sharing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate multi-platform sharing content")

# Viral referral links with tracking
@api_router.post("/sharing/create-viral-link")
@limiter.limit("10/minute")
async def create_viral_referral_link(
    request: Request,
    link_data: dict,
    user_id: str = Depends(get_current_user)
):
    """Create tracked viral referral link with incentives"""
    try:
        campaign_type = link_data.get("campaign_type", "general_referral")
        custom_message = link_data.get("custom_message", "")
        
        # Generate unique tracking code
        tracking_code = f"{user_id[:8]}-{str(uuid.uuid4())[:8]}-{campaign_type}"
        
        # Get user info for personalization
        user_info = await db.users.find_one({"user_id": user_id})
        user_name = user_info.get("name", "Your friend")
        university = user_info.get("university", "")
        
        # Create viral referral record
        viral_link = {
            "link_id": str(uuid.uuid4()),
            "user_id": user_id,
            "tracking_code": tracking_code,
            "campaign_type": campaign_type,
            "custom_message": custom_message,
            "clicks": 0,
            "conversions": 0,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
            "is_active": True
        }
        
        await db.viral_referral_links.insert_one(viral_link)
        
        # Generate referral URL
        base_url = "https://earnaura.app"
        referral_url = f"{base_url}/join?ref={tracking_code}"
        
        # Create sharing templates with urgency and social proof
        sharing_templates = {
            "achievement_viral": {
                "title": "I just hit my savings goal! 🎯",
                "message": f"Just saved ₹5000 using EarnAura! The app made it so much easier with gamification and friend challenges.\n\nJoin me and get ₹50 bonus when you save your first ₹500! 💰\n\nLimited time: Only 100 spots left this month!\n\n{referral_url}",
                "urgency": "Only 100 spots left this month!",
                "incentive": "₹50 bonus for first ₹500 saved"
            },
            "challenge_viral": {
                "title": "Join my savings challenge! 🏆", 
                "message": f"Starting a 30-day savings challenge with friends on EarnAura!\n\nWe're competing to see who can save the most. Want to join us? 🎯\n\n🎁 New members get ₹50 bonus\n⏰ Challenge starts in 3 days\n👥 {university} students only\n\n{referral_url}",
                "urgency": "Challenge starts in 3 days",
                "incentive": "₹50 joining bonus + competition prizes"
            },
            "milestone_viral": {
                "title": "This app changed my money habits! 📊",
                "message": f"EarnAura helped me save ₹10,000 in just 2 months! 🎉\n\nThe social features and AI insights are incredible. My friends and I challenge each other daily.\n\n🎁 Get ₹50 when you join\n🔥 Limited: Only for {university} students\n⭐ 4.8/5 rating\n\n{referral_url}",
                "urgency": f"Limited to {university} students",
                "incentive": "₹50 welcome bonus"
            }
        }
        
        template = sharing_templates.get(campaign_type, sharing_templates["achievement_viral"])
        
        return {
            "referral_url": referral_url,
            "tracking_code": tracking_code,
            "sharing_template": template,
            "qr_code_url": f"/api/sharing/qr-code/{tracking_code}",
            "analytics_url": f"/api/sharing/link-analytics/{viral_link['link_id']}",
            "expiry_date": viral_link["expires_at"].isoformat(),
            "viral_tips": [
                "Share in student WhatsApp groups for maximum reach",
                "Post when your friends are most active (evenings)",
                "Add personal success story for credibility",
                "Follow up with friends who click but don't sign up"
            ]
        }
        
    except Exception as e:
        logger.error(f"Viral referral link error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create viral referral link")

# ================================================================================================
# PHASE 5: ADVANCED SOCIAL & GROWTH MECHANICS
# ================================================================================================

# Campus ambassador program
@api_router.post("/advanced/apply-campus-ambassador")
@limiter.limit("5/minute")
async def apply_campus_ambassador(
    request: Request,
    application_data: dict,
    user_id: str = Depends(get_current_user)
):
    """Apply for campus ambassador program"""
    try:
        # Check eligibility requirements
        user_stats = await db.user_stats.find_one({"user_id": user_id})
        transaction_count = await db.transactions.count_documents({"user_id": user_id})
        referral_count = await db.referral_programs.count_documents({
            "referred_by": user_id,
            "status": "active"
        })
        
        # Requirements: 50+ transactions, 10+ referrals, 30+ days active
        eligible = (
            transaction_count >= 50 and
            referral_count >= 10 and
            user_stats and user_stats.get("days_active", 0) >= 30
        )
        
        if not eligible:
            return {
                "eligible": False,
                "requirements": {
                    "transactions_needed": max(0, 50 - transaction_count),
                    "referrals_needed": max(0, 10 - referral_count),
                    "days_needed": max(0, 30 - user_stats.get("days_active", 0) if user_stats else 30)
                },
                "message": "Complete the requirements to unlock Ambassador status!"
            }
        
        # Create ambassador application
        application = {
            "application_id": str(uuid.uuid4()),
            "user_id": user_id,
            "motivation": application_data.get("motivation", ""),
            "campus_influence": application_data.get("campus_influence", ""),
            "social_media_handles": application_data.get("social_media", {}),
            "marketing_ideas": application_data.get("marketing_ideas", []),
            "status": "pending",
            "applied_at": datetime.now(timezone.utc),
            "stats_at_application": {
                "transactions": transaction_count,
                "referrals": referral_count,
                "days_active": user_stats.get("days_active", 0) if user_stats else 0
            }
        }
        
        await db.ambassador_applications.insert_one(application)
        
        return {
            "success": True,
            "application_id": application["application_id"],
            "message": "Application submitted! We'll review within 3-5 business days.",
            "benefits_preview": [
                "₹500/month base stipend",
                "₹50 per successful referral",
                "Exclusive ambassador badge and features",
                "Direct line to product team",
                "Campus event organizing opportunities"
            ]
        }
        
    except Exception as e:
        logger.error(f"Campus ambassador application error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit ambassador application")

# Group expense splitting with friends
@api_router.post("/advanced/create-expense-split")
@limiter.limit("20/minute")
async def create_group_expense_split(
    request: Request,
    split_data: dict,
    user_id: str = Depends(get_current_user)
):
    """Create group expense split with friends"""
    try:
        expense_title = split_data.get("title")
        total_amount = split_data.get("total_amount")
        participants = split_data.get("participants", [])  # List of friend user_ids
        split_type = split_data.get("split_type", "equal")  # equal, custom, percentage
        custom_splits = split_data.get("custom_splits", {})
        
        # Validate participants are friends
        for participant_id in participants:
            friendship = await db.friends.find_one({
                "$or": [
                    {"user_id": user_id, "friend_id": participant_id},
                    {"user_id": participant_id, "friend_id": user_id}
                ],
                "status": "accepted"
            })
            
            if not friendship:
                raise HTTPException(status_code=400, detail=f"User {participant_id} is not your friend")
        
        # Calculate splits
        splits = {}
        if split_type == "equal":
            amount_per_person = total_amount / (len(participants) + 1)  # +1 for creator
            splits[user_id] = amount_per_person
            for participant_id in participants:
                splits[participant_id] = amount_per_person
        else:
            splits = custom_splits
        
        # Create expense split record
        expense_split = {
            "split_id": str(uuid.uuid4()),
            "creator_id": user_id,
            "title": expense_title,
            "total_amount": total_amount,
            "split_type": split_type,
            "participants": participants + [user_id],
            "splits": splits,
            "payments": {user_id: total_amount},  # Creator paid initially
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "settled_at": None
        }
        
        await db.expense_splits.insert_one(expense_split)
        
        # Create notifications for participants
        for participant_id in participants:
            notification = {
                "notification_id": str(uuid.uuid4()),
                "user_id": participant_id,
                "type": "expense_split",
                "title": "New Expense Split",
                "message": f"You owe ₹{splits.get(participant_id, 0):.2f} for '{expense_title}'",
                "data": {
                    "split_id": expense_split["split_id"],
                    "amount_owed": splits.get(participant_id, 0)
                },
                "is_read": False,
                "created_at": datetime.now(timezone.utc)
            }
            await db.notifications.insert_one(notification)
        
        return {
            "success": True,
            "split_id": expense_split["split_id"],
            "splits": splits,
            "payment_link": f"/api/advanced/expense-split/{expense_split['split_id']}",
            "total_amount": total_amount,
            "participants_notified": len(participants)
        }
        
    except Exception as e:
        logger.error(f"Group expense split error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create expense split")

# Invite quota system (limited invites create urgency)
@api_router.get("/growth/invite-quota")
@limiter.limit("10/minute")
async def get_user_invite_quota(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get user's invite quota and usage"""
    try:
        # Base quota: 5 invites per month
        base_quota = 5
        
        # Bonus quota based on user level/achievements
        user_level = await get_user_level(user_id)
        achievement_count = await db.user_achievements.count_documents({"user_id": user_id})
        
        bonus_quota = 0
        if user_level >= 5:
            bonus_quota += 3  # Level 5+ users get 3 extra
        if achievement_count >= 10:
            bonus_quota += 2  # Users with 10+ achievements get 2 extra
        
        total_quota = base_quota + bonus_quota
        
        # Get current month usage
        month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        invites_used = await db.friend_invitations.count_documents({
            "inviter_id": user_id,
            "created_at": {"$gte": month_start}
        })
        
        remaining_quota = max(0, total_quota - invites_used)
        
        # Check if user qualifies for bonus invites
        bonus_opportunities = []
        if user_level < 10:
            bonus_opportunities.append({
                "action": "Reach level 10",
                "reward": "+5 monthly invites",
                "progress": f"Level {user_level}/10"
            })
        
        if achievement_count < 20:
            bonus_opportunities.append({
                "action": "Earn 20 achievements",
                "reward": "+3 monthly invites",
                "progress": f"{achievement_count}/20 achievements"
            })
        
        # Create urgency messaging
        urgency_message = ""
        if remaining_quota <= 2:
            urgency_message = "⚠️ Only 2 invites left this month! Use them wisely."
        elif remaining_quota <= 5:
            urgency_message = f"🔥 {remaining_quota} invites remaining - invite your closest friends!"
        
        return {
            "quota": {
                "total": total_quota,
                "used": invites_used,
                "remaining": remaining_quota,
                "resets_at": (month_start + timedelta(days=32)).replace(day=1).isoformat()
            },
            "breakdown": {
                "base_quota": base_quota,
                "level_bonus": 3 if user_level >= 5 else 0,
                "achievement_bonus": 2 if achievement_count >= 10 else 0
            },
            "urgency_message": urgency_message,
            "bonus_opportunities": bonus_opportunities,
            "scarcity_marketing": f"Only {remaining_quota} exclusive spots available this month!"
        }
        
    except Exception as e:
        logger.error(f"Invite quota error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get invite quota")

async def get_user_level(user_id: str) -> int:
    """Helper function to get user's current level"""
    try:
        gamification_service = get_gamification_service()
        if gamification_service:
            profile = await gamification_service.get_user_profile(user_id)
            return profile.get("level", 1)
        return 1
    except:
        return 1

# Waiting list for exclusive features
@api_router.post("/growth/join-waitlist")
@limiter.limit("5/minute")
async def join_feature_waitlist(
    request: Request,
    waitlist_data: dict,
    user_id: str = Depends(get_current_user)
):
    """Join waiting list for exclusive features"""
    try:
        feature_name = waitlist_data.get("feature_name")
        
        # Check if already on waitlist
        existing = await db.feature_waitlist.find_one({
            "user_id": user_id,
            "feature_name": feature_name
        })
        
        if existing:
            return {
                "success": False,
                "message": "You're already on the waitlist for this feature!"
            }
        
        # Get current waitlist position
        current_position = await db.feature_waitlist.count_documents({
            "feature_name": feature_name
        }) + 1
        
        # Create waitlist entry
        waitlist_entry = {
            "entry_id": str(uuid.uuid4()),
            "user_id": user_id,
            "feature_name": feature_name,
            "position": current_position,
            "joined_at": datetime.now(timezone.utc),
            "status": "waiting",
            "priority_score": await calculate_priority_score(user_id)
        }
        
        await db.feature_waitlist.insert_one(waitlist_entry)
        
        # Feature descriptions and estimated timeline
        features_info = {
            "crypto_tracking": {
                "description": "Portfolio tracking for cryptocurrency investments",
                "eta": "Q2 2025",
                "spots_available": 500
            },
            "ai_investment_advisor": {
                "description": "AI-powered investment recommendations",
                "eta": "Q3 2025", 
                "spots_available": 200
            },
            "premium_mentorship": {
                "description": "1-on-1 sessions with financial experts",
                "eta": "Q1 2025",
                "spots_available": 100
            }
        }
        
        feature_info = features_info.get(feature_name, {
            "description": "Exclusive new feature",
            "eta": "Coming soon",
            "spots_available": 1000
        })
        
        return {
            "success": True,
            "position": current_position,
            "feature_info": feature_info,
            "estimated_wait": f"{max(1, current_position // 50)} weeks",
            "early_access_tip": "Invite friends and complete challenges to move up the list!",
            "total_waiting": current_position
        }
        
    except Exception as e:
        logger.error(f"Waitlist join error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to join waitlist")

async def calculate_priority_score(user_id: str) -> int:
    """Calculate user's priority score for waitlists"""
    score = 0
    
    # Base score from transactions
    transaction_count = await db.transactions.count_documents({"user_id": user_id})
    score += min(transaction_count * 2, 100)  # Max 100 from transactions
    
    # Referrals bonus
    referral_count = await db.referral_programs.count_documents({"referred_by": user_id})
    score += min(referral_count * 10, 200)  # Max 200 from referrals
    
    # Achievement bonus
    achievement_count = await db.user_achievements.count_documents({"user_id": user_id})
    score += min(achievement_count * 5, 150)  # Max 150 from achievements
    
    # Active days bonus
    user_stats = await db.user_stats.find_one({"user_id": user_id})
    if user_stats:
        days_active = user_stats.get("days_active", 0)
        score += min(days_active * 2, 100)  # Max 100 from activity
    
    return score

# ================================================================================================
# ADDITIONAL ENGAGEMENT & RETENTION FEATURES
# ================================================================================================

# Limited-time offers/challenges with deadlines  
@api_router.get("/engagement/limited-offers")
@limiter.limit("10/minute")
async def get_limited_time_offers(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get current limited-time offers and challenges"""
    try:
        now = datetime.now(timezone.utc)
        
        # Create dynamic offers based on time
        offers = []
        
        # Weekend saving bonus (Friday-Sunday)
        if now.weekday() >= 4:  # Friday=4, Saturday=5, Sunday=6
            weekend_end = now.replace(hour=23, minute=59, second=59)
            if now.weekday() == 6:  # Sunday
                weekend_end = now.replace(hour=23, minute=59, second=59)
            else:
                # Calculate next Sunday
                days_until_sunday = 6 - now.weekday()
                weekend_end = now + timedelta(days=days_until_sunday)
                weekend_end = weekend_end.replace(hour=23, minute=59, second=59)
            
            offers.append({
                "id": "weekend_bonus",
                "title": "Weekend Savings Bonus! 🎉",
                "description": "Earn double points for all transactions this weekend",
                "type": "points_multiplier",
                "multiplier": 2,
                "deadline": weekend_end.isoformat(),
                "hours_remaining": int((weekend_end - now).total_seconds() // 3600),
                "urgency": "high",
                "icon": "⚡"
            })
        
        # Monthly challenge (last week of month)
        if now.day >= 22:
            month_end = (now.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            month_end = month_end.replace(hour=23, minute=59, second=59)
            
            offers.append({
                "id": "month_end_challenge",
                "title": "Month-End Sprint Challenge! 🏃‍♂️",
                "description": "Save ₹1000 before month ends - win ₹200 bonus!",
                "type": "savings_challenge",
                "target_amount": 1000,
                "reward": 200,
                "deadline": month_end.isoformat(),
                "days_remaining": (month_end.date() - now.date()).days,
                "urgency": "medium",
                "icon": "🎯"
            })
        
        # Flash social challenge (24-48 hours)
        flash_challenge_end = now + timedelta(hours=36)
        offers.append({
            "id": "flash_social",
            "title": "Flash Social Challenge! ⚡",
            "description": "Invite 3 friends in 36 hours - unlock exclusive badge",
            "type": "social_challenge",
            "target": 3,
            "reward": "Exclusive 'Social Lightning' badge",
            "deadline": flash_challenge_end.isoformat(),
            "hours_remaining": 36,
            "urgency": "high",
            "icon": "👥"
        })
        
        # Check user's participation in current offers
        for offer in offers:
            participation = await db.limited_offers_participation.find_one({
                "user_id": user_id,
                "offer_id": offer["id"],
                "expires_at": {"$gt": now}
            })
            offer["participated"] = bool(participation)
            offer["progress"] = participation.get("progress", 0) if participation else 0
        
        return {
            "offers": offers,
            "total_active": len(offers),
            "urgency_message": "⏰ Limited time offers expire soon! Act fast!",
            "next_offers_in": "New offers every weekend and month-end!"
        }
        
    except Exception as e:
        logger.error(f"Limited offers error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get limited offers")

# FOMO mechanics ("Only 50 spots left in challenge")
@api_router.get("/engagement/fomo-alerts")
@limiter.limit("10/minute")
async def get_fomo_alerts(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get FOMO (Fear of Missing Out) alerts and scarcity notifications"""
    try:
        fomo_alerts = []
        
        # Limited spots in challenges
        active_challenges = await db.group_challenges.find({
            "status": "active",
            "spots_remaining": {"$lte": 100, "$gt": 0}
        }).to_list(None)
        
        for challenge in active_challenges:
            spots_left = challenge.get("spots_remaining", 0)
            urgency_level = "high" if spots_left <= 10 else "medium" if spots_left <= 50 else "low"
            
            fomo_alerts.append({
                "type": "challenge_spots",
                "title": f"Only {spots_left} spots left! 🔥",
                "message": f"Challenge '{challenge['title']}' is filling up fast!",
                "urgency": urgency_level,
                "action": "Join now",
                "action_url": f"/group-challenges/{challenge['challenge_id']}",
                "spots_remaining": spots_left,
                "icon": "⚠️"
            })
        
        # Limited mentor slots
        available_mentors = 15 - (hash(user_id) % 10)  # Dynamic based on user
        if available_mentors <= 5:
            fomo_alerts.append({
                "type": "mentor_slots",
                "title": f"Only {available_mentors} mentor slots left this month!",
                "message": "Premium mentorship program almost full",
                "urgency": "high",
                "action": "Book session",
                "action_url": "/mentorship/book",
                "slots_remaining": available_mentors,
                "icon": "👨‍🏫"
            })
        
        # Exclusive feature access
        beta_spots = 25 - (len(user_id) % 15)  # Dynamic
        if beta_spots <= 10:
            fomo_alerts.append({
                "type": "beta_access",
                "title": f"Beta access: {beta_spots} spots remaining!",
                "message": "Early access to AI investment advisor",
                "urgency": "medium",
                "action": "Join beta",
                "action_url": "/growth/join-waitlist",
                "spots_remaining": beta_spots,
                "icon": "🚀"
            })
        
        # Time-sensitive achievements
        if datetime.now().day <= 7:  # First week of month
            fomo_alerts.append({
                "type": "achievement_window",
                "title": "Early Bird Achievement - 7 days left! 🐦",
                "message": "Complete 10 transactions this month for exclusive badge",
                "urgency": "medium",
                "action": "Start tracking",
                "action_url": "/transactions",
                "time_remaining": f"{7 - datetime.now().day} days",
                "icon": "🏆"
            })
        
        # Social pressure (friends' activity)
        friend_count = await db.friends.count_documents({
            "$or": [{"user_id": user_id}, {"friend_id": user_id}],
            "status": "accepted"
        })
        
        if friend_count >= 5:
            active_friends = friend_count // 2  # Estimate active friends
            fomo_alerts.append({
                "type": "social_pressure",
                "title": f"{active_friends} friends are actively saving!",
                "message": "Don't get left behind - join the savings streak",
                "urgency": "low",
                "action": "See friend activity",
                "action_url": "/social/friend-activity-feed",
                "friends_count": active_friends,
                "icon": "👫"
            })
        
        return {
            "alerts": fomo_alerts,
            "total_alerts": len(fomo_alerts),
            "psychology_tip": "Scarcity and social proof drive action - use them wisely!",
            "user_urgency_score": sum(1 for alert in fomo_alerts if alert["urgency"] == "high") * 3 + 
                                 sum(1 for alert in fomo_alerts if alert["urgency"] == "medium") * 2 +
                                 sum(1 for alert in fomo_alerts if alert["urgency"] == "low")
        }
        
    except Exception as e:
        logger.error(f"FOMO alerts error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get FOMO alerts")

# Enhanced FOMO mechanics with countdown timers
@api_router.get("/engagement/countdown-alerts")
@limiter.limit("10/minute")
async def get_countdown_alerts(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get time-sensitive alerts with precise countdown timers"""
    try:
        now = datetime.now(timezone.utc)
        countdown_alerts = []
        
        # Flash savings challenge (6-hour windows)
        flash_end_times = [
            now.replace(hour=11, minute=0, second=0, microsecond=0),  # 11 AM
            now.replace(hour=17, minute=0, second=0, microsecond=0),  # 5 PM  
            now.replace(hour=21, minute=0, second=0, microsecond=0)   # 9 PM
        ]
        
        # Find the next flash challenge window
        next_flash = None
        for flash_time in flash_end_times:
            if flash_time > now:
                next_flash = flash_time
                break
        
        if not next_flash:
            # If no more windows today, use tomorrow's 11 AM
            next_flash = (now + timedelta(days=1)).replace(hour=11, minute=0, second=0, microsecond=0)
        
        seconds_remaining = int((next_flash - now).total_seconds())
        if seconds_remaining > 0 and seconds_remaining <= 21600:  # Within 6 hours
            countdown_alerts.append({
                "id": "flash_savings",
                "type": "flash_challenge",
                "title": "⚡ Flash Savings Challenge",
                "message": f"Save ₹100 in the next {seconds_remaining//3600}h {(seconds_remaining%3600)//60}m - win 2x points!",
                "deadline": next_flash.isoformat(),
                "seconds_remaining": seconds_remaining,
                "urgency": "critical" if seconds_remaining <= 1800 else "high",  # Critical if < 30 min
                "reward": "Double points on all transactions",
                "action": "Make Transaction",
                "action_url": "/transactions/new",
                "countdown_display": "live"
            })
        
        # Daily milestone deadline (11:59 PM)
        today_end = now.replace(hour=23, minute=59, second=0, microsecond=0)
        seconds_to_midnight = int((today_end - now).total_seconds())
        
        # Check if user needs to complete daily goal
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_transactions = await db.transactions.find({
            "user_id": user_id,
            "created_at": {"$gte": today_start, "$lt": today_end}
        }).to_list(None)
        
        if len(today_transactions) == 0 and seconds_to_midnight > 0:
            countdown_alerts.append({
                "id": "daily_streak",
                "type": "daily_deadline",
                "title": "🔥 Save Your Streak!",
                "message": f"Add 1 transaction before midnight to maintain your streak!",
                "deadline": today_end.isoformat(),
                "seconds_remaining": seconds_to_midnight,
                "urgency": "critical" if seconds_to_midnight <= 3600 else "high",  # Critical if < 1 hour
                "consequence": "Lose current streak",
                "action": "Quick Add",
                "action_url": "/transactions/quick",
                "countdown_display": "live"
            })
        
        # Weekend challenge countdown (Friday 6 PM to Sunday 11:59 PM)
        if now.weekday() == 4 and now.hour >= 18:  # Friday after 6 PM
            sunday_end = now + timedelta(days=2)
            sunday_end = sunday_end.replace(hour=23, minute=59, second=0, microsecond=0)
            weekend_seconds = int((sunday_end - now).total_seconds())
            
            countdown_alerts.append({
                "id": "weekend_challenge",
                "type": "weekend_special",
                "title": "🎉 Weekend Savings Sprint",
                "message": "Save ₹500 this weekend - unlock special badge!",
                "deadline": sunday_end.isoformat(),
                "seconds_remaining": weekend_seconds,
                "urgency": "medium",
                "reward": "Weekend Warrior badge + 100 points",
                "action": "Start Saving",
                "action_url": "/challenges/weekend",
                "countdown_display": "live"
            })
        
        # Limited mentor booking (next 2 hours)
        mentor_deadline = now + timedelta(hours=2)
        available_slots = max(0, 5 - (hash(user_id) % 7))
        
        if available_slots > 0:
            countdown_alerts.append({
                "id": "mentor_booking",
                "type": "limited_slots",
                "title": f"🎯 {available_slots} Mentor Slots Left",
                "message": "Book your 1-on-1 financial mentor session now!",
                "deadline": mentor_deadline.isoformat(),
                "seconds_remaining": 7200,  # 2 hours
                "urgency": "high" if available_slots <= 2 else "medium",
                "spots_remaining": available_slots,
                "action": "Book Now",
                "action_url": "/mentorship/book",
                "countdown_display": "slots"
            })
        
        # Referral bonus countdown (monthly reset)
        # Calculate next month's first day
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            next_month = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        month_end_seconds = int((next_month - now).total_seconds())
        
        # Check user's monthly referrals
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_referrals = await db.referral_programs.count_documents({
            "referred_by": user_id,
            "created_at": {"$gte": month_start}
        })
        
        if monthly_referrals < 5 and month_end_seconds <= 604800:  # Less than a week left
            countdown_alerts.append({
                "id": "referral_deadline",
                "type": "monthly_deadline",
                "title": "💰 Monthly Referral Bonus Ending",
                "message": f"Refer {5 - monthly_referrals} more friends to earn ₹500 bonus!",
                "deadline": next_month.isoformat(),
                "seconds_remaining": month_end_seconds,
                "urgency": "medium" if month_end_seconds > 86400 else "high",  # High if < 24 hours
                "progress": f"{monthly_referrals}/5 referrals",
                "reward": "₹500 referral bonus",
                "action": "Invite Friends", 
                "action_url": "/referrals/invite",
                "countdown_display": "progress"
            })
        
        # Sort by urgency (critical > high > medium > low)
        urgency_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        countdown_alerts.sort(key=lambda x: urgency_order.get(x["urgency"], 0), reverse=True)
        
        return {
            "countdown_alerts": countdown_alerts,
            "total_active": len(countdown_alerts),
            "critical_count": sum(1 for alert in countdown_alerts if alert["urgency"] == "critical"),
            "server_time": now.isoformat(),
            "timezone": "UTC",
            "update_frequency": "30s"  # Recommend frontend updates every 30 seconds
        }
        
    except Exception as e:
        logger.error(f"Countdown alerts error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get countdown alerts")

# Photo sharing for achievements  
@api_router.post("/engagement/upload-achievement-photo")
@limiter.limit("5/minute")
async def upload_achievement_photo(
    request: Request,
    file: UploadFile = File(...),
    achievement_id: str = None,
    caption: str = "",
    user_id: str = Depends(get_current_user)
):
    """Upload photo for achievement sharing"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Only image files are allowed")
        
        # Create unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        unique_filename = f"achievement_{user_id}_{uuid.uuid4()}.{file_extension}"
        file_path = UPLOADS_DIR / unique_filename
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create photo record
        achievement_photo = {
            "photo_id": str(uuid.uuid4()),
            "user_id": user_id,
            "achievement_id": achievement_id,
            "filename": unique_filename,
            "file_path": str(file_path),
            "photo_url": f"/uploads/{unique_filename}",
            "caption": caption,
            "likes": 0,
            "comments": [],
            "is_public": True,
            "uploaded_at": datetime.now(timezone.utc)
        }
        
        await db.achievement_photos.insert_one(achievement_photo)
        
        # Award points for sharing achievement photo
        gamification_service = get_gamification_service()
        if gamification_service:
            try:
                await gamification_service.add_experience_points(user_id, 25, "achievement_photo_shared")
            except:
                pass
        
        return {
            "success": True,
            "photo_id": achievement_photo["photo_id"],
            "photo_url": achievement_photo["photo_url"],
            "sharing_links": {
                "instagram": f"Share this achievement photo on your Instagram story!",
                "whatsapp": f"https://wa.me/?text=Check%20out%20my%20achievement!%20{achievement_photo['photo_url']}",
                "facebook": f"Post this achievement on Facebook to inspire friends!"
            },
            "points_earned": 25
        }
        
    except Exception as e:
        logger.error(f"Achievement photo upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload achievement photo")

# Story-style financial journey timeline
@api_router.get("/engagement/financial-journey")
@limiter.limit("10/minute")
async def get_financial_journey_timeline(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get story-style timeline of user's financial journey"""
    try:
        # Get user's financial milestones and events
        timeline_events = []
        
        # Registration milestone
        user_info = await db.users.find_one({"user_id": user_id})
        if user_info:
            timeline_events.append({
                "type": "milestone",
                "title": "Started Financial Journey! 🚀",
                "description": f"Joined EarnAura on {user_info['created_at'].strftime('%B %d, %Y')}",
                "date": user_info["created_at"],
                "icon": "🎯",
                "color": "blue"
            })
        
        # First transaction
        first_transaction = await db.transactions.find_one(
            {"user_id": user_id},
            sort=[("created_at", 1)]
        )
        if first_transaction:
            action = "earned" if first_transaction["type"] == "income" else "tracked spending of"
            timeline_events.append({
                "type": "transaction",
                "title": "First Transaction! 💰",
                "description": f"First {action} ₹{first_transaction['amount']} on {first_transaction['category']}",
                "date": first_transaction["created_at"],
                "icon": "💵",
                "color": "green",
                "amount": first_transaction["amount"]
            })
        
        # Achievements timeline
        achievements = await db.user_achievements.find(
            {"user_id": user_id}
        ).sort("earned_at", 1).to_list(None)
        
        for achievement in achievements:
            timeline_events.append({
                "type": "achievement",
                "title": f"Achievement Unlocked! 🏆",
                "description": achievement["achievement_name"],
                "date": achievement["earned_at"],
                "icon": "🎖️",
                "color": "gold"
            })
        
        # Major milestones
        milestones = await db.user_milestones.find(
            {"user_id": user_id}
        ).sort("achieved_at", 1).to_list(None)
        
        for milestone in milestones:
            timeline_events.append({
                "type": "milestone",
                "title": f"Milestone Reached! 🎉",
                "description": f"{milestone['milestone_type']} of ₹{milestone.get('amount', 0)}",
                "date": milestone["achieved_at"],
                "icon": "🏁",
                "color": "purple",
                "amount": milestone.get("amount", 0)
            })
        
        # Friend connections
        first_friend = await db.friends.find_one(
            {"$or": [{"user_id": user_id}, {"friend_id": user_id}]},
            sort=[("created_at", 1)]
        )
        if first_friend:
            timeline_events.append({
                "type": "social",
                "title": "First Friend Connected! 👫",
                "description": "Started building your financial network",
                "date": first_friend["created_at"],
                "icon": "🤝",
                "color": "pink"
            })
        
        # Sort timeline by date
        timeline_events.sort(key=lambda x: x["date"])
        
        # Add story-style descriptions
        for i, event in enumerate(timeline_events):
            event["story_position"] = i + 1
            event["days_ago"] = (datetime.now(timezone.utc) - event["date"]).days
            
            if event["days_ago"] == 0:
                event["time_text"] = "Today"
            elif event["days_ago"] == 1:
                event["time_text"] = "Yesterday"
            elif event["days_ago"] <= 7:
                event["time_text"] = f"{event['days_ago']} days ago"
            elif event["days_ago"] <= 30:
                event["time_text"] = f"{event['days_ago'] // 7} weeks ago"
            else:
                event["time_text"] = f"{event['days_ago'] // 30} months ago"
        
        # Calculate journey statistics
        total_savings = await get_user_total_savings(user_id)
        total_income = await get_user_total_income(user_id)
        journey_days = (datetime.now(timezone.utc) - user_info["created_at"]).days if user_info else 0
        
        return {
            "timeline": timeline_events,
            "journey_stats": {
                "days_active": journey_days,
                "total_savings": total_savings,
                "total_income": total_income,
                "milestones_reached": len([e for e in timeline_events if e["type"] == "milestone"]),
                "achievements_earned": len([e for e in timeline_events if e["type"] == "achievement"])
            },
            "story_summary": f"In {journey_days} days, you've saved ₹{total_savings:.0f} and unlocked {len(achievements)} achievements!",
            "next_milestone": "Keep going to unlock more achievements!"
        }
        
    except Exception as e:
        logger.error(f"Financial journey error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get financial journey")

# ==================== ENGAGEMENT FEATURES API ENDPOINTS ====================

# Daily Tips Endpoints
@api_router.get("/daily-tips")
@limiter.limit("20/minute")
async def get_daily_tip_endpoint(request: Request, user_id: str = Depends(get_current_user)):
    """Get today's personalized daily tip"""
    try:
        from daily_tips_service import get_daily_tips_service
        
        tips_service = await get_daily_tips_service()
        tip = await tips_service.generate_personalized_tip(user_id)
        
        return {"tip": tip}
        
    except Exception as e:
        logger.error(f"Get daily tip error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get daily tip")

@api_router.post("/daily-tips/{tip_id}/interact")
@limiter.limit("50/minute")
async def record_tip_interaction_endpoint(
    request: Request,
    tip_id: str,
    interaction_type: str,
    interaction_data: Optional[Dict[str, Any]] = None,
    user_id: str = Depends(get_current_user)
):
    """Record user interaction with daily tip"""
    try:
        from daily_tips_service import get_daily_tips_service
        
        tips_service = await get_daily_tips_service()
        success = await tips_service.record_tip_interaction(
            user_id, tip_id, interaction_type, interaction_data or {}
        )
        
        return {"success": success}
        
    except Exception as e:
        logger.error(f"Record tip interaction error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record interaction")

@api_router.get("/daily-tips/history")
@limiter.limit("10/minute")
async def get_tip_history_endpoint(
    request: Request,
    limit: int = 30,
    user_id: str = Depends(get_current_user)
):
    """Get user's daily tip history"""
    try:
        db = await get_database()
        tips = await db.daily_tip_notifications.find({
            "user_id": user_id
        }).sort("sent_at", -1).limit(limit).to_list(None)
        
        return {"tips": tips}
        
    except Exception as e:
        logger.error(f"Get tip history error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get tip history")

# Limited Offers Endpoints
@api_router.get("/offers")
@limiter.limit("20/minute")
async def get_active_offers_endpoint(request: Request, user_id: str = Depends(get_current_user)):
    """Get active limited-time offers for user"""
    try:
        from limited_offers_service import get_limited_offers_service
        
        offers_service = await get_limited_offers_service()
        offers = await offers_service.get_active_offers_for_user(user_id)
        
        return {"offers": offers}
        
    except Exception as e:
        logger.error(f"Get active offers error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get offers")

@api_router.post("/offers/{offer_id}/participate")
@limiter.limit("20/minute")
async def participate_in_offer_endpoint(
    request: Request,
    offer_id: str,
    user_id: str = Depends(get_current_user)
):
    """Participate in a limited-time offer"""
    try:
        from limited_offers_service import get_limited_offers_service
        
        offers_service = await get_limited_offers_service()
        result = await offers_service.participate_in_offer(user_id, offer_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Participate in offer error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to participate in offer")

@api_router.get("/offers/history")
@limiter.limit("10/minute")
async def get_offer_history_endpoint(request: Request, user_id: str = Depends(get_current_user)):
    """Get user's offer participation history"""
    try:
        from limited_offers_service import get_limited_offers_service
        
        offers_service = await get_limited_offers_service()
        history = await offers_service.get_user_participation_history(user_id)
        
        return {"history": history}
        
    except Exception as e:
        logger.error(f"Get offer history error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get offer history")

@api_router.post("/offers/create-challenge")
@limiter.limit("5/minute")
async def create_challenge_offer_endpoint(
    request: Request,
    challenge_data: Dict[str, Any],
    user_id: str = Depends(get_current_user)
):
    """Create a financial challenge offer (admin or high-level users)"""
    try:
        # Check if user has permission (admin or level 5+)
        user = await get_user_by_id(user_id)
        if not (user.get("is_admin") or user.get("level", 1) >= 5):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        from limited_offers_service import get_limited_offers_service
        
        offers_service = await get_limited_offers_service()
        offer = await offers_service.create_financial_challenge_offer(challenge_data)
        
        return {"offer": offer}
        
    except Exception as e:
        logger.error(f"Create challenge offer error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create challenge")

# Timeline/Story Endpoints
@api_router.get("/timeline")
@limiter.limit("30/minute")
async def get_timeline_endpoint(
    request: Request,
    timeline_type: str = "combined",  # "personal", "social", "combined"
    limit: int = 20,
    offset: int = 0,
    user_id: str = Depends(get_current_user)
):
    """Get user's timeline (personal, social, or combined)"""
    try:
        from timeline_service import get_timeline_service
        
        timeline_service = await get_timeline_service()
        timeline = await timeline_service.get_user_timeline(user_id, timeline_type, limit, offset)
        
        return {"timeline": timeline}
        
    except Exception as e:
        logger.error(f"Get timeline error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get timeline")

@api_router.get("/timeline/friends")
@limiter.limit("20/minute")
async def get_friend_timeline_endpoint(
    request: Request,
    limit: int = 15,
    offset: int = 0,
    user_id: str = Depends(get_current_user)
):
    """Get friend activities timeline"""
    try:
        from timeline_service import get_timeline_service
        
        timeline_service = await get_timeline_service()
        activities = await timeline_service.get_friend_activities_timeline(user_id, limit, offset)
        
        return {"activities": activities}
        
    except Exception as e:
        logger.error(f"Get friend timeline error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get friend activities")

@api_router.post("/timeline/events/{event_id}/react")
@limiter.limit("50/minute")
async def react_to_timeline_event_endpoint(
    request: Request,
    event_id: str,
    reaction_type: str,
    user_id: str = Depends(get_current_user)
):
    """React to a timeline event"""
    try:
        from timeline_service import get_timeline_service
        
        timeline_service = await get_timeline_service()
        success = await timeline_service.add_reaction_to_event(user_id, event_id, reaction_type)
        
        return {"success": success}
        
    except Exception as e:
        logger.error(f"React to timeline event error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to react to event")

@api_router.get("/timeline/stats")
@limiter.limit("10/minute")
async def get_timeline_stats_endpoint(request: Request, user_id: str = Depends(get_current_user)):
    """Get timeline statistics for user"""
    try:
        from timeline_service import get_timeline_service
        
        timeline_service = await get_timeline_service()
        stats = await timeline_service.get_timeline_stats(user_id)
        
        return {"stats": stats}
        
    except Exception as e:
        logger.error(f"Get timeline stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get timeline stats")

# Enhanced Photo Sharing Endpoints
@api_router.post("/photos/achievements/upload")
@limiter.limit("10/minute")
async def upload_achievement_photo_endpoint(
    request: Request,
    file: UploadFile = File(...),
    achievement_id: str = None,
    user_id: str = Depends(get_current_user)
):
    """Upload custom photo for achievement"""
    try:
        from enhanced_photo_service import get_enhanced_photo_service
        
        # Validate file
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read file content
        file_content = await file.read()
        
        photo_service = await get_enhanced_photo_service()
        result = await photo_service.upload_custom_achievement_photo(
            user_id, achievement_id or "general", file_content, file.filename
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Upload achievement photo error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload photo")

@api_router.post("/photos/achievements/generate-branded")
@limiter.limit("10/minute")
async def generate_branded_photo_endpoint(
    request: Request,
    achievement_data: Dict[str, Any],
    user_id: str = Depends(get_current_user)
):
    """Generate branded achievement photo"""
    try:
        from enhanced_photo_service import get_enhanced_photo_service
        
        photo_service = await get_enhanced_photo_service()
        result = await photo_service.generate_branded_achievement_photo(user_id, achievement_data)
        
        return result
        
    except Exception as e:
        logger.error(f"Generate branded photo error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate branded photo")

@api_router.get("/photos/achievements")
@limiter.limit("20/minute")
async def get_achievement_photos_endpoint(
    request: Request,
    limit: int = 20,
    user_id: str = Depends(get_current_user)
):
    """Get user's achievement photos"""
    try:
        from enhanced_photo_service import get_enhanced_photo_service
        
        photo_service = await get_enhanced_photo_service()
        photos = await photo_service.get_user_achievement_photos(user_id, limit)
        
        return {"photos": photos}
        
    except Exception as e:
        logger.error(f"Get achievement photos error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get photos")

@api_router.post("/photos/{photo_id}/like")
@limiter.limit("100/minute")
async def like_photo_endpoint(
    request: Request,
    photo_id: str,
    user_id: str = Depends(get_current_user)
):
    """Like or unlike an achievement photo"""
    try:
        from enhanced_photo_service import get_enhanced_photo_service
        
        photo_service = await get_enhanced_photo_service()
        result = await photo_service.like_achievement_photo(user_id, photo_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Like photo error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to like photo")

# Push Notification Subscription Management
@api_router.post("/notifications/subscribe")
@limiter.limit("10/minute")
async def create_push_subscription_endpoint(
    request: Request,
    subscription_data: Dict[str, Any],
    user_id: str = Depends(get_current_user)
):
    """Create or update push notification subscription"""
    try:
        push_service = await get_push_service()
        if not push_service:
            raise HTTPException(status_code=503, detail="Push notification service unavailable")
        
        result = await push_service.create_push_subscription(user_id, subscription_data)
        
        return result
        
    except Exception as e:
        logger.error(f"Create push subscription error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create subscription")

@api_router.get("/notifications/preferences")
@limiter.limit("20/minute")
async def get_notification_preferences_endpoint(request: Request, user_id: str = Depends(get_current_user)):
    """Get user's notification preferences"""
    try:
        push_service = await get_push_service()
        if not push_service:
            return {"preferences": {}}
        
        preferences = await push_service.get_user_notification_preferences(user_id)
        
        return {"preferences": preferences}
        
    except Exception as e:
        logger.error(f"Get notification preferences error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get preferences")

@api_router.put("/notifications/preferences")
@limiter.limit("20/minute")
async def update_notification_preferences_endpoint(
    request: Request,
    preferences: Dict[str, bool],
    user_id: str = Depends(get_current_user)
):
    """Update user's notification preferences"""
    try:
        push_service = await get_push_service()
        if not push_service:
            raise HTTPException(status_code=503, detail="Push notification service unavailable")
        
        success = await push_service.update_notification_preferences(user_id, preferences)
        
        return {"success": success}
        
    except Exception as e:
        logger.error(f"Update notification preferences error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update preferences")

# Missing Timeline/Friend Activity Endpoints (Added for Dashboard Activation)
@api_router.get("/timeline/activities")
@limiter.limit("30/minute")
async def get_timeline_activities_endpoint(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    activity_type: str = "all",  # "achievements", "transactions", "milestones", "social", "all"
    user_id: str = Depends(get_current_user)
):
    """Get timeline activities for dashboard"""
    try:
        # Get recent user activities
        db = await get_database()
        activities = []
        
        # Get recent achievements
        if activity_type in ["achievements", "all"]:
            recent_achievements = await db.achievements.find({
                "user_id": user_id,
                "created_at": {"$exists": True}
            }).sort("created_at", -1).limit(5).to_list(length=5)
            
            for achievement in recent_achievements:
                activities.append({
                    "id": str(achievement.get("_id", "")),
                    "type": "achievement",
                    "title": f"🏆 {achievement.get('title', 'Achievement Unlocked')}",
                    "description": achievement.get('description', 'New achievement earned!'),
                    "timestamp": achievement.get('created_at', datetime.now(timezone.utc)),
                    "icon": achievement.get('icon', '🎯'),
                    "points": achievement.get('points', 0)
                })
        
        # Get recent transactions
        if activity_type in ["transactions", "all"]:
            recent_transactions = await db.transactions.find({
                "user_id": user_id
            }).sort("created_at", -1).limit(3).to_list(length=3)
            
            for transaction in recent_transactions:
                activities.append({
                    "id": str(transaction.get("_id", "")),
                    "type": "transaction",
                    "title": f"💰 {transaction.get('type', '').title()}: {transaction.get('description', 'Transaction')}",
                    "description": f"Amount: ₹{transaction.get('amount', 0):.2f} | Category: {transaction.get('category', 'General')}",
                    "timestamp": transaction.get('created_at', datetime.now(timezone.utc)),
                    "icon": "💸" if transaction.get('type') == 'expense' else "💰",
                    "amount": transaction.get('amount', 0)
                })
        
        # Get recent milestones
        if activity_type in ["milestones", "all"]:
            # Look for milestone achievements in user profile
            user = await db.users.find_one({"id": user_id})
            if user and user.get('milestones_reached'):
                for milestone in user.get('milestones_reached', [])[-3:]:
                    activities.append({
                        "id": f"milestone_{milestone.get('type', 'unknown')}",
                        "type": "milestone",
                        "title": f"🎉 Milestone Reached: {milestone.get('title', 'Goal Achieved')}",
                        "description": milestone.get('description', 'You hit an important milestone!'),
                        "timestamp": milestone.get('achieved_at', datetime.now(timezone.utc)),
                        "icon": "🚀",
                        "value": milestone.get('value', 0)
                    })
        
        # Sort activities by timestamp
        activities.sort(key=lambda x: x.get('timestamp', datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
        
        # Apply pagination
        paginated_activities = activities[offset:offset + limit]
        
        return {
            "activities": paginated_activities,
            "total": len(activities),
            "has_more": len(activities) > offset + limit
        }
        
    except Exception as e:
        logger.error(f"Get timeline activities error: {str(e)}")
        return {"activities": [], "total": 0, "has_more": False}

@api_router.get("/friends/activities")
@limiter.limit("20/minute")
async def get_friends_activities_endpoint(
    request: Request,
    limit: int = 15,
    offset: int = 0,
    user_id: str = Depends(get_current_user)
):
    """Get friend activities for dashboard"""
    try:
        db = await get_database()
        
        # Get user's friends
        friendships = await db.friendships.find({
            "$or": [
                {"user_id": user_id},
                {"friend_id": user_id}
            ],
            "status": "accepted"
        }).to_list(length=None)
        
        friend_ids = []
        for friendship in friendships:
            if friendship.get("user_id") == user_id:
                friend_ids.append(friendship.get("friend_id"))
            else:
                friend_ids.append(friendship.get("user_id"))
        
        if not friend_ids:
            return {"activities": [], "message": "No friends yet! Add friends to see their activities."}
        
        # Get recent activities from friends
        friend_activities = []
        
        # Get friends' recent achievements
        friend_achievements = await db.achievements.find({
            "user_id": {"$in": friend_ids},
            "created_at": {"$exists": True}
        }).sort("created_at", -1).limit(10).to_list(length=10)
        
        for achievement in friend_achievements:
            # Get friend's name
            friend = await db.users.find_one({"id": achievement.get("user_id")})
            friend_name = friend.get("full_name", "Friend") if friend else "Friend"
            
            friend_activities.append({
                "id": str(achievement.get("_id", "")),
                "type": "friend_achievement",
                "user_name": friend_name,
                "title": f"{friend_name} earned an achievement!",
                "description": f"🏆 {achievement.get('title', 'New Achievement')} - {achievement.get('description', '')}",
                "timestamp": achievement.get('created_at', datetime.now(timezone.utc)),
                "icon": achievement.get('icon', '🎯'),
                "points": achievement.get('points', 0)
            })
        
        # Get friends' recent milestones
        friends_data = await db.users.find({
            "id": {"$in": friend_ids},
            "milestones_reached": {"$exists": True}
        }).to_list(length=None)
        
        for friend in friends_data:
            friend_name = friend.get("full_name", "Friend")
            recent_milestones = friend.get('milestones_reached', [])[-2:]  # Last 2 milestones
            
            for milestone in recent_milestones:
                friend_activities.append({
                    "id": f"friend_milestone_{friend.get('id')}_{milestone.get('type', 'unknown')}",
                    "type": "friend_milestone",
                    "user_name": friend_name,
                    "title": f"{friend_name} reached a milestone!",
                    "description": f"🚀 {milestone.get('title', 'Goal Achieved')} - {milestone.get('description', '')}",
                    "timestamp": milestone.get('achieved_at', datetime.now(timezone.utc)),
                    "icon": "🎉",
                    "value": milestone.get('value', 0)
                })
        
        # Sort by timestamp
        friend_activities.sort(key=lambda x: x.get('timestamp', datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
        
        # Apply pagination
        paginated_activities = friend_activities[offset:offset + limit]
        
        return {
            "activities": paginated_activities,
            "total": len(friend_activities),
            "has_more": len(friend_activities) > offset + limit
        }
        
    except Exception as e:
        logger.error(f"Get friends activities error: {str(e)}")
        return {"activities": [], "message": "Unable to load friend activities"}

@api_router.get("/friends/timeline")
@limiter.limit("20/minute")
async def get_friends_timeline_endpoint(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    user_id: str = Depends(get_current_user)
):
    """Get combined timeline with friend activities"""
    try:
        db = await get_database()
        
        # Get friends list
        friendships = await db.friendships.find({
            "$or": [
                {"user_id": user_id},
                {"friend_id": user_id}
            ],
            "status": "accepted"
        }).to_list(length=None)
        
        friend_ids = []
        for friendship in friendships:
            if friendship.get("user_id") == user_id:
                friend_ids.append(friendship.get("friend_id"))
            else:
                friend_ids.append(friendship.get("user_id"))
        
        # Include user's own activities
        all_user_ids = friend_ids + [user_id]
        
        timeline_events = []
        
        # Get achievements for all users (self + friends)
        achievements = await db.achievements.find({
            "user_id": {"$in": all_user_ids},
            "created_at": {"$exists": True}
        }).sort("created_at", -1).limit(15).to_list(length=15)
        
        for achievement in achievements:
            user_data = await db.users.find_one({"id": achievement.get("user_id")})
            user_name = user_data.get("full_name", "Unknown") if user_data else "Unknown"
            is_self = achievement.get("user_id") == user_id
            
            timeline_events.append({
                "id": str(achievement.get("_id", "")),
                "type": "achievement",
                "user_id": achievement.get("user_id"),
                "user_name": user_name,
                "is_self": is_self,
                "title": achievement.get('title', 'Achievement Unlocked'),
                "description": achievement.get('description', 'New achievement earned!'),
                "timestamp": achievement.get('created_at', datetime.now(timezone.utc)),
                "icon": achievement.get('icon', '🎯'),
                "points": achievement.get('points', 0)
            })
        
        # Get recent transactions for timeline
        recent_transactions = await db.transactions.find({
            "user_id": {"$in": all_user_ids},
            "type": "income"  # Only show income for privacy
        }).sort("created_at", -1).limit(10).to_list(length=10)
        
        for transaction in recent_transactions:
            user_data = await db.users.find_one({"id": transaction.get("user_id")})
            user_name = user_data.get("full_name", "Unknown") if user_data else "Unknown"
            is_self = transaction.get("user_id") == user_id
            
            timeline_events.append({
                "id": str(transaction.get("_id", "")),
                "type": "income",
                "user_id": transaction.get("user_id"),
                "user_name": user_name,
                "is_self": is_self,
                "title": f"Earned ₹{transaction.get('amount', 0):.2f}",
                "description": f"Income from {transaction.get('category', 'work')}",
                "timestamp": transaction.get('created_at', datetime.now(timezone.utc)),
                "icon": "💰",
                "amount": transaction.get('amount', 0)
            })
        
        # Sort timeline by timestamp
        timeline_events.sort(key=lambda x: x.get('timestamp', datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
        
        # Apply pagination
        paginated_events = timeline_events[offset:offset + limit]
        
        return {
            "timeline": paginated_events,
            "total": len(timeline_events),
            "has_more": len(timeline_events) > offset + limit,
            "friends_count": len(friend_ids)
        }
        
    except Exception as e:
        logger.error(f"Get friends timeline error: {str(e)}")
        return {"timeline": [], "total": 0, "has_more": False, "friends_count": 0}

@api_router.get("/social/timeline")
@limiter.limit("20/minute")
async def get_social_timeline_endpoint(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    user_id: str = Depends(get_current_user)
):
    """Get social timeline with public activities"""
    try:
        db = await get_database()
        
        social_events = []
        
        # Get recent public achievements from all users
        public_achievements = await db.achievements.find({
            "is_public": {"$ne": False},  # Default to public unless explicitly private
            "created_at": {"$exists": True}
        }).sort("created_at", -1).limit(25).to_list(length=25)
        
        for achievement in public_achievements:
            user_data = await db.users.find_one({"id": achievement.get("user_id")})
            if not user_data:
                continue
                
            user_name = user_data.get("full_name", "Anonymous User")
            avatar = user_data.get("avatar", "person")
            university = user_data.get("university", "Unknown University")
            
            social_events.append({
                "id": str(achievement.get("_id", "")),
                "type": "public_achievement",
                "user_id": achievement.get("user_id"),
                "user_name": user_name,
                "user_avatar": avatar,
                "user_university": university,
                "title": f"{user_name} earned an achievement!",
                "description": f"🏆 {achievement.get('title', 'Achievement Unlocked')} - {achievement.get('description', '')}",
                "timestamp": achievement.get('created_at', datetime.now(timezone.utc)),
                "icon": achievement.get('icon', '🎯'),
                "points": achievement.get('points', 0),
                "rarity": achievement.get('rarity', 'common')
            })
        
        # Get public milestones
        users_with_milestones = await db.users.find({
            "milestones_reached": {"$exists": True},
            "privacy_settings.milestones_public": {"$ne": False}
        }).limit(20).to_list(length=20)
        
        for user in users_with_milestones:
            recent_milestones = user.get('milestones_reached', [])[-1:]  # Latest milestone
            user_name = user.get("full_name", "Anonymous User")
            avatar = user.get("avatar", "person")
            university = user.get("university", "Unknown University")
            
            for milestone in recent_milestones:
                social_events.append({
                    "id": f"public_milestone_{user.get('id')}_{milestone.get('type', 'unknown')}",
                    "type": "public_milestone",
                    "user_id": user.get('id'),
                    "user_name": user_name,
                    "user_avatar": avatar,
                    "user_university": university,
                    "title": f"{user_name} reached a milestone!",
                    "description": f"🚀 {milestone.get('title', 'Goal Achieved')}",
                    "timestamp": milestone.get('achieved_at', datetime.now(timezone.utc)),
                    "icon": "🎉",
                    "value": milestone.get('value', 0)
                })
        
        # Sort by timestamp
        social_events.sort(key=lambda x: x.get('timestamp', datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
        
        # Apply pagination
        paginated_events = social_events[offset:offset + limit]
        
        return {
            "timeline": paginated_events,
            "total": len(social_events),
            "has_more": len(social_events) > offset + limit,
            "message": "Social timeline showing public achievements and milestones"
        }
        
    except Exception as e:
        logger.error(f"Get social timeline error: {str(e)}")
        return {"timeline": [], "total": 0, "has_more": False}

@api_router.get("/engagement/timeline")
@limiter.limit("30/minute")
async def get_engagement_timeline_endpoint(
    request: Request,
    limit: int = 15,
    offset: int = 0,
    user_id: str = Depends(get_current_user)
):
    """Get engagement-focused timeline for dashboard"""
    try:
        db = await get_database()
        
        engagement_events = []
        
        # Get user's recent engagement activities
        user = await db.users.find_one({"id": user_id})
        if not user:
            return {"events": [], "message": "User not found"}
        
        # Recent achievements
        recent_achievements = await db.achievements.find({
            "user_id": user_id
        }).sort("created_at", -1).limit(3).to_list(length=3)
        
        for achievement in recent_achievements:
            engagement_events.append({
                "id": str(achievement.get("_id", "")),
                "type": "achievement",
                "title": f"🏆 {achievement.get('title', 'Achievement Unlocked')}",
                "description": achievement.get('description', 'You earned a new achievement!'),
                "timestamp": achievement.get('created_at', datetime.now(timezone.utc)),
                "icon": achievement.get('icon', '🎯'),
                "engagement_score": 10,
                "action_url": "/gamification"
            })
        
        # Streak activities
        current_streak = user.get('current_streak', 0)
        if current_streak > 0:
            engagement_events.append({
                "id": f"streak_{current_streak}",
                "type": "streak",
                "title": f"🔥 {current_streak} Day Streak Active!",
                "description": "Keep logging transactions to maintain your streak",
                "timestamp": datetime.now(timezone.utc),
                "icon": "🔥",
                "engagement_score": min(current_streak, 50),
                "action_url": "/transactions"
            })
        
        # Recent milestone progress
        if user.get('milestones_reached'):
            latest_milestone = user.get('milestones_reached', [])[-1]
            engagement_events.append({
                "id": f"milestone_{latest_milestone.get('type')}",
                "type": "milestone",
                "title": f"🚀 Milestone: {latest_milestone.get('title', 'Goal Achieved')}",
                "description": latest_milestone.get('description', 'You reached an important goal!'),
                "timestamp": latest_milestone.get('achieved_at', datetime.now(timezone.utc)),
                "icon": "🎉",
                "engagement_score": 25,
                "action_url": "/goals"
            })
        
        # Level progress
        experience_points = user.get('experience_points', 0)
        level = user.get('level', 1)
        engagement_events.append({
            "id": f"level_{level}",
            "type": "level",
            "title": f"⭐ Level {level} - {experience_points} XP",
            "description": f"Keep earning XP to reach the next level!",
            "timestamp": datetime.now(timezone.utc),
            "icon": "⭐",
            "engagement_score": experience_points // 10,
            "action_url": "/gamification"
        })
        
        # Recent transactions for engagement
        recent_transactions = await db.transactions.find({
            "user_id": user_id
        }).sort("created_at", -1).limit(2).to_list(length=2)
        
        for transaction in recent_transactions:
            engagement_events.append({
                "id": str(transaction.get("_id", "")),
                "type": "transaction",
                "title": f"💰 Recent {transaction.get('type', '').title()}",
                "description": f"{transaction.get('description', 'Transaction')} - ₹{transaction.get('amount', 0):.2f}",
                "timestamp": transaction.get('created_at', datetime.now(timezone.utc)),
                "icon": "💸" if transaction.get('type') == 'expense' else "💰",
                "engagement_score": 5,
                "action_url": "/analytics"
            })
        
        # Sort by engagement score and timestamp
        engagement_events.sort(key=lambda x: (x.get('engagement_score', 0), x.get('timestamp', datetime.min.replace(tzinfo=timezone.utc))), reverse=True)
        
        # Apply pagination
        paginated_events = engagement_events[offset:offset + limit]
        
        return {
            "events": paginated_events,
            "total": len(engagement_events),
            "has_more": len(engagement_events) > offset + limit,
            "user_engagement_score": sum(event.get('engagement_score', 0) for event in engagement_events)
        }
        
    except Exception as e:
        logger.error(f"Get engagement timeline error: {str(e)}")
        return {"events": [], "total": 0, "has_more": False}

@api_router.get("/engagement/friend-activities")
@limiter.limit("20/minute")
async def get_engagement_friend_activities_endpoint(
    request: Request,
    limit: int = 10,
    offset: int = 0,
    user_id: str = Depends(get_current_user)
):
    """Get friend activities for engagement dashboard"""
    try:
        db = await get_database()
        
        # Get friends
        friendships = await db.friendships.find({
            "$or": [
                {"user_id": user_id},
                {"friend_id": user_id}
            ],
            "status": "accepted"
        }).to_list(length=None)
        
        friend_ids = []
        for friendship in friendships:
            if friendship.get("user_id") == user_id:
                friend_ids.append(friendship.get("friend_id"))
            else:
                friend_ids.append(friendship.get("user_id"))
        
        if not friend_ids:
            return {
                "activities": [],
                "message": "Add friends to see their activities and achievements!",
                "suggested_action": "Visit /friends to connect with other users"
            }
        
        friend_activities = []
        
        # Get friends' recent achievements with engagement metrics
        friend_achievements = await db.achievements.find({
            "user_id": {"$in": friend_ids}
        }).sort("created_at", -1).limit(8).to_list(length=8)
        
        for achievement in friend_achievements:
            friend = await db.users.find_one({"id": achievement.get("user_id")})
            if not friend:
                continue
                
            friend_name = friend.get("full_name", "Friend")
            friend_avatar = friend.get("avatar", "person")
            
            friend_activities.append({
                "id": str(achievement.get("_id", "")),
                "type": "friend_achievement",
                "friend_id": achievement.get("user_id"),
                "friend_name": friend_name,
                "friend_avatar": friend_avatar,
                "title": f"{friend_name} earned: {achievement.get('title', 'Achievement')}",
                "description": achievement.get('description', 'New achievement unlocked!'),
                "timestamp": achievement.get('created_at', datetime.now(timezone.utc)),
                "icon": achievement.get('icon', '🏆'),
                "points": achievement.get('points', 0),
                "engagement_type": "achievement",
                "can_congratulate": True
            })
        
        # Get friends' milestones
        friends_data = await db.users.find({
            "id": {"$in": friend_ids},
            "milestones_reached": {"$exists": True}
        }).limit(5).to_list(length=5)
        
        for friend in friends_data:
            friend_name = friend.get("full_name", "Friend")
            friend_avatar = friend.get("avatar", "person")
            recent_milestones = friend.get('milestones_reached', [])[-1:]  # Latest milestone
            
            for milestone in recent_milestones:
                friend_activities.append({
                    "id": f"friend_milestone_{friend.get('id')}_{milestone.get('type')}",
                    "type": "friend_milestone",
                    "friend_id": friend.get('id'),
                    "friend_name": friend_name,
                    "friend_avatar": friend_avatar,
                    "title": f"{friend_name} reached: {milestone.get('title', 'Milestone')}",
                    "description": milestone.get('description', 'Important milestone achieved!'),
                    "timestamp": milestone.get('achieved_at', datetime.now(timezone.utc)),
                    "icon": "🚀",
                    "value": milestone.get('value', 0),
                    "engagement_type": "milestone",
                    "can_congratulate": True
                })
        
        # Sort by timestamp
        friend_activities.sort(key=lambda x: x.get('timestamp', datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
        
        # Apply pagination
        paginated_activities = friend_activities[offset:offset + limit]
        
        return {
            "activities": paginated_activities,
            "total": len(friend_activities),
            "has_more": len(friend_activities) > offset + limit,
            "friends_count": len(friend_ids),
            "engagement_summary": {
                "recent_achievements": len([a for a in friend_activities if a.get('type') == 'friend_achievement']),
                "recent_milestones": len([a for a in friend_activities if a.get('type') == 'friend_milestone'])
            }
        }
        
    except Exception as e:
        logger.error(f"Get engagement friend activities error: {str(e)}")
        return {"activities": [], "total": 0, "has_more": False}

# ==================== END ENGAGEMENT FEATURES ====================

# ==================== PERFORMANCE MONITORING ENDPOINTS ====================

@api_router.get("/admin/performance/cache")
@limiter.limit("5/minute")
async def get_cache_statistics(request: Request, current_user: str = Depends(get_current_user)):
    """Get comprehensive cache performance statistics (Admin only)"""
    try:
        user = await get_user_by_id(current_user)
        if not user or user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get cache statistics
        cache_stats = await advanced_cache.get_stats()
        
        # Get database optimizer stats
        db_stats = await db_optimizer.get_performance_stats()
        
        # Get API optimizer stats
        api_stats = api_optimizer.get_performance_stats()
        
        # Get background task stats
        task_stats = background_processor.get_statistics()
        
        return api_optimizer.optimize_json_response({
            "cache_performance": cache_stats,
            "database_performance": db_stats,
            "api_performance": api_stats,
            "background_tasks": task_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get performance stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get performance statistics")

@api_router.post("/admin/performance/cache/warm")
@limiter.limit("2/hour")
async def warm_application_cache(request: Request, current_user: Dict[str, Any] = Depends(get_current_super_admin)):
    """Warm up application caches (Admin only)"""
    try:
        user = await get_user_by_id(current_user)
        if not user or user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Add cache warming task to background processor
        task_id = await background_processor.create_and_add_task(
            "cache_warming",
            cache_warming_task,
            priority=TaskPriority.HIGH
        )
        
        return {
            "message": "Cache warming initiated",
            "task_id": task_id,
            "status": "queued"
        }
        
    except Exception as e:
        logger.error(f"Cache warming error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate cache warming")

@api_router.post("/admin/performance/database/optimize")
@limiter.limit("1/hour")
async def optimize_database_performance(request: Request, current_user: Dict[str, Any] = Depends(get_current_super_admin)):
    """Run database optimization tasks (Admin only)"""
    try:
        user = await get_user_by_id(current_user)
        if not user or user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Add database maintenance task to background processor
        task_id = await background_processor.create_and_add_task(
            "database_maintenance",
            database_maintenance_task,
            priority=TaskPriority.MEDIUM
        )
        
        return {
            "message": "Database optimization initiated",
            "task_id": task_id,
            "status": "queued"
        }
        
    except Exception as e:
        logger.error(f"Database optimization error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate database optimization")

@api_router.get("/admin/performance/tasks/{task_id}")
@limiter.limit("10/minute")
async def get_task_status(request: Request, task_id: str, current_user: Dict[str, Any] = Depends(get_current_super_admin)):
    """Get background task status (Admin only)"""
    try:
        user = await get_user_by_id(current_user)
        if not user or user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        task_status = await background_processor.get_task_status(task_id)
        if not task_status:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task_status
        
    except Exception as e:
        logger.error(f"Get task status error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get task status")

# ==================== END PERFORMANCE MONITORING ====================

# Router will be included at the very end after ALL endpoints are defined

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Performance optimization startup and shutdown events
@app.on_event("startup")
async def startup_performance_services():
    """Initialize performance optimization services"""
    try:
        # Initialize database optimizer and create indexes
        await db_optimizer.create_performance_indexes()
        logger.info("✅ Database performance indexes created")
        
        # Start background task processor
        asyncio.create_task(background_processor.start_processing())
        logger.info("✅ Background task processor started")
        
        # Warm up critical caches
        await background_processor.create_and_add_task(
            "initial_cache_warming",
            cache_warming_task,
            priority=TaskPriority.HIGH
        )
        logger.info("✅ Initial cache warming queued")
        
        # Schedule periodic maintenance tasks
        await background_processor.create_and_add_task(
            "database_maintenance",
            database_maintenance_task,
            priority=TaskPriority.LOW,
            scheduled_for=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        logger.info("✅ Periodic maintenance scheduled")
        
        # Schedule inter-college competition progress updates (every 5 minutes)
        await background_processor.create_and_add_task(
            "inter_college_progress_update",
            update_inter_college_competitions_progress,
            priority=TaskPriority.MEDIUM,
            scheduled_for=datetime.now(timezone.utc) + timedelta(minutes=5)
        )
        logger.info("✅ Inter-college competition progress tracking scheduled")
        
        # Schedule auto-completion check for expired competitions (every 10 minutes)
        await background_processor.create_and_add_task(
            "auto_complete_competitions",
            auto_complete_expired_competitions,
            priority=TaskPriority.HIGH,
            scheduled_for=datetime.now(timezone.utc) + timedelta(minutes=10)
        )
        logger.info("✅ Auto-completion of expired competitions scheduled")
        
        logger.info("🚀 Performance optimization services initialized successfully")
        
    except Exception as e:
        logger.error(f"Performance services startup error: {str(e)}")

@app.on_event("shutdown")
async def shutdown_db_client():
    """Close database connection and performance services on shutdown"""
    try:
        # Stop background task processor
        await background_processor.stop_processing()
        logger.info("✅ Background task processor stopped")
        
        # Close database connection
        client.close()
        logger.info("✅ Database connection closed")
        
        # Clean up thread pools
        advanced_cache.thread_pool.shutdown(wait=True)
        logger.info("✅ Thread pools shut down")
        
        logger.info("🛑 All services shut down successfully")
        
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}")

# ===== CAMPUS ADMIN VERIFICATION SYSTEM =====

@api_router.post("/admin/campus/request")
@limiter.limit("3/day")  # Limited to prevent spam
async def request_campus_admin_privileges(
    request: Request,
    admin_request_data: CampusAdminRequestCreate,
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Request campus admin privileges with verification workflow - Routes to Super Admin"""
    try:
        db = await get_database()
        
        # Only allow campus_admin requests on this endpoint
        if admin_request_data.requested_admin_type != "campus_admin":
            raise HTTPException(
                status_code=400, 
                detail="This endpoint is only for campus admin requests. Use /admin/club/request for club admin requests."
            )
        
        # Check if user already has pending or approved request
        existing_request = await db.campus_admin_requests.find_one({
            "user_id": current_user["id"],
            "status": {"$in": ["pending", "under_review", "approved"]}
        })
        
        if existing_request:
            status = existing_request.get("status")
            if status == "approved":
                raise HTTPException(status_code=400, detail="You already have campus admin privileges")
            else:
                raise HTTPException(status_code=400, detail=f"You already have a {status} admin request")
        
        # Get user details
        user = await get_user_by_id(current_user["id"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check college-specific admin limits
        college_name = admin_request_data.college_name
        requested_type = admin_request_data.requested_admin_type
        
        # Count existing approved campus admins for this college
        existing_campus_admins = await db.campus_admins.count_documents({
            "college_name": college_name,
            "admin_type": "campus_admin",
            "status": "active"
        })
        
        # Check limits: max 5 campus admins per college
        if existing_campus_admins >= 5:
            raise HTTPException(
                status_code=400, 
                detail=f"College '{college_name}' has reached the maximum limit of 5 Campus Admins. Current count: {existing_campus_admins}"
            )
        
        # Process the admin request
        request_data = admin_request_data.dict()
        request_data["email"] = user.get("email")
        
        workflow_result = await admin_workflow_manager.process_admin_request(request_data, current_user)
        
        if not workflow_result["request_created"]:
            raise HTTPException(status_code=500, detail=workflow_result.get("error", "Failed to create admin request"))
        
        # Save the request to database
        admin_request = workflow_result["admin_request"]
        await db.campus_admin_requests.insert_one(admin_request)
        
        # Send real-time notification to system admins
        try:
            notification_service = await get_notification_service(db)
            await notification_service.notify_admin_request_submitted(admin_request)
        except Exception as e:
            logger.error(f"Failed to send real-time notification: {str(e)}")
        
        # Create system admin notification
        notification = {
            "id": str(uuid.uuid4()),
            "title": f"New Campus Admin Request: {admin_request['requested_admin_type'].title()}",
            "message": f"{admin_request['full_name']} from {admin_request['college_name']} has requested {admin_request['requested_admin_type']} privileges",
            "notification_type": "admin_request",
            "priority": "normal",
            "source_type": "user",
            "source_id": current_user,
            "related_request_id": admin_request["id"],
            "related_user_id": current_user,
            "action_buttons": [
                {"label": "Review Request", "action": "review_admin_request"},
                {"label": "View Profile", "action": "view_user_profile"}
            ],
            "is_read": False,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(days=30)
        }
        await db.system_admin_notifications.insert_one(notification)
        
        # Log the action
        audit_log = await admin_workflow_manager.create_audit_log(
            admin_user_id="system",
            action_type="admin_request_submitted",
            action_description=f"Campus admin request submitted by {user.get('email')}",
            target_type="admin_request",
            target_id=admin_request["id"],
            affected_entities=[{"type": "user", "id": current_user, "name": user.get("full_name", "Unknown")}],
            ip_address=request.client.host
        )
        await db.admin_audit_logs.insert_one(audit_log)
        
        return {
            "message": "Admin request submitted successfully",
            "request_id": admin_request["id"],
            "status": admin_request["status"],
            "verification_method": admin_request["verification_method"],
            "email_verification": workflow_result.get("email_verification"),
            "requires_documents": workflow_result.get("requires_documents", False),
            "next_steps": workflow_result.get("next_steps", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Campus admin request error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit admin request")

@api_router.post("/admin/club/request")
@limiter.limit("3/day")  # Limited to prevent spam
async def request_club_admin_privileges(
    request: Request,
    admin_request_data: CampusAdminRequestCreate,
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Request club admin privileges - Routes to Campus Admin for approval"""
    try:
        db = await get_database()
        
        # Only allow club_admin requests on this endpoint
        if admin_request_data.requested_admin_type != "club_admin":
            raise HTTPException(
                status_code=400, 
                detail="This endpoint is only for club admin requests. Use /admin/campus/request for campus admin requests."
            )
        
        # Ensure club_name is provided for club admin requests
        if not admin_request_data.club_name:
            raise HTTPException(status_code=400, detail="Club name is required for club admin requests")
        
        # Check if user already has pending or approved club admin request
        existing_request = await db.club_admin_requests.find_one({
            "user_id": current_user["id"],
            "status": {"$in": ["pending", "approved"]}
        })
        
        if existing_request:
            status = existing_request.get("status")
            if status == "approved":
                raise HTTPException(status_code=400, detail="You already have club admin privileges")
            else:
                raise HTTPException(status_code=400, detail=f"You already have a {status} club admin request")
        
        # Get user details
        user = await get_user_by_id(current_user["id"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check college-specific club admin limits
        college_name = admin_request_data.college_name
        existing_club_admins = await db.campus_admins.count_documents({
            "college_name": college_name,
            "admin_type": "club_admin", 
            "status": "active"
        })
        
        # Check limits: max 10 club admins per college
        if existing_club_admins >= 10:
            raise HTTPException(
                status_code=400,
                detail=f"College '{college_name}' has reached the maximum limit of 10 Club Admins. Current count: {existing_club_admins}"
            )
        
        # Find campus admin for this college
        campus_admin = await db.campus_admins.find_one({
            "college_name": college_name,
            "admin_type": "campus_admin",
            "status": "active"
        })
        
        if not campus_admin:
            raise HTTPException(
                status_code=400, 
                detail=f"No active campus admin found for {college_name}. Contact your college administration to request a campus admin first."
            )
        
        # Create club admin request
        club_admin_request = ClubAdminRequest(
            user_id=current_user["id"],
            campus_admin_id=campus_admin["user_id"],
            college_name=college_name,
            club_name=admin_request_data.club_name,
            club_type=admin_request_data.club_type,
            full_name=admin_request_data.full_name,
            email=user.get("email"),
            phone_number=admin_request_data.phone_number,
            motivation=admin_request_data.motivation,
            previous_experience=admin_request_data.previous_experience,
            status="pending"
        )
        
        # Save the request to database
        await db.club_admin_requests.insert_one(club_admin_request.dict())
        
        # Create campus admin notification
        notification = {
            "id": str(uuid.uuid4()),
            "title": f"New Club Admin Request: {admin_request_data.club_name}",
            "message": f"{admin_request_data.full_name} has requested club admin privileges for {admin_request_data.club_name} at {college_name}",
            "notification_type": "club_admin_request",
            "priority": "normal",
            "source_type": "user",
            "source_id": current_user["id"],
            "related_request_id": club_admin_request.id,
            "related_user_id": current_user["id"],
            "action_buttons": [
                {"label": "Review Request", "action": "review_club_admin_request"},
                {"label": "View Profile", "action": "view_user_profile"}
            ],
            "is_read": False,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(days=30)
        }
        
        # Send notification to campus admin, not super admin
        await db.campus_admin_notifications.insert_one(notification)
        
        # Send real-time notification to campus admin
        try:
            notification_service = await get_notification_service(db)
            await notification_service.notify_campus_admin_club_request(campus_admin["user_id"], club_admin_request.dict())
        except Exception as e:
            logger.error(f"Failed to send real-time notification: {str(e)}")
        
        # Log the action
        audit_log = {
            "id": str(uuid.uuid4()),
            "admin_user_id": campus_admin["user_id"],
            "action_type": "club_admin_request_submitted",
            "action_description": f"Club admin request submitted by {user.get('email')} for {admin_request_data.club_name}",
            "target_type": "club_admin_request",
            "target_id": club_admin_request.id,
            "affected_entities": [{"type": "user", "id": current_user["id"], "name": user.get("full_name", "Unknown")}],
            "ip_address": request.client.host,
            "severity": "info",
            "admin_level": "campus_admin",
            "college_name": college_name,
            "success": True,
            "created_at": datetime.now(timezone.utc)
        }
        await db.admin_audit_logs.insert_one(audit_log)
        
        return {
            "message": "Club admin request submitted successfully",
            "request_id": club_admin_request.id,
            "status": "pending",
            "campus_admin_notified": True,
            "college_name": college_name,
            "club_name": admin_request_data.club_name,
            "next_steps": [
                f"Your request has been sent to the campus admin of {college_name}",
                "The campus admin will review your request and club details",
                "You will receive a notification once the decision is made",
                "Check your notifications for updates"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Club admin request error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit club admin request")

@api_router.post("/admin/campus/verify-email/{request_id}")
@limiter.limit("10/minute")
async def verify_admin_email(
    request: Request,
    request_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Verify institutional email for admin request"""
    try:
        db = await get_database()
        
        # Get admin request
        admin_request = await db.campus_admin_requests.find_one({
            "id": request_id,
            "user_id": current_user["id"],
            "status": {"$in": ["pending", "under_review"]}
        })
        
        if not admin_request:
            raise HTTPException(status_code=404, detail="Admin request not found or already processed")
        
        if not admin_request.get("institutional_email"):
            raise HTTPException(status_code=400, detail="No institutional email provided for verification")
        
        # Verify email domain
        verification_result = await email_verifier.verify_email_domain(
            admin_request["institutional_email"],
            admin_request["college_name"]
        )
        
        # Update request with verification result
        update_data = {
            "email_verified": verification_result["verified"],
            "college_email_domain": verification_result["domain"]
        }
        
        if verification_result["verified"]:
            update_data["email_verified_at"] = datetime.now(timezone.utc)
            update_data["email_verification_token"] = str(uuid.uuid4())
            
            # Auto-approve if domain is in verified database
            if verification_result.get("auto_approved"):
                update_data["status"] = "approved"
                update_data["decision_made_at"] = datetime.now(timezone.utc)
                update_data["reviewed_by"] = "system_auto"
                update_data["review_notes"] = "Auto-approved based on verified institutional email domain"
                
                # Create campus admin record
                admin_privileges = admin_workflow_manager.generate_admin_permissions(
                    admin_request["requested_admin_type"]
                )
                
                campus_admin = {
                    "id": str(uuid.uuid4()),
                    "user_id": current_user["id"],
                    "request_id": request_id,
                    "admin_type": admin_request["requested_admin_type"],
                    "college_name": admin_request["college_name"],
                    "club_name": admin_request.get("club_name"),
                    "permissions": admin_privileges["permissions"],
                    "can_create_inter_college": admin_privileges["can_create_inter_college"],
                    "can_create_intra_college": admin_privileges["can_create_intra_college"],
                    "can_manage_reputation": admin_privileges["can_manage_reputation"],
                    "max_competitions_per_month": admin_privileges["max_competitions_per_month"],
                    "status": "active",
                    "appointed_at": datetime.now(timezone.utc),
                    "appointed_by": "system_auto",
                    "expires_at": datetime.now(timezone.utc) + timedelta(days=365),
                    "competitions_created": 0,
                    "challenges_created": 0,
                    "participants_managed": 0,
                    "reputation_points_awarded": 0,
                    "warnings_count": 0
                }
                await db.campus_admins.insert_one(campus_admin)
            else:
                update_data["status"] = "under_review"
                update_data["review_started_at"] = datetime.now(timezone.utc)
        
        await db.campus_admin_requests.update_one(
            {"id": request_id},
            {"$set": update_data}
        )
        
        return {
            "message": "Email verification completed",
            "verified": verification_result["verified"],
            "verification_result": verification_result,
            "status": update_data.get("status", admin_request["status"]),
            "auto_approved": verification_result.get("auto_approved", False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify email")

@api_router.post("/admin/campus/upload-document/{request_id}")
@limiter.limit("10/hour")
async def upload_admin_document(
    request: Request,
    request_id: str,
    document_type: str,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Upload verification document for admin request"""
    try:
        db = await get_database()
        
        # Validate document type
        if document_type not in ["college_id", "club_registration", "faculty_endorsement"]:
            raise HTTPException(status_code=400, detail="Invalid document type")
        
        # Get admin request
        admin_request = await db.campus_admin_requests.find_one({
            "id": request_id,
            "user_id": current_user["id"],
            "status": {"$in": ["pending", "under_review"]}
        })
        
        if not admin_request:
            raise HTTPException(status_code=404, detail="Admin request not found or already processed")
        
        # Read file content
        file_content = await file.read()
        
        # Save document
        document_result = await document_verifier.save_document(
            file_content, file.filename, current_user, document_type
        )
        
        if not document_result["success"]:
            raise HTTPException(status_code=400, detail=document_result["error"])
        
        # Update admin request with document info
        document_info = {
            "type": document_type,
            "filename": document_result["filename"],
            "original_filename": document_result["original_filename"],
            "file_path": document_result["file_path"],
            "file_size": document_result["file_size"],
            "upload_time": document_result["upload_time"].isoformat()
        }
        
        # Add to uploaded_documents array and set specific document field
        update_data = {
            "$push": {"uploaded_documents": document_info},
            "$set": {f"{document_type}_document": document_result["filename"]}
        }
        
        # Update verification method if this is the first document
        if not admin_request.get("uploaded_documents"):
            if admin_request.get("email_verified"):
                update_data["$set"]["verification_method"] = "both"
            else:
                update_data["$set"]["verification_method"] = "manual"
        
        await db.campus_admin_requests.update_one(
            {"id": request_id},
            update_data
        )
        
        return {
            "message": f"{document_type.replace('_', ' ').title()} uploaded successfully",
            "document_info": document_info,
            "upload_success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload document")

@api_router.get("/admin/campus/request/status")
@limiter.limit("20/minute")
async def get_admin_request_status(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Get current user's admin request status"""
    try:
        db = await get_database()
        
        # Get user's latest admin request
        admin_request = await db.campus_admin_requests.find_one(
            {"user_id": current_user["id"]},
            sort=[("submission_date", -1)]
        )
        
        if not admin_request:
            return {
                "has_request": False,
                "message": "No admin request found"
            }
        
        # Check if user is already an approved admin
        campus_admin = await db.campus_admins.find_one({
            "user_id": current_user["id"],
            "status": "active"
        })
        
        response = {
            "has_request": True,
            "request": {
                "id": admin_request["id"],
                "status": admin_request["status"],
                "requested_admin_type": admin_request["requested_admin_type"],
                "college_name": admin_request["college_name"],
                "club_name": admin_request.get("club_name"),
                "submission_date": admin_request["submission_date"].isoformat(),
                "verification_method": admin_request["verification_method"],
                "email_verified": admin_request.get("email_verified", False),
                "documents_uploaded": len(admin_request.get("uploaded_documents", [])),
                "review_notes": admin_request.get("review_notes"),
                "rejection_reason": admin_request.get("rejection_reason")
            }
        }
        
        if campus_admin:
            response["is_admin"] = True
            response["admin_details"] = {
                "admin_type": campus_admin["admin_type"],
                "permissions": campus_admin["permissions"],
                "can_create_inter_college": campus_admin["can_create_inter_college"],
                "competitions_created": campus_admin["competitions_created"],
                "appointed_at": campus_admin["appointed_at"].isoformat(),
                "expires_at": campus_admin.get("expires_at").isoformat() if campus_admin.get("expires_at") else None
            }
        else:
            response["is_admin"] = False
        
        return response
        
    except Exception as e:
        logger.error(f"Get admin request status error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get request status")

@api_router.get("/admin/club/request/status")
@limiter.limit("20/minute")
async def get_club_admin_request_status(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Get current user's club admin request status"""
    try:
        db = await get_database()
        
        # Get user's club admin request
        club_admin_request = await db.club_admin_requests.find_one({"user_id": current_user["id"]})
        
        if not club_admin_request:
            return {
                "has_request": False,
                "is_admin": False,
                "message": "No club admin request found"
            }
        
        # Check if user is already a club admin
        club_admin_record = await db.campus_admins.find_one({
            "user_id": current_user["id"],
            "admin_type": "club_admin",
            "status": "active"
        })
        
        response = {
            "has_request": True,
            "request": {
                "id": club_admin_request["id"],
                "status": club_admin_request["status"],
                "requested_admin_type": "club_admin",
                "college_name": club_admin_request["college_name"],
                "club_name": club_admin_request.get("club_name"),
                "submission_date": club_admin_request["submitted_at"],
                "email_verified": True,  # Club admin requests don't require email verification
                "documents_uploaded": 0,  # Club admin requests don't require document uploads
                "verification_method": "campus_admin_review",
                "review_notes": club_admin_request.get("review_notes"),
                "rejection_reason": club_admin_request.get("rejection_reason")
            },
            "is_admin": bool(club_admin_record),
            "admin_details": clean_mongo_doc(club_admin_record) if club_admin_record else None
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Get club admin request status error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get club admin request status")

# ===== SYSTEM ADMIN ENDPOINTS =====

@api_router.get("/super-admin/requests")
@limiter.limit("20/minute")
async def get_pending_admin_requests(
    request: Request,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    current_user: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Get pending admin requests for system admin review"""
    try:
        db = await get_database()
        
        # Check if user is system admin
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="System admin access required")
        
        # Build query filter
        query_filter = {}
        if status:
            query_filter["status"] = status
        else:
            query_filter["status"] = {"$in": ["pending", "under_review"]}
        
        # Get total count
        total_count = await db.campus_admin_requests.count_documents(query_filter)
        
        # Get paginated requests
        skip = (page - 1) * limit
        requests_cursor = db.campus_admin_requests.find(query_filter).sort("submission_date", -1).skip(skip).limit(limit)
        admin_requests = await requests_cursor.to_list(None)
        
        # Enrich with user details
        for req in admin_requests:
            user = await get_user_by_id(req["user_id"])
            if user:
                req["user_details"] = {
                    "full_name": user.get("full_name", req.get("full_name")),
                    "email": user.get("email"),
                    "university": user.get("university"),
                    "created_at": user.get("created_at"),
                    "last_login": user.get("last_login"),
                    "is_active": user.get("is_active", True)
                }
        
        return {
            "requests": clean_mongo_doc(admin_requests),
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total_count,
                "total_pages": (total_count + limit - 1) // limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get admin requests error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get admin requests")

@api_router.post("/super-admin/requests/{request_id}/review")
@limiter.limit("10/minute")
async def review_admin_request(
    request: Request,
    request_id: str,
    review_data: AdminRequestReview,
    current_user: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Review and approve/reject admin request"""
    try:
        db = await get_database()
        
        # Check if user is system admin
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="System admin access required")
        
        # Get admin request
        admin_request = await db.campus_admin_requests.find_one({
            "id": request_id,
            "status": {"$in": ["pending", "under_review"]}
        })
        
        if not admin_request:
            raise HTTPException(status_code=404, detail="Admin request not found or already processed")
        
        # Get user information
        # Handle both cases where user_id might be an object or string
        user_id = admin_request["user_id"]
        if isinstance(user_id, dict):
            # user_id is already the user object
            user = user_id
            actual_user_id = user_id["id"]
        else:
            # user_id is a string, need to fetch user
            actual_user_id = user_id
            user = await get_user_by_id(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
        
        decision_time = datetime.now(timezone.utc)
        
        # Prepare update data
        update_data = {
            "status": "approved" if review_data.decision == "approve" else "rejected",
            "decision_made_at": decision_time,
            "reviewed_by": current_user,
            "review_notes": review_data.review_notes
        }
        
        if review_data.decision == "reject":
            update_data["rejection_reason"] = review_data.rejection_reason
        else:
            update_data["approval_conditions"] = review_data.approval_conditions
            
            # Create campus admin record
            admin_type = review_data.admin_type or admin_request["requested_admin_type"]
            permissions = review_data.permissions or admin_workflow_manager.generate_admin_permissions(admin_type)["permissions"]
            
            campus_admin = {
                "id": str(uuid.uuid4()),
                "user_id": actual_user_id,
                "request_id": request_id,
                "admin_type": admin_type,
                "college_name": admin_request["college_name"],
                "club_name": admin_request.get("club_name"),
                "permissions": permissions,
                "can_create_inter_college": review_data.can_create_inter_college,
                "can_create_intra_college": True,
                "can_manage_reputation": admin_type == "campus_admin",
                "max_competitions_per_month": review_data.max_competitions_per_month,
                "status": "active",
                "appointed_at": decision_time,
                "appointed_by": current_user,
                "expires_at": decision_time + timedelta(days=30 * review_data.expires_in_months),
                "competitions_created": 0,
                "challenges_created": 0,
                "participants_managed": 0,
                "reputation_points_awarded": 0,
                "warnings_count": 0
            }
            await db.campus_admins.insert_one(campus_admin)
            
            # Update user's admin_level field
            await db.users.update_one(
                {"id": actual_user_id},
                {"$set": {
                    "admin_level": admin_type,
                    "is_admin": True
                }}
            )
        
        # Update admin request
        await db.campus_admin_requests.update_one(
            {"id": request_id},
            {"$set": update_data}
        )
        
        # Send real-time notification to user
        try:
            notification_service = await get_notification_service(db)
            updated_request = {**admin_request, **update_data}
            
            # Send status update notification
            await notification_service.notify_admin_request_status_update(
                actual_user_id, 
                updated_request
            )
            
            # If approved, also send admin privileges granted notification
            if review_data.decision == "approve":
                await notification_service.notify_admin_privileges_granted(
                    actual_user_id,
                    {
                        "admin_type": admin_type,
                        "permissions": permissions,
                        "can_create_inter_college": review_data.can_create_inter_college,
                        "max_competitions_per_month": review_data.max_competitions_per_month,
                        "expires_at": (decision_time + timedelta(days=30 * review_data.expires_in_months)).isoformat()
                    }
                )
        except Exception as e:
            logger.error(f"Failed to send real-time notification: {str(e)}")
        
        # Create audit log
        audit_log = await admin_workflow_manager.create_audit_log(
            admin_user_id=current_user["id"],
            action_type="admin_request_reviewed",
            action_description=f"Admin request {review_data.decision}d for {user['full_name']}",
            target_type="admin_request",
            target_id=request_id,
            before_state={"status": admin_request["status"]},
            after_state={"status": update_data["status"]},
            severity="info",
            ip_address=request.client.host
        )
        await db.admin_audit_logs.insert_one(audit_log)
        
        return {
            "message": f"Admin request {review_data.decision}d successfully",
            "decision": review_data.decision,
            "request_id": request_id,
            "admin_created": review_data.decision == "approve"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Review admin request error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to review admin request")

@api_router.get("/super-admin/admins")
@limiter.limit("20/minute")
async def get_campus_admins(
    request: Request,
    status: Optional[str] = None,
    admin_type: Optional[str] = None,
    college_name: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    current_user: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Get all campus admins for system admin management"""
    try:
        db = await get_database()
        
        # Check if user is system admin
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="System admin access required")
        
        # Build query filter
        query_filter = {}
        if status:
            query_filter["status"] = status
        if admin_type:
            query_filter["admin_type"] = admin_type
        if college_name:
            query_filter["college_name"] = {"$regex": college_name, "$options": "i"}
        
        # Get total count
        total_count = await db.campus_admins.count_documents(query_filter)
        
        # Get paginated admins
        skip = (page - 1) * limit
        admins_cursor = db.campus_admins.find(query_filter).sort("appointed_at", -1).skip(skip).limit(limit)
        campus_admins = await admins_cursor.to_list(None)
        
        # Enrich with user details
        for admin in campus_admins:
            user = await get_user_by_id(admin["user_id"])
            if user:
                admin["user_details"] = {
                    "full_name": user.get("full_name"),
                    "email": user.get("email"),
                    "last_login": user.get("last_login"),
                    "is_active": user.get("is_active", True)
                }
            
            # Calculate activity metrics
            admin["activity_metrics"] = {
                "total_competitions": admin["competitions_created"],
                "total_challenges": admin["challenges_created"],
                "participants_managed": admin["participants_managed"],
                "reputation_awarded": admin["reputation_points_awarded"],
                "warnings": admin["warnings_count"],
                "days_active": (datetime.now(timezone.utc) - admin["appointed_at"]).days
            }
        
        return {
            "admins": clean_mongo_doc(campus_admins),
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total_count,
                "total_pages": (total_count + limit - 1) // limit
            },
            "summary": {
                "total_active": await db.campus_admins.count_documents({"status": "active"}),
                "total_suspended": await db.campus_admins.count_documents({"status": "suspended"}),
                "club_admins": await db.campus_admins.count_documents({"admin_type": "club_admin"}),
                "campus_admins": await db.campus_admins.count_documents({"admin_type": "campus_admin"})
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get campus admins error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get campus admins")

@api_router.put("/super-admin/admins/{admin_id}/privileges")
@limiter.limit("10/minute")
async def update_admin_privileges(
    request: Request,
    admin_id: str,
    privilege_update: AdminPrivilegeUpdate,
    current_user: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Update campus admin privileges (suspend, reactivate, revoke, update permissions)"""
    try:
        db = await get_database()
        
        # Check if user is system admin
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="System admin access required")
        
        # Get campus admin
        campus_admin = await db.campus_admins.find_one({"id": admin_id})
        
        if not campus_admin:
            raise HTTPException(status_code=404, detail="Campus admin not found")
        
        # Store previous state for audit
        previous_state = {
            "status": campus_admin["status"],
            "permissions": campus_admin["permissions"]
        }
        
        # Apply updates based on action
        update_data = {}
        
        if privilege_update.action == "suspend":
            update_data["status"] = "suspended"
            if privilege_update.suspension_duration_days:
                update_data["suspension_expires_at"] = datetime.now(timezone.utc) + timedelta(days=privilege_update.suspension_duration_days)
        
        elif privilege_update.action == "reactivate":
            update_data["status"] = "active"
            update_data["$unset"] = {"suspension_expires_at": ""}
        
        elif privilege_update.action == "revoke":
            update_data["status"] = "revoked"
            update_data["expires_at"] = datetime.now(timezone.utc)
        
        elif privilege_update.action == "update_permissions":
            if privilege_update.new_permissions:
                update_data["permissions"] = privilege_update.new_permissions
        
        # Add metadata
        update_data["last_privilege_update"] = datetime.now(timezone.utc)
        update_data["last_updated_by"] = current_user
        
        # Apply update
        await db.campus_admins.update_one(
            {"id": admin_id},
            {"$set": update_data} if "$unset" not in update_data else {"$set": {k: v for k, v in update_data.items() if k != "$unset"}, "$unset": update_data["$unset"]}
        )
        
        # Create audit log
        audit_log = await admin_workflow_manager.create_audit_log(
            admin_user_id=current_user["id"],
            action_type=f"admin_privilege_{privilege_update.action}",
            action_description=f"Campus admin privileges {privilege_update.action}d: {privilege_update.reason}",
            target_type="campus_admin",
            target_id=admin_id,
            before_state=previous_state,
            after_state=update_data,
            severity="warning" if privilege_update.action in ["suspend", "revoke"] else "info",
            ip_address=request.client.host
        )
        await db.admin_audit_logs.insert_one(audit_log)
        
        return {
            "message": f"Admin privileges {privilege_update.action}d successfully",
            "action": privilege_update.action,
            "admin_id": admin_id,
            "reason": privilege_update.reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update admin privileges error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update admin privileges")

@api_router.get("/super-admin/audit-logs")
@limiter.limit("20/minute")
async def get_admin_audit_logs(
    request: Request,
    action_type: Optional[str] = None,
    severity: Optional[str] = None,
    days: int = 30,
    page: int = 1,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Get admin audit logs for system admin review"""
    try:
        db = await get_database()
        
        # Check if user is system admin
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="System admin access required")
        
        # Build query filter
        query_filter = {
            "timestamp": {"$gte": datetime.now(timezone.utc) - timedelta(days=days)}
        }
        
        if action_type:
            query_filter["action_type"] = action_type
        if severity:
            query_filter["severity"] = severity
        
        # Get total count
        total_count = await db.admin_audit_logs.count_documents(query_filter)
        
        # Get paginated logs
        skip = (page - 1) * limit
        logs_cursor = db.admin_audit_logs.find(query_filter).sort("timestamp", -1).skip(skip).limit(limit)
        audit_logs = await logs_cursor.to_list(None)
        
        # Enrich with admin details
        for log in audit_logs:
            if log.get("admin_user_id") and log["admin_user_id"] != "system":
                admin_user = await get_user_by_id(log["admin_user_id"])
                if admin_user:
                    log["admin_details"] = {
                        "full_name": admin_user.get("full_name"),
                        "email": admin_user.get("email")
                    }
        
        return {
            "audit_logs": clean_mongo_doc(audit_logs),
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total_count,
                "total_pages": (total_count + limit - 1) // limit
            },
            "summary": {
                "total_actions": total_count,
                "date_range": f"Last {days} days",
                "action_types": await db.admin_audit_logs.distinct("action_type", query_filter),
                "severity_counts": {
                    "info": await db.admin_audit_logs.count_documents({**query_filter, "severity": "info"}),
                    "warning": await db.admin_audit_logs.count_documents({**query_filter, "severity": "warning"}),
                    "error": await db.admin_audit_logs.count_documents({**query_filter, "severity": "error"}),
                    "critical": await db.admin_audit_logs.count_documents({**query_filter, "severity": "critical"})
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get audit logs error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get audit logs")



# ===== SUPER ADMIN OVERSIGHT ENDPOINTS =====

@api_router.get("/super-admin/dashboard")
@limiter.limit("20/minute")
async def get_super_admin_dashboard(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Get super admin dashboard with comprehensive oversight metrics"""
    try:
        db = await get_database()
        
        # Get counts for all admin levels
        total_campus_admins = await db.campus_admins.count_documents({"admin_type": "campus_admin"})
        active_campus_admins = await db.campus_admins.count_documents({
            "admin_type": "campus_admin",
            "status": "active"
        })
        total_club_admins = await db.campus_admins.count_documents({"admin_type": "club_admin"})
        active_club_admins = await db.campus_admins.count_documents({
            "admin_type": "club_admin",
            "status": "active"
        })
        
        # Get pending requests
        pending_requests = await db.campus_admin_requests.count_documents({"status": "pending"})
        
        # Get recent admin activity (last 24 hours)
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        recent_activity = await db.admin_audit_logs.count_documents({
            "timestamp": {"$gte": yesterday}
        })
        
        # Get critical alerts
        unread_alerts = await db.admin_alerts.count_documents({
            "read_at": None,
            "severity": {"$in": ["warning", "critical"]}
        })
        
        # Get performance metrics
        last_month = datetime.now(timezone.utc) - timedelta(days=30)
        total_competitions = await db.inter_college_competitions.count_documents({
            "created_at": {"$gte": last_month}
        })
        total_challenges = await db.prize_challenges.count_documents({
            "created_at": {"$gte": last_month}
        })
        
        # Get top performing admins
        top_admins_cursor = db.campus_admins.find({
            "status": "active"
        }).sort("competitions_created", -1).limit(5)
        top_admins = await top_admins_cursor.to_list(None)
        
        for admin in top_admins:
            user = await get_user_by_id(admin["user_id"])
            if user:
                admin["full_name"] = user.get("full_name")
                admin["email"] = user.get("email")
        
        return {
            "summary": {
                "total_campus_admins": total_campus_admins,
                "active_campus_admins": active_campus_admins,
                "total_club_admins": total_club_admins,
                "active_club_admins": active_club_admins,
                "pending_requests": pending_requests,
                "unread_alerts": unread_alerts
            },
            "activity": {
                "recent_actions_24h": recent_activity,
                "competitions_last_30d": total_competitions,
                "challenges_last_30d": total_challenges
            },
            "top_performers": clean_mongo_doc(top_admins)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get super admin dashboard error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")

@api_router.get("/super-admin/campus-admins")
@limiter.limit("30/minute")
async def get_campus_admins_list(
    request: Request,
    status: Optional[str] = None,
    college_name: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Get list of all campus admins with detailed information"""
    try:
        db = await get_database()
        
        # Build query
        query = {"admin_type": "campus_admin"}
        if status:
            query["status"] = status
        if college_name:
            query["college_name"] = college_name
        
        # Get total count
        total_count = await db.campus_admins.count_documents(query)
        
        # Get paginated campus admins
        skip = (page - 1) * limit
        campus_admins_cursor = db.campus_admins.find(query).sort("appointed_at", -1).skip(skip).limit(limit)
        campus_admins = await campus_admins_cursor.to_list(None)
        
        # Enrich with user details
        for admin in campus_admins:
            # Get user details
            user = await get_user_by_id(admin["user_id"])
            if user:
                admin["full_name"] = user.get("full_name")
                admin["email"] = user.get("email")
                admin["university"] = user.get("university")
            
            # Get appointing admin details if appointed by someone
            if admin.get("appointed_by"):
                if isinstance(admin["appointed_by"], dict):
                    admin["appointed_by_name"] = admin["appointed_by"].get("full_name", "Unknown")
                else:
                    appointer = await get_user_by_id(admin["appointed_by"])
                    if appointer:
                        admin["appointed_by_name"] = appointer.get("full_name", "Unknown")
        
        return {
            "campus_admins": clean_mongo_doc(campus_admins),
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total_count,
                "total_pages": (total_count + limit - 1) // limit
            },
            "summary": {
                "total_campus_admins": total_count,
                "by_status": {
                    "active": await db.campus_admins.count_documents({**query, "status": "active"}),
                    "suspended": await db.campus_admins.count_documents({**query, "status": "suspended"}),
                    "revoked": await db.campus_admins.count_documents({**query, "status": "revoked"})
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get campus admins list error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get campus admins")

@api_router.get("/super-admin/campus-admins/activities")
@limiter.limit("30/minute")
async def get_campus_admin_activities(
    request: Request,
    admin_id: Optional[str] = None,
    college_name: Optional[str] = None,
    days: int = 30,
    current_user: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Monitor all campus admin activities across universities"""
    try:
        db = await get_database()
        
        # Build query
        query = {"timestamp": {"$gte": datetime.now(timezone.utc) - timedelta(days=days)}}
        if admin_id:
            # Get admin user_id from admin_id
            admin = await db.campus_admins.find_one({"id": admin_id})
            if admin:
                query["admin_user_id"] = admin["user_id"]
        if college_name:
            query["college_name"] = college_name
        
        # Get activities
        activities_cursor = db.admin_audit_logs.find(query).sort("timestamp", -1).limit(100)
        activities = await activities_cursor.to_list(None)
        
        # Enrich with admin details
        for activity in activities:
            if activity.get("admin_user_id"):
                user = await get_user_by_id(activity["admin_user_id"])
                if user:
                    activity["admin_details"] = {
                        "full_name": user.get("full_name"),
                        "email": user.get("email"),
                        "university": user.get("university")
                    }
                
                # Get admin record
                admin = await db.campus_admins.find_one({"user_id": activity["admin_user_id"]})
                if admin:
                    activity["admin_type"] = admin.get("admin_type")
                    activity["college_name"] = admin.get("college_name")
        
        return {
            "activities": clean_mongo_doc(activities),
            "total_count": len(activities),
            "date_range": f"Last {days} days"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get campus admin activities error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get activities")

@api_router.get("/super-admin/campus-admins/{admin_id}/metrics")
@limiter.limit("30/minute")
async def get_campus_admin_metrics(
    request: Request,
    admin_id: str,
    period_days: int = 30,
    current_user: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Get detailed performance metrics for a specific campus admin"""
    try:
        db = await get_database()
        
        # Get admin record
        admin = await db.campus_admins.find_one({"id": admin_id})
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        
        # Get user details
        user = await get_user_by_id(admin["user_id"])
        
        # Calculate time-based metrics
        appointed_date = admin.get("appointed_at", datetime.now(timezone.utc))
        days_since_appointment = (datetime.now(timezone.utc) - appointed_date).days
        
        # Get activity metrics
        period_start = datetime.now(timezone.utc) - timedelta(days=period_days)
        
        competitions_created = await db.inter_college_competitions.count_documents({
            "created_by": admin["user_id"],
            "created_at": {"$gte": period_start}
        })
        
        challenges_created = await db.prize_challenges.count_documents({
            "created_by": admin["user_id"],
            "created_at": {"$gte": period_start}
        })
        
        # Get audit logs for this admin
        admin_actions = await db.admin_audit_logs.count_documents({
            "admin_user_id": admin["user_id"],
            "timestamp": {"$gte": period_start}
        })
        
        # Calculate success rate
        total_competitions = admin.get("competitions_created", 0)
        completed_competitions = await db.inter_college_competitions.count_documents({
            "created_by": admin["user_id"],
            "status": "completed"
        })
        success_rate = (completed_competitions / total_competitions * 100) if total_competitions > 0 else 0
        
        # Get club admins managed (if campus admin)
        club_admins_managed = 0
        if admin.get("admin_type") == "campus_admin":
            club_admins_managed = await db.campus_admins.count_documents({
                "admin_type": "club_admin",
                "college_name": admin.get("college_name"),
                "appointed_by": admin["user_id"]
            })
        
        return {
            "admin_details": {
                "id": admin["id"],
                "user_id": admin["user_id"],
                "full_name": user.get("full_name") if user else "Unknown",
                "email": user.get("email") if user else "Unknown",
                "admin_type": admin.get("admin_type"),
                "college_name": admin.get("college_name"),
                "club_name": admin.get("club_name"),
                "status": admin.get("status"),
                "appointed_at": admin.get("appointed_at")
            },
            "time_metrics": {
                "days_since_appointment": days_since_appointment,
                "days_active": admin.get("days_active", 0),
                "last_activity": admin.get("last_activity")
            },
            "activity_metrics": {
                "competitions_created_period": competitions_created,
                "challenges_created_period": challenges_created,
                "total_competitions": total_competitions,
                "total_challenges": admin.get("challenges_created", 0),
                "participants_managed": admin.get("participants_managed", 0),
                "club_admins_managed": club_admins_managed,
                "total_actions_period": admin_actions
            },
            "performance_metrics": {
                "success_rate": round(success_rate, 2),
                "completed_competitions": completed_competitions,
                "reputation_points_awarded": admin.get("reputation_points_awarded", 0),
                "warnings_count": admin.get("warnings_count", 0)
            },
            "period_info": {
                "period_days": period_days,
                "period_start": period_start,
                "period_end": datetime.now(timezone.utc)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get admin metrics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get admin metrics")

@api_router.put("/super-admin/campus-admins/{admin_id}/suspend")
@limiter.limit("10/minute")
async def suspend_campus_admin(
    request: Request,
    admin_id: str,
    suspension_reason: str,
    duration_days: Optional[int] = None,
    current_user: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Suspend a campus admin temporarily"""
    try:
        db = await get_database()
        
        # Get admin record
        admin = await db.campus_admins.find_one({"id": admin_id})
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        
        # Update admin status
        update_data = {
            "status": "suspended",
            "suspension_reason": suspension_reason,
            "suspended_at": datetime.now(timezone.utc),
            "suspended_by": current_user["id"]
        }
        
        # Add expiry if duration specified
        if duration_days:
            update_data["suspension_expires_at"] = datetime.now(timezone.utc) + timedelta(days=duration_days)
        
        await db.campus_admins.update_one(
            {"id": admin_id},
            {"$set": update_data}
        )
        
        # Create audit log
        await create_audit_log(
            db=db,
            admin_user_id=current_user["id"],
            action_type="suspend_admin",
            action_description=f"Suspended {admin.get('admin_type')} admin: {suspension_reason}",
            target_type="campus_admin",
            target_id=admin_id,
            affected_entities=[{
                "type": "admin",
                "id": admin_id,
                "name": admin.get("user_id")
            }],
            before_state={"status": admin.get("status")},
            after_state=update_data,
            severity="warning",
            ip_address=request.client.host,
            admin_level="super_admin",
            college_name=admin.get("college_name"),
            success=True
        )
        
        return {
            "success": True,
            "message": "Admin suspended successfully",
            "admin_id": admin_id,
            "suspension_expires_at": update_data.get("suspension_expires_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Suspend admin error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to suspend admin")

@api_router.put("/super-admin/campus-admins/{admin_id}/revoke")
@limiter.limit("10/minute")
async def revoke_campus_admin(
    request: Request,
    admin_id: str,
    revocation_reason: str,
    current_user: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Permanently revoke campus admin privileges"""
    try:
        db = await get_database()
        
        # Get admin record
        admin = await db.campus_admins.find_one({"id": admin_id})
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        
        # Update admin status
        update_data = {
            "status": "revoked",
            "revocation_reason": revocation_reason,
            "revoked_at": datetime.now(timezone.utc),
            "revoked_by": current_user["id"]
        }
        
        await db.campus_admins.update_one(
            {"id": admin_id},
            {"$set": update_data}
        )
        
        # Create audit log
        await create_audit_log(
            db=db,
            admin_user_id=current_user["id"],
            action_type="revoke_admin",
            action_description=f"Revoked {admin.get('admin_type')} admin privileges: {revocation_reason}",
            target_type="campus_admin",
            target_id=admin_id,
            affected_entities=[{
                "type": "admin",
                "id": admin_id,
                "name": admin.get("user_id")
            }],
            before_state={"status": admin.get("status")},
            after_state=update_data,
            severity="critical",
            ip_address=request.client.host,
            admin_level="super_admin",
            college_name=admin.get("college_name"),
            success=True,
            alert_sent=True
        )
        
        return {
            "success": True,
            "message": "Admin privileges revoked successfully",
            "admin_id": admin_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revoke admin error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to revoke admin")

@api_router.put("/super-admin/campus-admins/{admin_id}/reactivate")
@limiter.limit("10/minute")
async def reactivate_campus_admin(
    request: Request,
    admin_id: str,
    reactivation_notes: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Reactivate a suspended campus admin"""
    try:
        db = await get_database()
        
        # Get admin record
        admin = await db.campus_admins.find_one({"id": admin_id})
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        
        if admin.get("status") != "suspended":
            raise HTTPException(status_code=400, detail="Admin is not suspended")
        
        # Update admin status
        update_data = {
            "status": "active",
            "suspension_reason": None,
            "suspended_at": None,
            "suspended_by": None,
            "suspension_expires_at": None,
            "reactivated_at": datetime.now(timezone.utc),
            "reactivated_by": current_user["id"],
            "reactivation_notes": reactivation_notes
        }
        
        await db.campus_admins.update_one(
            {"id": admin_id},
            {"$set": update_data, "$unset": {"suspension_expires_at": ""}}
        )
        
        # Create audit log
        await create_audit_log(
            db=db,
            admin_user_id=current_user["id"],
            action_type="reactivate_admin",
            action_description=f"Reactivated {admin.get('admin_type')} admin" + (f": {reactivation_notes}" if reactivation_notes else ""),
            target_type="campus_admin",
            target_id=admin_id,
            affected_entities=[{
                "type": "admin",
                "id": admin_id,
                "name": admin.get("user_id")
            }],
            before_state={"status": "suspended"},
            after_state={"status": "active"},
            severity="info",
            ip_address=request.client.host,
            admin_level="super_admin",
            college_name=admin.get("college_name"),
            success=True
        )
        
        return {
            "success": True,
            "message": "Admin reactivated successfully",
            "admin_id": admin_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reactivate admin error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reactivate admin")

@api_router.get("/super-admin/club-admins")
@limiter.limit("30/minute")
async def get_club_admins_overview(
    request: Request,
    college_name: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Get overview of all club admins with visibility into campus admin management"""
    try:
        db = await get_database()
        
        # Build query
        query = {"admin_type": "club_admin"}
        if college_name:
            query["college_name"] = college_name
        if status:
            query["status"] = status
        
        # Get total count
        total_count = await db.campus_admins.count_documents(query)
        
        # Get paginated club admins
        skip = (page - 1) * limit
        club_admins_cursor = db.campus_admins.find(query).sort("appointed_at", -1).skip(skip).limit(limit)
        club_admins = await club_admins_cursor.to_list(None)
        
        # Enrich with details
        for club_admin in club_admins:
            # Get user details
            user = await get_user_by_id(club_admin["user_id"])
            if user:
                club_admin["full_name"] = user.get("full_name")
                club_admin["email"] = user.get("email")
            
            # Get campus admin who appointed them
            if club_admin.get("appointed_by"):
                campus_admin_user = await get_user_by_id(club_admin["appointed_by"])
                if campus_admin_user:
                    club_admin["appointed_by_name"] = campus_admin_user.get("full_name")
        
        return {
            "club_admins": clean_mongo_doc(club_admins),
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total_count,
                "total_pages": (total_count + limit - 1) // limit
            },
            "summary": {
                "total_club_admins": total_count,
                "by_status": {
                    "active": await db.campus_admins.count_documents({**query, "status": "active"}),
                    "suspended": await db.campus_admins.count_documents({**query, "status": "suspended"}),
                    "revoked": await db.campus_admins.count_documents({**query, "status": "revoked"})
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get club admins overview error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get club admins")

@api_router.get("/super-admin/prize-challenges/{challenge_id}/participants")
@limiter.limit("30/minute")
async def get_prize_challenge_participants(
    request: Request,
    challenge_id: str,
    page: int = 1,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Get list of all participants for a specific prize challenge"""
    try:
        db = await get_database()
        
        # Get challenge details
        challenge = await db.prize_challenges.find_one({"id": challenge_id})
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        # Get total participant count
        total_count = await db.prize_challenge_participations.count_documents({"challenge_id": challenge_id})
        
        # Get paginated participants
        skip = (page - 1) * limit
        participants_cursor = db.prize_challenge_participations.find(
            {"challenge_id": challenge_id}
        ).sort("joined_at", -1).skip(skip).limit(limit)
        participants = await participants_cursor.to_list(None)
        
        # Enrich with user details
        for participant in participants:
            user = await get_user_by_id(participant["user_id"])
            if user:
                participant["full_name"] = user.get("full_name")
                participant["email"] = user.get("email")
                participant["university"] = user.get("university")
                participant["level"] = user.get("level", 1)
                participant["current_streak"] = user.get("current_streak", 0)
        
        return {
            "challenge": {
                "id": challenge["id"],
                "title": challenge["title"],
                "description": challenge.get("description"),
                "prize_type": challenge.get("prize_type"),
                "total_prize_value": challenge.get("total_prize_value")
            },
            "participants": clean_mongo_doc(participants),
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total_count,
                "total_pages": (total_count + limit - 1) // limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get prize challenge participants error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get challenge participants")

@api_router.get("/super-admin/inter-college/{competition_id}/participants")
@limiter.limit("30/minute")
async def get_inter_college_participants(
    request: Request,
    competition_id: str,
    campus: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Get list of all participants for a specific inter-college competition"""
    try:
        db = await get_database()
        
        # Get competition details
        competition = await db.inter_college_competitions.find_one({"id": competition_id})
        if not competition:
            raise HTTPException(status_code=404, detail="Competition not found")
        
        # Build query
        query = {"competition_id": competition_id}
        if campus:
            query["campus"] = campus
        
        # Get total participant count
        total_count = await db.campus_competition_participations.count_documents(query)
        
        # Get campus-wise breakdown
        pipeline = [
            {"$match": {"competition_id": competition_id}},
            {"$group": {
                "_id": "$campus",
                "count": {"$sum": 1}
            }}
        ]
        campus_breakdown_cursor = db.campus_competition_participations.aggregate(pipeline)
        campus_breakdown = await campus_breakdown_cursor.to_list(None)
        
        # Get paginated participants
        skip = (page - 1) * limit
        participants_cursor = db.campus_competition_participations.find(query).sort("registered_at", -1).skip(skip).limit(limit)
        participants = await participants_cursor.to_list(None)
        
        # Enrich with user details
        for participant in participants:
            user = await get_user_by_id(participant["user_id"])
            if user:
                participant["full_name"] = user.get("full_name")
                participant["email"] = user.get("email")
                participant["university"] = user.get("university")
                participant["level"] = user.get("level", 1)
        
        return {
            "competition": {
                "id": competition["id"],
                "title": competition["title"],
                "description": competition.get("description"),
                "prize_pool": competition.get("prize_pool"),
                "competition_type": competition.get("competition_type")
            },
            "participants": clean_mongo_doc(participants),
            "campus_breakdown": campus_breakdown,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total_count,
                "total_pages": (total_count + limit - 1) // limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get inter-college participants error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get competition participants")

@api_router.get("/super-admin/alerts")
@limiter.limit("30/minute")
async def get_super_admin_alerts(
    request: Request,
    severity: Optional[str] = None,
    unread_only: bool = False,
    page: int = 1,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Get real-time alerts for super admin"""
    try:
        db = await get_database()
        
        # Build query
        query = {}
        if severity:
            query["severity"] = severity
        if unread_only:
            query["read_at"] = None
        
        # Get total count
        total_count = await db.admin_alerts.count_documents(query)
        
        # Get paginated alerts
        skip = (page - 1) * limit
        alerts_cursor = db.admin_alerts.find(query).sort("created_at", -1).skip(skip).limit(limit)
        alerts = await alerts_cursor.to_list(None)
        
        return {
            "alerts": clean_mongo_doc(alerts),
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total_count,
                "total_pages": (total_count + limit - 1) // limit
            },
            "summary": {
                "total_unread": await db.admin_alerts.count_documents({"read_at": None}),
                "by_severity": {
                    "info": await db.admin_alerts.count_documents({**query, "severity": "info"}),
                    "warning": await db.admin_alerts.count_documents({**query, "severity": "warning"}),
                    "critical": await db.admin_alerts.count_documents({**query, "severity": "critical"})
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get alerts error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get alerts")

@api_router.put("/super-admin/alerts/{alert_id}/read")
@limiter.limit("30/minute")
async def mark_alert_as_read(
    request: Request,
    alert_id: str,
    current_user: Dict[str, Any] = Depends(get_current_super_admin)
):
    """Mark an alert as read"""
    try:
        db = await get_database()
        
        await db.admin_alerts.update_one(
            {"id": alert_id},
            {"$set": {"read_at": datetime.now(timezone.utc)}}
        )
        
        return {"success": True, "message": "Alert marked as read"}
        
    except Exception as e:
        logger.error(f"Mark alert as read error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark alert as read")

# ===== CAMPUS ADMIN DASHBOARD ENDPOINTS =====

@api_router.get("/campus-admin/dashboard")
@limiter.limit("20/minute")
async def get_campus_admin_dashboard(
    request: Request,
    current_campus_admin: Dict[str, Any] = Depends(get_current_campus_admin)
):
    """Get campus admin dashboard with statistics and recent activities"""
    try:
        db = await get_database()
        
        # Get admin statistics
        competitions_count = await db.inter_college_competitions.count_documents({
            "created_by": current_campus_admin["user_id"]
        })
        
        challenges_count = await db.prize_challenges.count_documents({
            "created_by": current_campus_admin["user_id"]
        })
        
        # Get recent competitions and challenges
        recent_competitions = await db.inter_college_competitions.find({
            "created_by": current_campus_admin["user_id"]
        }).sort("created_at", -1).limit(5).to_list(None)
        
        recent_challenges = await db.prize_challenges.find({
            "created_by": current_campus_admin["user_id"]
        }).sort("created_at", -1).limit(5).to_list(None)
        
        # Get campus reputation stats if admin can manage reputation
        campus_reputation = None
        if current_campus_admin.get("can_manage_reputation"):
            campus_reputation = await db.campus_reputation.find_one({
                "campus": current_campus_admin["college_name"]
            })
        
        # Get pending admin requests if this is a college admin
        pending_requests = []
        if current_campus_admin["admin_type"] == "campus_admin":
            pending_requests = await db.campus_admin_requests.find({
                "college_name": current_campus_admin["college_name"],
                "status": {"$in": ["pending", "under_review"]}
            }).limit(10).to_list(None)
        
        # Calculate remaining monthly quota
        current_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        competitions_this_month = await db.inter_college_competitions.count_documents({
            "created_by": current_campus_admin["user_id"],
            "created_at": {"$gte": current_month}
        })
        challenges_this_month = await db.prize_challenges.count_documents({
            "created_by": current_campus_admin["user_id"],
            "created_at": {"$gte": current_month}
        })
        
        total_this_month = competitions_this_month + challenges_this_month
        remaining_quota = max(0, current_campus_admin["max_competitions_per_month"] - total_this_month)
        
        return {
            "admin_details": {
                "admin_type": current_campus_admin["admin_type"],
                "college_name": current_campus_admin["college_name"],
                "club_name": current_campus_admin.get("club_name"),
                "permissions": current_campus_admin["permissions"],
                "appointed_at": current_campus_admin["appointed_at"].isoformat(),
                "expires_at": current_campus_admin.get("expires_at").isoformat() if current_campus_admin.get("expires_at") else None
            },
            "statistics": {
                "total_competitions": competitions_count,
                "total_challenges": challenges_count,
                "competitions_this_month": competitions_this_month,
                "challenges_this_month": challenges_this_month,
                "remaining_monthly_quota": remaining_quota,
                "participants_managed": current_campus_admin["participants_managed"],
                "reputation_points_awarded": current_campus_admin["reputation_points_awarded"]
            },
            "recent_competitions": clean_mongo_doc(recent_competitions),
            "recent_challenges": clean_mongo_doc(recent_challenges),
            "campus_reputation": clean_mongo_doc(campus_reputation) if campus_reputation else None,
            "pending_requests": clean_mongo_doc(pending_requests),
            "capabilities": {
                "can_create_inter_college": current_campus_admin["can_create_inter_college"],
                "can_create_intra_college": current_campus_admin["can_create_intra_college"],
                "can_manage_reputation": current_campus_admin["can_manage_reputation"],
                "max_competitions_per_month": current_campus_admin["max_competitions_per_month"]
            }
        }
        
    except Exception as e:
        logger.error(f"Campus admin dashboard error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get admin dashboard")

@api_router.get("/campus-admin/competitions")
@limiter.limit("20/minute")
async def get_campus_admin_competitions(
    request: Request,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    current_campus_admin: Dict[str, Any] = Depends(get_current_campus_admin)
):
    """Get competitions created by current campus admin"""
    try:
        db = await get_database()
        
        # Build query filter
        query_filter = {"created_by": current_campus_admin["user_id"]}
        if status:
            query_filter["status"] = status
        
        # Get total count
        total_count = await db.inter_college_competitions.count_documents(query_filter)
        
        # Get paginated competitions
        skip = (page - 1) * limit
        competitions_cursor = db.inter_college_competitions.find(query_filter).sort("created_at", -1).skip(skip).limit(limit)
        competitions = await competitions_cursor.to_list(None)
        
        # Enrich with participation statistics
        for comp in competitions:
            participant_count = await db.campus_competition_participations.count_documents({
                "competition_id": comp["id"]
            })
            comp["current_participants"] = participant_count
            
            # Get campus participation stats
            campus_stats = await db.campus_leaderboards.find({
                "competition_id": comp["id"]
            }).to_list(None)
            comp["participating_campuses"] = len(campus_stats)
        
        return {
            "competitions": clean_mongo_doc(competitions),
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total_count,
                "total_pages": (total_count + limit - 1) // limit
            }
        }
        
    except Exception as e:
        logger.error(f"Get campus admin competitions error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get competitions")

@api_router.get("/campus-admin/challenges")
@limiter.limit("20/minute")
async def get_campus_admin_challenges(
    request: Request,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    current_campus_admin: Dict[str, Any] = Depends(get_current_campus_admin)
):
    """Get challenges created by current campus admin"""
    try:
        db = await get_database()
        
        # Build query filter
        query_filter = {"created_by": current_campus_admin["user_id"]}
        if status:
            query_filter["status"] = status
        
        # Get total count
        total_count = await db.prize_challenges.count_documents(query_filter)
        
        # Get paginated challenges
        skip = (page - 1) * limit
        challenges_cursor = db.prize_challenges.find(query_filter).sort("created_at", -1).skip(skip).limit(limit)
        challenges = await challenges_cursor.to_list(None)
        
        # Enrich with participation statistics
        for challenge in challenges:
            participant_count = await db.prize_challenge_participations.count_documents({
                "challenge_id": challenge["id"]
            })
            challenge["current_participants"] = participant_count
        
        return {
            "challenges": clean_mongo_doc(challenges),
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total_count,
                "total_pages": (total_count + limit - 1) // limit
            }
        }
        
    except Exception as e:
        logger.error(f"Get campus admin challenges error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get challenges")

@api_router.post("/campus-admin/competitions/{competition_id}/moderate")
@limiter.limit("10/minute")
async def moderate_competition_participant(
    request: Request,
    competition_id: str,
    user_id: str,
    action: str,  # "warn", "disqualify", "reinstate"
    reason: str,
    current_campus_admin: Dict[str, Any] = Depends(get_current_campus_admin)
):
    """Moderate competition participants (warnings, disqualifications)"""
    try:
        db = await get_database()
        
        if action not in ["warn", "disqualify", "reinstate"]:
            raise HTTPException(status_code=400, detail="Invalid moderation action")
        
        # Verify the competition belongs to the admin
        competition = await db.inter_college_competitions.find_one({
            "id": competition_id,
            "created_by": current_campus_admin["user_id"]
        })
        
        if not competition:
            raise HTTPException(status_code=404, detail="Competition not found or not authorized")
        
        # Get participant record
        participant = await db.campus_competition_participations.find_one({
            "competition_id": competition_id,
            "user_id": user_id
        })
        
        if not participant:
            raise HTTPException(status_code=404, detail="Participant not found in competition")
        
        # Apply moderation action
        update_data = {}
        if action == "warn":
            warnings = participant.get("warnings", [])
            warnings.append({
                "reason": reason,
                "issued_by": current_campus_admin["user_id"],
                "issued_at": datetime.now(timezone.utc)
            })
            update_data["warnings"] = warnings
            
        elif action == "disqualify":
            update_data["registration_status"] = "disqualified"
            update_data["disqualification_reason"] = reason
            update_data["disqualified_by"] = current_campus_admin["user_id"]
            update_data["disqualified_at"] = datetime.now(timezone.utc)
            
        elif action == "reinstate":
            update_data["registration_status"] = "active"
            update_data["$unset"] = {
                "disqualification_reason": "",
                "disqualified_by": "",
                "disqualified_at": ""
            }
        
        # Update participant record
        if "$unset" in update_data:
            await db.campus_competition_participations.update_one(
                {"competition_id": competition_id, "user_id": user_id},
                {"$set": {k: v for k, v in update_data.items() if k != "$unset"}, "$unset": update_data["$unset"]}
            )
        else:
            await db.campus_competition_participations.update_one(
                {"competition_id": competition_id, "user_id": user_id},
                {"$set": update_data}
            )
        
        # Update admin statistics
        await db.campus_admins.update_one(
            {"id": current_campus_admin["id"]},
            {
                "$inc": {"participants_managed": 1},
                "$set": {"last_activity": datetime.now(timezone.utc)}
            }
        )
        
        # Create audit log
        audit_log = await admin_workflow_manager.create_audit_log(
            admin_user_id=current_campus_admin["user_id"],
            action_type="moderate_competition_participant",
            action_description=f"Applied {action} to participant in {competition['title']}: {reason}",
            target_type="competition_participant",
            target_id=f"{competition_id}_{user_id}",
            affected_entities=[
                {"type": "competition", "id": competition_id, "name": competition["title"]},
                {"type": "user", "id": user_id, "name": "Participant"}
            ],
            severity="warning" if action == "disqualify" else "info",
            ip_address=request.client.host
        )
        await db.admin_audit_logs.insert_one(audit_log)
        
        return {
            "message": f"Participant {action}d successfully",
            "action": action,
            "competition_id": competition_id,
            "user_id": user_id,
            "reason": reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Moderate competition participant error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to moderate participant")

# ===== CAMPUS ADMIN COLLEGE EVENTS MANAGEMENT =====

@api_router.get("/campus-admin/college-events")
@limiter.limit("20/minute")
async def get_campus_admin_college_events(
    request: Request,
    status: Optional[str] = None,
    event_type: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    current_campus_admin: Dict[str, Any] = Depends(get_current_campus_admin)
):
    """Get college events in campus admin's institution"""
    try:
        db = await get_database()
        college_name = current_campus_admin["college_name"]
        
        # Build query filter - events in this college
        query_filter = {
            "$or": [
                {"college_name": college_name},  # Events created by this college
                {"visibility": "all_colleges"},  # Public events
                {"eligible_colleges": college_name}  # Events this college is invited to
            ]
        }
        
        if status:
            query_filter["status"] = status
        if event_type:
            query_filter["event_type"] = event_type
        
        # Get total count
        total_count = await db.college_events.count_documents(query_filter)
        
        # Get paginated events
        skip = (page - 1) * limit
        events_cursor = db.college_events.find(query_filter).sort("created_at", -1).skip(skip).limit(limit)
        events = await events_cursor.to_list(None)
        
        # Enrich with registration statistics
        enhanced_events = []
        for event in events:
            if "_id" in event:
                del event["_id"]
                
            # Get registration count
            registration_count = await db.event_registrations.count_documents({
                "event_id": event["id"]
            })
            
            # Get pending registrations count
            pending_count = await db.event_registrations.count_documents({
                "event_id": event["id"],
                "status": "pending"
            })
            
            # Get creator details
            creator = await get_user_by_id(event["created_by"])
            
            event_info = {
                **event,
                "current_registrations": registration_count,
                "pending_registrations": pending_count,
                "creator_name": creator.get("full_name", "Unknown") if creator else "Unknown",
                "creator_email": creator.get("email") if creator else None,
                "can_manage": event["college_name"] == college_name  # Can manage if created by this college
            }
            enhanced_events.append(event_info)
        
        return {
            "events": enhanced_events,
            "total": total_count,
            "page": page,
            "limit": limit,
            "college_name": college_name
        }
        
    except Exception as e:
        logger.error(f"Get campus admin college events error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get college events")

@api_router.get("/campus-admin/college-events/{event_id}/registrations")
@limiter.limit("20/minute")
async def get_campus_admin_event_registrations(
    request: Request,
    event_id: str,
    status: Optional[str] = None,
    registration_type: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    current_campus_admin: Dict[str, Any] = Depends(get_current_campus_admin)
):
    """Get registrations for a college event (campus admin view)"""
    try:
        db = await get_database()
        college_name = current_campus_admin["college_name"]
        
        # Verify event belongs to this campus admin's college
        event = await db.college_events.find_one({"id": event_id})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        if event["college_name"] != college_name:
            raise HTTPException(status_code=403, detail="Cannot access registrations for events from other colleges")
        
        # Build query filter
        query_filter = {"event_id": event_id}
        if status:
            query_filter["status"] = status
        if registration_type:
            query_filter["registration_type"] = registration_type
        
        # Get total count
        total_count = await db.event_registrations.count_documents(query_filter)
        
        # Get paginated registrations
        skip = (page - 1) * limit
        registrations_cursor = db.event_registrations.find(query_filter).sort("registration_date", -1).skip(skip).limit(limit)
        registrations = await registrations_cursor.to_list(None)
        
        # Enrich with user details
        enhanced_registrations = []
        for reg in registrations:
            if "_id" in reg:
                del reg["_id"]
            
            # Get user details
            user = await get_user_by_id(reg["user_id"])
            if user:
                reg["user_details"] = {
                    "full_name": user.get("full_name"),
                    "email": user.get("email"),
                    "university": user.get("university"),
                    "points": user.get("points", 0)
                }
            
            enhanced_registrations.append(reg)
        
        return {
            "registrations": enhanced_registrations,
            "total": total_count,
            "page": page,
            "limit": limit,
            "event_title": event["title"],
            "event_id": event_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get campus admin event registrations error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get registrations")

@api_router.post("/campus-admin/college-events/{event_id}/registrations/manage")
@limiter.limit("10/minute")
async def manage_campus_admin_event_registration(
    request: Request,
    event_id: str,
    action_data: Dict[str, Any],
    current_campus_admin: Dict[str, Any] = Depends(get_current_campus_admin)
):
    """Approve/reject college event registrations (campus admin level)"""
    try:
        db = await get_database()
        college_name = current_campus_admin["college_name"]
        
        # Verify event belongs to this campus admin's college
        event = await db.college_events.find_one({"id": event_id})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        if event["college_name"] != college_name:
            raise HTTPException(status_code=403, detail="Cannot manage registrations for events from other colleges")
        
        registration_id = action_data.get("registration_id")
        action = action_data.get("action")  # "approve" or "reject"
        reason = action_data.get("reason", "")
        
        if not registration_id or not action:
            raise HTTPException(status_code=400, detail="Registration ID and action are required")
        
        if action not in ["approve", "reject"]:
            raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")
        
        # Get registration
        registration = await db.event_registrations.find_one({"id": registration_id, "event_id": event_id})
        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found")
        
        # Update registration status
        new_status = "approved" if action == "approve" else "rejected"
        update_data = {
            "status": new_status,
            "reviewed_at": datetime.now(timezone.utc),
            "reviewed_by": current_campus_admin["user_id"],
            "reviewer_type": "campus_admin",
            "review_notes": reason
        }
        
        await db.event_registrations.update_one(
            {"id": registration_id},
            {"$set": update_data}
        )
        
        # Send notification to user
        try:
            user = await get_user_by_id(registration["user_id"])
            if user:
                notification_title = f"Registration {new_status.title()}"
                if action == "approve":
                    message = f"Your registration for '{event['title']}' has been approved by campus administration!"
                    priority = "high"
                else:
                    message = f"Your registration for '{event['title']}' was not approved. {reason if reason else 'Please contact the organizers for more information.'}"
                    priority = "medium"
                
                from websocket_service import notification_service
                await notification_service.create_and_notify_in_app_notification(
                    user_id=registration["user_id"],
                    title=notification_title,
                    message=message,
                    priority=priority,
                    action_url="/my-registrations",
                    metadata={
                        "type": "registration_update",
                        "event_id": event_id,
                        "registration_id": registration_id,
                        "action": action,
                        "reviewer": "campus_admin"
                    }
                )
        except Exception as notification_error:
            logger.error(f"Failed to send registration notification: {notification_error}")
        
        # Create audit log
        audit_log = AdminAuditLog(
            admin_id=current_campus_admin["user_id"],
            admin_type="campus_admin",
            admin_level="campus",
            college_name=college_name,
            action_type="registration_management",
            action_description=f"Campus admin {action}d registration for event '{event['title']}': {reason}",
            target_type="event_registration",
            target_id=registration_id,
            affected_entities=[
                {"type": "event", "id": event_id, "name": event["title"]},
                {"type": "user", "id": registration["user_id"], "name": registration.get("user_name", "Unknown")}
            ],
            severity="info",
            ip_address=request.client.host
        )
        await db.admin_audit_logs.insert_one(audit_log.dict())
        
        return {
            "message": f"Registration {action}d successfully",
            "registration_id": registration_id,
            "action": action,
            "event_title": event["title"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manage campus admin event registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to manage registration")

# ===== CLUB ADMIN DASHBOARD ENDPOINTS =====

@api_router.get("/club-admin/dashboard")
@limiter.limit("20/minute")
async def get_club_admin_dashboard(
    request: Request,
    current_club_admin: Dict[str, Any] = Depends(get_current_club_admin)
):
    """Get club admin dashboard with statistics and recent activities"""
    try:
        db = await get_database()
        
        # Get admin statistics
        competitions_count = await db.inter_college_competitions.count_documents({
            "created_by": current_club_admin["user_id"]
        })
        
        challenges_count = await db.prize_challenges.count_documents({
            "created_by": current_club_admin["user_id"]
        })
        
        # Get recent competitions and challenges
        recent_competitions = await db.inter_college_competitions.find({
            "created_by": current_club_admin["user_id"]
        }).sort("created_at", -1).limit(5).to_list(None)
        
        recent_challenges = await db.prize_challenges.find({
            "created_by": current_club_admin["user_id"]
        }).sort("created_at", -1).limit(5).to_list(None)
        
        # Calculate remaining monthly quota
        current_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        competitions_this_month = await db.inter_college_competitions.count_documents({
            "created_by": current_club_admin["user_id"],
            "created_at": {"$gte": current_month}
        })
        challenges_this_month = await db.prize_challenges.count_documents({
            "created_by": current_club_admin["user_id"],
            "created_at": {"$gte": current_month}
        })
        
        # Count total participants across all competitions/challenges
        total_participants = 0
        for comp in recent_competitions:
            total_participants += comp.get("current_participants", 0)
        for chal in recent_challenges:
            total_participants += chal.get("current_participants", 0)
        
        total_this_month = competitions_this_month + challenges_this_month
        max_per_month = current_club_admin.get("max_events_per_month", current_club_admin.get("max_competitions_per_month", 5))
        remaining_quota = max(0, max_per_month - total_this_month)
        
        return {
            "admin_details": {
                "admin_type": current_club_admin["admin_type"],
                "college_name": current_club_admin["college_name"],
                "club_name": current_club_admin.get("club_name"),
                "permissions": current_club_admin["permissions"],
                "appointed_at": current_club_admin["appointed_at"].isoformat(),
                "expires_at": current_club_admin.get("expires_at").isoformat() if current_club_admin.get("expires_at") else None
            },
            "statistics": {
                "total_competitions": competitions_count,
                "total_challenges": challenges_count,
                "total_events": competitions_count + challenges_count,
                "competitions_this_month": competitions_this_month,
                "challenges_this_month": challenges_this_month,
                "events_this_month": total_this_month,
                "remaining_monthly_quota": remaining_quota,
                "participants_managed": total_participants,
                "max_events_per_month": max_per_month
            },
            "recent_competitions": clean_mongo_doc(recent_competitions),
            "recent_challenges": clean_mongo_doc(recent_challenges),
            "capabilities": {
                "can_create_competitions": "create_competitions" in current_club_admin.get("permissions", []) or "create_events" in current_club_admin.get("permissions", []),
                "can_create_challenges": "create_challenges" in current_club_admin.get("permissions", []) or "create_events" in current_club_admin.get("permissions", []),
                "can_manage_participants": "manage_participants" in current_club_admin.get("permissions", []),
                "max_events_per_month": max_per_month
            }
        }
        
    except Exception as e:
        logger.error(f"Club admin dashboard error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get club admin dashboard")

@api_router.get("/club-admin/competitions")
@limiter.limit("20/minute")
async def get_club_admin_competitions(
    request: Request,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    current_club_admin: Dict[str, Any] = Depends(get_current_club_admin)
):
    """Get competitions created by this club admin"""
    try:
        db = await get_database()
        
        # Build query - only show competitions created by this club admin
        query = {"created_by": current_club_admin["user_id"]}
        
        if status:
            query["status"] = status
        
        # Get total count
        total_count = await db.inter_college_competitions.count_documents(query)
        
        # Get paginated competitions
        skip = (page - 1) * limit
        competitions = await db.inter_college_competitions.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(None)
        
        # Enhance each competition with participant counts
        for competition in competitions:
            participant_count = await db.inter_college_participants.count_documents({
                "competition_id": competition["id"]
            })
            competition["current_participants"] = participant_count
            
            # Count participating campuses
            campuses = await db.inter_college_participants.distinct("campus", {
                "competition_id": competition["id"]
            })
            competition["participating_campuses"] = len(campuses)
        
        return {
            "competitions": clean_mongo_doc(competitions),
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit
        }
        
    except Exception as e:
        logger.error(f"Get club admin competitions error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get competitions")

@api_router.get("/club-admin/challenges")
@limiter.limit("20/minute")
async def get_club_admin_challenges(
    request: Request,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    current_club_admin: Dict[str, Any] = Depends(get_current_club_admin)
):
    """Get challenges created by this club admin"""
    try:
        db = await get_database()
        
        # Build query - only show challenges created by this club admin
        query = {"created_by": current_club_admin["user_id"]}
        
        if status:
            query["status"] = status
        
        # Get total count
        total_count = await db.prize_challenges.count_documents(query)
        
        # Get paginated challenges
        skip = (page - 1) * limit
        challenges = await db.prize_challenges.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(None)
        
        # Enhance each challenge with participant counts
        for challenge in challenges:
            participant_count = await db.challenge_participants.count_documents({
                "challenge_id": challenge["id"]
            })
            challenge["current_participants"] = participant_count
        
        return {
            "challenges": clean_mongo_doc(challenges),
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit
        }
        
    except Exception as e:
        logger.error(f"Get club admin challenges error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get challenges")

@api_router.get("/club-admin/college-events")
@limiter.limit("20/minute")
async def get_club_admin_college_events(
    request: Request,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    current_club_admin: Dict[str, Any] = Depends(get_current_club_admin)
):
    """Get college events created by this club admin"""
    try:
        db = await get_database()
        
        # Build query - only show events created by this club admin
        query = {"created_by": current_club_admin["user_id"]}
        
        if status:
            query["status"] = status
        
        # Get total count
        total_count = await db.college_events.count_documents(query)
        
        # Get paginated events
        skip = (page - 1) * limit
        events = await db.college_events.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(None)
        
        # Enhance each event with registration counts
        for event in events:
            registration_count = await db.event_registrations.count_documents({
                "event_id": event["id"]
            })
            event["current_participants"] = registration_count
            event["registered_count"] = registration_count
        
        return {
            "events": clean_mongo_doc(events),
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit
        }
        
    except Exception as e:
        logger.error(f"Get club admin college events error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get college events")

# ===== CAMPUS ADMIN CLUB ADMIN MANAGEMENT ENDPOINTS =====

@api_router.get("/campus-admin/club-admin-requests")
@limiter.limit("20/minute")
async def get_club_admin_requests(
    request: Request,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    current_campus_admin: Dict[str, Any] = Depends(get_current_campus_admin)
):
    """Get club admin requests for campus admin's college"""
    try:
        db = await get_database()
        
        # Build query filter for requests in campus admin's college
        query_filter = {"college_name": current_campus_admin["college_name"]}
        if status:
            query_filter["status"] = status
        
        # Get total count
        total_count = await db.club_admin_requests.count_documents(query_filter)
        
        # Get paginated requests
        skip = (page - 1) * limit
        requests_cursor = db.club_admin_requests.find(query_filter).sort("submitted_at", -1).skip(skip).limit(limit)
        requests = await requests_cursor.to_list(None)
        
        # Enrich with user details
        for req in requests:
            user = await get_user_by_id(req["user_id"])
            if user:
                req["user_details"] = {
                    "full_name": user.get("full_name"),
                    "email": user.get("email"),
                    "avatar": user.get("avatar"),
                    "university": user.get("university")
                }
        
        return {
            "requests": clean_mongo_doc(requests),
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total_count,
                "total_pages": (total_count + limit - 1) // limit
            }
        }
        
    except Exception as e:
        logger.error(f"Get club admin requests error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get club admin requests")

@api_router.post("/campus-admin/club-admin-requests/{request_id}/approve")
@limiter.limit("10/minute")
async def approve_club_admin_request(
    request: Request,
    request_id: str,
    approval_data: Dict[str, Any],  # Contains permissions and limits
    current_campus_admin: Dict[str, Any] = Depends(get_current_campus_admin)
):
    """Approve club admin request and create club admin record"""
    try:
        db = await get_database()
        
        # Get the request
        club_request = await db.club_admin_requests.find_one({
            "id": request_id,
            "college_name": current_campus_admin["college_name"],
            "status": "pending"
        })
        
        if not club_request:
            raise HTTPException(status_code=404, detail="Request not found or already processed")
        
        # Update request status
        await db.club_admin_requests.update_one(
            {"id": request_id},
            {
                "$set": {
                    "status": "approved",
                    "reviewed_at": datetime.now(timezone.utc),
                    "review_notes": approval_data.get("review_notes", ""),
                    "approved_permissions": approval_data.get("permissions", ["create_events"]),
                    "max_events_per_month": approval_data.get("max_events_per_month", 3),
                    "expires_in_months": approval_data.get("expires_in_months", 6)
                }
            }
        )
        
        # Create club admin record
        club_admin_data = {
            "id": str(uuid.uuid4()),
            "user_id": club_request["user_id"],
            "admin_type": "club_admin",
            "college_name": club_request["college_name"],
            "club_name": club_request["club_name"],
            "appointed_by": current_campus_admin["user_id"],  # Campus admin who approved
            "appointed_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(days=approval_data.get("expires_in_months", 6) * 30),
            "status": "active",
            "permissions": approval_data.get("permissions", ["create_events"]),
            "max_events_per_month": approval_data.get("max_events_per_month", 3),
            "events_created": 0,
            "participants_managed": 0,
            "reputation_points_awarded": 0
        }
        
        await db.campus_admins.insert_one(club_admin_data)
        
        # Update user's admin level
        await db.users.update_one(
            {"id": club_request["user_id"]},
            {"$set": {"admin_level": "club_admin", "is_admin": True}}
        )
        
        # Update campus admin's stats
        await db.campus_admins.update_one(
            {"id": current_campus_admin["id"]},
            {
                "$inc": {"club_admins_managed": 1},
                "$set": {"last_activity": datetime.now(timezone.utc)}
            }
        )
        
        # Create audit log
        await create_audit_log(
            db=db,
            admin_user_id=current_campus_admin["user_id"],
            action_type="approve_club_admin_request",
            action_description=f"Approved club admin request for {club_request['club_name']}",
            target_type="club_admin_request",
            target_id=request_id,
            affected_entities=[
                {"type": "user", "id": club_request["user_id"], "name": club_request["full_name"]},
                {"type": "club", "id": club_request["club_name"], "name": club_request["club_name"]}
            ],
            severity="info",
            ip_address=request.client.host,
            admin_level="campus_admin",
            college_name=current_campus_admin["college_name"]
        )
        
        return {
            "message": "Club admin request approved successfully",
            "request_id": request_id,
            "club_admin_id": club_admin_data["id"],
            "approved_permissions": club_admin_data["permissions"],
            "expires_at": club_admin_data["expires_at"].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Approve club admin request error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to approve club admin request")

@api_router.post("/campus-admin/club-admin-requests/{request_id}/reject")
@limiter.limit("10/minute")
async def reject_club_admin_request(
    request: Request,
    request_id: str,
    rejection_data: Dict[str, str],  # Contains rejection_reason and review_notes
    current_campus_admin: Dict[str, Any] = Depends(get_current_campus_admin)
):
    """Reject club admin request with reason"""
    try:
        db = await get_database()
        
        # Get the request
        club_request = await db.club_admin_requests.find_one({
            "id": request_id,
            "college_name": current_campus_admin["college_name"],
            "status": "pending"
        })
        
        if not club_request:
            raise HTTPException(status_code=404, detail="Request not found or already processed")
        
        # Update request status
        await db.club_admin_requests.update_one(
            {"id": request_id},
            {
                "$set": {
                    "status": "rejected",
                    "reviewed_at": datetime.now(timezone.utc),
                    "rejection_reason": rejection_data.get("rejection_reason", ""),
                    "review_notes": rejection_data.get("review_notes", "")
                }
            }
        )
        
        # Create audit log
        await create_audit_log(
            db=db,
            admin_user_id=current_campus_admin["user_id"],
            action_type="reject_club_admin_request",
            action_description=f"Rejected club admin request for {club_request['club_name']}: {rejection_data.get('rejection_reason', '')}",
            target_type="club_admin_request",
            target_id=request_id,
            affected_entities=[
                {"type": "user", "id": club_request["user_id"], "name": club_request["full_name"]},
                {"type": "club", "id": club_request["club_name"], "name": club_request["club_name"]}
            ],
            severity="info",
            ip_address=request.client.host,
            admin_level="campus_admin",
            college_name=current_campus_admin["college_name"]
        )
        
        return {
            "message": "Club admin request rejected successfully",
            "request_id": request_id,
            "rejection_reason": rejection_data.get("rejection_reason", ""),
            "rejected_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reject club admin request error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reject club admin request")

@api_router.get("/campus-admin/my-club-admins")
@limiter.limit("20/minute")
async def get_my_club_admins(
    request: Request,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    current_campus_admin: Dict[str, Any] = Depends(get_current_campus_admin)
):
    """List all club admins managed by this campus admin"""
    try:
        db = await get_database()
        
        # Build query filter for club admins appointed by this campus admin
        query_filter = {
            "appointed_by": current_campus_admin["user_id"],
            "admin_type": "club_admin"
        }
        if status:
            query_filter["status"] = status
        
        # Get total count
        total_count = await db.campus_admins.count_documents(query_filter)
        
        # Get paginated club admins
        skip = (page - 1) * limit
        club_admins_cursor = db.campus_admins.find(query_filter).sort("appointed_at", -1).skip(skip).limit(limit)
        club_admins = await club_admins_cursor.to_list(None)
        
        # Enrich with user details and statistics
        for admin in club_admins:
            user = await get_user_by_id(admin["user_id"])
            if user:
                admin["user_details"] = {
                    "full_name": user.get("full_name"),
                    "email": user.get("email"),
                    "avatar": user.get("avatar"),
                    "last_login": user.get("last_login")
                }
            
            # Get recent activity statistics
            current_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            admin["monthly_stats"] = {
                "events_this_month": admin.get("events_created", 0),  # You might want to count from events collection
                "remaining_events": max(0, admin.get("max_events_per_month", 3) - admin.get("events_created", 0))
            }
        
        return {
            "club_admins": clean_mongo_doc(club_admins),
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total_count,
                "total_pages": (total_count + limit - 1) // limit
            },
            "summary": {
                "total_managed": total_count,
                "active": await db.campus_admins.count_documents({**query_filter, "status": "active"}),
                "suspended": await db.campus_admins.count_documents({**query_filter, "status": "suspended"})
            }
        }
        
    except Exception as e:
        logger.error(f"Get my club admins error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get club admins")

@api_router.put("/campus-admin/club-admins/{club_admin_id}/update-privileges")
@limiter.limit("10/minute")
async def update_club_admin_privileges(
    request: Request,
    club_admin_id: str,
    privilege_data: Dict[str, Any],  # Contains permissions and limits
    current_campus_admin: Dict[str, Any] = Depends(get_current_campus_admin)
):
    """Update club admin permissions and limits"""
    try:
        db = await get_database()
        
        # Verify the club admin is managed by this campus admin
        club_admin = await db.campus_admins.find_one({
            "id": club_admin_id,
            "appointed_by": current_campus_admin["user_id"],
            "admin_type": "club_admin"
        })
        
        if not club_admin:
            raise HTTPException(status_code=404, detail="Club admin not found or not authorized to manage")
        
        # Prepare update data
        update_data = {}
        if "permissions" in privilege_data:
            update_data["permissions"] = privilege_data["permissions"]
        if "max_events_per_month" in privilege_data:
            update_data["max_events_per_month"] = privilege_data["max_events_per_month"]
        if "expires_at" in privilege_data:
            # Allow extending expiry date
            update_data["expires_at"] = datetime.fromisoformat(privilege_data["expires_at"].replace("Z", "+00:00"))
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid privilege data provided")
        
        update_data["last_modified"] = datetime.now(timezone.utc)
        update_data["last_modified_by"] = current_campus_admin["user_id"]
        
        # Update club admin record
        await db.campus_admins.update_one(
            {"id": club_admin_id},
            {"$set": update_data}
        )
        
        # Create audit log
        await create_audit_log(
            db=db,
            admin_user_id=current_campus_admin["user_id"],
            action_type="update_club_admin_privileges",
            action_description=f"Updated privileges for club admin {club_admin['club_name']}",
            target_type="club_admin",
            target_id=club_admin_id,
            affected_entities=[
                {"type": "user", "id": club_admin["user_id"], "name": club_admin["club_name"]},
                {"type": "club", "id": club_admin["club_name"], "name": club_admin["club_name"]}
            ],
            before_state={"permissions": club_admin.get("permissions"), "max_events_per_month": club_admin.get("max_events_per_month")},
            after_state=update_data,
            severity="info",
            ip_address=request.client.host,
            admin_level="campus_admin",
            college_name=current_campus_admin["college_name"]
        )
        
        return {
            "message": "Club admin privileges updated successfully",
            "club_admin_id": club_admin_id,
            "updated_privileges": update_data,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update club admin privileges error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update club admin privileges")

@api_router.put("/campus-admin/club-admins/{club_admin_id}/suspend")
@limiter.limit("10/minute")
async def suspend_club_admin(
    request: Request,
    club_admin_id: str,
    suspension_data: Dict[str, Any],  # Contains reason and duration
    current_campus_admin: Dict[str, Any] = Depends(get_current_campus_admin)
):
    """Suspend club admin (campus-level suspension)"""
    try:
        db = await get_database()
        
        # Verify the club admin is managed by this campus admin
        club_admin = await db.campus_admins.find_one({
            "id": club_admin_id,
            "appointed_by": current_campus_admin["user_id"],
            "admin_type": "club_admin",
            "status": "active"
        })
        
        if not club_admin:
            raise HTTPException(status_code=404, detail="Club admin not found or not authorized to manage")
        
        # Calculate suspension end date
        suspension_days = suspension_data.get("suspension_days", 30)  # Default 30 days
        suspension_end = datetime.now(timezone.utc) + timedelta(days=suspension_days)
        
        # Update club admin record
        update_data = {
            "status": "suspended",
            "suspension_reason": suspension_data.get("reason", ""),
            "suspended_at": datetime.now(timezone.utc),
            "suspended_by": current_campus_admin["user_id"],
            "suspension_end": suspension_end,
            "last_modified": datetime.now(timezone.utc),
            "last_modified_by": current_campus_admin["user_id"]
        }
        
        await db.campus_admins.update_one(
            {"id": club_admin_id},
            {"$set": update_data}
        )
        
        # Update user's admin status (temporarily remove admin privileges)
        await db.users.update_one(
            {"id": club_admin["user_id"]},
            {"$set": {"admin_level": "user", "is_admin": False, "suspension_status": "suspended"}}
        )
        
        # Create audit log
        await create_audit_log(
            db=db,
            admin_user_id=current_campus_admin["user_id"],
            action_type="suspend_club_admin",
            action_description=f"Suspended club admin {club_admin['club_name']} for {suspension_days} days: {suspension_data.get('reason', '')}",
            target_type="club_admin",
            target_id=club_admin_id,
            affected_entities=[
                {"type": "user", "id": club_admin["user_id"], "name": club_admin["club_name"]},
                {"type": "club", "id": club_admin["club_name"], "name": club_admin["club_name"]}
            ],
            severity="warning",
            ip_address=request.client.host,
            admin_level="campus_admin",
            college_name=current_campus_admin["college_name"]
        )
        
        return {
            "message": "Club admin suspended successfully",
            "club_admin_id": club_admin_id,
            "suspension_reason": suspension_data.get("reason", ""),
            "suspension_end": suspension_end.isoformat(),
            "suspended_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Suspend club admin error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to suspend club admin")

@api_router.post("/campus-admin/invite-club-admin")
@limiter.limit("10/minute")
async def invite_club_admin(
    request: Request,
    invitation_data: Dict[str, Any],  # Contains club details and user info
    current_campus_admin: Dict[str, Any] = Depends(get_current_campus_admin)
):
    """Invite/create club admin request"""
    try:
        db = await get_database()
        
        # Validate required fields
        required_fields = ["user_id", "club_name", "club_type"]
        for field in required_fields:
            if field not in invitation_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Check if user exists
        user = await get_user_by_id(invitation_data["user_id"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user is already a club admin
        existing_admin = await db.campus_admins.find_one({
            "user_id": invitation_data["user_id"],
            "admin_type": "club_admin",
            "status": "active"
        })
        if existing_admin:
            raise HTTPException(status_code=400, detail="User is already a club admin")
        
        # Check for existing pending request
        existing_request = await db.club_admin_requests.find_one({
            "user_id": invitation_data["user_id"],
            "college_name": current_campus_admin["college_name"],
            "status": "pending"
        })
        if existing_request:
            raise HTTPException(status_code=400, detail="Pending request already exists for this user")
        
        # Create club admin request
        club_request_data = {
            "id": str(uuid.uuid4()),
            "user_id": invitation_data["user_id"],
            "campus_admin_id": current_campus_admin["user_id"],
            "college_name": current_campus_admin["college_name"],
            "club_name": invitation_data["club_name"],
            "club_type": invitation_data.get("club_type", "student_organization"),
            "full_name": user.get("full_name", ""),
            "email": user.get("email", ""),
            "phone_number": user.get("phone", ""),
            "motivation": invitation_data.get("motivation", "Invited by campus admin"),
            "previous_experience": invitation_data.get("previous_experience", ""),
            "status": "pending",
            "submitted_at": datetime.now(timezone.utc),
            "approved_permissions": invitation_data.get("permissions", ["create_events"]),
            "max_events_per_month": invitation_data.get("max_events_per_month", 3),
            "expires_in_months": invitation_data.get("expires_in_months", 6)
        }
        
        await db.club_admin_requests.insert_one(club_request_data)
        
        # Create audit log
        await create_audit_log(
            db=db,
            admin_user_id=current_campus_admin["user_id"],
            action_type="invite_club_admin",
            action_description=f"Invited user to be club admin for {invitation_data['club_name']}",
            target_type="club_admin_invitation",
            target_id=club_request_data["id"],
            affected_entities=[
                {"type": "user", "id": invitation_data["user_id"], "name": user.get("full_name", "")},
                {"type": "club", "id": invitation_data["club_name"], "name": invitation_data["club_name"]}
            ],
            severity="info",
            ip_address=request.client.host,
            admin_level="campus_admin",
            college_name=current_campus_admin["college_name"]
        )
        
        return {
            "message": "Club admin invitation created successfully",
            "request_id": club_request_data["id"],
            "club_name": invitation_data["club_name"],
            "invited_user": {
                "user_id": invitation_data["user_id"],
                "full_name": user.get("full_name", ""),
                "email": user.get("email", "")
            },
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Invite club admin error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create club admin invitation")

# ===== VIRAL IMPACT FEATURES =====

# 1. PUBLIC CAMPUS BATTLE DASHBOARD
@api_router.get("/public/campus-battle")
async def get_public_campus_battle():
    """Public campus battle dashboard - no authentication required"""
    try:
        # Get all users with their campus data
        users_cursor = db.users.find(
            {"university": {"$ne": None}, "is_active": True},
            {"university": 1, "total_earnings": 1, "net_savings": 1, "current_streak": 1, "last_activity_date": 1, "created_at": 1}
        )
        users = await users_cursor.to_list(None)
        
        # Get transactions for active spending calculation
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        
        # Campus aggregation
        campus_stats = {}
        
        for user in users:
            campus = user.get('university', 'Unknown')
            if campus not in campus_stats:
                campus_stats[campus] = {
                    'total_savings': 0,
                    'total_users': 0,
                    'active_users_7d': 0,
                    'total_earnings': 0,
                    'recent_activity': 0
                }
            
            campus_stats[campus]['total_savings'] += user.get('net_savings', 0)
            campus_stats[campus]['total_earnings'] += user.get('total_earnings', 0)
            campus_stats[campus]['total_users'] += 1
            
            # Check if active in last 7 days
            last_activity = user.get('last_activity_date')
            if last_activity:
                # Ensure timezone compatibility
                if last_activity.tzinfo is None:
                    last_activity = last_activity.replace(tzinfo=timezone.utc)
                if last_activity > seven_days_ago:
                    campus_stats[campus]['active_users_7d'] += 1
                    campus_stats[campus]['recent_activity'] += 1
        
        # Calculate averages and rankings
        battle_data = []
        for campus, stats in campus_stats.items():
            if stats['total_users'] > 0:  # Only include campuses with users
                avg_savings = stats['total_savings'] / stats['total_users'] if stats['total_users'] > 0 else 0
                
                battle_data.append({
                    'campus': campus,
                    'total_savings': round(stats['total_savings'], 2),
                    'average_monthly_savings': round(avg_savings, 2),
                    'active_users': stats['active_users_7d'],
                    'total_users': stats['total_users'],
                    'recent_activity_score': stats['recent_activity'],
                    'total_earnings': round(stats['total_earnings'], 2)
                })
        
        # Sort by total savings for ranking
        battle_data.sort(key=lambda x: x['total_savings'], reverse=True)
        
        # Add rankings
        for i, campus_data in enumerate(battle_data):
            campus_data['rank'] = i + 1
        
        # Find trending campus (most recent activity)
        trending_campus = max(battle_data, key=lambda x: x['recent_activity_score']) if battle_data else None
        
        return {
            "success": True,
            "campus_battle": battle_data[:20],  # Top 20 campuses
            "trending_campus": trending_campus['campus'] if trending_campus else None,
            "total_campuses": len(battle_data),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "auto_refresh_seconds": 30
        }
        
    except Exception as e:
        logger.error(f"Campus battle dashboard error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving campus battle data")

# 2. ANONYMOUS SPENDING INSIGHTS
@api_router.get("/insights/campus-spending/{campus}")
async def get_campus_spending_insights(campus: str, current_user: Dict[str, Any] = Depends(get_current_super_admin)):
    """Get anonymous spending insights for a specific campus"""
    try:
        # Get all users from this campus
        campus_users = await db.users.find(
            {"university": campus, "is_active": True}
        ).to_list(None)
        
        if not campus_users:
            raise HTTPException(status_code=404, detail="Campus not found or no active users")
        
        user_ids = [user["id"] for user in campus_users]
        
        # Get last 30 days of expense transactions
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        
        transactions_cursor = db.transactions.find({
            "user_id": {"$in": user_ids},
            "type": "expense",
            "date": {"$gte": thirty_days_ago}
        })
        transactions = await transactions_cursor.to_list(None)
        
        # Analyze spending by category
        category_spending = {}
        total_spending = 0
        
        for transaction in transactions:
            category = transaction['category']
            amount = transaction['amount']
            
            category_spending[category] = category_spending.get(category, 0) + amount
            total_spending += amount
        
        # Calculate percentages and insights
        insights = []
        focus_categories = ['Food', 'Entertainment', 'Shopping', 'Transportation', 'Books']
        
        for category in focus_categories:
            if category in category_spending:
                percentage = (category_spending[category] / total_spending * 100) if total_spending > 0 else 0
                amount = category_spending[category]
                
                insights.append({
                    "category": category,
                    "amount": round(amount, 2),
                    "percentage": round(percentage, 1),
                    "insight_text": f"Your campus spends {percentage:.1f}% of its budget on {category.lower()}",
                    "emoji": {"Food": "🍕", "Entertainment": "🎬", "Shopping": "🛍️", 
                             "Transportation": "🚗", "Books": "📚"}.get(category, "💰")
                })
        
        # Sort by percentage
        insights.sort(key=lambda x: x['percentage'], reverse=True)
        
        # Generate shareable insight
        if insights:
            top_category = insights[0]
            shareable_text = f"Our {campus} campus spends {top_category['percentage']}% of its budget on {top_category['category'].lower()} {top_category['emoji']} #EarnAura #StudentFinance"
        else:
            shareable_text = f"{campus} students are building great financial habits! #EarnAura"
        
        return {
            "success": True,
            "campus": campus,
            "total_users": len(campus_users),
            "total_spending": round(total_spending, 2),
            "insights": insights,
            "shareable_text": shareable_text,
            "period": "Last 30 days"
        }
        
    except Exception as e:
        logger.error(f"Campus spending insights error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving spending insights")

# 3. VIRAL MILESTONE ANNOUNCEMENTS
@api_router.get("/milestones/check")
async def check_viral_milestones():
    """Check for viral milestones (app-wide and campus-specific)"""
    try:
        # Get all users for app-wide stats
        users_cursor = db.users.find({"is_active": True})
        users = await users_cursor.to_list(None)
        
        # Calculate app-wide totals
        total_app_savings = sum(user.get('net_savings', 0) for user in users)
        total_app_earnings = sum(user.get('total_earnings', 0) for user in users)
        
        milestones = [100000, 500000, 1000000, 5000000, 10000000, 100000000]  # ₹1L to ₹10 crore
        
        # Check app-wide milestones
        app_milestones = []
        for milestone in milestones:
            if total_app_savings >= milestone:
                milestone_text = f"All EarnAura students have saved ₹{milestone/100000:.0f} lakh total!"
                if milestone >= 10000000:
                    milestone_text = f"All EarnAura students have saved ₹{milestone/10000000:.0f} crore total!"
                
                app_milestones.append({
                    "type": "app_wide",
                    "milestone": milestone,
                    "current_value": total_app_savings,
                    "achievement_text": milestone_text,
                    "celebration_level": "major" if milestone >= 1000000 else "minor"
                })
        
        # Check campus-specific milestones
        campus_milestones = []
        campus_totals = {}
        
        for user in users:
            campus = user.get('university', 'Unknown')
            if campus != 'Unknown':
                if campus not in campus_totals:
                    campus_totals[campus] = {'savings': 0, 'users': 0}
                campus_totals[campus]['savings'] += user.get('net_savings', 0)
                campus_totals[campus]['users'] += 1
        
        for campus, data in campus_totals.items():
            for milestone in milestones:
                if data['savings'] >= milestone and data['users'] >= 5:  # Minimum 5 users for campus milestone
                    milestone_text = f"{campus} crossed ₹{milestone/100000:.0f}L in total student savings!"
                    if milestone >= 10000000:
                        milestone_text = f"{campus} crossed ₹{milestone/10000000:.0f} crore in total student savings!"
                    
                    campus_milestones.append({
                        "type": "campus_specific",
                        "campus": campus,
                        "milestone": milestone,
                        "current_value": data['savings'],
                        "achievement_text": milestone_text,
                        "celebration_level": "major" if milestone >= 1000000 else "minor"
                    })
        
        return {
            "success": True,
            "app_wide_milestones": app_milestones[-3:] if app_milestones else [],  # Latest 3
            "campus_milestones": campus_milestones[-5:] if campus_milestones else [],  # Latest 5
            "total_app_savings": round(total_app_savings, 2),
            "total_app_users": len(users),
            "celebration_ready": len(app_milestones) > 0 or len(campus_milestones) > 0
        }
        
    except Exception as e:
        logger.error(f"Viral milestones check error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error checking milestones")

# 4. FRIEND COMPARISONS (Anonymous)
@api_router.get("/insights/friend-comparison")
async def get_friend_comparison_insights(current_user = Depends(get_current_user_dict)):
    """Get anonymous friend spending comparisons"""
    try:
        user_id = current_user["id"]
        
        # Get user's friends from friendships collection
        db = await get_database()
        friendships = await db.friendships.find({
            "$or": [
                {"user1_id": user_id, "status": "active"},
                {"user2_id": user_id, "status": "active"}
            ]
        }).to_list(None)
        
        if not friendships:
            return {
                "success": True,
                "has_friends": False,
                "friend_count": 0,
                "message": "Add friends to see spending comparisons!",
                "comparisons": []
            }
        
        # Extract friend IDs
        friend_ids = []
        for friendship in friendships:
            friend_id = friendship["user2_id"] if friendship["user1_id"] == user_id else friendship["user1_id"]
            friend_ids.append(friend_id)
        friend_ids.append(user_id)  # Include current user
        
        # Get last 30 days transactions for user and friends
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        
        transactions_cursor = db.transactions.find({
            "user_id": {"$in": friend_ids},
            "type": "expense",
            "date": {"$gte": thirty_days_ago}
        })
        transactions = await transactions_cursor.to_list(None)
        
        # Calculate spending by user
        user_spending = {}
        for friend_id in friend_ids:
            user_spending[friend_id] = {
                'total': 0,
                'Food': 0,
                'Entertainment': 0,
                'Shopping': 0,
                'categories': {}
            }
        
        for transaction in transactions:
            user_tx_id = transaction['user_id']
            category = transaction['category']
            amount = transaction['amount']
            
            user_spending[user_tx_id]['total'] += amount
            user_spending[user_tx_id]['categories'][category] = user_spending[user_tx_id]['categories'].get(category, 0) + amount
            
            if category in ['Food', 'Entertainment', 'Shopping']:
                user_spending[user_tx_id][category] += amount
        
        # Calculate comparisons
        current_user_spending = user_spending[user_id]
        friend_spending_values = [user_spending[fid] for fid in friend_ids if fid != user_id]
        
        if not friend_spending_values:
            return {
                "success": True,
                "has_friends": True,
                "message": "Your friends haven't recorded any expenses yet!",
                "comparisons": []
            }
        
        # Calculate friend averages
        friend_totals = {
            'total': sum(fs['total'] for fs in friend_spending_values) / len(friend_spending_values),
            'Food': sum(fs['Food'] for fs in friend_spending_values) / len(friend_spending_values),
            'Entertainment': sum(fs['Entertainment'] for fs in friend_spending_values) / len(friend_spending_values),
            'Shopping': sum(fs['Shopping'] for fs in friend_spending_values) / len(friend_spending_values)
        }
        
        # Generate comparisons
        comparisons = []
        categories_to_compare = ['total', 'Food', 'Entertainment', 'Shopping']
        
        for category in categories_to_compare:
            user_amount = current_user_spending.get(category, 0)
            friend_avg = friend_totals[category]
            
            if friend_avg > 0:
                percentage_diff = ((user_amount - friend_avg) / friend_avg) * 100
                
                if abs(percentage_diff) >= 10:  # Only show significant differences
                    if percentage_diff > 0:
                        comparison_text = f"You spend {abs(percentage_diff):.0f}% more on {category.lower()} than your friends"
                        trend = "higher"
                    else:
                        comparison_text = f"You spend {abs(percentage_diff):.0f}% less on {category.lower()} than your friends"
                        trend = "lower"
                    
                    comparisons.append({
                        "category": category,
                        "user_amount": round(user_amount, 2),
                        "friend_average": round(friend_avg, 2),
                        "percentage_difference": round(percentage_diff, 1),
                        "comparison_text": comparison_text,
                        "trend": trend,
                        "emoji": {"total": "💰", "Food": "🍕", "Entertainment": "🎬", "Shopping": "🛍️"}.get(category, "💸")
                    })
        
        return {
            "success": True,
            "has_friends": True,
            "friend_count": len(friend_ids) - 1,
            "comparisons": comparisons,
            "period": "Last 30 days"
        }
        
    except Exception as e:
        logger.error(f"Friend comparison insights error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving friend comparisons")

# 5. MEDIA-READY DATA STORIES
@api_router.get("/public/impact-stats")
async def get_media_ready_impact_stats():
    """Generate media-ready data stories for press/sharing"""
    try:
        # Get all users and transactions for comprehensive stats
        db = await get_database()
        users_cursor = db.users.find({"is_active": True})
        users = await users_cursor.to_list(None)
        
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        transactions_cursor = db.transactions.find({
            "date": {"$gte": thirty_days_ago}
        })
        transactions = await transactions_cursor.to_list(None)
        
        # Calculate comprehensive statistics
        total_users = len(users)
        total_savings = sum(user.get('net_savings', 0) for user in users)
        total_earnings = sum(user.get('total_earnings', 0) for user in users)
        
        # Monthly activity
        monthly_transactions = len([t for t in transactions if t['date'] > thirty_days_ago])
        monthly_volume = sum(t['amount'] for t in transactions if t['date'] > thirty_days_ago)
        
        # Campus analysis
        campus_spending = {}
        for user in users:
            campus = user.get('university', 'Unknown')
            if campus != 'Unknown':
                user_transactions = [t for t in transactions if t['user_id'] == user['id'] and t['type'] == 'expense']
                campus_total = sum(t['amount'] for t in user_transactions)
                
                if campus not in campus_spending:
                    campus_spending[campus] = {'total': 0, 'users': 0}
                campus_spending[campus]['total'] += campus_total
                campus_spending[campus]['users'] += 1
        
        # Calculate average spending per campus
        campus_averages = {}
        for campus, data in campus_spending.items():
            if data['users'] > 0:
                campus_averages[campus] = data['total'] / data['users']
        
        # Find top spending cities
        top_spending_campus = max(campus_averages.items(), key=lambda x: x[1]) if campus_averages else None
        
        # Generate press-worthy stories
        stories = [
            {
                "headline": f"Students across India saved ₹{total_savings/100000:.1f} lakh through financial tracking",
                "stat": f"₹{total_savings/100000:.1f}L",
                "description": f"Over {total_users} students have collectively saved ₹{total_savings/100000:.1f} lakh using smart financial tracking tools",
                "category": "savings_milestone",
                "shareable": True
            },
            {
                "headline": f"Indian students earned ₹{total_earnings/100000:.1f} lakh through side hustles last month",
                "stat": f"₹{total_earnings/100000:.1f}L",
                "description": f"Student entrepreneurs generated ₹{total_earnings/100000:.1f} lakh in additional income through verified side hustles",
                "category": "earnings_report", 
                "shareable": True
            }
        ]
        
        if top_spending_campus:
            campus_name, avg_spending = top_spending_campus
            stories.append({
                "headline": f"{campus_name} students lead in financial activity with ₹{avg_spending:.0f} average monthly transactions",
                "stat": f"₹{avg_spending:.0f}",
                "description": f"{campus_name} shows highest student financial engagement with ₹{avg_spending:.0f} average monthly activity",
                "category": "campus_comparison",
                "shareable": True
            })
        
        # Add growth statistics
        stories.append({
            "headline": f"{monthly_transactions} financial transactions worth ₹{monthly_volume/100000:.1f}L recorded this month",
            "stat": f"{monthly_transactions} transactions",
            "description": f"Students are actively managing finances with {monthly_transactions} transactions totaling ₹{monthly_volume/100000:.1f} lakh this month",
            "category": "activity_report",
            "shareable": True
        })
        
        return {
            "success": True,
            "impact_stories": stories,
            "summary_stats": {
                "total_users": total_users,
                "total_savings": round(total_savings, 2),
                "total_earnings": round(total_earnings, 2),
                "monthly_transactions": monthly_transactions,
                "monthly_volume": round(monthly_volume, 2),
                "active_campuses": len(campus_spending)
            },
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "refresh_schedule": "weekly"
        }
        
    except Exception as e:
        logger.error(f"Impact stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving impact statistics")

# ===== ADDITIONAL VIRAL FEATURE ENDPOINTS =====

@api_router.get("/campus/battle-arena")
async def get_campus_battle_arena(current_user: Dict[str, Any] = Depends(get_current_user_dict)):
    """Get campus battle arena data"""
    try:
        battles = await db.campus_battle_arena.find({"status": "active"}).to_list(None)
        
        # Clean MongoDB ObjectIds
        for battle in battles:
            battle["_id"] = str(battle["_id"])
        
        return {
            "success": True,
            "battles": battles,
            "total_active_battles": len(battles)
        }
        
    except Exception as e:
        logger.error(f"Campus battle arena error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get battle arena data")

@api_router.get("/insights/spending/{campus}")
async def get_campus_spending_insights(campus: str, current_user: Dict[str, Any] = Depends(get_current_super_admin)):
    """Get spending insights for a specific campus"""
    try:
        # Get campus spending insights
        insight = await db.campus_spending_insights.find_one({"campus": campus})
        
        if not insight:
            # Generate basic insight if not found
            insight = {
                "campus": campus,
                "insights": [
                    {
                        "category": "Food",
                        "percentage": 32.0,
                        "amount": 8500,
                        "emoji": "🍕",
                        "trend": "stable",
                        "insight_text": f"{campus} students spend 32% of their budget on food"
                    }
                ],
                "total_users": 25,
                "total_spending": 26500,
                "period": "Last 30 days",
                "shareable_text": f"{campus} students are building great financial habits! #EarnNest",
                "updated_at": datetime.now(timezone.utc)
            }
        else:
            insight["_id"] = str(insight["_id"])
        
        return {
            "success": True,
            **insight
        }
        
    except Exception as e:
        logger.error(f"Campus spending insights error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get spending insights")

@api_router.get("/viral-milestones/live")
async def get_live_viral_milestones():
    """Get live viral milestones (public endpoint)"""
    try:
        # Get recent viral milestones
        milestones = await db.viral_milestones.find().sort("created_at", -1).limit(10).to_list(10)
        
        # Clean MongoDB ObjectIds
        for milestone in milestones:
            milestone["_id"] = str(milestone["_id"])
            
        # Separate app-wide and campus milestones
        app_milestones = [m for m in milestones if m["type"] == "app_wide"]
        campus_milestones = [m for m in milestones if m["type"] == "campus"]
        
        return {
            "success": True,
            "app_wide_milestones": app_milestones,
            "campus_milestones": campus_milestones,
            "celebration_ready": len(milestones) > 0,
            "total_milestones": len(milestones)
        }
        
    except Exception as e:
        logger.error(f"Live viral milestones error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get viral milestones")

# ===== REAL-TIME WEBSOCKET ENDPOINTS =====
# WebSocket endpoints must use /api prefix for Kubernetes ingress routing

@app.websocket("/api/ws/test")
async def test_websocket_endpoint(websocket: WebSocket):
    """Simple WebSocket test endpoint"""
    await websocket.accept()
    await websocket.send_text(json.dumps({
        "type": "connection_established",
        "message": "Test WebSocket connection successful!",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }))
    
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(json.dumps({
                "type": "echo",
                "message": f"Echo: {data}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }))
    except WebSocketDisconnect:
        logger.info("Test WebSocket disconnected")

@app.websocket("/api/ws/notifications/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time notifications with proper cleanup"""
    try:
        # Verify user authentication via query params or headers BEFORE accepting
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=1008, reason="Authentication required")
            return
        
        # Verify JWT token
        try:
            import jwt
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            authenticated_user_id = payload.get("user_id")
            token_type = payload.get("type")
            
            if not authenticated_user_id or token_type != "access":
                await websocket.close(code=1008, reason="Invalid token type")
                return
            
            if authenticated_user_id != user_id:
                await websocket.close(code=1008, reason="User ID mismatch")
                return
                
        except jwt.ExpiredSignatureError:
            logger.error("WebSocket auth error: Token expired")
            await websocket.close(code=1008, reason="Token expired")
            return
        except jwt.InvalidTokenError as e:
            logger.error(f"WebSocket auth error: Invalid token - {str(e)}")
            await websocket.close(code=1008, reason="Invalid token")
            return
        except Exception as e:
            logger.error(f"WebSocket auth error: {str(e)}")
            await websocket.close(code=1008, reason=f"Authentication failed")
            return
        
        # Connect user via connection manager (handles accept and tracking)
        await connection_manager.connect_user(websocket, user_id)
        logger.info(f"WebSocket connection established for user {user_id}")
        
        try:
            while True:
                # Keep connection alive and handle incoming messages
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Update timestamp on activity
                await connection_manager.update_connection_timestamp(websocket)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await connection_manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }, websocket)
                elif message.get("type") == "mark_notification_read":
                    # Handle marking notifications as read
                    notification_id = message.get("notification_id")
                    if notification_id:
                        db = await get_database()
                        await db.in_app_notifications.update_one(
                            {"id": notification_id, "user_id": user_id},
                            {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc)}}
                        )
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user_id}")
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {str(e)}")
        finally:
            # Always clean up connection properly
            await connection_manager.disconnect_user(websocket, user_id)
            
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
        try:
            await websocket.close(code=4500, reason="Internal server error")
        except:
            pass

@app.websocket("/api/ws/admin/{user_id}")
async def admin_websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for admin real-time notifications"""
    try:
        # Verify admin authentication BEFORE accepting
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=1008, reason="Authentication required")
            return
        
        try:
            import jwt
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            authenticated_user_id = payload.get("user_id")
            token_type = payload.get("type")
            
            if not authenticated_user_id or token_type != "access":
                await websocket.close(code=1008, reason="Invalid token type")
                return
            
            if authenticated_user_id != user_id:
                await websocket.close(code=1008, reason="User ID mismatch")
                return
                
        except jwt.ExpiredSignatureError:
            logger.error("Admin WebSocket auth error: Token expired")
            await websocket.close(code=1008, reason="Token expired")
            return
        except jwt.InvalidTokenError as e:
            logger.error(f"Admin WebSocket auth error: Invalid token - {str(e)}")
            await websocket.close(code=1008, reason="Invalid token")
            return
        except Exception as e:
            logger.error(f"Admin WebSocket auth error: {str(e)}")
            await websocket.close(code=1008, reason="Authentication failed")
            return
        
        # Check if user is admin
        db = await get_database()
        user_doc = await db.users.find_one({"id": user_id})
        
        if not user_doc:
            await websocket.close(code=1008, reason="User not found")
            return
        
        # Check admin privileges
        admin_type = "user"
        
        # Check if system admin
        if user_doc.get("is_admin", False):
            admin_type = "system_admin"
        else:
            # Check if campus admin
            campus_admin = await db.campus_admin_requests.find_one({
                "user_id": user_id,
                "status": "approved"
            })
            if campus_admin:
                admin_type = "campus_admin"
        
        if admin_type == "user":
            await websocket.close(code=1008, reason="Admin privileges required")
            return
        
        # Accept connection AFTER validation
        await websocket.accept()
        logger.info(f"Admin WebSocket connection accepted for user {user_id} ({admin_type})")
        
        # Send connection established message
        await websocket.send_text(json.dumps({
            "type": "admin_connection_established",
            "admin_type": admin_type,
            "message": f"Connected to admin real-time system ({admin_type})",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }))
        
        # Add to connection manager
        if user_id not in connection_manager.admin_connections:
            connection_manager.admin_connections[user_id] = set()
        connection_manager.admin_connections[user_id].add(websocket)
        
        if admin_type == "system_admin":
            connection_manager.system_admin_connections.add(websocket)
        
        try:
            while True:
                # Keep connection alive and handle admin-specific messages
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await connection_manager.send_personal_message({
                        "type": "pong",
                        "admin_type": admin_type,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }, websocket)
                elif message.get("type") == "get_pending_requests" and admin_type == "system_admin":
                    # Send current pending requests count
                    pending_count = await db.campus_admin_requests.count_documents({"status": "pending"})
                    await connection_manager.send_personal_message({
                        "type": "pending_requests_count",
                        "count": pending_count,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }, websocket)
                
        except WebSocketDisconnect:
            await connection_manager.disconnect_user(websocket, user_id)
        except Exception as e:
            logger.error(f"Admin WebSocket error for user {user_id}: {str(e)}")
            await connection_manager.disconnect_user(websocket, user_id)
            
    except Exception as e:
        logger.error(f"Admin WebSocket connection error: {str(e)}")
        try:
            await websocket.close(code=4500, reason="Internal server error")
        except:
            pass

@api_router.get("/websocket/status")
@limiter.limit("10/minute")
async def websocket_status(request: Request):
    """Get WebSocket server status"""
    return {
        "connected_users": connection_manager.get_connected_users_count(),
        "connected_admins": connection_manager.get_connected_admins_count(),
        "server_status": "running",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ==========================================
# COMPREHENSIVE REGISTRATION ENDPOINTS
# ==========================================

from registration_service import (
    save_student_id_card, validate_registration_data,
    get_registrations_for_event, get_college_statistics,
    export_registrations_to_csv, export_registrations_to_excel,
    export_registrations_to_pdf, export_registrations_to_docx
)
from models import (
    EventRegistration, PrizeChallengeRegistration, 
    InterCollegeRegistration, RegistrationApproval
)

# College Events - Detailed Registration
@api_router.post("/college-events/{event_id}/register-detailed")
@limiter.limit("10/minute")
async def register_for_event_detailed(
    request: Request,
    event_id: str,
    registration_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Register for college event with detailed information"""
    try:
        db = await get_database()
        
        # Get event
        event = await db.college_events.find_one({"id": event_id})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Check if registration is open
        if event["status"] not in ["upcoming", "registration_open"]:
            raise HTTPException(status_code=400, detail="Registration is not open")
        
        # Check if already registered
        existing = await db.event_registrations.find_one({
            "event_id": event_id,
            "user_id": current_user["id"]
        })
        if existing:
            raise HTTPException(status_code=400, detail="Already registered")
        
        # Validate registration data
        reg_type = registration_data.get("registration_type", "individual")
        validation = await validate_registration_data(reg_type, registration_data)
        
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail={"errors": validation["errors"]})
        
        # Create registration
        registration = EventRegistration(
            event_id=event_id,
            user_id=current_user["id"],
            user_name=registration_data.get("full_name", current_user.get("full_name", "")),
            user_email=registration_data.get("email", current_user.get("email", "")),
            user_college=registration_data.get("college", current_user.get("university", "")),
            registration_type=reg_type,
            usn=registration_data.get("usn"),
            phone_number=registration_data.get("phone_number"),
            semester=registration_data.get("semester"),
            year=registration_data.get("year"),
            branch=registration_data.get("branch"),
            section=registration_data.get("section"),
            student_id_card_url=registration_data.get("student_id_card_url"),
            team_name=registration_data.get("team_name"),
            team_leader_name=registration_data.get("team_leader_name"),
            team_leader_usn=registration_data.get("team_leader_usn"),
            team_leader_email=registration_data.get("team_leader_email"),
            team_leader_phone=registration_data.get("team_leader_phone"),
            team_size=registration_data.get("team_size"),
            team_members=registration_data.get("team_members", [])
        )
        
        await db.event_registrations.insert_one(registration.dict())
        
        # Update participant count
        await db.college_events.update_one(
            {"id": event_id},
            {"$inc": {"current_participants": 1}}
        )
        
        return {
            "message": "Registration submitted successfully",
            "registration_id": registration.id,
            "status": "pending",
            "note": "Your registration is pending approval by the event organizer"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Failed to register")

# Prize Challenges - Detailed Registration
@api_router.post("/prize-challenges/{challenge_id}/register-detailed")
@limiter.limit("10/minute")
async def register_for_prize_challenge_detailed(
    request: Request,
    challenge_id: str,
    registration_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Register for prize challenge with detailed information"""
    try:
        db = await get_database()
        
        # Get challenge
        challenge = await db.prize_challenges.find_one({"id": challenge_id})
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        # Check if already registered
        existing = await db.prize_challenge_registrations.find_one({
            "challenge_id": challenge_id,
            "user_id": current_user["id"]
        })
        if existing:
            raise HTTPException(status_code=400, detail="Already registered")
        
        # Get user's phone number from profile if not provided
        phone_number = registration_data.get("phone_number")
        if not phone_number:
            user = await db.users.find_one({"id": current_user["id"]})
            phone_number = user.get("phone_number") if user else None
        
        # Validate required fields (removed usn, using phone_number from profile)
        required_fields = ["full_name", "email", "college", "semester", "year", "branch"]
        missing_fields = [f for f in required_fields if not registration_data.get(f)]
        
        if missing_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        if not phone_number:
            raise HTTPException(
                status_code=400,
                detail="Phone number is required. Please update your profile."
            )
        
        # Create registration
        registration = PrizeChallengeRegistration(
            challenge_id=challenge_id,
            user_id=current_user["id"],
            full_name=registration_data["full_name"],
            email=registration_data["email"],
            phone_number=phone_number,
            college=registration_data["college"],
            semester=registration_data["semester"],
            year=registration_data["year"],
            branch=registration_data["branch"],
            section=registration_data.get("section"),
            student_id_card_url=registration_data.get("student_id_card_url")
        )
        
        await db.prize_challenge_registrations.insert_one(registration.dict())
        
        return {
            "message": "Registration submitted successfully",
            "registration_id": registration.id,
            "status": "pending",
            "note": "Your registration is pending approval"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Failed to register")

# Inter-College Competitions - Detailed Registration
@api_router.post("/inter-college/competitions/{competition_id}/register-detailed")
@limiter.limit("10/minute")
async def register_for_competition_detailed(
    request: Request,
    competition_id: str,
    registration_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Register for inter-college competition with detailed information"""
    try:
        db = await get_database()
        
        # Get competition
        competition = await db.inter_college_competitions.find_one({"id": competition_id})
        if not competition:
            raise HTTPException(status_code=404, detail="Competition not found")
        
        # Check if already registered
        existing = await db.inter_college_registrations.find_one({
            "competition_id": competition_id,
            "user_id": current_user["id"]
        })
        if existing:
            raise HTTPException(status_code=400, detail="Already registered")
        
        # Get user's phone number from profile if not provided
        user = await db.users.find_one({"id": current_user["id"]})
        user_phone = user.get("phone_number") if user else None
        
        # Create registration
        reg_type = registration_data.get("registration_type", "admin")
        
        # Auto-populate phone numbers from user profile if not provided
        team_leader_phone = registration_data.get("team_leader_phone") or user_phone
        admin_phone = registration_data.get("admin_phone") or user_phone
        
        registration = InterCollegeRegistration(
            competition_id=competition_id,
            user_id=current_user["id"],
            registration_type=reg_type,
            admin_name=registration_data.get("admin_name"),
            admin_email=registration_data.get("admin_email"),
            admin_phone=admin_phone,
            campus_name=registration_data.get("campus_name"),
            team_name=registration_data.get("team_name"),
            team_type=registration_data.get("team_type"),
            team_leader_name=registration_data.get("team_leader_name"),
            team_leader_email=registration_data.get("team_leader_email"),
            team_leader_phone=team_leader_phone,
            team_leader_semester=registration_data.get("team_leader_semester"),
            team_leader_year=registration_data.get("team_leader_year"),
            team_leader_branch=registration_data.get("team_leader_branch"),
            team_size=registration_data.get("team_size"),
            team_members=registration_data.get("team_members", [])
        )
        
        await db.inter_college_registrations.insert_one(registration.dict())
        
        return {
            "message": "Registration submitted successfully",
            "registration_id": registration.id,
            "status": "pending"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Failed to register")

# Club Admin - View Registrations
@api_router.get("/club-admin/registrations/{event_type}/{event_id}")
@api_router.get("/super-admin/registrations/{event_type}/{event_id}")
async def get_event_registrations(
    event_type: str,  # "college_event", "prize_challenge", "inter_college"
    event_id: str,
    college: Optional[str] = None,
    status: Optional[str] = None,
    registration_type: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Get all registrations for an event with filters and pagination (Club Admin and Super Admin)"""
    try:
        db = await get_database()
        
        # Build filters
        filters = {}
        if college:
            filters["college"] = college
        if status:
            filters["status"] = status
        if registration_type:
            filters["registration_type"] = registration_type
        
        # Get all registrations for statistics (without pagination)
        all_registrations = await get_registrations_for_event(db, event_id, event_type, filters)
        
        # Get college statistics from all registrations
        stats = await get_college_statistics(all_registrations)
        
        # Apply pagination
        total_count = len(all_registrations)
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_registrations = all_registrations[start_index:end_index]
        
        total_pages = (total_count + limit - 1) // limit  # Ceiling division
        
        # Calculate status counts
        status_counts = {
            "pending": sum(1 for r in all_registrations if r.get("status") == "pending"),
            "approved": sum(1 for r in all_registrations if r.get("status") == "approved"),
            "rejected": sum(1 for r in all_registrations if r.get("status") == "rejected")
        }
        
        return {
            "registrations": paginated_registrations,
            "total_count": total_count,
            "status_counts": status_counts,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
            "college_statistics": stats,
            "filters_applied": filters
        }
    
    except Exception as e:
        print(f"Error fetching registrations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch registrations")

# Club Admin / Super Admin - Approve/Reject Registration
@api_router.post("/club-admin/registrations/{event_type}/approve-reject")
@api_router.post("/super-admin/registrations/{event_type}/approve-reject")
async def approve_reject_registration(
    event_type: str,
    approval_data: RegistrationApproval,
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Approve or reject a registration (Club Admin and Super Admin)"""
    try:
        db = await get_database()
        
        # Map event type to collection
        collection_map = {
            "college_event": "event_registrations",
            "prize_challenge": "prize_challenge_registrations",
            "inter_college": "inter_college_registrations"
        }
        
        collection_name = collection_map.get(event_type)
        if not collection_name:
            raise HTTPException(status_code=400, detail="Invalid event type")
        
        # Get registration
        registration = await db[collection_name].find_one({"id": approval_data.registration_id})
        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found")
        
        # Validate rejection reason
        if approval_data.action == "reject" and not approval_data.reason:
            raise HTTPException(status_code=400, detail="Rejection reason is required")
        
        # Update registration
        update_data = {
            "status": "approved" if approval_data.action == "approve" else "rejected",
            "approved_by": current_user["id"],
            "approved_at": datetime.now(timezone.utc)
        }
        
        if approval_data.action == "reject":
            update_data["rejection_reason"] = approval_data.reason
        
        await db[collection_name].update_one(
            {"id": approval_data.registration_id},
            {"$set": update_data}
        )
        
        # If approved, update user profile with phone number from registration
        if approval_data.action == "approve":
            phone_number = registration.get("phone") or registration.get("user_phone")
            if phone_number and registration.get("user_id"):
                try:
                    await db.users.update_one(
                        {"id": registration["user_id"]},
                        {"$set": {"phone": phone_number}}
                    )
                    print(f"Updated user phone number: {registration['user_id']} -> {phone_number}")
                except Exception as e:
                    print(f"Failed to update user phone number: {e}")
                    # Continue execution even if phone update fails
        
        # If approved for prize challenge, create participation record
        if approval_data.action == "approve" and event_type == "prize_challenge":
            participation = {
                "id": str(uuid.uuid4()),
                "challenge_id": registration["challenge_id"],
                "user_id": registration["user_id"],
                "joined_at": datetime.now(timezone.utc),
                "participation_status": "active",
                "current_progress": 0.0,
                "progress_percentage": 0.0
            }
            await db.prize_challenge_participations.insert_one(participation)
        
        # 🔔 REAL-TIME NOTIFICATIONS: Send registration status update notification
        try:
            notification_service = await get_notification_service()
            
            # Map event type to correct ID field name
            event_id_field_map = {
                "college_event": "event_id",
                "prize_challenge": "challenge_id",
                "inter_college": "competition_id"
            }
            id_field = event_id_field_map.get(event_type, "event_id")
            
            # Get event details for notification
            event_collection_map = {
                "college_event": "college_events",
                "prize_challenge": "prize_challenges", 
                "inter_college": "inter_college_competitions"
            }
            event_collection = event_collection_map.get(event_type)
            event_details = await db[event_collection].find_one({
                "id": registration.get(id_field)
            }) if event_collection else {}
            
            event_title = event_details.get("title", "Event") if event_details else "Event"
            
            if approval_data.action == "approve":
                # Get event ID value using the correct field name
                event_id_value = registration.get(id_field)
                
                await notification_service.create_and_notify_in_app_notification(registration["user_id"], {
                    "type": "registration_approved",
                    "title": "🎉 Registration Approved!",
                    "message": f"Your registration for '{event_title}' has been approved. You're all set to participate!",
                    "priority": "high",
                    "action_url": f"/{event_type.replace('_', '-')}s/{event_id_value}",
                    "metadata": {
                        "event_type": event_type,
                        "event_title": event_title,
                        "registration_id": approval_data.registration_id,
                        "approved_by": current_user.get("full_name", "Admin"),
                        "approved_at": update_data["approved_at"].isoformat()
                    }
                })
            else:  # reject
                await notification_service.create_and_notify_in_app_notification(registration["user_id"], {
                    "type": "registration_rejected", 
                    "title": "❌ Registration Declined",
                    "message": f"Your registration for '{event_title}' has been declined. Reason: {approval_data.reason}",
                    "priority": "medium",
                    "action_url": f"/my-registrations",
                    "metadata": {
                        "event_type": event_type,
                        "event_title": event_title,
                        "registration_id": approval_data.registration_id,
                        "rejection_reason": approval_data.reason,
                        "rejected_by": current_user.get("full_name", "Admin"),
                        "rejected_at": update_data["approved_at"].isoformat()
                    }
                })
                
        except Exception as e:
            print(f"Failed to send registration status notification: {e}")
            # Continue execution even if notification fails
        
        return {
            "message": f"Registration {approval_data.action}d successfully",
            "registration_id": approval_data.registration_id,
            "new_status": update_data["status"],
            "notification_sent": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing approval: {e}")
        raise HTTPException(status_code=500, detail="Failed to process approval")

# Club Admin / Super Admin - Export Registrations in Multiple Formats
@api_router.get("/club-admin/registrations/{event_type}/{event_id}/export")
@api_router.get("/super-admin/registrations/{event_type}/{event_id}/export")
async def export_registrations(
    event_type: str,
    event_id: str,
    format: str = "csv",  # csv, excel, pdf, docx
    college: Optional[str] = None,
    status: Optional[str] = None,
    registration_type: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Export registrations in multiple formats (CSV, Excel, PDF, DOCX) with filters (Club Admin and Super Admin)"""
    try:
        db = await get_database()
        
        # Get event name
        event_collection_map = {
            "college_event": "college_events",
            "prize_challenge": "prize_challenges",
            "inter_college": "inter_college_competitions"
        }
        
        event_collection = event_collection_map.get(event_type)
        event = await db[event_collection].find_one({"id": event_id})
        event_name = event.get("title", "event") if event else "event"
        
        # Build filters
        filters = {}
        if college:
            filters["college"] = college
        if status:
            filters["status"] = status
        if registration_type:
            filters["registration_type"] = registration_type
        
        # Get registrations with filters
        registrations = await get_registrations_for_event(db, event_id, event_type, filters)
        
        if not registrations:
            raise HTTPException(status_code=404, detail="No registrations found")
        
        # Export in requested format
        file_path = None
        format_lower = format.lower()
        
        if format_lower == "csv":
            file_path = await export_registrations_to_csv(registrations, event_name, event_type)
        elif format_lower == "excel" or format_lower == "xlsx":
            file_path = await export_registrations_to_excel(registrations, event_name, event_type)
        elif format_lower == "pdf":
            file_path = await export_registrations_to_pdf(registrations, event_name, event_type)
        elif format_lower == "docx" or format_lower == "word":
            file_path = await export_registrations_to_docx(registrations, event_name, event_type)
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use: csv, excel, pdf, docx")
        
        if not file_path:
            raise HTTPException(status_code=500, detail="Export failed")
        
        return {
            "message": f"Export successful ({format.upper()})",
            "file_path": file_path,
            "format": format_lower,
            "total_registrations": len(registrations),
            "download_url": f"{BACKEND_URL}{file_path}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Export error: {e}")
        raise HTTPException(status_code=500, detail="Failed to export registrations")

# Upload Student ID Card
@api_router.post("/upload/student-id")
async def upload_student_id(
    file: UploadFile,
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Upload student ID card with size validation (max 5MB)"""
    try:
        # Validate file type
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Validate file size (5MB limit)
        MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes
        
        # Read file content to check size
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size ({file_size / (1024*1024):.2f}MB) exceeds maximum limit of 5MB"
            )
        
        # Reset file pointer for save operation
        await file.seek(0)
        
        # Save file
        file_url = await save_student_id_card(file, current_user["id"])
        
        if not file_url:
            raise HTTPException(status_code=500, detail="Failed to save file")
        
        return {
            "message": "File uploaded successfully",
            "file_url": file_url
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file")

# User Dashboard - Get My Registrations
@api_router.get("/my-registrations")
async def get_my_registrations(
    current_user: Dict[str, Any] = Depends(get_current_user_dict)
):
    """Get all registrations for current user"""
    try:
        db = await get_database()
        
        user_id = current_user["id"]
        
        # Get all types of registrations
        event_regs = await db.event_registrations.find({"user_id": user_id}).to_list(100)
        prize_regs = await db.prize_challenge_registrations.find({"user_id": user_id}).to_list(100)
        comp_regs = await db.inter_college_registrations.find({"user_id": user_id}).to_list(100)
        
        # Remove MongoDB _id fields and fetch event details
        for reg in event_regs:
            if "_id" in reg:
                del reg["_id"]
            event = await db.college_events.find_one({"id": reg["event_id"]})
            if event and "_id" in event:
                del event["_id"]
            reg["event_details"] = event if event else {}
        
        for reg in prize_regs:
            if "_id" in reg:
                del reg["_id"]
            challenge = await db.prize_challenges.find_one({"id": reg["challenge_id"]})
            if challenge and "_id" in challenge:
                del challenge["_id"]
            reg["challenge_details"] = challenge if challenge else {}
        
        for reg in comp_regs:
            if "_id" in reg:
                del reg["_id"]
            competition = await db.inter_college_competitions.find_one({"id": reg["competition_id"]})
            if competition and "_id" in competition:
                del competition["_id"]
            reg["competition_details"] = competition if competition else {}
        
        return {
            "college_events": event_regs,
            "prize_challenges": prize_regs,
            "inter_college_competitions": comp_regs,
            "total_registrations": len(event_regs) + len(prize_regs) + len(comp_regs)
        }
    
    except Exception as e:
        print(f"Error fetching registrations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch registrations")

# Include ALL API routes after ALL endpoint definitions
app.include_router(api_router)

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

