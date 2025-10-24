from pydantic import BaseModel, Field, EmailStr, validator, root_validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone, timedelta
import uuid
import re

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None  # Phone number field
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
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v:
            # Remove spaces and dashes
            phone = v.strip().replace(' ', '').replace('-', '')
            # Check if it's a valid phone number format (10-15 digits)
            if not re.match(r'^\+?\d{10,15}$', phone):
                raise ValueError('Phone number must be 10-15 digits')
        return v
    
    availability_hours: int = 10  # hours per week
    location: str  # MANDATORY - cannot be empty, must be valid location format
    bio: Optional[str] = None
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
    is_admin: bool = False  # Keep for backward compatibility
    is_super_admin: bool = False  # Top-level admin authority
    admin_level: str = "user"  # "user", "club_admin", "campus_admin", "super_admin"
    failed_login_attempts: int = 0
    last_failed_login: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    @validator('admin_level')
    def validate_admin_level(cls, v):
        allowed_levels = ["user", "club_admin", "campus_admin", "super_admin"]
        if v not in allowed_levels:
            raise ValueError(f'Admin level must be one of: {", ".join(allowed_levels)}')
        return v
    
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
    phone_number: str  # MANDATORY - Phone number field
    role: str  # MANDATORY
    student_level: str
    university: Optional[str] = None  # For campus integration
    skills: List[str] = []
    availability_hours: int = 10
    location: str  # MANDATORY
    bio: Optional[str] = None

    @validator('phone_number')
    def validate_phone_number(cls, v):
        if not v or not v.strip():
            raise ValueError('Phone number is required')
        # Remove spaces and dashes
        phone = v.strip().replace(' ', '').replace('-', '')
        # Check if it's a valid phone number format (10-15 digits)
        if not re.match(r'^\+?\d{10,15}$', phone):
            raise ValueError('Phone number must be 10-15 digits')
        return v

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
        
        if len(v) > 20:
            raise ValueError('Cannot have more than 20 skills')
        
        # Check if all skills are valid (not empty) and clean them
        cleaned_skills = []
        for skill in v:
            cleaned = skill.strip()
            if cleaned and len(cleaned) <= 50:
                cleaned_skills.append(cleaned)
        
        if len(cleaned_skills) == 0:
            raise ValueError('At least one valid skill is required')
        
        return cleaned_skills

    @validator('bio')
    def validate_bio(cls, v):
        if v and len(v) > 500:
            raise ValueError('Bio cannot exceed 500 characters')
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
    platform: str  # "instagram", "whatsapp", "twitter", "facebook", "linkedin", "snapchat"
    achievement_type: str  # "savings_milestone", "streak_achievement", "badge_earned", etc.
    milestone_text: str
    image_filename: str
    amount: Optional[float] = None
    shared_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    engagement_count: int = 0  # likes, comments, shares from platform
    click_count: int = 0  # clicks on shared content links
    conversion_count: int = 0  # actual signups from shared content
    viral_coefficient: float = 0.0  # engagement/conversion metrics
    
    @validator('platform')
    def validate_platform(cls, v):
        allowed_platforms = ["instagram", "whatsapp", "twitter", "facebook", "linkedin", "snapchat"]
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

# ===== ENHANCED SHARING & TRACKING MODELS =====

class ViralReferralLink(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    referral_code: str
    shortened_url: str
    original_url: str
    click_count: int = 0
    conversion_count: int = 0
    platform_source: Optional[str] = None  # where the link was shared
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    is_active: bool = True
    viral_coefficient: float = 0.0  # conversions/clicks ratio

class ReferralClick(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    referral_link_id: str
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    platform_source: Optional[str] = None
    clicked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    converted: bool = False
    converted_user_id: Optional[str] = None
    geographic_location: Optional[Dict[str, Any]] = None

class LinkedInPost(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    achievement_type: str
    milestone_text: str
    professional_content: str  # LinkedIn-optimized text
    hashtags: List[str] = []
    image_filename: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    shared_manually: bool = True  # since we're doing copy-to-clipboard

class ExpenseReceipt(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    transaction_id: Optional[str] = None
    filename: str
    original_filename: str
    merchant_name: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    date_extracted: Optional[datetime] = None
    ocr_text: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    shared_count: int = 0
    shared_platforms: List[str] = []

# ===== CAMPUS AMBASSADOR MODELS (MOVED TO REFERRAL SECTION) =====

# ===== GROUP EXPENSE SPLITTING MODELS =====

class GroupExpense(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    creator_id: str
    title: str
    description: Optional[str] = None
    total_amount: float
    category: str
    receipt_filename: Optional[str] = None
    participants: List[Dict[str, Any]] = []  # [{"user_id": "abc", "amount": 150.0, "paid": True}]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    settled: bool = False
    settlement_method: Optional[str] = None  # "equal", "custom", "percentage"

class ExpenseSettlement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    group_expense_id: str
    payer_id: str
    payee_id: str
    amount: float
    status: str = "pending"  # "pending", "completed", "disputed"
    settled_at: Optional[datetime] = None
    payment_method: Optional[str] = None
    
    @validator('status')
    def validate_settlement_status(cls, v):
        allowed_statuses = ["pending", "completed", "disputed"]
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v

# ===== GROWTH MECHANICS MODELS =====

class InviteQuota(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    monthly_limit: int = 5  # starts with 5 invites per month
    used_this_month: int = 0
    bonus_invites: int = 0  # earned through achievements
    reset_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(day=1) + timedelta(days=32))
    total_earned: int = 0  # lifetime bonus invites earned

class FeatureWaitlist(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    feature_name: str
    priority_score: float = 0.0  # calculated based on user activity/status
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    granted_access: bool = False
    granted_at: Optional[datetime] = None
    position: Optional[int] = None

class BetaFeatureAccess(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    feature_name: str
    access_criteria_met: List[str] = []  # ["top_saver", "campus_ambassador", "high_referrals"]
    granted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    usage_count: int = 0

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

# ===== INTER-COLLEGE COMPETITION MODELS =====

class InterCollegeCompetition(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    competition_type: str  # "campus_savings", "campus_streak", "campus_referrals", "campus_goals"
    # Competition details
    start_date: datetime
    end_date: datetime
    registration_start: datetime
    registration_end: datetime
    duration_days: int
    # Participation criteria
    min_participants_per_campus: int = 10
    max_participants_per_campus: int = 100
    eligible_universities: List[str] = []  # Empty = all universities
    min_user_level: int = 1
    # Competition mechanics
    scoring_method: str = "total"  # "total", "average", "percentage", "top_performers"
    target_metric: str  # "total_savings", "average_streak", "referral_count", "goals_completed"
    target_value: Optional[float] = None
    # Prizes and rewards
    prize_pool: float  # Total monetary prize pool
    prize_distribution: Dict[str, Any] = {}  # {"1st": 50000, "2nd": 30000, "3rd": 20000}
    campus_reputation_points: Dict[str, int] = {}  # Points awarded to winning campuses
    participation_rewards: Dict[str, Any] = {}  # Rewards for all participants
    # Status and visibility
    status: str = "upcoming"  # "upcoming", "registration_open", "active", "completed", "cancelled"
    is_featured: bool = False
    visibility: str = "public"  # "public", "invited_only"
    created_by: str  # Admin who created the competition
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('competition_type')
    def validate_competition_type(cls, v):
        allowed_types = ["campus_savings", "campus_streak", "campus_referrals", "campus_goals"]
        if v not in allowed_types:
            raise ValueError(f'Competition type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ["upcoming", "registration_open", "active", "completed", "cancelled"]
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v
    
    @validator('scoring_method')
    def validate_scoring_method(cls, v):
        allowed_methods = ["total", "average", "percentage", "top_performers"]
        if v not in allowed_methods:
            raise ValueError(f'Scoring method must be one of: {", ".join(allowed_methods)}')
        return v

class CampusCompetitionParticipation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    competition_id: str
    user_id: str
    campus: str  # University name
    # Registration details
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    registration_status: str = "registered"  # "registered", "active", "disqualified", "withdrawn"
    # Performance tracking
    individual_score: float = 0.0
    individual_rank: int = 0
    campus_contribution: float = 0.0  # This user's contribution to campus total
    # Progress tracking
    daily_progress: Dict[str, float] = {}  # Date -> progress value
    milestones_achieved: List[str] = []
    # Rewards
    individual_rewards: List[Dict[str, Any]] = []
    reward_eligibility: Dict[str, bool] = {}
    
    @validator('registration_status')
    def validate_registration_status(cls, v):
        allowed_statuses = ["registered", "active", "disqualified", "withdrawn"]
        if v not in allowed_statuses:
            raise ValueError(f'Registration status must be one of: {", ".join(allowed_statuses)}')
        return v

class CampusLeaderboard(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    competition_id: str
    campus: str
    # Team statistics
    total_participants: int = 0
    active_participants: int = 0
    # Performance metrics
    campus_total_score: float = 0.0
    campus_average_score: float = 0.0
    campus_rank: int = 0
    # Progress tracking
    daily_totals: Dict[str, float] = {}  # Date -> daily total
    milestone_achievements: List[Dict[str, Any]] = []
    # Campus reputation
    reputation_points_earned: int = 0
    bonus_points: int = 0  # Extra points for achievements
    # Last updated timestamp
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ===== PRIZE-BASED CHALLENGE MODELS =====

class PrizeChallenge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    challenge_type: str  # "weekly", "monthly", "flash", "seasonal"
    # Challenge mechanics
    challenge_category: str  # "savings", "streak", "referrals", "goals", "engagement", "mixed"
    difficulty_level: str = "medium"  # "easy", "medium", "hard", "extreme"
    target_metric: str  # "amount_saved", "days_streak", "referrals_made", "goals_completed"
    target_value: float
    # Timing
    start_date: datetime
    end_date: datetime
    duration_hours: int  # For flash challenges
    # Participation
    max_participants: Optional[int] = None  # None = unlimited
    current_participants: int = 0
    entry_requirements: Dict[str, Any] = {}  # Level, streak, etc.
    # Prizes and rewards
    prize_type: str  # "monetary", "scholarship", "points", "badge", "mixed"
    total_prize_value: float  # In rupees for monetary prizes
    prize_structure: Dict[str, Any] = {}  # Detailed prize breakdown
    scholarship_details: Optional[Dict[str, Any]] = None  # For scholarship prizes
    # Campus reputation rewards
    campus_reputation_rewards: Dict[str, int] = {}

# ===== ADMIN VERIFICATION WORKFLOW MODELS =====

class CampusAdminRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    # Contact and identity information
    email: str
    full_name: str
    phone_number: Optional[str] = None
    # College and club information
    college_name: str
    college_email_domain: Optional[str] = None  # Extracted from institutional email
    club_name: Optional[str] = None
    club_type: str = "student_organization"  # "student_organization", "academic_society", "cultural_club", "sports_club"
    requested_admin_type: str = "campus_admin"  # "campus_admin" only for user requests
    # Verification details
    verification_method: str = "email"  # "email", "manual", "both"
    institutional_email: Optional[str] = None
    email_verified: bool = False
    email_verification_token: Optional[str] = None
    email_verified_at: Optional[datetime] = None
    # Document uploads
    uploaded_documents: List[Dict[str, str]] = []  # [{"type": "college_id", "url": "...", "filename": "..."}]
    college_id_document: Optional[str] = None
    club_registration_document: Optional[str] = None
    faculty_endorsement_document: Optional[str] = None
    # Request workflow
    status: str = "pending"  # "pending", "under_review", "approved", "rejected"
    submission_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    review_started_at: Optional[datetime] = None
    decision_made_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None  # System admin user ID
    # Review details
    review_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    approval_conditions: Optional[str] = None
    # Admin privileges (set upon approval)
    admin_privileges: Dict[str, Any] = {}
    privileges_expires_at: Optional[datetime] = None
    is_active: bool = True

    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ["pending", "under_review", "approved", "rejected", "suspended"]
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v

    @validator('requested_admin_type')
    def validate_admin_type(cls, v):
        allowed_types = ["club_admin", "campus_admin"]
        if v not in allowed_types:
            raise ValueError(f'Admin type must be one of: {", ".join(allowed_types)}')
        return v

    @validator('verification_method')
    def validate_verification_method(cls, v):
        allowed_methods = ["email", "manual", "both"]
        if v not in allowed_methods:
            raise ValueError(f'Verification method must be one of: {", ".join(allowed_methods)}')
        return v

class CampusAdmin(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    request_id: str  # Reference to original admin request
    # Admin details
    admin_type: str = "club_admin"  # "club_admin", "campus_admin"
    college_name: str
    club_name: Optional[str] = None
    # Privileges and permissions
    permissions: List[str] = []  # ["create_competitions", "manage_participants", "moderate_content"]
    can_create_inter_college: bool = False
    can_create_intra_college: bool = True
    can_manage_reputation: bool = False
    max_competitions_per_month: int = 5
    # Status and lifecycle
    status: str = "active"  # "active", "suspended", "revoked"
    appointed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    appointed_by: str  # System admin user ID
    last_activity: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    # Performance metrics
    competitions_created: int = 0
    challenges_created: int = 0
    participants_managed: int = 0
    reputation_points_awarded: int = 0
    warnings_count: int = 0
    days_active: int = 0  # Number of days admin has been active
    success_rate: float = 0.0  # Success rate of competitions/challenges
    club_admins_managed: int = 0  # For campus admins managing club admins
    # Audit trail
    creation_ip: Optional[str] = None
    creation_user_agent: Optional[str] = None
    last_login_ip: Optional[str] = None
    last_login_at: Optional[datetime] = None
    suspension_reason: Optional[str] = None
    suspended_at: Optional[datetime] = None
    suspended_by: Optional[str] = None  # Super admin user ID
    revocation_reason: Optional[str] = None
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None  # Super admin user ID

    @validator('admin_type')
    def validate_admin_type(cls, v):
        allowed_types = ["club_admin", "campus_admin"]
        if v not in allowed_types:
            raise ValueError(f'Admin type must be one of: {", ".join(allowed_types)}')
        return v

    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ["active", "suspended", "revoked"]
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v

class AdminAuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    # Action details
    admin_user_id: str
    action_type: str  # "create_competition", "approve_request", "suspend_admin", "moderate_content"
    action_description: str
    target_type: str  # "competition", "challenge", "admin_request", "user", "campus_reputation"
    target_id: Optional[str] = None
    # Context information
    affected_entities: List[Dict[str, str]] = []  # [{"type": "user", "id": "...", "name": "..."}]
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    # Metadata
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    # Classification
    severity: str = "info"  # "info", "warning", "error", "critical"
    category: str = "admin_action"  # "admin_action", "system_event", "security_event"
    is_system_generated: bool = False
    # Additional context for super admin oversight
    admin_level: Optional[str] = None  # "club_admin", "campus_admin", "super_admin"
    college_name: Optional[str] = None  # For campus-specific actions
    success: bool = True  # Whether the action was successful
    error_message: Optional[str] = None  # If action failed
    alert_sent: bool = False  # Whether real-time alert was sent

    @validator('severity')
    def validate_severity(cls, v):
        allowed_severities = ["info", "warning", "error", "critical"]
        if v not in allowed_severities:
            raise ValueError(f'Severity must be one of: {", ".join(allowed_severities)}')
        return v

    @validator('category')
    def validate_category(cls, v):
        allowed_categories = ["admin_action", "system_event", "security_event"]
        if v not in allowed_categories:
            raise ValueError(f'Category must be one of: {", ".join(allowed_categories)}')
        return v

class EmailDomainVerification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email_domain: str
    college_name: str
    verification_status: str = "unverified"  # "unverified", "verified", "blacklisted"
    # Verification details
    verified_by: Optional[str] = None  # System admin who verified
    verified_at: Optional[datetime] = None
    verification_method: str = "manual"  # "manual", "automatic", "api"
    # Domain information
    domain_type: str = "educational"  # "educational", "government", "commercial"
    country: str = "IN"
    state: Optional[str] = None
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    usage_count: int = 0  # How many requests used this domain
    last_used: Optional[datetime] = None

    @validator('verification_status')
    def validate_verification_status(cls, v):
        allowed_statuses = ["unverified", "verified", "blacklisted"]
        if v not in allowed_statuses:
            raise ValueError(f'Verification status must be one of: {", ".join(allowed_statuses)}')
        return v

class SystemAdminNotification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    # Notification content
    title: str
    message: str
    notification_type: str = "admin_request"  # "admin_request", "system_alert", "audit_alert"
    priority: str = "normal"  # "low", "normal", "high", "urgent"
    # Target and source
    target_admin_id: Optional[str] = None  # If None, sent to all system admins
    source_type: str = "system"  # "system", "user", "automated"
    source_id: Optional[str] = None
    # Related entities
    related_request_id: Optional[str] = None
    related_user_id: Optional[str] = None
    related_competition_id: Optional[str] = None
    # Action buttons
    action_url: Optional[str] = None
    action_buttons: List[Dict[str, str]] = []  # [{"label": "Approve", "action": "approve_request"}]
    # Status
    is_read: bool = False
    read_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    @validator('priority')
    def validate_priority(cls, v):
        allowed_priorities = ["low", "normal", "high", "urgent"]
        if v not in allowed_priorities:
            raise ValueError(f'Priority must be one of: {", ".join(allowed_priorities)}')
        return v

# ===== REQUEST MODELS FOR ADMIN WORKFLOW =====

class CampusAdminRequestCreate(BaseModel):
    # Personal information
    full_name: str = Field(..., min_length=2, max_length=100)
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    # College and club information
    college_name: str = Field(..., min_length=2, max_length=200)
    institutional_email: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    club_name: Optional[str] = Field(None, max_length=200)
    club_type: str = Field(default="student_organization")
    requested_admin_type: str = Field(default="campus_admin")
    # Reasoning and motivation
    motivation: str = Field(..., min_length=50, max_length=1000)
    previous_experience: Optional[str] = Field(None, max_length=1000)
    planned_activities: Optional[str] = Field(None, max_length=1000)

    @validator('requested_admin_type')
    def validate_admin_type(cls, v):
        # Allow both campus_admin and club_admin requests
        allowed_types = ["campus_admin", "club_admin"]
        if v not in allowed_types:
            raise ValueError('Admin type must be either campus_admin or club_admin.')
        return v

    @validator('club_type')
    def validate_club_type(cls, v):
        allowed_types = ["student_organization", "academic_society", "cultural_club", "sports_club", "technical_club", "social_service"]
        if v not in allowed_types:
            raise ValueError(f'Club type must be one of: {", ".join(allowed_types)}')
        return v

class AdminRequestReview(BaseModel):
    decision: str = Field(..., pattern=r'^(approve|reject)$')
    review_notes: Optional[str] = Field(None, max_length=1000)
    rejection_reason: Optional[str] = Field(None, max_length=500)
    approval_conditions: Optional[str] = Field(None, max_length=500)
    # Admin privileges (only for approval)
    admin_type: Optional[str] = None
    permissions: Optional[List[str]] = None
    can_create_inter_college: bool = False
    max_competitions_per_month: int = 5
    expires_in_months: int = 12

class DocumentUploadRequest(BaseModel):
    request_id: str
    document_type: str = Field(..., pattern=r'^(college_id|club_registration|faculty_endorsement)$')
    document_description: Optional[str] = None

class AdminPrivilegeUpdate(BaseModel):
    admin_id: str
    action: str = Field(..., pattern=r'^(suspend|reactivate|revoke|update_permissions)$')
    reason: str = Field(..., min_length=10, max_length=500)
    new_permissions: Optional[List[str]] = None
    suspension_duration_days: Optional[int] = Field(None, ge=1, le=365)

class PrizeChallengeParticipation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    challenge_id: str
    user_id: str
    # Participation details
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    participation_status: str = "active"  # "active", "completed", "disqualified", "withdrawn"
    # Performance tracking
    current_progress: float = 0.0
    target_progress: float = 0.0
    progress_percentage: float = 0.0
    current_rank: int = 0
    # Timeline tracking
    progress_history: Dict[str, float] = {}  # Timestamp -> progress value
    milestones_achieved: List[Dict[str, Any]] = []
    # Rewards earned
    rewards_earned: List[Dict[str, Any]] = []
    prize_eligibility: Dict[str, bool] = {}
    final_reward: Optional[Dict[str, Any]] = None
    
    @validator('participation_status')
    def validate_participation_status(cls, v):
        allowed_statuses = ["active", "completed", "disqualified", "withdrawn"]
        if v not in allowed_statuses:
            raise ValueError(f'Participation status must be one of: {", ".join(allowed_statuses)}')
        return v

class ChallengeReward(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    challenge_id: str
    user_id: str
    # Reward details
    reward_type: str  # "monetary", "scholarship", "points", "badge", "campus_reputation"
    reward_value: Union[float, int, str]  # Amount, points, or description
    reward_rank: int  # 1st place, 2nd place, etc.
    # Monetary reward details (if applicable)
    amount_inr: Optional[float] = None
    payment_method: Optional[str] = None  # "upi", "bank_transfer", "paytm"
    payment_status: str = "pending"  # "pending", "processing", "completed", "failed"
    payment_details: Optional[Dict[str, Any]] = None
    # Scholarship details (if applicable)
    scholarship_info: Optional[Dict[str, Any]] = None
    scholarship_provider: Optional[str] = None
    # Campus reputation (if applicable)
    campus_reputation_points: int = 0
    campus_affected: Optional[str] = None
    # Status and timeline
    awarded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    claimed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    status: str = "awarded"  # "awarded", "claimed", "expired", "cancelled"
    
    @validator('reward_type')
    def validate_reward_type(cls, v):
        allowed_types = ["monetary", "scholarship", "points", "badge", "campus_reputation"]
        if v not in allowed_types:
            raise ValueError(f'Reward type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('payment_status')
    def validate_payment_status(cls, v):
        allowed_statuses = ["pending", "processing", "completed", "failed"]
        if v not in allowed_statuses:
            raise ValueError(f'Payment status must be one of: {", ".join(allowed_statuses)}')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ["awarded", "claimed", "expired", "cancelled"]
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v

# ===== CAMPUS REPUTATION SYSTEM =====

class CampusReputation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    campus: str  # University name
    # Reputation metrics
    total_reputation_points: int = 0
    monthly_reputation_points: int = 0
    current_rank: int = 0
    previous_rank: int = 0
    # Performance categories
    academic_performance: int = 0  # Points from academic-related achievements
    financial_literacy: int = 0   # Points from financial goal achievements
    social_engagement: int = 0    # Points from social activities and referrals
    competition_wins: int = 0     # Points from inter-college competition wins
    innovation_points: int = 0    # Points from unique achievements
    # Historical tracking
    reputation_history: Dict[str, int] = {}  # Month-Year -> points
    achievements: List[Dict[str, Any]] = []  # Notable campus achievements
    # Campus statistics
    total_students: int = 0
    active_students: int = 0
    ambassador_count: int = 0
    # Rankings and comparisons
    national_rank: int = 0
    regional_rank: int = 0
    category_rankings: Dict[str, int] = {}  # Category -> rank
    # Last updated
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    monthly_reset_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ReputationTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    campus: str
    # Transaction details
    transaction_type: str  # "earned", "deducted", "bonus", "penalty"
    points: int
    reason: str
    category: str  # "academic", "financial", "social", "competition", "innovation"
    # Source information
    source_type: str  # "competition", "challenge", "user_achievement", "admin_action"
    source_id: Optional[str] = None  # Related entity ID
    user_id: Optional[str] = None  # User who contributed (if applicable)
    # Timestamp
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('transaction_type')
    def validate_transaction_type(cls, v):
        allowed_types = ["earned", "deducted", "bonus", "penalty"]
        if v not in allowed_types:
            raise ValueError(f'Transaction type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('category')
    def validate_category(cls, v):
        allowed_categories = ["academic", "financial", "social", "competition", "innovation"]
        if v not in allowed_categories:
            raise ValueError(f'Category must be one of: {", ".join(allowed_categories)}')
        return v
    
    @validator('source_type')
    def validate_source_type(cls, v):
        allowed_sources = ["competition", "challenge", "user_achievement", "admin_action"]
        if v not in allowed_sources:
            raise ValueError(f'Source type must be one of: {", ".join(allowed_sources)}')
        return v

# ===== REQUEST MODELS FOR NEW FEATURES =====

class InterCollegeCompetitionCreate(BaseModel):
    title: str
    description: str
    competition_type: str
    start_date: datetime
    end_date: datetime
    registration_start: datetime
    registration_end: datetime
    min_participants_per_campus: int = 10
    max_participants_per_campus: int = 100
    eligible_universities: List[str] = []
    min_user_level: int = 1
    scoring_method: str = "total"
    target_metric: str
    target_value: Optional[float] = None
    prize_pool: float
    prize_distribution: Dict[str, Any] = {}
    campus_reputation_points: Dict[str, int] = {}
    participation_rewards: Dict[str, Any] = {}

class PrizeChallengeCreate(BaseModel):
    title: str
    description: str
    challenge_type: str
    challenge_category: str
    difficulty_level: str = "medium"
    target_metric: str
    target_value: float
    start_date: datetime
    end_date: datetime
    duration_hours: int = 0
    max_participants: Optional[int] = None
    entry_requirements: Dict[str, Any] = {}
    prize_type: str
    total_prize_value: float
    prize_structure: Dict[str, Any] = {}
    scholarship_details: Optional[Dict[str, Any]] = None
    campus_reputation_rewards: Dict[str, int] = {}

class InterCollegeCompetitionUpdate(BaseModel):
    """Update model for inter-college competitions"""
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    registration_start: Optional[datetime] = None
    registration_end: Optional[datetime] = None
    min_participants_per_campus: Optional[int] = None
    max_participants_per_campus: Optional[int] = None
    eligible_universities: Optional[List[str]] = None
    target_value: Optional[float] = None
    prize_pool: Optional[float] = None
    prize_distribution: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class PrizeChallengeUpdate(BaseModel):
    """Update model for prize challenges"""
    title: Optional[str] = None
    description: Optional[str] = None
    difficulty_level: Optional[str] = None
    target_value: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_participants: Optional[int] = None
    total_prize_value: Optional[float] = None
    prize_structure: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


# ===== SUPER ADMIN OVERSIGHT MODELS =====

class AdminActivityMetrics(BaseModel):
    """Comprehensive metrics for campus/club admin performance"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    admin_user_id: str
    admin_type: str  # "club_admin", "campus_admin"
    college_name: str
    # Time-based metrics
    days_active: int = 0
    last_active_date: Optional[datetime] = None
    average_daily_actions: float = 0.0
    # Activity metrics
    total_competitions_created: int = 0
    total_challenges_created: int = 0
    total_participants_managed: int = 0
    total_club_admins_approved: int = 0  # For campus admins
    # Success metrics
    competitions_completed: int = 0
    competitions_cancelled: int = 0
    success_rate: float = 0.0
    average_participant_satisfaction: float = 0.0
    # Engagement metrics
    total_users_engaged: int = 0
    reputation_points_awarded: int = 0
    average_competition_size: float = 0.0
    # Compliance metrics
    warnings_received: int = 0
    policy_violations: int = 0
    response_time_hours: float = 0.0  # Average response time to issues
    # Calculated at
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    period_start: datetime
    period_end: datetime

class ClubAdminRequest(BaseModel):
    """Request from campus admin to approve a club admin"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # User requesting club admin status
    campus_admin_id: str  # Campus admin reviewing the request
    # Club information
    college_name: str
    club_name: str
    club_type: str = "student_organization"
    # Request details
    full_name: str
    email: str
    phone_number: Optional[str] = None
    motivation: str
    previous_experience: Optional[str] = None
    # Status and workflow
    status: str = "pending"  # "pending", "approved", "rejected"
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    # Approval details
    approved_permissions: List[str] = []
    max_events_per_month: int = 3
    expires_in_months: int = 6

class AdminSessionTracker(BaseModel):
    """Track admin login sessions for security monitoring"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_user_id: str
    admin_level: str  # "club_admin", "campus_admin", "super_admin"
    session_id: str
    # Session details
    login_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    logout_at: Optional[datetime] = None
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Security tracking
    ip_address: str
    user_agent: str
    location: Optional[Dict[str, str]] = None  # Geolocation data
    device_fingerprint: Optional[str] = None
    # Anomaly detection
    is_suspicious: bool = False
    suspicious_reasons: List[str] = []
    risk_score: float = 0.0
    # Actions performed
    actions_count: int = 0
    critical_actions_count: int = 0
    last_action_type: Optional[str] = None

class AdminAlert(BaseModel):
    """Real-time alerts for super admin"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    alert_type: str  # "new_request", "suspicious_activity", "high_priority_action", "policy_violation"
    severity: str  # "info", "warning", "critical"
    title: str
    message: str
    # Target information
    admin_user_id: Optional[str] = None
    admin_level: Optional[str] = None
    related_entity_type: Optional[str] = None  # "admin_request", "campus_admin", "competition"
    related_entity_id: Optional[str] = None
    # Alert metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    read_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None  # Super admin user ID
    # Action required
    requires_action: bool = False
    action_deadline: Optional[datetime] = None
    action_taken: Optional[str] = None
    action_taken_at: Optional[datetime] = None

    @validator('alert_type')
    def validate_alert_type(cls, v):
        allowed_types = ["new_request", "suspicious_activity", "high_priority_action", "policy_violation", "performance_issue", "security_alert"]
        if v not in allowed_types:
            raise ValueError(f'Alert type must be one of: {", ".join(allowed_types)}')
        return v

class AdminPerformanceReport(BaseModel):
    """Aggregated performance report for super admin review"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_type: str  # "daily", "weekly", "monthly", "quarterly"
    period_start: datetime
    period_end: datetime
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Overall metrics
    total_campus_admins: int = 0
    active_campus_admins: int = 0
    total_club_admins: int = 0
    active_club_admins: int = 0
    # Activity summary
    total_competitions_created: int = 0
    total_challenges_created: int = 0
    total_participants: int = 0
    total_requests_received: int = 0
    total_requests_approved: int = 0
    total_requests_rejected: int = 0
    # Performance indicators
    average_success_rate: float = 0.0
    average_response_time_hours: float = 0.0
    total_warnings_issued: int = 0
    total_suspensions: int = 0
    # Top performers
    top_campus_admins: List[Dict[str, Any]] = []
    underperforming_admins: List[Dict[str, Any]] = []
    # Issues and alerts
    critical_issues: List[Dict[str, Any]] = []
    pending_actions: List[Dict[str, Any]] = []


# ===== COLLEGE EVENTS SYSTEM =====

class CollegeEvent(BaseModel):
    """Model for college events (technical, club activities, hackathons, etc.)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Basic Information
    title: str
    description: str
    event_type: str  # "hackathon", "workshop", "competition", "seminar", "tech_talk", "club_meeting"
    category: str = "technical"  # Always "technical" for now
    
    # Schedule
    start_date: datetime
    end_date: datetime
    registration_deadline: Optional[datetime] = None
    
    # Location
    venue: str  # Physical location or "Virtual"
    is_virtual: bool = False
    meeting_link: Optional[str] = None
    college_name: str  # Host college
    
    # Visibility and Access
    visibility: str = "college_only"  # "college_only", "all_colleges", "selected_colleges"
    eligible_colleges: List[str] = []  # For "selected_colleges" visibility
    
    # Organizer Information
    club_name: Optional[str] = None  # e.g., "IEEE", "Photonics Club", "Robotics Club"
    organizer_name: str
    organizer_email: Optional[str] = None
    organizer_phone: Optional[str] = None
    
    # Registration
    registration_required: bool = True
    max_participants: Optional[int] = None
    current_participants: int = 0
    registration_fee: float = 0.0
    allowed_registration_types: List[str] = ["individual"]  # Can contain "individual", "group", or both
    group_size_min: Optional[int] = None  # Minimum team size if group registration allowed
    group_size_max: Optional[int] = None  # Maximum team size if group registration allowed
    
    # Media and Resources
    banner_image: Optional[str] = None
    attachments: List[str] = []  # Links to documents, guidelines, etc.
    tags: List[str] = []  # e.g., ["AI", "Machine Learning", "24-hour", "Team Event"]
    
    # Event Details
    rules: Optional[str] = None
    prizes: Optional[Dict[str, Any]] = None  # {"1st": "10000", "2nd": "5000"}
    requirements: Optional[str] = None
    
    # Admin and Status
    created_by: str  # User ID of creator
    created_by_admin_type: str  # "club_admin", "campus_admin", "super_admin"
    admin_id: Optional[str] = None  # Campus/Club Admin ID
    status: str = "upcoming"  # "upcoming", "registration_open", "ongoing", "completed", "cancelled"
    is_featured: bool = False
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('event_type')
    def validate_event_type(cls, v):
        allowed_types = ["hackathon", "workshop", "coding_competition", "tech_talk", 
                        "seminar", "conference", "club_meeting", "project_showcase"]
        if v not in allowed_types:
            raise ValueError(f'Event type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('visibility')
    def validate_visibility(cls, v):
        allowed_visibility = ["college_only", "all_colleges", "selected_colleges"]
        if v not in allowed_visibility:
            raise ValueError(f'Visibility must be one of: {", ".join(allowed_visibility)}')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ["upcoming", "registration_open", "ongoing", "completed", "cancelled"]
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v

class CollegeEventCreate(BaseModel):
    """Create model for college events"""
    title: str
    description: str
    event_type: str
    start_date: datetime
    end_date: datetime
    registration_deadline: Optional[datetime] = None
    venue: str
    is_virtual: bool = False
    meeting_link: Optional[str] = None
    visibility: str = "college_only"
    eligible_colleges: List[str] = []
    club_name: Optional[str] = None
    organizer_name: str
    organizer_email: Optional[str] = None
    organizer_phone: Optional[str] = None
    registration_required: bool = True
    max_participants: Optional[int] = None
    registration_fee: float = 0.0
    allowed_registration_types: List[str] = ["individual"]
    group_size_min: Optional[int] = None
    group_size_max: Optional[int] = None
    banner_image: Optional[str] = None
    tags: List[str] = []
    rules: Optional[str] = None
    prizes: Optional[Dict[str, Any]] = None
    requirements: Optional[str] = None

class CollegeEventUpdate(BaseModel):
    """Update model for college events"""
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    registration_deadline: Optional[datetime] = None
    venue: Optional[str] = None
    is_virtual: Optional[bool] = None
    meeting_link: Optional[str] = None
    visibility: Optional[str] = None
    eligible_colleges: Optional[List[str]] = None
    club_name: Optional[str] = None
    organizer_name: Optional[str] = None
    organizer_email: Optional[str] = None
    organizer_phone: Optional[str] = None
    registration_required: Optional[bool] = None
    max_participants: Optional[int] = None
    registration_fee: Optional[float] = None
    allowed_registration_types: Optional[List[str]] = None
    group_size_min: Optional[int] = None
    group_size_max: Optional[int] = None
    banner_image: Optional[str] = None
    tags: Optional[List[str]] = None
    rules: Optional[str] = None
    prizes: Optional[Dict[str, Any]] = None
    requirements: Optional[str] = None
    status: Optional[str] = None

class EventRegistration(BaseModel):
    """Model for event registrations"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str
    user_id: str
    user_name: str
    user_email: str
    user_college: str
    registration_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "pending"  # "pending", "approved", "rejected", "attended", "cancelled"
    rejection_reason: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    # Individual registration details
    registration_type: str = "individual"  # "individual" or "group"
    usn: Optional[str] = None
    phone_number: Optional[str] = None
    semester: Optional[int] = None
    year: Optional[int] = None
    branch: Optional[str] = None
    section: Optional[str] = None
    student_id_card_url: Optional[str] = None

    # Group registration details
    team_name: Optional[str] = None
    team_leader_name: Optional[str] = None
    team_leader_usn: Optional[str] = None
    team_leader_email: Optional[str] = None
    team_leader_phone: Optional[str] = None
    team_size: Optional[int] = None
    team_members: List[Dict[str, Any]] = []  # Full member details with USN, email, phone, etc.

    additional_info: Optional[Dict[str, Any]] = None


class PrizeChallengeRegistration(BaseModel):
    """Detailed registration model for Prize Challenges"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    challenge_id: str
    user_id: str
    registration_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "pending"  # "pending", "approved", "rejected", "active", "completed"
    rejection_reason: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    # Student details
    full_name: str
    email: str
    phone_number: str  # Replaced USN with phone number
    college: str
    semester: int = Field(ge=1, le=8)
    year: int = Field(ge=1, le=4)
    branch: str
    section: Optional[str] = None
    student_id_card_url: Optional[str] = None
    
    # Performance tracking (once approved)
    current_progress: float = 0.0
    progress_percentage: float = 0.0
    current_rank: Optional[int] = None
    
    additional_info: Optional[Dict[str, Any]] = None

class InterCollegeRegistration(BaseModel):
    """Detailed registration model for Inter-College Competitions"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    competition_id: str
    user_id: str
    registration_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "pending"  # "pending", "approved", "rejected", "active", "completed"
    rejection_reason: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    # Registration type
    registration_type: str = "admin"  # "admin" (individual campus admin) or "team"
    
    # For admin registration
    admin_name: Optional[str] = None
    admin_email: Optional[str] = None
    admin_phone: Optional[str] = None
    campus_name: Optional[str] = None
    
    # For team registration
    team_name: Optional[str] = None
    team_type: Optional[str] = None  # "team_leader" (creating new team) or "join_team" (joining existing)
    existing_team_id: Optional[str] = None
    team_leader_name: Optional[str] = None
    team_leader_email: Optional[str] = None
    team_leader_phone: Optional[str] = None  # Primary identifier - replaced USN
    team_leader_semester: Optional[int] = None
    team_leader_year: Optional[int] = None
    team_leader_branch: Optional[str] = None
    team_size: Optional[int] = Field(None, ge=1, le=5)
    min_team_size: Optional[int] = Field(None, ge=1)
    max_team_size: Optional[int] = Field(None, le=5)
    
    # Team members (for team_leader type)
    team_members: List[Dict[str, Any]] = []  # Full member details - phone instead of USN
    
    # Performance tracking
    campus_score: float = 0.0
    campus_rank: Optional[int] = None
    
    additional_info: Optional[Dict[str, Any]] = None

class RegistrationApproval(BaseModel):
    """Model for approving/rejecting registrations"""
    registration_id: str
    action: str = Field(..., pattern=r'^(approve|reject)$')
    reason: Optional[str] = None  # Required for rejection
    additional_notes: Optional[str] = None

