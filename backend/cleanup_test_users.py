#!/usr/bin/env python3
"""
Clean up test users and ensure only real registered users appear in leaderboards
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add backend directory to path
sys.path.append(os.path.dirname(__file__))

from database import get_database
from gamification_service import GamificationService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def cleanup_test_users_and_fake_data():
    """Remove test users and ensure only real registered users appear in leaderboards"""
    
    try:
        db = await get_database()
        
        logger.info("🧹 Cleaning up test users and fake leaderboard data...")
        
        # 1. REMOVE ALL TEST USERS I CREATED
        logger.info("🗑️ Removing test users...")
        
        test_user_emails = [
            "test1@example.com",
            "test2@example.com", 
            "test3@example.com",
            "test4@example.com",
            "test5@example.com"
        ]
        
        # Remove test users
        deleted_users = await db.users.delete_many({
            "email": {"$in": test_user_emails}
        })
        logger.info(f"🗑️ Removed {deleted_users.deleted_count} test users")
        
        # Remove their referral programs
        deleted_referrals = await db.referral_programs.delete_many({
            "referrer_id": {"$regex": "^68e4c08"}  # Test user ID pattern
        })
        logger.info(f"🗑️ Removed {deleted_referrals.deleted_count} test referral programs")
        
        # Remove their transactions
        deleted_transactions = await db.transactions.delete_many({
            "user_id": {"$regex": "^68e4c08"}  # Test user ID pattern
        })
        logger.info(f"🗑️ Removed {deleted_transactions.deleted_count} test transactions")
        
        # Remove their friendships
        deleted_friendships = await db.friendships.delete_many({
            "$or": [
                {"user1_id": {"$regex": "^68e4c08"}},
                {"user2_id": {"$regex": "^68e4c08"}}
            ]
        })
        logger.info(f"🗑️ Removed {deleted_friendships.deleted_count} test friendships")
        
        # 2. CLEAN ALL LEADERBOARD ENTRIES
        logger.info("🧹 Cleaning all leaderboard entries...")
        
        # Remove ALL leaderboard entries (we'll repopulate with real users only)
        deleted_leaderboards = await db.leaderboards.delete_many({})
        logger.info(f"🗑️ Removed {deleted_leaderboards.deleted_count} leaderboard entries")
        
        # 3. GET REAL REGISTERED USERS ONLY
        logger.info("👥 Finding real registered users...")
        
        # Find users who registered normally (not test users)
        real_users = await db.users.find({
            "email": {"$nin": test_user_emails},  # Exclude test emails
            "is_active": True,
            "email_verified": True
        }).to_list(None)
        
        logger.info(f"✅ Found {len(real_users)} real registered users")
        
        if len(real_users) == 0:
            logger.info("ℹ️ No real registered users found. Leaderboards will be empty until users register.")
            return {
                "test_users_removed": deleted_users.deleted_count,
                "leaderboard_entries_cleaned": deleted_leaderboards.deleted_count,
                "real_users_found": 0
            }
        
        # 4. POPULATE LEADERBOARDS WITH REAL USERS ONLY
        logger.info("🏆 Populating leaderboards with real registered users only...")
        
        gamification = GamificationService(db)
        updated_count = 0
        
        for user in real_users:
            try:
                user_id = user.get("id") or str(user["_id"])
                await gamification.update_leaderboards(user_id)
                updated_count += 1
                logger.info(f"✅ Updated leaderboards for real user: {user.get('full_name', 'Unknown')}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to update leaderboard for user {user.get('full_name', 'Unknown')}: {str(e)}")
                continue
        
        # 5. VERIFY FINAL STATE
        logger.info("🔍 Verifying final leaderboard state...")
        
        total_lb_entries = await db.leaderboards.count_documents({})
        total_users = await db.users.count_documents({"is_active": True})
        
        logger.info(f"📊 Final state:")
        logger.info(f"   👥 Active users: {total_users}")
        logger.info(f"   🏆 Leaderboard entries: {total_lb_entries}")
        
        # Show sample leaderboard data if any
        if total_lb_entries > 0:
            sample_entries = await db.leaderboards.find({
                "leaderboard_type": "savings",
                "period": "weekly"
            }).limit(5).to_list(None)
            
            logger.info("📋 Sample leaderboard entries:")
            for entry in sample_entries:
                user_data = await db.users.find_one({"id": entry["user_id"]})
                if user_data:
                    logger.info(f"   {entry['rank']}. {user_data.get('full_name', 'Unknown')} - Score: {entry['score']}")
        
        logger.info("🎉 Cleanup completed! Only real registered users will appear in leaderboards.")
        
        return {
            "test_users_removed": deleted_users.deleted_count,
            "leaderboard_entries_cleaned": deleted_leaderboards.deleted_count,
            "real_users_found": len(real_users),
            "leaderboards_updated": updated_count
        }
        
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {str(e)}")
        raise

async def main():
    """Main function"""
    logger.info("🚀 Starting cleanup of test users and fake data...")
    
    result = await cleanup_test_users_and_fake_data()
    
    logger.info("✅ Cleanup completed!")
    logger.info(f"📊 Summary: {result}")
    
    return result

if __name__ == "__main__":
    asyncio.run(main())
