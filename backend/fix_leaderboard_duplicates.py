#!/usr/bin/env python3
"""
Fix Leaderboard Duplicates and Ensure Real Users Only
Fixes the issues mentioned by user:
1. Live ranking repeating users along with new users again and again
2. Ensures only real active users appear in leaderboards
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
import logging

# Add backend directory to path
sys.path.append(os.path.dirname(__file__))

from database import get_database
from gamification_service import GamificationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_leaderboard_duplicates():
    """Clean up duplicate leaderboard entries and populate with real users only"""
    
    try:
        db = await get_database()
        
        logger.info("🚀 Starting leaderboard cleanup and fix...")
        
        # 1. GET ALL REAL USER IDs
        logger.info("📋 Getting all real user IDs...")
        real_user_ids = set()
        
        async for user in db.users.find({}, {"id": 1, "_id": 1}):
            if "id" in user:
                real_user_ids.add(user["id"])
            if "_id" in user:
                real_user_ids.add(str(user["_id"]))
        
        logger.info(f"✅ Found {len(real_user_ids)} real users")
        
        # 2. REMOVE ALL FAKE/DUPLICATE LEADERBOARD ENTRIES
        logger.info("🗑️ Removing fake leaderboard entries...")
        
        # Delete leaderboard entries that don't correspond to real users
        deleted_fake = await db.leaderboards.delete_many({
            "user_id": {"$nin": list(real_user_ids)}
        })
        logger.info(f"🗑️ Removed {deleted_fake.deleted_count} fake leaderboard entries")
        
        # 3. REMOVE DUPLICATE ENTRIES FOR SAME USER (INCLUDING UNIVERSITY-SPECIFIC ONES)
        logger.info("🔍 Removing duplicate entries for same users...")
        
        # Find and remove duplicate entries (same user_id, leaderboard_type, period)
        # Handle both global and university-specific entries properly
        duplicates_removed = 0
        
        # Get all unique combinations - treating null/missing university as different from actual university
        unique_combinations = await db.leaderboards.aggregate([
            {
                "$group": {
                    "_id": {
                        "user_id": "$user_id",
                        "leaderboard_type": "$leaderboard_type", 
                        "period": "$period",
                        "university": {"$ifNull": ["$university", "__global__"]}  # Handle null university
                    },
                    "docs": {"$push": {"_id": "$_id", "updated_at": "$updated_at"}},
                    "count": {"$sum": 1}
                }
            },
            {"$match": {"count": {"$gt": 1}}}
        ]).to_list(None)
        
        for combo in unique_combinations:
            # Keep the most recently updated document, remove the rest
            docs = combo["docs"]
            docs.sort(key=lambda x: x.get("updated_at", datetime.min), reverse=True)
            docs_to_remove = [doc["_id"] for doc in docs[1:]]  # All but the most recent
            
            if docs_to_remove:
                result = await db.leaderboards.delete_many({
                    "_id": {"$in": docs_to_remove}
                })
                duplicates_removed += result.deleted_count
        
        logger.info(f"🗑️ Removed {duplicates_removed} duplicate leaderboard entries")
        
        # 4. POPULATE LEADERBOARDS WITH REAL ACTIVE USERS
        logger.info("🏆 Populating leaderboards with real active users...")
        
        # Get real active users
        active_users = await db.users.find({
            "is_active": True,
            "email_verified": True
        }).to_list(None)
        
        if not active_users:
            logger.warning("⚠️ No active users found!")
            return
        
        logger.info(f"👥 Found {len(active_users)} active users")
        
        # Update leaderboards for all active users
        gamification = GamificationService(db)
        updated_count = 0
        
        for user in active_users:
            try:
                user_id = user.get("id") or str(user["_id"])
                await gamification.update_leaderboards(user_id)
                updated_count += 1
                
                if updated_count % 10 == 0:
                    logger.info(f"🔄 Updated leaderboards for {updated_count} users...")
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to update leaderboard for user {user.get('full_name', 'Unknown')}: {str(e)}")
                continue
        
        logger.info(f"✅ Updated leaderboards for {updated_count} real users")
        
        # 5. VERIFY LEADERBOARD INTEGRITY
        logger.info("🔍 Verifying leaderboard integrity...")
        
        # Count entries per leaderboard type
        for lb_type in ["savings", "streak", "points", "goals"]:
            for period in ["weekly", "monthly", "all_time"]:
                count = await db.leaderboards.count_documents({
                    "leaderboard_type": lb_type,
                    "period": period
                })
                logger.info(f"📊 {lb_type.capitalize()} {period}: {count} entries")
        
        # Check for users with multiple entries (should not exist after cleanup)
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "user_id": "$user_id",
                        "leaderboard_type": "$leaderboard_type",
                        "period": "$period"
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$match": {"count": {"$gt": 1}}}
        ]
        
        remaining_duplicates = await db.leaderboards.aggregate(pipeline).to_list(None)
        if remaining_duplicates:
            logger.warning(f"⚠️ Still found {len(remaining_duplicates)} potential duplicates")
        else:
            logger.info("✅ No duplicate entries found - leaderboards are clean!")
        
        logger.info("🎉 Leaderboard cleanup and fix completed successfully!")
        
        return {
            "fake_entries_removed": deleted_fake.deleted_count,
            "duplicates_removed": duplicates_removed,
            "users_updated": updated_count,
            "real_users_found": len(real_user_ids),
            "active_users_found": len(active_users)
        }
        
    except Exception as e:
        logger.error(f"❌ Error during leaderboard cleanup: {str(e)}")
        raise

async def main():
    """Main function to run the leaderboard fix"""
    logger.info("🚀 Starting Leaderboard Duplicate Fix...")
    
    result = await fix_leaderboard_duplicates()
    
    logger.info("✅ Leaderboard fix completed!")
    logger.info(f"📊 Summary: {result}")
    
    return result

if __name__ == "__main__":
    asyncio.run(main())
