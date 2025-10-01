"""
Background task to process referral bonuses and update referral statuses
Run this script daily as a cron job
"""
import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(__file__))

from database import get_database
import logging

logger = logging.getLogger(__name__)

async def process_30_day_activity_bonuses():
    """Process 30-day activity bonuses for referred users"""
    try:
        db = await get_database()
        
        # Find users who signed up 30 days ago and are still pending
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        
        pending_referrals = await db.referred_users.find({
            "status": "pending",
            "signed_up_at": {"$lte": thirty_days_ago}
        }).to_list(None)
        
        processed_count = 0
        
        for referral in pending_referrals:
            try:
                user_id = referral["referred_user_id"]
                referrer_id = referral["referrer_id"]
                
                # Check if user has been active (has transactions in last 30 days)
                recent_activity = await db.transactions.find_one({
                    "user_id": user_id,
                    "date": {"$gte": thirty_days_ago}
                })
                
                if recent_activity:
                    # User is active - award bonus
                    
                    # Create ₹200 activity bonus for referrer
                    activity_earning = {
                        "referrer_id": referrer_id,
                        "referred_user_id": user_id,
                        "earning_type": "activity_bonus",
                        "amount": 200.0,
                        "description": f"30-day activity bonus for active referral",
                        "status": "confirmed",
                        "created_at": datetime.now(timezone.utc),
                        "confirmed_at": datetime.now(timezone.utc)
                    }
                    await db.referral_earnings.insert_one(activity_earning)
                    
                    # Update referrer's earnings and successful referrals count
                    await db.referral_programs.update_one(
                        {"referrer_id": referrer_id},
                        {
                            "$inc": {
                                "total_earnings": 200.0,
                                "successful_referrals": 1
                            }
                        }
                    )
                    
                    # Update referred user status to completed
                    await db.referred_users.update_one(
                        {"_id": referral["_id"]},
                        {
                            "$set": {
                                "status": "completed",
                                "completed_at": datetime.now(timezone.utc),
                                "earnings_awarded": 250.0  # Total: 50 signup + 200 activity
                            }
                        }
                    )
                    
                    logger.info(f"Processed 30-day bonus for referral: {referrer_id} -> {user_id}")
                    processed_count += 1
                    
                else:
                    # User is inactive - mark as inactive
                    await db.referred_users.update_one(
                        {"_id": referral["_id"]},
                        {"$set": {"status": "inactive"}}
                    )
                    logger.info(f"Marked referral as inactive: {referrer_id} -> {user_id}")
                    
            except Exception as e:
                logger.error(f"Error processing referral {referral.get('_id')}: {str(e)}")
                continue
        
        logger.info(f"Processed {processed_count} 30-day activity bonuses")
        return processed_count
        
    except Exception as e:
        logger.error(f"Error in process_30_day_activity_bonuses: {str(e)}")
        return 0

async def process_milestone_bonuses():
    """Process milestone bonuses for referrers who hit 5, 10, 20+ successful referrals"""
    try:
        db = await get_database()
        
        # Get all referrers with successful referrals
        referrers = await db.referral_programs.find({
            "successful_referrals": {"$gte": 5}
        }).to_list(None)
        
        processed_count = 0
        
        for referrer in referrers:
            try:
                referrer_id = referrer["referrer_id"]
                successful_referrals = referrer["successful_referrals"]
                
                # Check which milestones they've hit
                milestones = []
                if successful_referrals >= 5 and successful_referrals < 10:
                    milestones.append((5, 500))  # ₹500 for 5 referrals
                elif successful_referrals >= 10 and successful_referrals < 20:
                    milestones.extend([(5, 500), (10, 1000)])  # ₹1000 for 10 referrals
                elif successful_referrals >= 20:
                    milestones.extend([(5, 500), (10, 1000), (20, 2000)])  # ₹2000 for 20 referrals
                
                for milestone_count, bonus_amount in milestones:
                    # Check if milestone bonus already awarded
                    existing_bonus = await db.referral_earnings.find_one({
                        "referrer_id": referrer_id,
                        "earning_type": "milestone_bonus",
                        "description": {"$regex": f"{milestone_count} referrals"}
                    })
                    
                    if not existing_bonus:
                        # Award milestone bonus
                        milestone_earning = {
                            "referrer_id": referrer_id,
                            "referred_user_id": None,
                            "earning_type": "milestone_bonus",
                            "amount": float(bonus_amount),
                            "description": f"Milestone bonus for {milestone_count} successful referrals",
                            "status": "confirmed",
                            "created_at": datetime.now(timezone.utc),
                            "confirmed_at": datetime.now(timezone.utc)
                        }
                        await db.referral_earnings.insert_one(milestone_earning)
                        
                        # Update referrer's total earnings
                        await db.referral_programs.update_one(
                            {"referrer_id": referrer_id},
                            {"$inc": {"total_earnings": bonus_amount}}
                        )
                        
                        logger.info(f"Awarded {milestone_count}-referral milestone bonus of ₹{bonus_amount} to {referrer_id}")
                        processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing milestone for referrer {referrer.get('referrer_id')}: {str(e)}")
                continue
        
        logger.info(f"Processed {processed_count} milestone bonuses")
        return processed_count
        
    except Exception as e:
        logger.error(f"Error in process_milestone_bonuses: {str(e)}")
        return 0

async def main():
    """Main function to run all referral processing tasks"""
    logger.info("🚀 Starting referral bonus processing...")
    
    activity_bonuses = await process_30_day_activity_bonuses()
    milestone_bonuses = await process_milestone_bonuses()
    
    total_processed = activity_bonuses + milestone_bonuses
    logger.info(f"✅ Completed referral processing. Total bonuses processed: {total_processed}")
    
    return total_processed

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())
