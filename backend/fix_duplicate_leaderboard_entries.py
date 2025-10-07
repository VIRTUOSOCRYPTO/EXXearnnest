#!/usr/bin/env python3
"""
Fix duplicate leaderboard entries - ensure each user appears only once per leaderboard type/period
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add backend directory to path
sys.path.append(os.path.dirname(__file__))

from database import get_database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_duplicate_leaderboard_entries():
    """Remove duplicate leaderboard entries - keep only one entry per user per leaderboard type/period"""
    
    try:
        db = await get_database()
        
        logger.info("🔧 Fixing duplicate leaderboard entries...")
        
        # Get all leaderboard types and periods
        leaderboard_types = ["savings", "streak", "points", "goals"]
        periods = ["weekly", "monthly", "all_time"]
        
        total_removed = 0
        
        for lb_type in leaderboard_types:
            for period in periods:
                logger.info(f"📊 Processing {lb_type} {period} leaderboard...")
                
                # Find users with multiple entries in this leaderboard type/period
                pipeline = [
                    {
                        "$match": {
                            "leaderboard_type": lb_type,
                            "period": period
                        }
                    },
                    {
                        "$group": {
                            "_id": "$user_id",
                            "entries": {
                                "$push": {
                                    "doc_id": "$_id",
                                    "university": "$university",
                                    "score": "$score",
                                    "updated_at": "$updated_at"
                                }
                            },
                            "count": {"$sum": 1}
                        }
                    },
                    {
                        "$match": {"count": {"$gt": 1}}
                    }
                ]
                
                users_with_duplicates = await db.leaderboards.aggregate(pipeline).to_list(None)
                
                for user_duplicate in users_with_duplicates:
                    user_id = user_duplicate["_id"]
                    entries = user_duplicate["entries"]
                    
                    # Sort entries to prioritize:
                    # 1. University-specific entries (non-null university) over global (null university)
                    # 2. Higher scores
                    # 3. More recent updates
                    entries.sort(key=lambda x: (
                        x["university"] is not None,  # Prioritize university-specific
                        x["score"],                   # Higher score
                        x["updated_at"] or datetime.min  # More recent
                    ), reverse=True)
                    
                    # Keep the first (best) entry, remove the rest
                    entries_to_keep = entries[0]
                    entries_to_remove = entries[1:]
                    
                    if entries_to_remove:
                        doc_ids_to_remove = [entry["doc_id"] for entry in entries_to_remove]
                        
                        result = await db.leaderboards.delete_many({
                            "_id": {"$in": doc_ids_to_remove}
                        })
                        
                        total_removed += result.deleted_count
                        logger.info(f"🗑️ Removed {result.deleted_count} duplicate entries for user {user_id} in {lb_type} {period}")
        
        logger.info(f"✅ Total duplicate entries removed: {total_removed}")
        
        # Now recalculate ranks for all leaderboards
        logger.info("🔄 Recalculating leaderboard ranks...")
        
        for lb_type in leaderboard_types:
            for period in periods:
                # Get all entries for this leaderboard type/period sorted by score
                entries = await db.leaderboards.find({
                    "leaderboard_type": lb_type,
                    "period": period
                }).sort("score", -1).to_list(None)
                
                # Update ranks
                for i, entry in enumerate(entries):
                    await db.leaderboards.update_one(
                        {"_id": entry["_id"]},
                        {"$set": {"rank": i + 1}}
                    )
        
        logger.info("✅ Leaderboard ranks recalculated")
        
        # Final verification
        logger.info("🔍 Final verification...")
        
        for lb_type in leaderboard_types:
            for period in periods:
                # Check for remaining duplicates
                pipeline = [
                    {
                        "$match": {
                            "leaderboard_type": lb_type,
                            "period": period
                        }
                    },
                    {
                        "$group": {
                            "_id": "$user_id",
                            "count": {"$sum": 1}
                        }
                    },
                    {
                        "$match": {"count": {"$gt": 1}}
                    }
                ]
                
                remaining_duplicates = await db.leaderboards.aggregate(pipeline).to_list(None)
                
                if remaining_duplicates:
                    logger.warning(f"⚠️ Still found {len(remaining_duplicates)} duplicates in {lb_type} {period}")
                else:
                    entry_count = await db.leaderboards.count_documents({
                        "leaderboard_type": lb_type,
                        "period": period
                    })
                    logger.info(f"✅ {lb_type} {period}: {entry_count} unique entries")
        
        logger.info("🎉 Leaderboard duplicate fix completed!")
        
        return {
            "duplicates_removed": total_removed,
            "leaderboards_processed": len(leaderboard_types) * len(periods)
        }
        
    except Exception as e:
        logger.error(f"❌ Error fixing duplicates: {str(e)}")
        raise

async def main():
    """Main function"""
    logger.info("🚀 Starting leaderboard duplicate fix...")
    
    result = await fix_duplicate_leaderboard_entries()
    
    logger.info("✅ Fix completed!")
    logger.info(f"📊 Summary: {result}")
    
    return result

if __name__ == "__main__":
    asyncio.run(main())
