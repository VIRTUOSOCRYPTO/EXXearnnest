"""
Registration Service for Campus Features
Handles detailed registration for Prize Challenges, Inter-College Competitions, and College Events
"""
from typing import Dict, Any, List, Optional
from fastapi import UploadFile
import os
import uuid
from datetime import datetime, timezone

async def save_student_id_card(file: UploadFile, user_id: str) -> str:
    """Save uploaded student ID card and return URL"""
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = "/app/uploads/student_ids"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        filename = f"student_id_{user_id}_{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, filename)
        
        # Save file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Return URL path
        return f"/uploads/student_ids/{filename}"
    except Exception as e:
        print(f"Error saving student ID card: {e}")
        return None

async def validate_registration_data(
    registration_type: str,
    data: Dict[str, Any],
    required_individual_fields: List[str] = None,
    required_group_fields: List[str] = None
) -> Dict[str, Any]:
    """Validate registration data based on type"""
    errors = []
    
    if registration_type == "individual":
        required_fields = required_individual_fields or [
            "full_name", "email", "phone_number", "college", 
            "usn", "semester", "year", "branch"
        ]
        
        for field in required_fields:
            if not data.get(field):
                errors.append(f"{field} is required for individual registration")
    
    elif registration_type == "group":
        required_fields = required_group_fields or [
            "team_name", "team_leader_name", "team_leader_email",
            "team_leader_phone", "team_size", "team_members"
        ]
        
        for field in required_fields:
            if not data.get(field):
                errors.append(f"{field} is required for group registration")
        
        # Validate team size
        team_size = data.get("team_size", 0)
        team_members = data.get("team_members", [])
        
        if team_size < 2:
            errors.append("Team size must be at least 2")
        
        if len(team_members) != team_size - 1:  # -1 for team leader
            errors.append(f"Expected {team_size - 1} team members, got {len(team_members)}")
        
        # Validate each team member
        for idx, member in enumerate(team_members):
            member_required = ["name", "email", "phone", "usn"]
            for field in member_required:
                if not member.get(field):
                    errors.append(f"Team member {idx + 1}: {field} is required")
    
    if errors:
        return {"valid": False, "errors": errors}
    
    return {"valid": True, "errors": []}

async def get_registrations_for_event(
    db, 
    event_id: str, 
    event_type: str,
    filters: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """Get registrations for an event with optional filters"""
    collection_map = {
        "college_event": "event_registrations",
        "prize_challenge": "prize_challenge_registrations",
        "inter_college": "inter_college_registrations"
    }
    
    collection_name = collection_map.get(event_type)
    if not collection_name:
        return []
    
    # Build query
    query = {f"{event_type.replace('_', '')}_id" if event_type != "college_event" else "event_id": event_id}
    
    if filters:
        # Add college filter
        if filters.get("college"):
            query["$or"] = [
                {"college": filters["college"]},
                {"user_college": filters["college"]},
                {"campus_name": filters["college"]}
            ]
        
        # Add status filter
        if filters.get("status"):
            query["status"] = filters["status"]
        
        # Add registration type filter
        if filters.get("registration_type"):
            query["registration_type"] = filters["registration_type"]
        
        # Add date range filter
        if filters.get("start_date"):
            query["registration_date"] = {"$gte": filters["start_date"]}
        if filters.get("end_date"):
            if "registration_date" not in query:
                query["registration_date"] = {}
            query["registration_date"]["$lte"] = filters["end_date"]
    
    # Fetch registrations
    registrations = await db[collection_name].find(query).to_list(length=1000)
    
    return registrations

async def get_college_statistics(registrations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate college-wise statistics from registrations"""
    college_stats = {}
    
    for reg in registrations:
        college = reg.get("college") or reg.get("user_college") or reg.get("campus_name", "Unknown")
        
        if college not in college_stats:
            college_stats[college] = {
                "total": 0,
                "individual": 0,
                "group": 0,
                "pending": 0,
                "approved": 0,
                "rejected": 0
            }
        
        college_stats[college]["total"] += 1
        
        # Count by type
        reg_type = reg.get("registration_type", "individual")
        if reg_type == "individual":
            college_stats[college]["individual"] += 1
        elif reg_type == "group":
            college_stats[college]["group"] += 1
        
        # Count by status
        status = reg.get("status", "pending")
        if status in college_stats[college]:
            college_stats[college][status] += 1
    
    return college_stats

async def export_registrations_to_csv(registrations: List[Dict[str, Any]], event_name: str) -> str:
    """Export registrations to CSV file"""
    import csv
    import io
    
    if not registrations:
        return None
    
    # Create CSV content
    output = io.StringIO()
    
    # Determine fields based on registration type
    if registrations[0].get("registration_type") == "group":
        fieldnames = [
            "Registration ID", "Date", "Status", "Team Name", "Team Leader", 
            "Leader Email", "Leader Phone", "Leader USN", "Team Size", 
            "College", "Branch", "Semester", "Year"
        ]
    else:
        fieldnames = [
            "Registration ID", "Date", "Status", "Name", "Email", "Phone", 
            "USN", "College", "Branch", "Section", "Semester", "Year"
        ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for reg in registrations:
        if reg.get("registration_type") == "group":
            row = {
                "Registration ID": reg.get("id", ""),
                "Date": reg.get("registration_date", ""),
                "Status": reg.get("status", ""),
                "Team Name": reg.get("team_name", ""),
                "Team Leader": reg.get("team_leader_name", ""),
                "Leader Email": reg.get("team_leader_email", ""),
                "Leader Phone": reg.get("team_leader_phone", ""),
                "Leader USN": reg.get("team_leader_usn", ""),
                "Team Size": reg.get("team_size", ""),
                "College": reg.get("college", reg.get("user_college", "")),
                "Branch": reg.get("team_leader_branch", reg.get("branch", "")),
                "Semester": reg.get("team_leader_semester", reg.get("semester", "")),
                "Year": reg.get("team_leader_year", reg.get("year", ""))
            }
        else:
            row = {
                "Registration ID": reg.get("id", ""),
                "Date": reg.get("registration_date", ""),
                "Status": reg.get("status", ""),
                "Name": reg.get("full_name", reg.get("user_name", "")),
                "Email": reg.get("email", reg.get("user_email", "")),
                "Phone": reg.get("phone_number", ""),
                "USN": reg.get("usn", ""),
                "College": reg.get("college", reg.get("user_college", "")),
                "Branch": reg.get("branch", ""),
                "Section": reg.get("section", ""),
                "Semester": reg.get("semester", ""),
                "Year": reg.get("year", "")
            }
        writer.writerow(row)
    
    # Save to file
    filename = f"registrations_{event_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = f"/app/exports/{filename}"
    
    os.makedirs("/app/exports", exist_ok=True)
    
    with open(filepath, "w") as f:
        f.write(output.getvalue())
    
    return f"/exports/{filename}"
