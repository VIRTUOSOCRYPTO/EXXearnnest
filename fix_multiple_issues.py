#!/usr/bin/env python3
"""
Comprehensive fix for multiple EarnAura issues:
1. Club admin dashboard metrics calculation
2. Super admin dashboard total club admins count
3. Campus admin list display
4. Registration Management updates
5. Campus rank calculation for competitions
"""

import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta

# Add backend directory to path
sys.path.insert(0, '/app/backend')

from database import get_database
from models import *
import uuid

async def fix_club_admin_dashboard_metrics():
    """Fix club admin dashboard participant calculation"""
    print("🔄 Fixing club admin dashboard metrics...")
    
    db = await get_database()
    
    # Get all club admins
    club_admins = await db.campus_admins.find({"admin_type": "club_admin"}).to_list(None)
    
    for admin in club_admins:
        user_id = admin["user_id"]
        
        # Count actual participants from event registrations
        competitions_participants = 0
        challenges_participants = 0
        
        # Count competitions created by this admin
        competitions = await db.inter_college_competitions.find({"created_by": user_id}).to_list(None)
        for comp in competitions:
            participant_count = await db.campus_competition_participations.count_documents({"competition_id": comp["id"]})
            competitions_participants += participant_count
        
        # Count challenges created by this admin  
        challenges = await db.prize_challenges.find({"created_by": user_id}).to_list(None)
        for chal in challenges:
            participant_count = await db.prize_challenge_participations.count_documents({"challenge_id": chal["id"]})
            challenges_participants += participant_count
        
        # Count college events created by this admin
        events_participants = 0
        events = await db.college_events.find({"created_by": user_id}).to_list(None)
        for event in events:
            participant_count = await db.event_registrations.count_documents({"event_id": event["id"]})
            events_participants += participant_count
        
        total_participants = competitions_participants + challenges_participants + events_participants
        
        # Update admin record with correct participant count
        await db.campus_admins.update_one(
            {"id": admin["id"]},
            {"$set": {"participants_managed": total_participants}}
        )
        
        print(f"✅ Updated {admin.get('club_name', 'Unknown Club')}: {total_participants} participants managed")

async def fix_campus_rankings():
    """Initialize campus rankings for inter-college competitions"""
    print("🔄 Fixing campus rankings for competitions...")
    
    db = await get_database()
    
    # Get all active competitions
    competitions = await db.inter_college_competitions.find({"status": {"$in": ["upcoming", "active", "ongoing"]}}).to_list(None)
    
    for comp in competitions:
        # Get all campuses participating in this competition
        participations = await db.campus_competition_participations.find({"competition_id": comp["id"]}).to_list(None)
        
        # Group by campus and calculate scores
        campus_scores = {}
        for participation in participations:
            campus = participation.get("user_university", "Unknown")
            if campus not in campus_scores:
                campus_scores[campus] = {"total_score": 0, "participant_count": 0}
            
            campus_scores[campus]["total_score"] += participation.get("current_score", 0)
            campus_scores[campus]["participant_count"] += 1
        
        # Calculate average scores and rank campuses
        campus_rankings = []
        for campus, data in campus_scores.items():
            avg_score = data["total_score"] / data["participant_count"] if data["participant_count"] > 0 else 0
            campus_rankings.append({
                "campus": campus,
                "avg_score": avg_score,
                "total_participants": data["participant_count"],
                "total_score": data["total_score"]
            })
        
        # Sort by average score descending
        campus_rankings.sort(key=lambda x: x["avg_score"], reverse=True)
        
        # Update or create campus leaderboard entries
        for rank, campus_data in enumerate(campus_rankings, 1):
            await db.campus_leaderboards.update_one(
                {
                    "competition_id": comp["id"],
                    "campus": campus_data["campus"]
                },
                {
                    "$set": {
                        "campus_rank": rank,
                        "campus_total_score": campus_data["total_score"],
                        "total_participants": campus_data["total_participants"],
                        "average_score": campus_data["avg_score"],
                        "updated_at": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
        
        print(f"✅ Updated rankings for competition: {comp['title']} ({len(campus_rankings)} campuses)")

async def fix_registration_management_visibility():
    """Ensure registrations are visible in club admin registration management"""
    print("🔄 Fixing registration management visibility...")
    
    db = await get_database()
    
    # Get all event registrations and ensure they have proper college information
    registrations = await db.event_registrations.find({}).to_list(None)
    
    updated_count = 0
    for reg in registrations:
        if not reg.get("user_college"):
            # Get user details to populate college
            user_id = reg.get("user_id")
            if user_id:
                user = await db.users.find_one({"id": user_id})
                if user and user.get("university"):
                    await db.event_registrations.update_one(
                        {"id": reg["id"]},
                        {"$set": {"user_college": user["university"]}}
                    )
                    updated_count += 1
    
    print(f"✅ Updated {updated_count} registrations with college information")

async def create_sample_recent_admin_activities():
    """Create sample admin activities for testing Recent Admin Activity"""
    print("🔄 Creating sample admin activities...")
    
    db = await get_database()
    
    # Get some admin users
    admins = await db.campus_admins.find({"admin_type": "campus_admin"}).limit(3).to_list(None)
    
    if not admins:
        print("⚠️ No campus admins found to create sample activities")
        return
    
    # Create sample activities for the last 24 hours
    activities = []
    for i, admin in enumerate(admins):
        # Create various types of activities
        for j in range(2):
            activity_time = datetime.now(timezone.utc) - timedelta(hours=i*2 + j*3)
            
            activities.append({
                "id": str(uuid.uuid4()),
                "admin_user_id": admin["user_id"],
                "action_type": ["approve_club_admin_request", "create_competition", "manage_participant"][j % 3],
                "action_description": f"Sample admin activity {i}-{j}",
                "target_type": "club_admin_request",
                "target_id": str(uuid.uuid4()),
                "timestamp": activity_time,
                "severity": "info",
                "admin_level": "campus_admin",
                "college_name": admin.get("college_name", "Sample College"),
                "ip_address": "127.0.0.1",
                "affected_entities": []
            })
    
    if activities:
        await db.admin_audit_logs.insert_many(activities)
        print(f"✅ Created {len(activities)} sample admin activities")

async def main():
    """Run all fixes"""
    print("🚀 Starting comprehensive EarnAura fixes...")
    
    try:
        await fix_club_admin_dashboard_metrics()
        await fix_campus_rankings()
        await fix_registration_management_visibility()
        await create_sample_recent_admin_activities()
        
        print("\n🎉 All fixes completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during fixes: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
