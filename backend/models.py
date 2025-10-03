from pydantic import BaseModel, Field, EmailStr, validator, root_validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone
import uuid
import re

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    role: str  # "Student", "Professional", "Other" - MANDATORY
    student_level: str  # "undergraduate", "graduate", "high_school"
    university: Optional[str] = None  # For campus integration
    skills: List[str] = []

    @validator('skills')
    def validate_skills(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one skill is required')
        
        # Check if all skills are valid (not empty)
        valid_skills = [skill.strip() for skill in v if skill.strip()]
        if len(valid_skills) == 0:
            raise ValueError('At least one valid skill is required')
        
        return valid_skills
    availability_hours: int = 10  # hours per week
    location: str  # MANDATORY - cannot be empty, must be valid location format
    bio: Optional[str] = None
    avatar: str = "boy"  # MANDATORY - avatar selection (boy, man, girl, woman, grandfather, grandmother)
    profile_photo: Optional[str] = None  # Keep for backward compatibility
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_earnings: float = 0.0
    net_savings: float = 0.0
    current_streak: int = 0
    last_activity_date: Optional[datetime] = None
    
    # Gamification fields
    badges: List[Dict[str, Any]] = []
    achievement_points: int = 0
    level: int = 1
    experience_points: int = 0
    title: str = "Beginner"  # e.g., "Savings Champion", "Budget Master"
    
    # Community features
    achievements_shared: int = 0  # Count of achievements shared
    community_rank: Optional[int] = None
    campus_rank: Optional[int] = None
    email_verified: bool = False
    is_active: bool = True
    is_admin: bool = False
    failed_login_attempts: int = 0
    last_failed_login: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    @validator('role')
    def validate_role(cls, v):
        allowed_roles = ["Student", "Professional", "Other"]
        if v not in allowed_roles:
            raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v
    
    @validator('location')
    def validate_location(cls, v):
        if not v or not v.strip():
            raise ValueError('Location is required and cannot be empty')
        
        # Basic location format validation (City, State or City, Country)
        v = v.strip()
        if len(v) < 3:
            raise ValueError('Location must be at least 3 characters long')
        
        # Check for basic city, state/country format
        if ',' not in v and len(v.split()) < 2:
            raise ValueError('Location should include city and state/country (e.g., "Mumbai, Maharashtra" or "New York, USA")')
        
        return v

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str  # MANDATORY
    student_level: str
    university: Optional[str] = None  # For campus integration
    skills: List[str] = []
    availability_hours: int = 10
    location: str  # MANDATORY
    bio: Optional[str] = None
    avatar: str = "boy"  # MANDATORY - avatar selection

    @validator('role')
    def validate_role(cls, v):
        allowed_roles = ["Student", "Professional", "Other"]
        if v not in allowed_roles:
            raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v
    
    @validator('location')
    def validate_location(cls, v):
        if not v or not v.strip():
            raise ValueError('Location is required and cannot be empty')
        
        # Basic location format validation (City, State or City, Country)
        v = v.strip()
        if len(v) < 3:
            raise ValueError('Location must be at least 3 characters long')
        
        # Check for basic city, state/country format
        if ',' not in v and len(v.split()) < 2:
            raise ValueError('Location should include city and state/country (e.g., "Mumbai, Maharashtra" or "New York, USA")')
        
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        # Check for common passwords
        common_passwords = [
            'password', '12345678', 'password123', 'admin123', 'welcome123',
            'qwerty123', '123456789', 'letmein123', 'password1', 'admin1234'
        ]
        if v.lower() in common_passwords:
            raise ValueError('Password is too common. Please choose a stronger password')
        
        return v

    @validator('full_name')
    def validate_full_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters long')
        if not re.match(r'^[a-zA-Z\s.]+$', v):
            raise ValueError('Full name can only contain letters, spaces, and periods')
        return v.strip()

    @validator('skills')
    def validate_skills(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one skill is required')
        
        # Check if all skills are valid (not empty)
        valid_skills = [skill.strip() for skill in v if skill.strip()]
        if len(valid_skills) == 0:
            raise ValueError('At least one valid skill is required')
        
        return valid_skills

    @validator('bio')
    def validate_bio(cls, v):
        if v and len(v) > 500:
            raise ValueError('Bio cannot exceed 500 characters')
        return v

    @validator('skills')
    def validate_skills(cls, v):
        if len(v) > 20:
            raise ValueError('Cannot have more than 20 skills')
        cleaned_skills = []
        for skill in v:
            cleaned = skill.strip()
            if cleaned and len(cleaned) <= 50:
                cleaned_skills.append(cleaned)
        return cleaned_skills

    @validator('avatar')
    def validate_avatar(cls, v):
        allowed_avatars = ["boy", "man", "girl", "woman", "grandfather", "grandmother"]
        if v not in allowed_avatars:
            raise ValueError(f'Avatar must be one of: {", ".join(allowed_avatars)}')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    skills: Optional[List[str]] = None
    availability_hours: Optional[int] = None 
    location: Optional[str] = None
    bio: Optional[str] = None
    student_level: Optional[str] = None
    avatar: Optional[str] = None

    @validator('role')
    def validate_role(cls, v):
        if v is not None:
            allowed_roles = ["Student", "Professional", "Other"]
            if v not in allowed_roles:
                raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v
    
    @validator('location') 
    def validate_location(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Location cannot be empty')
            v = v.strip()
            if len(v) < 3:
                raise ValueError('Location must be at least 3 characters long')
            if ',' not in v and len(v.split()) < 2:
                raise ValueError('Location should include city and state/country (e.g., "Mumbai, Maharashtra" or "New York, USA")')
        return v

    @validator('full_name')
    def validate_full_name(cls, v):
        if v is not None:
            if len(v.strip()) < 2:
                raise ValueError('Full name must be at least 2 characters long')
            if not re.match(r'^[a-zA-Z\s.]+$', v):
                raise ValueError('Full name can only contain letters, spaces, and periods')
            return v.strip()
        return v


class EmailVerificationRequest(BaseModel):
    email: EmailStr

class EmailVerificationConfirm(BaseModel):
    email: EmailStr
    verification_code: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    email: EmailStr
    reset_code: str
    new_password: str

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v

class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str  # "income" or "expense"
    amount: float
    category: str
    description: str
    source: Optional[str] = None  # for income: "hustle", "part_time", "scholarship", etc.
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_hustle_related: bool = False

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        if v > 10000000:  # 1 crore limit
            raise ValueError('Amount cannot exceed ₹1,00,00,000')
        return round(v, 2)

    @validator('description')
    def validate_description(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Description must be at least 3 characters long')
        if len(v) > 200:
            raise ValueError('Description cannot exceed 200 characters')
        return v.strip()

class TransactionCreate(BaseModel):
    type: str
    amount: float
    category: str
    description: str
    source: Optional[str] = None
    is_hustle_related: bool = False

    @validator('type')
    def validate_type(cls, v):
        if v not in ['income', 'expense']:
            raise ValueError('Type must be either "income" or "expense"')
        return v

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        if v > 10000000:  # 1 crore limit
            raise ValueError('Amount cannot exceed ₹1,00,00,000')
        return round(v, 2)

class ContactInfo(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    
    @validator('email')
    def validate_email(cls, v):
        if v:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                raise ValueError('Invalid email format')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v:
            phone_pattern = r'^[\+]?[1-9][\d]{3,14}$'
            if not re.match(phone_pattern, v):
                raise ValueError('Invalid phone number format')
        return v
    
    @validator('website')
    def validate_website(cls, v):
        if v:
            url_pattern = r'^https?://[^\s]+$'
            if not re.match(url_pattern, v):
                raise ValueError('Invalid website URL format')
        return v
    
    @validator('linkedin')
    def validate_linkedin(cls, v):
        if v:
            linkedin_pattern = r'^https?://[^\s]*linkedin\.com[^\s]*$'
            if not re.match(linkedin_pattern, v):
                raise ValueError('Invalid LinkedIn URL format')
        return v

class LocationInfo(BaseModel):
    area: str
    city: str
    state: str
    
    @validator('area', 'city', 'state')
    def validate_location_fields(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('All location fields must be at least 2 characters long')
        return v.strip()

class UserHustle(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_by: str  # user_id
    title: str
    description: str
    category: str  # "tutoring", "freelance", "content_creation", "delivery", "micro_tasks"
    pay_rate: float
    pay_type: str  # "hourly", "fixed", "per_task"
    time_commitment: str
    required_skills: List[str]
    difficulty_level: str  # "beginner", "intermediate", "advanced"
    location: Optional[LocationInfo] = None
    is_remote: bool = True
    contact_info: ContactInfo
    application_deadline: Optional[datetime] = None
    max_applicants: Optional[int] = None
    status: str = "active"  # "active", "closed", "completed"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    applicants: List[str] = []  # user_ids who applied
    is_admin_posted: bool = False

    @validator('pay_rate')
    def validate_pay_rate(cls, v):
        if v <= 0:
            raise ValueError('Pay rate must be greater than 0')
        if v > 100000:  # 1 lakh per hour/task limit
            raise ValueError('Pay rate cannot exceed ₹1,00,000')
        return round(v, 2)

    @root_validator(skip_on_failure=True)
    def validate_contact_info(cls, values):
        contact_info = values.get('contact_info')
        if isinstance(contact_info, dict):
            contact_info = ContactInfo(**contact_info)
        
        # At least one contact method must be provided
        if not any([contact_info.email, contact_info.phone, contact_info.website, contact_info.linkedin]):
            raise ValueError('At least one contact method must be provided')
        return values

class UserHustleCreate(BaseModel):
    title: str
    description: str
    category: str
    pay_rate: float
    pay_type: str
    time_commitment: str
    required_skills: List[str]
    difficulty_level: str
    location: Optional[Union[str, LocationInfo]] = None
    is_remote: bool = True
    contact_info: Union[str, ContactInfo]
    application_deadline: Optional[datetime] = None
    max_applicants: Optional[int] = None

    @root_validator(pre=True)
    def parse_flexible_inputs(cls, values):
        """Convert string inputs to structured objects"""
        
        # Handle contact_info - accept string or object
        contact_info = values.get('contact_info')
        if isinstance(contact_info, str) and contact_info:
            # Parse string into ContactInfo object
            contact_obj = {}
            contact_str = contact_info.strip()
            
            # Email pattern
            if '@' in contact_str and '.' in contact_str:
                contact_obj['email'] = contact_str
            # Phone pattern (accept various formats)
            elif any(char.isdigit() for char in contact_str):
                # Clean phone number - remove spaces, dashes, parentheses, plus signs
                clean_phone = re.sub(r'[\s\-\(\)\+]', '', contact_str)
                # Convert to expected format (e.g., +91-xxx becomes 91xxx)
                if clean_phone.startswith('91') and len(clean_phone) >= 10:
                    contact_obj['phone'] = clean_phone
                elif len(clean_phone) >= 10:
                    contact_obj['phone'] = clean_phone
            # Website pattern
            elif contact_str.startswith(('http://', 'https://')):
                contact_obj['website'] = contact_str
            else:
                # Default to email if it contains @, otherwise phone
                if '@' in contact_str:
                    contact_obj['email'] = contact_str
                else:
                    contact_obj['phone'] = contact_str
                    
            values['contact_info'] = contact_obj
        
        # Handle location - accept string or object  
        location = values.get('location')
        if isinstance(location, str) and location:
            location_str = location.strip()
            # Simple parsing - split by comma if available
            if ',' in location_str:
                parts = [p.strip() for p in location_str.split(',')]
                if len(parts) >= 2:
                    values['location'] = {
                        'area': parts[0],
                        'city': parts[0], 
                        'state': parts[-1]
                    }
                else:
                    values['location'] = {
                        'area': location_str,
                        'city': location_str,
                        'state': location_str
                    }
            else:
                # Single string - use as all fields
                values['location'] = {
                    'area': location_str,
                    'city': location_str, 
                    'state': location_str
                }
        elif location == '':
            values['location'] = None
            
        return values

    @validator('title')
    def validate_title(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('Title must be at least 5 characters long')
        if len(v) > 100:
            raise ValueError('Title cannot exceed 100 characters')
        return v.strip()

    @validator('description')  
    def validate_description(cls, v):
        if len(v.strip()) < 20:
            raise ValueError('Description must be at least 20 characters long')
        if len(v) > 1000:
            raise ValueError('Description cannot exceed 1000 characters')
        return v.strip()

class UserHustleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    pay_rate: Optional[float] = None
    pay_type: Optional[str] = None
    time_commitment: Optional[str] = None
    required_skills: Optional[List[str]] = None
    difficulty_level: Optional[str] = None
    location: Optional[Union[str, LocationInfo]] = None
    is_remote: Optional[bool] = None
    contact_info: Optional[Union[str, ContactInfo]] = None
    application_deadline: Optional[datetime] = None
    max_applicants: Optional[int] = None
    status: Optional[str] = None

    @root_validator(pre=True)
    def parse_flexible_inputs(cls, values):
        """Convert string inputs to structured objects"""
        
        # Handle contact_info - accept string or object
        contact_info = values.get('contact_info')
        if isinstance(contact_info, str) and contact_info:
            # Parse string into ContactInfo object
            contact_obj = {}
            contact_str = contact_info.strip()
            
            # Email pattern
            if '@' in contact_str and '.' in contact_str:
                contact_obj['email'] = contact_str
            # Phone pattern (accept various formats)
            elif any(char.isdigit() for char in contact_str):
                # Clean phone number - remove spaces, dashes, parentheses, plus signs
                clean_phone = re.sub(r'[\s\-\(\)\+]', '', contact_str)
                # Convert to expected format (e.g., +91-xxx becomes 91xxx)
                if clean_phone.startswith('91') and len(clean_phone) >= 10:
                    contact_obj['phone'] = clean_phone
                elif len(clean_phone) >= 10:
                    contact_obj['phone'] = clean_phone
            # Website pattern
            elif contact_str.startswith(('http://', 'https://')):
                contact_obj['website'] = contact_str
            else:
                # Default to email if it contains @, otherwise phone
                if '@' in contact_str:
                    contact_obj['email'] = contact_str
                else:
                    contact_obj['phone'] = contact_str
                    
            values['contact_info'] = contact_obj
        elif contact_info == '':
            values['contact_info'] = None
        
        # Handle location - accept string or object  
        location = values.get('location')
        if isinstance(location, str) and location:
            location_str = location.strip()
            # Simple parsing - split by comma if available
            if ',' in location_str:
                parts = [p.strip() for p in location_str.split(',')]
                if len(parts) >= 2:
                    values['location'] = {
                        'area': parts[0],
                        'city': parts[0], 
                        'state': parts[-1]
                    }
                else:
                    values['location'] = {
                        'area': location_str,
                        'city': location_str,
                        'state': location_str
                    }
            else:
                # Single string - use as all fields
                values['location'] = {
                    'area': location_str,
                    'city': location_str, 
                    'state': location_str
                }
        elif location == '':
            values['location'] = None
            
        return values

    @validator('title')
    def validate_title(cls, v):
        if v and len(v.strip()) < 5:
            raise ValueError('Title must be at least 5 characters long')
        if v and len(v) > 100:
            raise ValueError('Title cannot exceed 100 characters')
        return v.strip() if v else v

    @validator('description')
    def validate_description(cls, v):
        if v and len(v.strip()) < 20:
            raise ValueError('Description must be at least 20 characters long')
        if v and len(v) > 1000:
            raise ValueError('Description cannot exceed 1000 characters')
        return v.strip() if v else v

class HustleApplication(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hustle_id: str
    applicant_id: str
    applicant_name: str
    applicant_email: str
    cover_message: str
    applied_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "pending"  # "pending", "accepted", "rejected"

class HustleApplicationCreate(BaseModel):
    cover_message: str

    @validator('cover_message')
    def validate_cover_message(cls, v):
        if len(v.strip()) < 20:
            raise ValueError('Cover message must be at least 20 characters long')
        if len(v) > 500:
            raise ValueError('Cover message cannot exceed 500 characters')
        return v.strip()

class HustleOpportunity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    category: str  # "tutoring", "freelance", "content_creation", "delivery", "micro_tasks"
    estimated_pay: float
    time_commitment: str
    required_skills: List[str]
    difficulty_level: str  # "beginner", "intermediate", "advanced"
    platform: str
    application_link: Optional[str] = None
    ai_recommended: bool = False
    match_score: float = 0.0

class Budget(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    category: str
    allocated_amount: float
    spent_amount: float = 0.0
    month: str  # "2024-01"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @validator('allocated_amount')
    def validate_allocated_amount(cls, v):
        if v <= 0:
            raise ValueError('Allocated amount must be greater than 0')
        if v > 10000000:  # 1 crore limit
            raise ValueError('Allocated amount cannot exceed ₹1,00,00,000')
        return round(v, 2)

class BudgetCreate(BaseModel):
    category: str
    allocated_amount: float
    month: str

    @validator('category')
    def validate_category(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Category must be at least 2 characters long')
        return v.strip()

class BudgetUpdate(BaseModel):
    category: Optional[str] = None
    allocated_amount: Optional[float] = None
    month: Optional[str] = None

    @validator('category')
    def validate_category(cls, v):
        if v is not None:
            if len(v.strip()) < 2:
                raise ValueError('Category must be at least 2 characters long')
            return v.strip()
        return v

    @validator('allocated_amount')
    def validate_amount(cls, v):
        if v is not None:
            if v <= 0:
                raise ValueError('Allocated amount must be greater than 0')
            if v > 10000000:  # 1 crore limit
                raise ValueError('Allocated amount cannot exceed ₹1,00,00,000')
            return round(v, 2)
        return v

class AdminHustleCreate(BaseModel):
    title: str
    description: str
    category: str
    estimated_pay: float
    time_commitment: str
    required_skills: List[str]
    difficulty_level: str
    platform: str
    application_link: Optional[str] = None

    @validator('application_link')
    def validate_application_link(cls, v):
        if v:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            phone_pattern = r'^[\+]?[1-9][\d]{3,14}$'
            url_pattern = r'^https?://[^\s]+$'
            
            if not (re.match(email_pattern, v) or re.match(phone_pattern, v) or re.match(url_pattern, v)):
                raise ValueError('Application link must be a valid email, phone number, or website URL')
        return v

# Financial Goals Models
class FinancialGoal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    category: str  # "emergency_fund", "monthly_income", "graduation", "custom"
    target_amount: float = Field(gt=0, le=50000000)  # Up to ₹5 crores
    current_amount: float = Field(default=0.0, ge=0)
    description: Optional[str] = None
    target_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_completed: bool = False
    
    @validator('category')
    def validate_category(cls, v):
        allowed_categories = ["emergency_fund", "monthly_income", "graduation", "custom"]
        if v not in allowed_categories:
            raise ValueError(f'Category must be one of: {", ".join(allowed_categories)}')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Goal name is required')
        if len(v.strip()) > 100:
            raise ValueError('Goal name must be less than 100 characters')
        return v.strip()

class FinancialGoalCreate(BaseModel):
    name: str
    category: str
    target_amount: float = Field(gt=0, le=50000000)
    current_amount: float = Field(default=0.0, ge=0)
    description: Optional[str] = None
    target_date: Optional[datetime] = None
    
    @validator('category')
    def validate_category(cls, v):
        allowed_categories = ["emergency_fund", "monthly_income", "graduation", "custom"]
        if v not in allowed_categories:
            raise ValueError(f'Category must be one of: {", ".join(allowed_categories)}')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Goal name is required')
        if len(v.strip()) > 100:
            raise ValueError('Goal name must be less than 100 characters')
        return v.strip()

class FinancialGoalUpdate(BaseModel):
    name: Optional[str] = None
    target_amount: Optional[float] = Field(None, gt=0, le=50000000)
    current_amount: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    target_date: Optional[datetime] = None
    is_completed: Optional[bool] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Goal name cannot be empty')
            if len(v.strip()) > 100:
                raise ValueError('Goal name must be less than 100 characters')
            return v.strip()
        return v

# Category Suggestions Models
class CategorySuggestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str
    name: str
    url: str
    logo_url: Optional[str] = None
    description: Optional[str] = None
    rating: Optional[float] = None
    offers: Optional[str] = None
    cashback: Optional[str] = None
    type: str  # "app", "website", "both"
    is_active: bool = True
    priority: int = 0  # Higher number = higher priority
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EmergencyType(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    icon: str
    description: str
    urgency_level: str  # "high", "medium", "low"

class Hospital(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    address: str
    city: str
    state: str
    phone: str
    emergency_phone: Optional[str] = None
    latitude: float
    longitude: float
    rating: Optional[float] = None
    specialties: List[str] = []
    is_emergency: bool = True
    is_24x7: bool = True
    type: str  # "government", "private", "clinic"

class ClickAnalytics(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    category: str
    suggestion_name: str
    suggestion_url: str
    clicked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_location: Optional[str] = None
    session_id: Optional[str] = None

class ClickAnalyticsCreate(BaseModel):
    category: str
    suggestion_name: str
    suggestion_url: str
    user_location: Optional[str] = None
    session_id: Optional[str] = None

class PriceComparisonQuery(BaseModel):
    product_name: str
    category: str = "Shopping"
    budget_range: Optional[str] = None  # "under_1000", "1000_5000", "5000_above"

# Advanced Income Tracking System Models

class AutoImportSource(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    source_type: str  # "email", "sms"
    provider: str  # "gmail", "outlook", "sms_provider"
    source_name: str  # User-friendly name
    is_active: bool = True
    last_sync: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('source_type')
    def validate_source_type(cls, v):
        allowed_types = ["email", "sms"]
        if v not in allowed_types:
            raise ValueError(f'Source type must be one of: {", ".join(allowed_types)}')
        return v

class AutoImportSourceCreate(BaseModel):
    source_type: str
    provider: str
    source_name: str
    
    @validator('source_type')
    def validate_source_type(cls, v):
        allowed_types = ["email", "sms"]
        if v not in allowed_types:
            raise ValueError(f'Source type must be one of: {", ".join(allowed_types)}')
        return v

class ParsedTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    source_id: Optional[str] = None  # Reference to AutoImportSource
    original_content: str  # Raw SMS/Email content
    parsed_data: Dict[str, Any]  # AI extracted data
    confidence_score: float = Field(ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TransactionSuggestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    parsed_transaction_id: str
    suggested_type: str  # "income" or "expense"
    suggested_amount: float
    suggested_category: str
    suggested_description: str
    suggested_source: Optional[str] = None  # For income: "freelance", "salary", "scholarship", "investment", "part_time"
    confidence_score: float = Field(ge=0.0, le=1.0)
    status: str = "pending"  # "pending", "approved", "rejected"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: Optional[datetime] = None
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ["pending", "approved", "rejected"]
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v
        
    @validator('suggested_type')
    def validate_suggested_type(cls, v):
        if v not in ['income', 'expense']:
            raise ValueError('Suggested type must be either "income" or "expense"')
        return v

class TransactionSuggestionCreate(BaseModel):
    parsed_transaction_id: str
    suggested_type: str
    suggested_amount: float
    suggested_category: str
    suggested_description: str
    suggested_source: Optional[str] = None
    confidence_score: float = Field(ge=0.0, le=1.0)
    
    @validator('suggested_type')
    def validate_suggested_type(cls, v):
        if v not in ['income', 'expense']:
            raise ValueError('Suggested type must be either "income" or "expense"')
        return v

class LearningFeedback(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    suggestion_id: str
    original_suggestion: Dict[str, Any]  # Original AI suggestion
    user_correction: Dict[str, Any]  # User's correction
    feedback_type: str  # "correction", "approval", "rejection"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('feedback_type')
    def validate_feedback_type(cls, v):
        allowed_types = ["correction", "approval", "rejection"]
        if v not in allowed_types:
            raise ValueError(f'Feedback type must be one of: {", ".join(allowed_types)}')
        return v

class LearningFeedbackCreate(BaseModel):
    suggestion_id: str
    original_suggestion: Dict[str, Any]
    user_correction: Dict[str, Any]
    feedback_type: str
    
    @validator('feedback_type')
    def validate_feedback_type(cls, v):
        allowed_types = ["correction", "approval", "rejection"]
        if v not in allowed_types:
            raise ValueError(f'Feedback type must be one of: {", ".join(allowed_types)}')
        return v

class ContentParseRequest(BaseModel):
    content: str
    content_type: str  # "sms", "email"
    
    @validator('content_type')
    def validate_content_type(cls, v):
        allowed_types = ["sms", "email"]
        if v not in allowed_types:
            raise ValueError(f'Content type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('content')
    def validate_content(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Content must be at least 10 characters long')
        if len(v) > 5000:
            raise ValueError('Content cannot exceed 5000 characters')
        return v.strip()

class SuggestionApprovalRequest(BaseModel):
    suggestion_id: str
    approved: bool
    corrections: Optional[Dict[str, Any]] = None  # If user wants to modify before approving

# ===== GAMIFICATION & VIRAL FEATURES MODELS =====

class Badge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    category: str  # "financial", "behavioral", "social", "side_hustle"
    icon: str  # emoji or icon code
    rarity: str  # "bronze", "silver", "gold", "platinum", "legendary"
    requirement_type: str  # "amount_saved", "streak_days", "goals_completed", "hustles_completed", etc.
    requirement_value: float  # threshold value to earn badge
    points_awarded: int  # experience points awarded when badge is earned
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    
    @validator('category')
    def validate_category(cls, v):
        allowed_categories = ["financial", "behavioral", "social", "side_hustle"]
        if v not in allowed_categories:
            raise ValueError(f'Badge category must be one of: {", ".join(allowed_categories)}')
        return v
    
    @validator('rarity')
    def validate_rarity(cls, v):
        allowed_rarities = ["bronze", "silver", "gold", "platinum", "legendary"]
        if v not in allowed_rarities:
            raise ValueError(f'Badge rarity must be one of: {", ".join(allowed_rarities)}')
        return v

class UserBadge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    badge_id: str
    earned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    progress_when_earned: Dict[str, Any]  # user stats when badge was earned
    is_showcased: bool = False  # whether user displays this badge prominently
    shared_count: int = 0  # how many times user shared this achievement

class Achievement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str  # "badge_earned", "milestone_reached", "streak_achieved", "goal_completed"
    title: str
    description: str
    icon: str
    achievement_data: Dict[str, Any]  # specific achievement details
    points_earned: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_shared: bool = False
    reaction_count: int = 0  # likes/reactions from community

class CommunityPost(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str  # "achievement_share", "tip_share", "milestone_celebration"
    content: str
    achievement_id: Optional[str] = None  # if sharing an achievement
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    is_featured: bool = False  # admin can feature posts

class CommunityInteraction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # user who made the interaction
    target_user_id: str  # user who owns the content
    post_id: Optional[str] = None
    achievement_id: Optional[str] = None
    interaction_type: str  # "like", "comment", "share", "congratulate"
    comment_text: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Leaderboard(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    leaderboard_type: str  # "savings", "streak", "goals", "side_hustles", "points"
    period: str  # "weekly", "monthly", "all_time"
    university: Optional[str] = None  # for campus-specific leaderboards
    rank: int
    score: float  # the value being ranked on
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('leaderboard_type')
    def validate_leaderboard_type(cls, v):
        allowed_types = ["savings", "streak", "goals", "side_hustles", "points"]
        if v not in allowed_types:
            raise ValueError(f'Leaderboard type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('period')
    def validate_period(cls, v):
        allowed_periods = ["weekly", "monthly", "all_time"]
        if v not in allowed_periods:
            raise ValueError(f'Period must be one of: {", ".join(allowed_periods)}')
        return v

class Challenge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    challenge_type: str  # "savings", "streak", "goals", "community"
    target_value: float  # e.g., save ₹5000, maintain 30-day streak
    duration_days: int  # how long the challenge runs
    start_date: datetime
    end_date: datetime
    reward_description: str
    reward_points: int
    max_participants: Optional[int] = None
    is_campus_specific: bool = False
    university: Optional[str] = None
    created_by: str  # admin user ID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    participant_count: int = 0

class ChallengeParticipant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    challenge_id: str
    user_id: str
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    current_progress: float = 0.0
    is_completed: bool = False
    completion_date: Optional[datetime] = None
    rank: Optional[int] = None  # final rank if challenge is completed

class University(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    short_name: str  # e.g., "IIT-B", "DU", "MIT"
    location: str
    type: str  # "university", "college", "institute"
    is_verified: bool = False  # admin-verified institutions
    student_count: int = 0  # number of registered students
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Request/Response Models for Gamification

class BadgeCreate(BaseModel):
    name: str
    description: str
    category: str
    icon: str
    rarity: str
    requirement_type: str
    requirement_value: float
    points_awarded: int
    
    @validator('category')
    def validate_category(cls, v):
        allowed_categories = ["financial", "behavioral", "social", "side_hustle"]
        if v not in allowed_categories:
            raise ValueError(f'Badge category must be one of: {", ".join(allowed_categories)}')
        return v

class LeaderboardResponse(BaseModel):
    leaderboard_type: str
    period: str
    university: Optional[str] = None
    rankings: List[Dict[str, Any]]  # list of user rankings with details
    user_rank: Optional[int] = None  # current user's rank in this leaderboard
    total_participants: int

class ChallengeCreate(BaseModel):
    title: str
    description: str
    challenge_type: str
    target_value: float
    duration_days: int
    reward_description: str
    reward_points: int
    max_participants: Optional[int] = None
    is_campus_specific: bool = False
    university: Optional[str] = None

class ChallengeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    target_value: Optional[float] = None
    duration_days: Optional[int] = None
    reward_description: Optional[str] = None
    reward_points: Optional[int] = None
    max_participants: Optional[int] = None
    is_campus_specific: Optional[bool] = None
    university: Optional[str] = None

class ChallengeReject(BaseModel):
    rejection_reason: str = Field(..., min_length=10, max_length=500)

class CommunityPostCreate(BaseModel):
    type: str
    content: str
    achievement_id: Optional[str] = None
    image_url: Optional[str] = None

class UniversityCreate(BaseModel):
    name: str
    short_name: str
    location: str
    type: str = "university"

# ===== REFERRAL SYSTEM WITH MONETARY INCENTIVES MODELS =====

class ReferralProgram(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    referrer_id: str
    referral_code: str  # unique code for sharing
    total_referrals: int = 0  # total people who signed up
    successful_referrals: int = 0  # people who stayed active for 30+ days
    total_earnings: float = 0.0  # total money earned from referrals
    pending_earnings: float = 0.0  # earnings waiting to be confirmed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

class ReferredUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    referrer_id: str  # who referred them
    referred_user_id: str  # the new user
    referral_code: str
    status: str = "pending"  # "pending", "completed", "inactive"
    signed_up_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None  # when they became "active" (30 days)
    earnings_awarded: float = 0.0  # how much referrer earned from this user
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ["pending", "completed", "inactive"]
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v

class ReferralEarning(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    referrer_id: str
    referred_user_id: str
    earning_type: str  # "signup_bonus", "activity_bonus", "milestone_bonus"
    amount: float
    description: str
    status: str = "pending"  # "pending", "confirmed", "paid"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confirmed_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    
    @validator('earning_type')
    def validate_earning_type(cls, v):
        allowed_types = ["signup_bonus", "activity_bonus", "milestone_bonus"]
        if v not in allowed_types:
            raise ValueError(f'Earning type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ["pending", "confirmed", "paid"]
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v

class CampusAmbassador(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    university: str
    status: str = "active"  # "active", "inactive", "suspended"
    appointed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_referrals: int = 0
    monthly_target: int = 20  # target referrals per month
    bonus_rate: float = 0.15  # 15% bonus on referral earnings
    special_perks: List[str] = []  # ["exclusive_badges", "early_features", "direct_support"]
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ["active", "inactive", "suspended"]
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v

class ViralChallenge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    challenge_type: str = "referral_based"  # "referral_based", "social_sharing", "campus_competition"
    target_referrals: int  # number of referrals needed to win
    reward_amount: float  # monetary reward for winner
    reward_description: str
    start_date: datetime
    end_date: datetime
    university_specific: bool = False
    university: Optional[str] = None
    created_by: str  # admin user ID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    participant_count: int = 0

class ViralChallengeParticipant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    challenge_id: str
    user_id: str
    current_referrals: int = 0
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_winner: bool = False
    reward_claimed: bool = False

# Request Models for Referral System
class ReferralSignupRequest(BaseModel):
    referral_code: str
    new_user_id: str

class EarningClaimRequest(BaseModel):
    earning_ids: List[str]  # list of earning IDs to claim

class CampusAmbassadorApplicationRequest(BaseModel):
    university: str
    motivation: str  # why they want to be an ambassador
    previous_experience: Optional[str] = None
    social_media_handles: Optional[Dict[str, str]] = None

# ===== SOCIAL SHARING SYSTEM MODELS =====

class SocialShare(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    platform: str  # "instagram", "whatsapp", "twitter", "facebook"
    achievement_type: str  # "savings_milestone", "streak_achievement", "badge_earned", etc.
    milestone_text: str
    image_filename: str
    amount: Optional[float] = None
    shared_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    engagement_count: int = 0  # likes, comments, shares from platform
    
    @validator('platform')
    def validate_platform(cls, v):
        allowed_platforms = ["instagram", "whatsapp", "twitter", "facebook", "snapchat"]
        if v not in allowed_platforms:
            raise ValueError(f'Platform must be one of: {", ".join(allowed_platforms)}')
        return v

class AchievementImageRequest(BaseModel):
    achievement_type: str
    milestone_text: str
    amount: Optional[float] = None

class MilestoneImageRequest(BaseModel):
    milestone_type: str  # "savings", "streak", "goal", "budget"
    achievement_text: str
    stats: Dict[str, Any]

class SocialShareRequest(BaseModel):
    platform: str
    achievement_type: str
    milestone_text: str
    image_filename: str
    amount: Optional[float] = None

# ===== FRIEND NETWORK & CAMPUS CHALLENGES SYSTEM MODELS =====

class FriendInvitation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    inviter_id: str
    invitee_email: Optional[str] = None
    invitee_phone: Optional[str] = None
    referral_code: str
    status: str = "pending"  # "pending", "accepted", "expired"
    invited_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    accepted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ["pending", "accepted", "expired"]
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v

class Friendship(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user1_id: str
    user2_id: str
    status: str = "active"  # "active", "blocked", "removed"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    friendship_points: int = 0  # Points earned together through activities
    
    @validator('status')
    def validate_friendship_status(cls, v):
        allowed_statuses = ["active", "blocked", "removed"]
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v

class GroupChallenge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    challenge_type: str = "group_savings"  # "group_savings", "group_streak", "group_goals"
    target_amount_per_person: float  # Individual target amount
    group_target_amount: float  # Total group target
    duration_days: int
    min_participants: int = 3
    max_participants: int = 10
    university: Optional[str] = None  # Campus-specific if set
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    start_date: datetime
    end_date: datetime
    is_active: bool = True
    current_participants: int = 0
    reward_points_per_person: int = 100
    penalty_points: int = 50  # Points deducted if individual fails
    
    @validator('challenge_type')
    def validate_group_challenge_type(cls, v):
        allowed_types = ["group_savings", "group_streak", "group_goals"]
        if v not in allowed_types:
            raise ValueError(f'Group challenge type must be one of: {", ".join(allowed_types)}')
        return v

class GroupChallengeParticipant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    group_challenge_id: str
    user_id: str
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    individual_target: float
    current_progress: float = 0.0
    is_completed: bool = False
    completion_date: Optional[datetime] = None
    points_earned: int = 0
    penalty_applied: bool = False

class InAppNotification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    notification_type: str  # "friend_joined", "challenge_invite", "milestone_achieved", "group_progress"
    title: str
    message: str
    action_url: Optional[str] = None
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    read_at: Optional[datetime] = None
    related_id: Optional[str] = None  # ID of related entity (friend, challenge, etc.)
    
    @validator('notification_type')
    def validate_notification_type(cls, v):
        allowed_types = [
            "friend_joined", "friend_invited", "challenge_invite", "challenge_created",
            "milestone_achieved", "group_progress", "group_completed", "streak_reminder",
            "leaderboard_rank", "badge_earned", "welcome"
        ]
        if v not in allowed_types:
            raise ValueError(f'Notification type must be one of: {", ".join(allowed_types)}')
        return v

class UserInvitationStats(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    monthly_invites_sent: int = 0
    monthly_invites_limit: int = 15  # Default limit per month
    current_month: int = Field(default_factory=lambda: datetime.now(timezone.utc).month)
    current_year: int = Field(default_factory=lambda: datetime.now(timezone.utc).year)
    total_successful_invites: int = 0
    invitation_bonus_points: int = 0
    last_reset_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StreakNotificationPreference(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    notification_time_hour: int = 19  # Default 7 PM
    notification_time_minute: int = 0
    timezone: str = "Asia/Kolkata"
    is_enabled: bool = True
    reminder_after_missed_days: int = 1  # Send reminder after X missed days
    final_nudge_after_days: int = 7  # Send final reactivation after X days
    
    @validator('notification_time_hour')
    def validate_hour(cls, v):
        if not 0 <= v <= 23:
            raise ValueError('Hour must be between 0-23')
        return v
    
    @validator('notification_time_minute')
    def validate_minute(cls, v):
        if not 0 <= v <= 59:
            raise ValueError('Minute must be between 0-59')
        return v

# Request Models for Phase 1 Features

class FriendInviteRequest(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    
    @root_validator(skip_on_failure=True)
    def validate_contact_info(cls, values):
        email = values.get('email')
        phone = values.get('phone')
        if not email and not phone:
            raise ValueError('Either email or phone must be provided')
        return values

class GroupChallengeCreateRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=100)
    description: str = Field(..., min_length=10, max_length=500)
    challenge_type: str = "group_savings"
    target_amount_per_person: float = Field(..., gt=0, le=100000)  # Max ₹1 lakh per person
    duration_days: int = Field(..., ge=7, le=90)  # 1 week to 3 months
    max_participants: int = Field(..., ge=3, le=10)
    university_only: bool = False  # If true, restrict to user's university

class GroupChallengeJoinRequest(BaseModel):
    group_challenge_id: str

class NotificationPreferencesRequest(BaseModel):
    notification_time_hour: int = Field(..., ge=0, le=23)
    notification_time_minute: int = Field(..., ge=0, le=59)
    timezone: str = "Asia/Kolkata"
    reminder_after_missed_days: int = Field(..., ge=1, le=7)
    final_nudge_after_days: int = Field(..., ge=3, le=14)

# ===== PHASE 1: CORE ENGAGEMENT & FOMO MODELS =====

class IndividualChallenge(BaseModel):
    challenge_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    challenger_id: str
    challenged_id: str
    challenge_type: str  # "savings_race", "streak_battle", "expense_limit"
    title: str = Field(..., min_length=5, max_length=100)
    description: str = Field(..., max_length=500)
    target_amount: float = Field(default=0, ge=0)
    duration_days: int = Field(..., ge=1, le=30)  # 1 day to 1 month
    start_date: datetime
    end_date: datetime
    status: str = "pending"  # "pending", "active", "completed", "declined"
    challenger_progress: float = 0
    challenged_progress: float = 0
    winner: Optional[str] = None  # user_id of winner or "tie"
    stakes: str = "Bragging rights!"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('challenge_type')
    def validate_challenge_type(cls, v):
        allowed_types = ["savings_race", "streak_battle", "expense_limit"]
        if v not in allowed_types:
            raise ValueError(f'Challenge type must be one of: {", ".join(allowed_types)}')
        return v

class IndividualChallengeCreateRequest(BaseModel):
    friend_id: str
    challenge_type: str = "savings_race"
    title: str = Field(..., min_length=5, max_length=100)
    description: str = Field(..., max_length=500)
    target_amount: float = Field(default=1000, ge=0, le=50000)
    duration_days: int = Field(default=7, ge=1, le=30)
    stakes: str = "Bragging rights!"

class NotificationSchedule(BaseModel):
    schedule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    notification_type: str  # "daily_tip", "streak_reminder", "challenge_update"
    scheduled_time: str  # "09:00" format
    timezone: str = "Asia/Kolkata"
    is_active: bool = True
    last_sent: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('notification_type')
    def validate_notification_type(cls, v):
        allowed_types = ["daily_tip", "streak_reminder", "challenge_update", "peer_comparison"]
        if v not in allowed_types:
            raise ValueError(f'Notification type must be one of: {", ".join(allowed_types)}')
        return v

class CountdownAlert(BaseModel):
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    alert_type: str  # "flash_challenge", "daily_deadline", "weekend_special"
    title: str
    message: str
    deadline: datetime
    urgency: str  # "critical", "high", "medium", "low"
    reward: Optional[str] = None
    action: str
    action_url: str
    countdown_display: str = "live"  # "live", "slots", "progress"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('urgency')
    def validate_urgency(cls, v):
        allowed_urgencies = ["critical", "high", "medium", "low"]
        if v not in allowed_urgencies:
            raise ValueError(f'Urgency must be one of: {", ".join(allowed_urgencies)}')
        return v

class PeerComparisonMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    message_type: str  # "friend_outperforming", "university_activity", "streak_pressure"
    urgency: str  # "critical", "high", "medium", "low"
    title: str
    message: str
    call_to_action: str
    action_url: str
    social_pressure: int = Field(..., ge=0, le=10)  # 0-10 scale
    expires_at: datetime
    is_dismissed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DailyTipNotification(BaseModel):
    tip_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    date: str  # YYYY-MM-DD format
    tip_title: str
    tip_content: str
    tip_type: str = "tip"  # "tip" or "quote"
    icon: str = "💡"
    sent_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    viewed_at: Optional[datetime] = None
    notification_method: str = "push"  # "push", "in_app", "both"
    
    @validator('tip_type')
    def validate_tip_type(cls, v):
        allowed_types = ["tip", "quote"]
        if v not in allowed_types:
            raise ValueError(f'Tip type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('notification_method')
    def validate_notification_method(cls, v):
        allowed_methods = ["push", "in_app", "both"]
        if v not in allowed_methods:
            raise ValueError(f'Notification method must be one of: {", ".join(allowed_methods)}')
        return v

# Enhanced Push Notification Models
class PushSubscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    subscription_data: Dict[str, Any]  # WebPush subscription object
    device_type: str = "web"  # "web", "mobile", "desktop"
    browser_info: Optional[Dict[str, Any]] = None
    notification_preferences: Dict[str, bool] = {
        "friend_activities": True,
        "milestone_achievements": True,
        "streak_reminders": True,
        "daily_tips": True,
        "limited_offers": True,
        "challenge_updates": True
    }
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_used_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deactivated_at: Optional[datetime] = None

class PushSubscriptionCreate(BaseModel):
    subscription_data: Dict[str, Any]
    device_type: str = "web"
    browser_info: Optional[Dict[str, Any]] = None
    notification_preferences: Optional[Dict[str, bool]] = None

# Limited-Time Offers Models
class LimitedOffer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    offer_type: str  # "challenge", "premium_unlock", "referral_bonus", "early_access"
    title: str
    description: str
    offer_details: Dict[str, Any]
    # FOMO mechanics
    total_spots: Optional[int] = None  # "Only X spots left"
    spots_claimed: int = 0
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Eligibility criteria
    eligible_users: Optional[List[str]] = None  # Specific user IDs, None = all users
    min_level: Optional[int] = None
    min_streak: Optional[int] = None
    target_audience: str = "all"  # "all", "students", "professionals", "new_users"
    # Rewards
    reward_type: str  # "points", "badge", "premium_feature", "cash", "discount"
    reward_value: Union[int, float, str]
    # Status
    is_active: bool = True
    auto_activate: bool = False
    # Visual styling
    urgency_level: int = Field(..., ge=1, le=5)  # 1-5 scale for FOMO intensity
    color_scheme: str = "red"  # "red", "orange", "blue", "purple"
    icon: str = "🔥"
    
    @validator('offer_type')
    def validate_offer_type(cls, v):
        allowed_types = ["challenge", "premium_unlock", "referral_bonus", "early_access"]
        if v not in allowed_types:
            raise ValueError(f'Offer type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('target_audience')
    def validate_target_audience(cls, v):
        allowed_audiences = ["all", "students", "professionals", "new_users"]
        if v not in allowed_audiences:
            raise ValueError(f'Target audience must be one of: {", ".join(allowed_audiences)}')
        return v
    
    @validator('reward_type')
    def validate_reward_type(cls, v):
        allowed_types = ["points", "badge", "premium_feature", "cash", "discount"]
        if v not in allowed_types:
            raise ValueError(f'Reward type must be one of: {", ".join(allowed_types)}')
        return v

class LimitedOfferCreate(BaseModel):
    offer_type: str
    title: str
    description: str
    offer_details: Dict[str, Any]
    total_spots: Optional[int] = None
    expires_at: datetime
    eligible_users: Optional[List[str]] = None
    min_level: Optional[int] = None
    min_streak: Optional[int] = None
    target_audience: str = "all"
    reward_type: str
    reward_value: Union[int, float, str]
    urgency_level: int = Field(..., ge=1, le=5)
    color_scheme: str = "red"
    icon: str = "🔥"

class OfferParticipation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    offer_id: str
    status: str = "active"  # "active", "completed", "expired", "abandoned"
    progress: Dict[str, Any] = {}
    reward_claimed: bool = False
    participated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ["active", "completed", "expired", "abandoned"]
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v

# Photo Sharing for Achievements Models
class AchievementPhoto(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    achievement_id: str
    achievement_type: str  # "milestone", "badge", "goal_completion", "streak"
    photo_type: str = "custom"  # "custom", "branded_template", "combined"
    # Photo data
    original_photo_url: Optional[str] = None  # User uploaded photo
    branded_photo_url: Optional[str] = None   # Generated branded version
    final_photo_url: str  # Final shareable image
    # Photo metadata
    photo_metadata: Dict[str, Any] = {}
    caption: Optional[str] = None
    tags: List[str] = []
    # Privacy and sharing
    privacy_level: str = "public"  # "private", "friends", "public"
    shared_platforms: List[str] = []  # ["instagram", "whatsapp", "facebook", "twitter"]
    share_count: int = 0
    like_count: int = 0
    # Status
    status: str = "active"  # "active", "archived", "reported", "deleted"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('photo_type')
    def validate_photo_type(cls, v):
        allowed_types = ["custom", "branded_template", "combined"]
        if v not in allowed_types:
            raise ValueError(f'Photo type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('privacy_level')
    def validate_privacy_level(cls, v):
        allowed_levels = ["private", "friends", "public"]
        if v not in allowed_levels:
            raise ValueError(f'Privacy level must be one of: {", ".join(allowed_levels)}')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ["active", "archived", "reported", "deleted"]
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v

class AchievementPhotoCreate(BaseModel):
    achievement_id: str
    achievement_type: str
    photo_type: str = "custom"
    caption: Optional[str] = None
    tags: List[str] = []
    privacy_level: str = "public"

class PhotoLike(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    photo_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Story Timeline Models
class TimelineEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # Owner of the timeline
    event_type: str  # "personal" or "social"
    # Event classification
    category: str  # "transaction", "milestone", "goal", "badge", "friend_activity", "challenge"
    subcategory: Optional[str] = None  # "income", "expense", "savings_milestone", "streak_badge", etc.
    # Event details
    title: str
    description: str
    amount: Optional[float] = None
    metadata: Dict[str, Any] = {}
    # Related entities
    related_user_id: Optional[str] = None  # For friend activities
    related_entity_id: Optional[str] = None  # Transaction ID, Achievement ID, etc.
    # Visual elements
    icon: str = "📊"
    color: str = "#3B82F6"
    image_url: Optional[str] = None
    # Timeline position
    event_date: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Privacy and visibility
    visibility: str = "friends"  # "private", "friends", "public"
    is_featured: bool = False  # Featured events appear more prominently
    
    @validator('event_type')
    def validate_event_type(cls, v):
        allowed_types = ["personal", "social"]
        if v not in allowed_types:
            raise ValueError(f'Event type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('category')
    def validate_category(cls, v):
        allowed_categories = ["transaction", "milestone", "goal", "badge", "friend_activity", "challenge"]
        if v not in allowed_categories:
            raise ValueError(f'Category must be one of: {", ".join(allowed_categories)}')
        return v
    
    @validator('visibility')
    def validate_visibility(cls, v):
        allowed_levels = ["private", "friends", "public"]
        if v not in allowed_levels:
            raise ValueError(f'Visibility must be one of: {", ".join(allowed_levels)}')
        return v

class TimelineEventCreate(BaseModel):
    event_type: str
    category: str
    subcategory: Optional[str] = None
    title: str
    description: str
    amount: Optional[float] = None
    metadata: Dict[str, Any] = {}
    related_user_id: Optional[str] = None
    related_entity_id: Optional[str] = None
    icon: str = "📊"
    color: str = "#3B82F6"
    image_url: Optional[str] = None
    event_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    visibility: str = "friends"

class TimelineReaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    timeline_event_id: str
    reaction_type: str  # "like", "celebrate", "motivate", "inspire"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('reaction_type')
    def validate_reaction_type(cls, v):
        allowed_types = ["like", "celebrate", "motivate", "inspire"]
        if v not in allowed_types:
            raise ValueError(f'Reaction type must be one of: {", ".join(allowed_types)}')
        return v

# Enhanced Daily Tips Models
class DailyTipPersonalization(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    # User financial profile for personalization
    spending_categories: List[str] = []
    financial_goals: List[str] = []
    current_challenges: List[str] = []
    learning_preferences: List[str] = []  # "budgeting", "investing", "saving", "earning"
    tip_delivery_time: str = "09:00"  # Preferred time for daily tips
    tip_frequency: str = "daily"  # "daily", "every_other_day", "weekly"
    # Tip history and preferences
    favorite_tip_types: List[str] = []
    dismissed_tip_topics: List[str] = []
    engagement_score: float = 0.0  # 0-1 based on tip interaction history
    last_tip_sent: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DailyTipInteraction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    tip_id: str
    interaction_type: str  # "viewed", "liked", "shared", "saved", "dismissed"
    interaction_data: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('interaction_type')
    def validate_interaction_type(cls, v):
        allowed_types = ["viewed", "liked", "shared", "saved", "dismissed"]
        if v not in allowed_types:
            raise ValueError(f'Interaction type must be one of: {", ".join(allowed_types)}')
        return v
