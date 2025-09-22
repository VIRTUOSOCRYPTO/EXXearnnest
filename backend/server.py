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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Ensure uploads directory exists
UPLOADS_DIR = ROOT_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# Create the main app
app = FastAPI(
    title="EarnWise - Student Finance & Side Hustle Platform",
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
    
    if not user.get("email_verified", False):
        raise HTTPException(status_code=401, detail="Email not verified")
    
    return user_id

async def get_current_admin(user_id: str = Depends(get_current_user)) -> str:
    """Get current authenticated admin user"""
    user = await get_user_by_id(user_id)
    if not user or not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id

async def get_enhanced_ai_hustle_recommendations(user_skills: List[str], availability: int, recent_earnings: float, location: str = None) -> List[Dict]:
    """Generate enhanced AI-powered hustle recommendations"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"hustle_rec_{uuid.uuid4()}",
            system_message="""You are an AI advisor for student side hustles in India. Based on user skills, availability, recent earnings, and location, recommend 8 specific hustle opportunities. Focus on Indian market opportunities and use INR currency.
            
            Return ONLY a JSON array with this exact format:
            [
                {
                    "title": "Exact hustle title",
                    "description": "Brief description focusing on Indian market",
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
            text=f"User profile: Skills: {', '.join(user_skills) if user_skills else 'General skills'}. Available {availability} hours/week{location_context}. {earnings_context}. Recommend 8 personalized side hustle opportunities with Indian market focus and INR rates."
        )
        
        response = await chat.send_message(user_message)
        
        # Try to parse JSON response
        import json
        try:
            recommendations = json.loads(response)
            return recommendations[:8]  # Ensure max 8 recommendations
        except json.JSONDecodeError:
            # Fallback recommendations for Indian market
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
                    "match_score": 90.0
                },
                {
                    "title": "Content Writing (Hindi/English)",
                    "description": "Write articles, blogs, and social media content for Indian brands",
                    "category": "freelance",
                    "estimated_pay": 250.0,
                    "time_commitment": "8-12 hours/week",
                    "required_skills": ["Writing", "Research"],
                    "difficulty_level": "intermediate",
                    "platform": "Upwork, Freelancer, Truelancer",
                    "match_score": 85.0
                },
                {
                    "title": "Food Delivery Partner",
                    "description": "Deliver food orders in your local area with flexible timing",
                    "category": "delivery",
                    "estimated_pay": 200.0,
                    "time_commitment": "15-20 hours/week",
                    "required_skills": ["Time Management", "Local Knowledge"],
                    "difficulty_level": "beginner",
                    "platform": "Zomato, Swiggy, Dunzo",
                    "match_score": 75.0
                },
                {
                    "title": "Social Media Management",
                    "description": "Manage social media accounts for small Indian businesses",
                    "category": "content_creation",
                    "estimated_pay": 400.0,
                    "time_commitment": "6-10 hours/week",
                    "required_skills": ["Social Media", "Content Creation"],
                    "difficulty_level": "intermediate",
                    "platform": "Direct Client Outreach",
                    "match_score": 80.0
                }
            ]
            
    except Exception as e:
        logging.error(f"AI recommendation error: {e}")
        return []

async def get_financial_insights(user_id: str) -> Dict[str, Any]:
    """Generate AI-powered financial insights"""
    try:
        # Get user's recent transactions
        transactions = await get_user_transactions(user_id, limit=50)
        
        if not transactions:
            return {"insights": ["Start tracking your expenses to get personalized insights!"]}
        
        # Calculate basic stats
        total_income = sum(t["amount"] for t in transactions if t["type"] == "income")
        total_expenses = sum(t["amount"] for t in transactions if t["type"] == "expense")
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"financial_insights_{user_id}",
            system_message="You are a financial advisor for Indian students. Provide 3-5 actionable insights based on their spending patterns. Use INR currency and be encouraging and specific to Indian context."
        ).with_model("openai", "gpt-4o")

        user_message = UserMessage(
            text=f"Indian student's financial summary: Total income: ₹{total_income}, Total expenses: ₹{total_expenses}. Recent transactions: {len(transactions)} entries. Provide personalized financial insights and tips for Indian students."
        )

        response = await chat.send_message(user_message)
        
        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_savings": total_income - total_expenses,
            "insights": [response]
        }
        
    except Exception as e:
        logging.error(f"Financial insights error: {e}")
        return {"insights": ["Keep tracking your finances to unlock AI-powered insights!"]}

# Enhanced Authentication Routes with Comprehensive OTP Security
@api_router.post("/auth/register")
@limiter.limit("5/minute")
async def register_user(request: Request, user_data: UserCreate):
    """
    Enhanced user registration with secure OTP email verification
    
    Features:
    - Advanced email validation
    - Rate limiting (global + per-email)
    - Comprehensive security logging
    - Dynamic OTP generation (6-8 digits)
    - 5-minute OTP expiry
    - Input sanitization and XSS protection
    """
    try:
        # Extract client information for security logging
        client_ip = getattr(request.client, 'host', 'Unknown') if hasattr(request, 'client') else 'Unknown'
        
        # Enhanced email validation
        if not validate_email_format(user_data.email):
            log_otp_attempt(user_data.email, "REGISTRATION_INVALID_EMAIL", False, request)
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Check email-specific rate limiting for registration
        rate_limit_result = await check_otp_rate_limit(user_data.email, "REGISTRATION", 3, 15)
        if rate_limit_result["is_limited"]:
            log_otp_attempt(user_data.email, "REGISTRATION_RATE_LIMITED", False, request, {
                "attempts_count": rate_limit_result["attempts_count"],
                "reset_time": rate_limit_result["reset_time"].isoformat()
            })
            raise HTTPException(
                status_code=429, 
                detail=f"Too many registration attempts. Try again in {rate_limit_result['window_minutes']} minutes."
            )
        
        # Check if user exists
        existing_user = await get_user_by_email(user_data.email)
        if existing_user:
            log_otp_attempt(user_data.email, "REGISTRATION_EMAIL_EXISTS", False, request)
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
        user_doc["email_verified"] = False
        user_doc["is_active"] = False  # Activate only after email verification
        
        await create_user(user_doc)
        
        # Generate enhanced verification code
        verification_code = generate_verification_code()
        expires_at = datetime.now(timezone.utc) + EMAIL_VERIFICATION_EXPIRY
        
        # Store verification code with enhanced security
        await store_verification_code(user_data.email, verification_code, expires_at)
        
        # Send enhanced email with client IP for security
        email_sent = await email_service.send_verification_email(user_data.email, verification_code, client_ip)
        
        if not email_sent:
            log_otp_attempt(user_data.email, "REGISTRATION_EMAIL_FAILED", False, request)
            raise HTTPException(status_code=500, detail="Failed to send verification email")
        
        # Log successful registration attempt
        await log_otp_attempt_to_db(user_data.email, "REGISTRATION", True, client_ip, 
                                  request.headers.get('user-agent', 'Unknown'))
        log_otp_attempt(user_data.email, "REGISTRATION_SUCCESS", True, request, {
            "otp_length": len(verification_code),
            "expiry_minutes": OTP_EXPIRY_MINUTES
        })
        
        return {
            "message": f"Registration successful! Please check your email for a {len(verification_code)}-digit verification code.",
            "email": user_data.email,
            "verification_required": True,
            "code_expires_in_minutes": OTP_EXPIRY_MINUTES,
            "code_length": len(verification_code)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_otp_attempt(user_data.email, "REGISTRATION_ERROR", False, request, {"error": str(e)})
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")

@api_router.post("/auth/verify-email")
@limiter.limit("10/minute")
async def verify_email(request: Request, verification: EmailVerificationConfirm):
    """
    Enhanced email verification with comprehensive security checks
    
    Features:
    - Advanced OTP verification with attempt tracking
    - Rate limiting and security logging
    - Automatic cleanup of expired codes
    - Enhanced error messages and feedback
    - Security event logging
    """
    try:
        # Extract client information
        client_ip = getattr(request.client, 'host', 'Unknown') if hasattr(request, 'client') else 'Unknown'
        
        # Validate email format
        if not validate_email_format(verification.email):
            log_otp_attempt(verification.email, "VERIFY_INVALID_EMAIL", False, request)
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Check verification rate limiting
        rate_limit_result = await check_otp_rate_limit(verification.email, "EMAIL_VERIFY", 5, 5)
        if rate_limit_result["is_limited"]:
            log_otp_attempt(verification.email, "VERIFY_RATE_LIMITED", False, request, {
                "attempts_count": rate_limit_result["attempts_count"]
            })
            raise HTTPException(
                status_code=429, 
                detail=f"Too many verification attempts. Try again in {rate_limit_result['window_minutes']} minutes."
            )
        
        # Use enhanced verification function
        verification_result = await verify_otp_with_security_checks(
            verification.email, 
            verification.verification_code, 
            "email_verification"
        )
        
        if not verification_result["success"]:
            # Log failed verification attempt
            await log_otp_attempt_to_db(verification.email, "EMAIL_VERIFY", False, client_ip,
                                      request.headers.get('user-agent', 'Unknown'),
                                      {"error": verification_result["error_code"]})
            log_otp_attempt(verification.email, "VERIFY_FAILED", False, request, 
                          {"error": verification_result["error_code"]})
            
            if verification_result["error_code"] == "OTP_EXPIRED":
                raise HTTPException(status_code=400, detail=f"Verification code expired. Codes expire after {OTP_EXPIRY_MINUTES} minutes for security.")
            elif verification_result["error_code"] == "OTP_INVALID":
                raise HTTPException(status_code=400, detail="Invalid verification code. Please check the code and try again.")
            else:
                raise HTTPException(status_code=400, detail=verification_result["error"])
        
        # Activate user account
        user_doc = await get_user_by_email(verification.email)
        if not user_doc:
            log_otp_attempt(verification.email, "VERIFY_USER_NOT_FOUND", False, request)
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update user status
        await update_user(
            user_doc["id"],
            {
                "email_verified": True,
                "is_active": True,
                "last_login": datetime.now(timezone.utc)
            }
        )
        
        # Send welcome email
        await email_service.send_welcome_email(verification.email, user_doc["full_name"])
        
        # Create JWT token
        token = create_jwt_token(user_doc["id"])
        
        # Log successful verification
        await log_otp_attempt_to_db(verification.email, "EMAIL_VERIFY", True, client_ip,
                                  request.headers.get('user-agent', 'Unknown'))
        log_otp_attempt(verification.email, "VERIFY_SUCCESS", True, request)
        await log_security_event("EMAIL_VERIFIED", user_doc["id"], verification.email, client_ip)
        
        # Remove password hash from response
        del user_doc["password_hash"]
        user = User(**user_doc)
        
        return {
            "message": "Email verified successfully! Welcome to EarnWise!",
            "token": token,
            "user": user.dict(),
            "verification_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_otp_attempt(verification.email, "VERIFY_ERROR", False, request, {"error": str(e)})
        logger.error(f"Email verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Email verification failed")

@api_router.post("/auth/resend-verification")
@limiter.limit("3/minute")
async def resend_verification(request: Request, email_request: EmailVerificationRequest):
    """
    Enhanced resend verification email with comprehensive security features
    
    Features:
    - Email-specific rate limiting (stricter than global)
    - Enhanced validation and security logging
    - Automatic cleanup of expired codes
    - Detailed security tracking
    - Client IP logging for security monitoring
    """
    try:
        # Extract client information
        client_ip = getattr(request.client, 'host', 'Unknown') if hasattr(request, 'client') else 'Unknown'
        
        # Validate email format
        if not validate_email_format(email_request.email):
            log_otp_attempt(email_request.email, "RESEND_INVALID_EMAIL", False, request)
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Check email-specific rate limiting for resend (2 requests per 5 minutes)
        rate_limit_result = await check_otp_rate_limit(email_request.email, "OTP_RESEND", 2, 5)
        if rate_limit_result["is_limited"]:
            log_otp_attempt(email_request.email, "RESEND_RATE_LIMITED", False, request, {
                "attempts_count": rate_limit_result["attempts_count"],
                "remaining_time": rate_limit_result["window_minutes"]
            })
            raise HTTPException(
                status_code=429, 
                detail=f"Too many resend requests. You can request a new code {rate_limit_result['remaining_attempts']} more times. Try again in {rate_limit_result['window_minutes']} minutes."
            )
        
        # Check if user exists
        user = await get_user_by_email(email_request.email)
        if not user:
            log_otp_attempt(email_request.email, "RESEND_USER_NOT_FOUND", False, request)
            # Don't reveal if email exists or not for security
            return {"message": "If the email exists and is not verified, a new verification code has been sent."}
        
        # Check if email is already verified
        if user.get("email_verified", False):
            log_otp_attempt(email_request.email, "RESEND_ALREADY_VERIFIED", False, request)
            raise HTTPException(status_code=400, detail="Email already verified")
        
        # Generate new enhanced verification code
        verification_code = generate_verification_code()
        expires_at = datetime.now(timezone.utc) + EMAIL_VERIFICATION_EXPIRY
        
        # Store new verification code (this will replace any existing code)
        await store_verification_code(email_request.email, verification_code, expires_at)
        
        # Send enhanced email with security information
        email_sent = await email_service.send_verification_email(email_request.email, verification_code, client_ip)
        
        if not email_sent:
            log_otp_attempt(email_request.email, "RESEND_EMAIL_FAILED", False, request)
            raise HTTPException(status_code=500, detail="Failed to send verification email")
        
        # Log successful resend
        await log_otp_attempt_to_db(email_request.email, "OTP_RESEND", True, client_ip,
                                  request.headers.get('user-agent', 'Unknown'))
        log_otp_attempt(email_request.email, "RESEND_SUCCESS", True, request, {
            "otp_length": len(verification_code),
            "expiry_minutes": OTP_EXPIRY_MINUTES
        })
        
        return {
            "message": f"New {len(verification_code)}-digit verification code sent successfully!",
            "code_expires_in_minutes": OTP_EXPIRY_MINUTES,
            "remaining_resend_attempts": rate_limit_result["remaining_attempts"] - 1,
            "resend_reset_time": rate_limit_result["reset_time"].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_otp_attempt(email_request.email, "RESEND_ERROR", False, request, {"error": str(e)})
        logger.error(f"Resend verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to resend verification")

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
        
        # Check if email is verified
        if not user_doc.get("email_verified", False):
            raise HTTPException(
                status_code=401,
                detail="Please verify your email before logging in"
            )
        
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
    
    # Log password strength check for security monitoring
    log_otp_attempt("system", "PASSWORD_STRENGTH_CHECK", True, request, {
        "strength_score": strength_info["score"],
        "strength_level": strength_info["strength"]
    })
    
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

@api_router.post("/auth/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, email_request: EmailVerificationRequest):
    """
    Enhanced forgot password with comprehensive security features
    
    Features:
    - Email-specific rate limiting
    - Enhanced validation and security logging
    - Dynamic OTP generation with 5-minute expiry
    - Client IP tracking for security monitoring
    - Comprehensive attempt logging
    """
    try:
        # Extract client information
        client_ip = getattr(request.client, 'host', 'Unknown') if hasattr(request, 'client') else 'Unknown'
        
        # Validate email format
        if not validate_email_format(email_request.email):
            log_otp_attempt(email_request.email, "FORGOT_INVALID_EMAIL", False, request)
            # Don't reveal validation failure for security
            return {"message": "If the email exists, a reset code has been sent"}
        
        # Check email-specific rate limiting for password reset (2 requests per 10 minutes)
        rate_limit_result = await check_otp_rate_limit(email_request.email, "PASSWORD_RESET", 2, 10)
        if rate_limit_result["is_limited"]:
            log_otp_attempt(email_request.email, "FORGOT_RATE_LIMITED", False, request, {
                "attempts_count": rate_limit_result["attempts_count"]
            })
            # Don't reveal rate limiting for security
            return {"message": "If the email exists, a reset code has been sent"}
        
        # Check if user exists
        user = await get_user_by_email(email_request.email)
        if not user:
            log_otp_attempt(email_request.email, "FORGOT_USER_NOT_FOUND", False, request)
            # Don't reveal if email exists or not for security
            return {"message": "If the email exists, a reset code has been sent"}
        
        # Check if account is active
        if not user.get("is_active", True):
            log_otp_attempt(email_request.email, "FORGOT_ACCOUNT_INACTIVE", False, request)
            return {"message": "If the email exists, a reset code has been sent"}
        
        # Generate enhanced reset code
        reset_code = generate_verification_code()
        expires_at = datetime.now(timezone.utc) + PASSWORD_RESET_EXPIRY
        
        # Store reset code with enhanced security
        await store_password_reset_code(email_request.email, reset_code, expires_at)
        
        # Send enhanced email with security information
        email_sent = await email_service.send_password_reset_email(email_request.email, reset_code, client_ip)
        
        if email_sent:
            # Log successful reset request
            await log_otp_attempt_to_db(email_request.email, "PASSWORD_RESET", True, client_ip,
                                      request.headers.get('user-agent', 'Unknown'))
            log_otp_attempt(email_request.email, "FORGOT_SUCCESS", True, request, {
                "otp_length": len(reset_code),
                "expiry_minutes": OTP_EXPIRY_MINUTES
            })
            await log_security_event("PASSWORD_RESET_REQUESTED", user["id"], email_request.email, client_ip)
        else:
            log_otp_attempt(email_request.email, "FORGOT_EMAIL_FAILED", False, request)
        
        # Always return the same message for security
        return {"message": "If the email exists, a reset code has been sent"}
        
    except Exception as e:
        log_otp_attempt(email_request.email, "FORGOT_ERROR", False, request, {"error": str(e)})
        logger.error(f"Forgot password error: {str(e)}")
        return {"message": "If the email exists, a reset code has been sent"}

@api_router.post("/auth/reset-password")
@limiter.limit("5/minute")
async def reset_password(request: Request, reset_data: PasswordResetConfirm):
    """
    Enhanced password reset with comprehensive security checks
    
    Features:
    - Advanced OTP verification with security checks
    - Rate limiting and attempt tracking
    - Enhanced password validation
    - Comprehensive security logging
    - Automatic security cleanup
    """
    try:
        # Extract client information
        client_ip = getattr(request.client, 'host', 'Unknown') if hasattr(request, 'client') else 'Unknown'
        
        # Validate email format
        if not validate_email_format(reset_data.email):
            log_otp_attempt(reset_data.email, "RESET_INVALID_EMAIL", False, request)
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Check reset rate limiting
        rate_limit_result = await check_otp_rate_limit(reset_data.email, "PASSWORD_RESET_CONFIRM", 5, 5)
        if rate_limit_result["is_limited"]:
            log_otp_attempt(reset_data.email, "RESET_RATE_LIMITED", False, request, {
                "attempts_count": rate_limit_result["attempts_count"]
            })
            raise HTTPException(
                status_code=429, 
                detail=f"Too many reset attempts. Try again in {rate_limit_result['window_minutes']} minutes."
            )
        
        # Use enhanced verification function
        verification_result = await verify_otp_with_security_checks(
            reset_data.email, 
            reset_data.reset_code, 
            "password_reset"
        )
        
        if not verification_result["success"]:
            # Log failed reset attempt
            await log_otp_attempt_to_db(reset_data.email, "PASSWORD_RESET_CONFIRM", False, client_ip,
                                      request.headers.get('user-agent', 'Unknown'),
                                      {"error": verification_result["error_code"]})
            log_otp_attempt(reset_data.email, "RESET_FAILED", False, request, 
                          {"error": verification_result["error_code"]})
            
            if verification_result["error_code"] == "OTP_EXPIRED":
                raise HTTPException(status_code=400, detail=f"Reset code expired. Codes expire after {OTP_EXPIRY_MINUTES} minutes for security.")
            elif verification_result["error_code"] == "OTP_INVALID":
                raise HTTPException(status_code=400, detail="Invalid reset code. Please check the code and try again.")
            else:
                raise HTTPException(status_code=400, detail=verification_result["error"])
        
        # Get user for password update
        user = await get_user_by_email(reset_data.email)
        if not user:
            log_otp_attempt(reset_data.email, "RESET_USER_NOT_FOUND", False, request)
            raise HTTPException(status_code=404, detail="User not found")
        
        # Validate new password strength
        password_strength = check_password_strength(reset_data.new_password)
        if password_strength["score"] < 40:  # Require at least medium strength
            log_otp_attempt(reset_data.email, "RESET_WEAK_PASSWORD", False, request, {
                "password_score": password_strength["score"]
            })
            raise HTTPException(
                status_code=400, 
                detail=f"Password too weak (score: {password_strength['score']}/100). " + 
                       ", ".join(password_strength["feedback"])
            )
        
        # Update password with enhanced security
        hashed_password = hash_password(reset_data.new_password)
        await update_user(
            user["id"], 
            {
                "password_hash": hashed_password,
                "failed_login_attempts": 0,
                "last_failed_login": None,
                "password_changed_at": datetime.now(timezone.utc)  # Track password changes
            }
        )
        
        # Log successful password reset
        await log_otp_attempt_to_db(reset_data.email, "PASSWORD_RESET_CONFIRM", True, client_ip,
                                  request.headers.get('user-agent', 'Unknown'))
        log_otp_attempt(reset_data.email, "RESET_SUCCESS", True, request)
        await log_security_event("PASSWORD_RESET_COMPLETED", user["id"], reset_data.email, client_ip, {
            "password_strength_score": password_strength["score"]
        })
        
        return {
            "message": "Password reset successfully! Your account is now secure.",
            "password_strength": {
                "score": password_strength["score"],
                "strength": password_strength["strength"]
            },
            "reset_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_otp_attempt(reset_data.email, "RESET_ERROR", False, request, {"error": str(e)})
        logger.error(f"Reset password error: {str(e)}")
        raise HTTPException(status_code=500, detail="Password reset failed")

# User Routes
@api_router.get("/user/profile", response_model=User)
@limiter.limit("30/minute")
async def get_user_profile(request: Request, user_id: str = Depends(get_current_user)):
    """Get user profile"""
    user_doc = await get_user_by_id(user_id)
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
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

@api_router.post("/user/profile/photo")
@limiter.limit("5/minute")
async def upload_profile_photo(request: Request, file: UploadFile = File(...), user_id: str = Depends(get_current_user)):
    """Upload profile photo with validation"""
    try:
        # Validate file
        validate_file_upload(file.filename, file.size)
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1]
        filename = f"profile_{user_id}_{uuid.uuid4()}.{file_extension}"
        file_path = UPLOADS_DIR / filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Update user profile
        photo_url = f"/uploads/{filename}"
        await update_user(user_id, {"profile_photo": photo_url})
        
        return {"message": "Profile photo uploaded successfully", "photo_url": photo_url}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Photo upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Photo upload failed")

# Transaction Routes
@api_router.post("/transactions", response_model=Transaction)
@limiter.limit("20/minute")
async def create_transaction_endpoint(request: Request, transaction_data: TransactionCreate, user_id: str = Depends(get_current_user)):
    """Create transaction with validation"""
    try:
        transaction_dict = transaction_data.dict()
        transaction_dict["user_id"] = user_id
        transaction_dict["description"] = sanitize_input(transaction_dict["description"])
        transaction_dict["category"] = sanitize_input(transaction_dict["category"])
        
        transaction = Transaction(**transaction_dict)
        await create_transaction(transaction.dict())
        
        # Update user's total earnings if it's income
        if transaction.type == "income":
            await db.users.update_one(
                {"id": user_id},
                {"$inc": {"total_earnings": transaction.amount}}
            )
        
        return transaction
        
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
        hustle_dict["contact_info"] = sanitize_input(hustle_dict["contact_info"])
        
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
    """Get hustle categories"""
    categories = [
        {"name": "tutoring", "display": "Tutoring & Teaching", "icon": "📚"},
        {"name": "freelance", "display": "Freelance Work", "icon": "💻"},
        {"name": "content_creation", "display": "Content Creation", "icon": "🎨"},
        {"name": "delivery", "display": "Delivery & Transportation", "icon": "🚗"},
        {"name": "micro_tasks", "display": "Micro Tasks", "icon": "⚡"}
    ]
    return categories

# Budget Routes
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

# Analytics Routes
@api_router.get("/analytics/insights")
@limiter.limit("10/minute")
async def get_analytics_insights_endpoint(request: Request, user_id: str = Depends(get_current_user)):
    """Get AI-powered financial insights"""
    insights = await get_financial_insights(user_id)
    return insights

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

# Include the router in the main app
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
    logger.info("EarnWise Production Server started successfully")

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
