"""
Fix Campus Rankings - Populate campus_leaderboards collection
This script calculates and updates campus rankings for all active competitions
"""

import asyncio
from datetime import datetime, timezone
from database import get_database
import uuid

async def update_campus_rankings():
    """Update campus rankings for all competitions"""
    db = await get_database()
    
    print("🔄 Starting campus rankings update...")
    
    # Get all active/upcoming competitions
    competitions = await db.inter_college_competitions.find({
        "status": {"$in": ["active", "upcoming"]}
    }).to_list(None)
    
    print(f"📊 Found {len(competitions)} active/upcoming competitions")
    
    for competition in competitions:
        competition_id = competition["id"]
        print(f"\n🏆 Processing: {competition.get('title', 'Untitled')}")
        
        # Get all participations for this competition
        participations = await db.campus_competition_participations.find({
            "competition_id": competition_id
        }).to_list(None)
        
        if not participations:
            print(f"   ⚠️  No participations found")
            continue
            
        # Group by campus and calculate scores
        campus_scores = {}
        for participation in participations:
            user_id = participation["user_id"]
            
            # Get user details
            user = await db.users.find_one({"id": user_id})
            if not user or not user.get("university"):
                continue
                
            campus = user["university"]
            score = participation.get("current_score", 0)
            
            if campus not in campus_scores:
                campus_scores[campus] = {
                    "total_score": 0,
                    "participants": 0,
                    "top_performers": []
                }
            
            campus_scores[campus]["total_score"] += score
            campus_scores[campus]["participants"] += 1
            campus_scores[campus]["top_performers"].append({
                "user_id": user_id,
                "name": user.get("full_name", "Unknown"),
                "score": score
            })
        
        # Sort campuses by total score
        sorted_campuses = sorted(
            campus_scores.items(),
            key=lambda x: x[1]["total_score"],
            reverse=True
        )
        
        # Update campus_leaderboards collection
        for rank, (campus, data) in enumerate(sorted_campuses, 1):
            # Sort top performers
            data["top_performers"] = sorted(
                data["top_performers"],
                key=lambda x: x["score"],
                reverse=True
            )[:10]  # Keep top 10
            
            # Upsert campus leaderboard entry
            await db.campus_leaderboards.update_one(
                {
                    "competition_id": competition_id,
                    "campus": campus
                },
                {
                    "$set": {
                        "competition_id": competition_id,
                        "campus": campus,
                        "campus_rank": rank,
                        "total_score": data["total_score"],
                        "total_participants": data["participants"],
                        "top_performers": data["top_performers"],
                        "updated_at": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
            
            print(f"   ✅ #{rank} {campus}: {data['participants']} participants, {data['total_score']} points")
    
    print("\n✅ Campus rankings update completed!")

async def main():
    try:
        await update_campus_rankings()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
