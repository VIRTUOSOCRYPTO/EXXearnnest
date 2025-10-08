"""
Admin Verification Service
Handles college email domain verification, document processing, and admin workflow management
"""

import re
import os
import uuid
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone, timedelta
from email_validator import validate_email, EmailNotValidError

# Configure logging
logger = logging.getLogger(__name__)

class EmailDomainVerifier:
    """Handles automated verification of college email domains"""
    
    def __init__(self):
        # Common Indian educational domain patterns
        self.indian_edu_patterns = [
            r'\.edu\.in$',
            r'\.ac\.in$',
            r'\.edu$',
            r'\.college\.edu\.in$',
            r'\.university\.ac\.in$',
        ]
        
        # Known verified domains (can be expanded)
        self.verified_domains = {
            # IITs
            'iitb.ac.in': {'name': 'Indian Institute of Technology Bombay', 'type': 'technical'},
            'iitd.ac.in': {'name': 'Indian Institute of Technology Delhi', 'type': 'technical'},
            'iitm.ac.in': {'name': 'Indian Institute of Technology Madras', 'type': 'technical'},
            'iitk.ac.in': {'name': 'Indian Institute of Technology Kanpur', 'type': 'technical'},
            'iitkgp.ac.in': {'name': 'Indian Institute of Technology Kharagpur', 'type': 'technical'},
            
            # NITs
            'nitc.ac.in': {'name': 'National Institute of Technology Calicut', 'type': 'technical'},
            'nitt.edu': {'name': 'National Institute of Technology Tiruchirappalli', 'type': 'technical'},
            
            # Central Universities
            'du.ac.in': {'name': 'University of Delhi', 'type': 'university'},
            'jnu.ac.in': {'name': 'Jawaharlal Nehru University', 'type': 'university'},
            'bhu.ac.in': {'name': 'Banaras Hindu University', 'type': 'university'},
            
            # State Universities (sample)
            'mumbai.university.ac.in': {'name': 'University of Mumbai', 'type': 'university'},
            'calcutta-university.ac.in': {'name': 'University of Calcutta', 'type': 'university'},
            'gu.ac.in': {'name': 'Gujarat University', 'type': 'university'},
            
            # Management Institutes
            'iima.ac.in': {'name': 'Indian Institute of Management Ahmedabad', 'type': 'management'},
            'iimb.ac.in': {'name': 'Indian Institute of Management Bangalore', 'type': 'management'},
            
            # International patterns (for reference)
            'harvard.edu': {'name': 'Harvard University', 'type': 'university'},
            'mit.edu': {'name': 'Massachusetts Institute of Technology', 'type': 'technical'},
            'stanford.edu': {'name': 'Stanford University', 'type': 'university'},
        }
        
    def extract_domain(self, email: str) -> str:
        """Extract domain from email address"""
        try:
            validated_email = validate_email(email)
            return validated_email.domain.lower()
        except EmailNotValidError:
            return ""
    
    def is_educational_domain(self, domain: str) -> Tuple[bool, str]:
        """Check if domain appears to be educational"""
        domain_lower = domain.lower()
        
        # Check against known verified domains
        if domain_lower in self.verified_domains:
            return True, "verified_database"
        
        # Check against educational patterns
        for pattern in self.indian_edu_patterns:
            if re.search(pattern, domain_lower):
                return True, "pattern_match"
        
        # Additional heuristics for educational domains
        educational_keywords = ['university', 'college', 'institute', 'school', 'academy']
        for keyword in educational_keywords:
            if keyword in domain_lower:
                return True, "keyword_match"
        
        return False, "no_match"
    
    def get_college_info(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get college information for a domain"""
        domain_lower = domain.lower()
        
        if domain_lower in self.verified_domains:
            return self.verified_domains[domain_lower]
        
        return None
    
    async def verify_email_domain(self, email: str, college_name: str) -> Dict[str, Any]:
        """Verify email domain and return verification result"""
        try:
            domain = self.extract_domain(email)
            if not domain:
                return {
                    "verified": False,
                    "reason": "invalid_email",
                    "message": "Invalid email format"
                }
            
            is_educational, match_type = self.is_educational_domain(domain)
            college_info = self.get_college_info(domain)
            
            verification_result = {
                "verified": is_educational,
                "domain": domain,
                "match_type": match_type,
                "college_info": college_info,
                "requires_manual_review": False
            }
            
            if is_educational and match_type == "verified_database":
                verification_result["message"] = "Email domain verified against known educational institutions"
                verification_result["auto_approved"] = True
            elif is_educational:
                verification_result["message"] = "Email domain appears educational but requires manual verification"
                verification_result["requires_manual_review"] = True
                verification_result["auto_approved"] = False
            else:
                verification_result["message"] = "Email domain not recognized as educational - manual verification required"
                verification_result["requires_manual_review"] = True
                verification_result["auto_approved"] = False
            
            return verification_result
            
        except Exception as e:
            logger.error(f"Email domain verification error: {str(e)}")
            # Try to extract domain even if there was an error
            domain = None
            try:
                domain = self.extract_domain(email)
            except:
                pass
            
            return {
                "verified": False,
                "domain": domain,
                "reason": "verification_error",
                "message": f"Error during verification: {str(e)}"
            }

class DocumentVerifier:
    """Handles document upload and basic verification"""
    
    def __init__(self):
        self.upload_dir = "/app/uploads/admin_documents"
        self.allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        
        # Ensure upload directory exists
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, str]:
        """Validate uploaded file"""
        if not filename:
            return False, "No filename provided"
        
        # Check file extension
        ext = os.path.splitext(filename.lower())[1]
        if ext not in self.allowed_extensions:
            return False, f"File type {ext} not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
        
        # Check file size
        if file_size > self.max_file_size:
            return False, f"File size too large. Maximum size: {self.max_file_size // (1024*1024)}MB"
        
        return True, "File validation passed"
    
    def generate_unique_filename(self, original_filename: str, user_id: str, document_type: str) -> str:
        """Generate unique filename for document"""
        ext = os.path.splitext(original_filename)[1]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{document_type}_{user_id}_{timestamp}_{unique_id}{ext}"
    
    async def save_document(self, file_content: bytes, filename: str, user_id: str, document_type: str) -> Dict[str, Any]:
        """Save uploaded document and return file info"""
        try:
            # Validate file
            is_valid, message = self.validate_file(filename, len(file_content))
            if not is_valid:
                return {"success": False, "error": message}
            
            # Generate unique filename
            unique_filename = self.generate_unique_filename(filename, user_id, document_type)
            file_path = os.path.join(self.upload_dir, unique_filename)
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            return {
                "success": True,
                "filename": unique_filename,
                "original_filename": filename,
                "file_path": file_path,
                "file_size": len(file_content),
                "upload_time": datetime.now(timezone.utc),
                "document_type": document_type
            }
            
        except Exception as e:
            logger.error(f"Document save error: {str(e)}")
            return {"success": False, "error": f"Failed to save document: {str(e)}"}

class AdminWorkflowManager:
    """Manages the admin verification workflow"""
    
    def __init__(self):
        self.email_verifier = EmailDomainVerifier()
        self.document_verifier = DocumentVerifier()
    
    async def process_admin_request(self, request_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Process new admin privilege request"""
        try:
            # Initialize verification result
            result = {
                "request_created": False,
                "email_verification": None,
                "requires_documents": False,
                "next_steps": []
            }
            
            # Verify institutional email if provided
            if request_data.get('institutional_email'):
                email_verification = await self.email_verifier.verify_email_domain(
                    request_data['institutional_email'],
                    request_data['college_name']
                )
                result["email_verification"] = email_verification
                
                if not email_verification["verified"]:
                    result["requires_documents"] = True
                    result["next_steps"].append("Upload college ID document")
                    result["next_steps"].append("Upload club registration certificate")
            else:
                result["requires_documents"] = True
                result["next_steps"].append("Provide institutional email OR upload verification documents")
            
            # Determine verification method
            if result["email_verification"] and result["email_verification"]["verified"]:
                if result["email_verification"].get("auto_approved"):
                    verification_method = "email"
                else:
                    verification_method = "both"  # Email + manual review
            else:
                verification_method = "manual"
            
            # Prepare request data
            admin_request = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "email": request_data["email"],
                "full_name": request_data["full_name"],
                "phone_number": request_data.get("phone_number"),
                "college_name": request_data["college_name"],
                "club_name": request_data.get("club_name"),
                "club_type": request_data.get("club_type", "student_organization"),
                "requested_admin_type": request_data.get("requested_admin_type", "club_admin"),
                "verification_method": verification_method,
                "institutional_email": request_data.get("institutional_email"),
                "status": "pending",
                "submission_date": datetime.now(timezone.utc),
                "is_active": True,
                "uploaded_documents": [],
                "admin_privileges": {},
            }
            
            # Add email domain info if available
            if result["email_verification"]:
                # Safely get domain field - it might not exist if there was an error
                admin_request["college_email_domain"] = result["email_verification"].get("domain", None)
                admin_request["email_verified"] = result["email_verification"]["verified"]
                if result["email_verification"]["verified"]:
                    admin_request["email_verified_at"] = datetime.now(timezone.utc)
            
            result["admin_request"] = admin_request
            result["request_created"] = True
            
            # Add final instructions
            if verification_method == "email" and result["email_verification"].get("auto_approved"):
                result["next_steps"] = ["Your request has been auto-approved based on verified institutional email"]
                admin_request["status"] = "approved"
            elif verification_method == "email":
                result["next_steps"] = ["Email verified - request forwarded to admin for final approval"]
                admin_request["status"] = "under_review"
            else:
                result["next_steps"].append("Request forwarded to admin for manual verification")
            
            return result
            
        except Exception as e:
            logger.error(f"Admin request processing error: {str(e)}")
            return {
                "request_created": False,
                "error": f"Failed to process request: {str(e)}"
            }
    
    def generate_admin_permissions(self, admin_type: str, college_type: str = "university") -> Dict[str, Any]:
        """Generate appropriate permissions for admin type"""
        base_permissions = ["view_dashboard", "manage_profile"]
        
        if admin_type == "club_admin":
            permissions = base_permissions + [
                "create_intra_competitions",
                "manage_club_participants", 
                "view_club_analytics",
                "moderate_club_content"
            ]
            return {
                "permissions": permissions,
                "can_create_inter_college": False,
                "can_create_intra_college": True,
                "can_manage_reputation": False,
                "max_competitions_per_month": 3
            }
        
        elif admin_type == "campus_admin":
            permissions = base_permissions + [
                "create_inter_competitions",
                "create_intra_competitions", 
                "manage_college_participants",
                "manage_campus_reputation",
                "view_college_analytics",
                "moderate_college_content",
                "manage_club_admins"
            ]
            return {
                "permissions": permissions,
                "can_create_inter_college": True,
                "can_create_intra_college": True,
                "can_manage_reputation": True,
                "max_competitions_per_month": 10
            }
        
        return {}
    
    async def create_audit_log(self, admin_user_id: str, action_type: str, 
                             action_description: str, target_type: str, 
                             target_id: str = None, **kwargs) -> Dict[str, Any]:
        """Create audit log entry"""
        return {
            "id": str(uuid.uuid4()),
            "admin_user_id": admin_user_id,
            "action_type": action_type,
            "action_description": action_description,
            "target_type": target_type,
            "target_id": target_id,
            "affected_entities": kwargs.get("affected_entities", []),
            "before_state": kwargs.get("before_state"),
            "after_state": kwargs.get("after_state"),
            "timestamp": datetime.now(timezone.utc),
            "ip_address": kwargs.get("ip_address"),
            "user_agent": kwargs.get("user_agent"),
            "severity": kwargs.get("severity", "info"),
            "category": kwargs.get("category", "admin_action"),
            "is_system_generated": kwargs.get("is_system_generated", False)
        }

# Initialize global instances
email_verifier = EmailDomainVerifier()
document_verifier = DocumentVerifier() 
admin_workflow_manager = AdminWorkflowManager()
