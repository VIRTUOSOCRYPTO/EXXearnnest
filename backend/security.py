import bcrypt
import jwt
import secrets
import re
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import HTTPException, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# JWT Configuration
JWT_SECRET = "earnaura-production-secret-key-2024-secure"
JWT_ALGORITHM = "HS256"

# Security constants
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=30)
EMAIL_VERIFICATION_EXPIRY = timedelta(hours=24)
PASSWORD_RESET_EXPIRY = timedelta(hours=1)

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT token"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    
    payload = {
        "user_id": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Optional[str]:
    """Verify JWT token and return user_id"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        token_type = payload.get("type")
        
        if not user_id or token_type != "access":
            return None
            
        return user_id
    except jwt.ExpiredSignatureError:
        logging.warning(f"Expired JWT token")
        return None
    except jwt.InvalidTokenError:
        logging.warning(f"Invalid JWT token")
        return None

def generate_verification_code() -> str:
    """Generate secure 6-digit verification code"""
    return str(secrets.randbelow(900000) + 100000)

def create_verification_token(email: str, code: str, token_type: str = "email_verification") -> str:
    """Create verification token for email verification or password reset"""
    expire = datetime.now(timezone.utc) + (
        EMAIL_VERIFICATION_EXPIRY if token_type == "email_verification" 
        else PASSWORD_RESET_EXPIRY
    )
    
    payload = {
        "email": email,
        "code": code,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": token_type
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_verification_token(token: str, provided_code: str, token_type: str = "email_verification") -> Optional[str]:
    """Verify verification token and code"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email = payload.get("email")
        stored_code = payload.get("code")
        stored_type = payload.get("type")
        
        if not email or not stored_code or stored_type != token_type:
            return None
            
        if stored_code != provided_code:
            return None
            
        return email
    except jwt.ExpiredSignatureError:
        logging.warning(f"Expired verification token")
        return None
    except jwt.InvalidTokenError:
        logging.warning(f"Invalid verification token")
        return None

def check_password_strength(password: str) -> dict:
    """Check password strength and return score with feedback
    
    ENHANCED SECURITY REQUIREMENTS:
    - Minimum 12 characters (enforced)
    - Must contain uppercase letter
    - Must contain lowercase letter  
    - Must contain number
    - Must contain special character
    """
    score = 0
    feedback = []
    
    # CRITICAL: Minimum 12 characters required
    if len(password) < 12:
        feedback.append("Password must be at least 12 characters long (REQUIRED)")
        return {
            "score": 0,
            "strength": "Invalid",
            "color": "red",
            "feedback": feedback,
            "valid": False
        }
    
    # Length bonus
    if len(password) >= 12:
        score += 20
    
    if len(password) >= 16:
        score += 10
    
    # REQUIRED: Character variety checks (all mandatory)
    has_uppercase = bool(re.search(r'[A-Z]', password))
    has_lowercase = bool(re.search(r'[a-z]', password))
    has_digit = bool(re.search(r'\d', password))
    has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;/~`]', password))
    
    # Check all requirements are met
    missing_requirements = []
    if not has_uppercase:
        missing_requirements.append("uppercase letter (A-Z)")
    if not has_lowercase:
        missing_requirements.append("lowercase letter (a-z)")
    if not has_digit:
        missing_requirements.append("number (0-9)")
    if not has_special:
        missing_requirements.append("special character (!@#$%^&* etc)")
    
    if missing_requirements:
        feedback.append(f"REQUIRED: Add {', '.join(missing_requirements)}")
        return {
            "score": 0,
            "strength": "Invalid",
            "color": "red",
            "feedback": feedback,
            "valid": False
        }
    
    # All requirements met, add points
    score += 15  # uppercase
    score += 15  # lowercase
    score += 15  # digit
    score += 15  # special
    
    # Complexity bonus
    if len(set(password)) >= 8:  # Unique characters
        score += 10
    
    # Common password penalty
    common_patterns = [
        r'password', r'123456', r'qwerty', r'admin', r'welcome',
        r'letmein', r'monkey', r'dragon'
    ]
    
    for pattern in common_patterns:
        if re.search(pattern, password.lower()):
            score -= 20
            feedback.append("Avoid common passwords")
            break
    
    # Sequential patterns penalty
    if re.search(r'(012|123|234|345|456|567|678|789|890)', password):
        score -= 10
        feedback.append("Avoid sequential numbers")
    
    if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
        score -= 10
        feedback.append("Avoid sequential letters")
    
    # Ensure score is between 0 and 100
    score = max(0, min(100, score))
    
    # Determine strength level
    if score >= 80:
        strength = "Very Strong"
        color = "green"
    elif score >= 60:
        strength = "Strong"
        color = "blue"
    elif score >= 40:
        strength = "Medium"
        color = "yellow"
    elif score >= 20:
        strength = "Weak"
        color = "orange"
    else:
        strength = "Very Weak"
        color = "red"
    
    return {
        "score": score,
        "strength": strength,
        "color": color,
        "feedback": feedback[:3] if feedback else ["Password meets all requirements"],
        "valid": True  # All requirements passed
    }

def is_account_locked(failed_attempts: int, last_failed_login: Optional[datetime]) -> bool:
    """Check if account is locked due to failed login attempts"""
    if failed_attempts < MAX_LOGIN_ATTEMPTS:
        return False
    
    if not last_failed_login:
        return False
    
    time_since_last_failure = datetime.now(timezone.utc) - last_failed_login
    return time_since_last_failure < LOCKOUT_DURATION

def get_lockout_remaining_time(last_failed_login: datetime) -> int:
    """Get remaining lockout time in minutes"""
    if not last_failed_login:
        return 0
    
    time_since_failure = datetime.now(timezone.utc) - last_failed_login
    remaining = LOCKOUT_DURATION - time_since_failure
    
    if remaining.total_seconds() <= 0:
        return 0
    
    return int(remaining.total_seconds() / 60)

def sanitize_input(text: str) -> str:
    """Basic input sanitization to prevent XSS"""
    if not text:
        return text
    
    # Remove potential HTML/script tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove potential JavaScript
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    
    # Remove potential SQL injection patterns
    dangerous_patterns = [
        r'(\bor\b|\band\b)\s+\d+\s*=\s*\d+',
        r'union\s+select',
        r'drop\s+table',
        r'delete\s+from',
        r'insert\s+into'
    ]
    
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text.strip()

def validate_file_upload(filename: str, file_size: int, allowed_extensions: list = None) -> bool:
    """Validate file upload"""
    if allowed_extensions is None:
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    
    # Check file extension
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
    if f'.{file_ext}' not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Check file size (5MB limit)
    max_size = 5 * 1024 * 1024  # 5MB
    if file_size > max_size:
        raise HTTPException(
            status_code=400, 
            detail="File size too large. Maximum size is 5MB"
        )
    
    return True

# Rate limiting decorators
def rate_limit_auth(request: Request):
    """Rate limit for authentication endpoints"""
    return limiter.limit("5/minute")(lambda: None)()

def rate_limit_api(request: Request):
    """Rate limit for general API endpoints"""
    return limiter.limit("100/minute")(lambda: None)()

def rate_limit_upload(request: Request):
    """Rate limit for upload endpoints"""
    return limiter.limit("10/minute")(lambda: None)()
