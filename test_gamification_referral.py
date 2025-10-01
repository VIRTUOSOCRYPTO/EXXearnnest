#!/usr/bin/env python3
"""
Comprehensive test script for gamification and referral systems
Tests ObjectId serialization issues and referral system functionality
"""

import asyncio
import sys
import json
import uuid
from datetime import datetime, timezone, timedelta
from bson import ObjectId

sys.path.append('/app/backend')
from database import get_database, get_user_by_id
from gamification_service import get_gamification_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GamificationReferralTester:
    def __init__(self):
        self.db = None
        self.gamification = None
        self.test_results = {}
        
    async def setup(self):
        """Initialize database and services"""
        try:
            self.db = await get_database()
            self.gamification = await get_gamification_service()
            logger.info("✅ Services initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            return False
    
    async def test_gamification_serialization(self):
        """Test ObjectId serialization in gamification endpoints"""
        test_name = "Gamification ObjectId Serialization"
        try:
            # Create a test user if not exists
            test_user_id = "test_gamification_user"
            
            # Test profile endpoint
            profile = await self.gamification.get_user_gamification_profile(test_user_id)
            
            # Try to serialize to JSON - this will fail if ObjectIds are present
            json_str = json.dumps(profile)
            
            # Test leaderboard endpoint
            leaderboard = await self.gamification.get_leaderboard("points", "all_time", limit=5)
            leaderboard_json = json.dumps(leaderboard)
            
            # Test badge initialization
            await self.gamification.initialize_badges()
            
            # Get a sample badge and check if it has ObjectId issues
            badges = await self.db.badges.find().limit(1).to_list(None)
            if badges:
                badge = badges[0]
                # This should be handled properly in the service
                badge_id_str = str(badge["_id"])
                
            self.test_results[test_name] = {
                "status": "✅ PASSED",
                "message": "All gamification objects serialize to JSON correctly",
                "profile_keys": list(profile.keys()) if profile else [],
                "leaderboard_keys": list(leaderboard.keys()) if leaderboard else []
            }
            
        except TypeError as e:
            if "ObjectId" in str(e):
                self.test_results[test_name] = {
                    "status": "❌ FAILED",
                    "message": f"ObjectId serialization error: {e}",
                    "error_type": "ObjectId JSON serialization"
                }
            else:
                self.test_results[test_name] = {
                    "status": "❌ FAILED", 
                    "message": f"JSON serialization error: {e}",
                    "error_type": "JSON serialization"
                }
        except Exception as e:
            self.test_results[test_name] = {
                "status": "❌ FAILED",
                "message": f"Gamification test error: {e}",
                "error_type": "General error"
            }
    
    async def test_referral_collections(self):
        """Test referral system database collections consistency"""
        test_name = "Referral Database Collections"
        try:
            collections = await self.db.list_collection_names()
            
            # Check required collections
            required_collections = ["referral_programs", "referred_users", "referral_earnings"]
            missing_collections = []
            existing_collections = []
            
            for col in required_collections:
                if col in collections:
                    count = await self.db[col].count_documents({})
                    existing_collections.append(f"{col}: {count} documents")
                else:
                    missing_collections.append(col)
            
            # Check for the incorrect collection name
            incorrect_collection = "referrals" in collections
            
            if missing_collections:
                self.test_results[test_name] = {
                    "status": "⚠️ WARNING",
                    "message": f"Missing collections: {missing_collections}",
                    "existing": existing_collections,
                    "incorrect_collection_exists": incorrect_collection
                }
            else:
                self.test_results[test_name] = {
                    "status": "✅ PASSED",
                    "message": "All referral collections exist",
                    "existing": existing_collections,
                    "incorrect_collection_exists": incorrect_collection
                }
                
        except Exception as e:
            self.test_results[test_name] = {
                "status": "❌ FAILED",
                "message": f"Collection test error: {e}",
                "error_type": "Database error"
            }
    
    async def test_referral_bonus_processing(self):
        """Test referral bonus processing script functionality"""
        test_name = "Referral Bonus Processing"
        try:
            # Test if we can run the referral bonus functions
            from process_referral_bonuses import process_30_day_activity_bonuses, process_milestone_bonuses
            
            # These functions should run without database errors (even if no data to process)
            activity_result = await process_30_day_activity_bonuses()
            milestone_result = await process_milestone_bonuses()
            
            self.test_results[test_name] = {
                "status": "✅ PASSED",
                "message": "Referral bonus processing functions run without errors",
                "activity_bonuses_processed": activity_result,
                "milestone_bonuses_processed": milestone_result
            }
            
        except Exception as e:
            self.test_results[test_name] = {
                "status": "❌ FAILED",
                "message": f"Referral bonus processing error: {e}",
                "error_type": "Processing error"
            }
    
    async def test_gamification_api_endpoints(self):
        """Test gamification API endpoint data structures"""
        test_name = "Gamification API Endpoints"
        try:
            # Test badge creation and retrieval
            test_user_id = "test_api_user"
            
            # Test badge checking
            badges_earned = await self.gamification.check_and_award_badges(
                test_user_id, 
                "test_event", 
                {"test_data": "test"}
            )
            
            # Test streak update
            await self.gamification.update_user_streak(test_user_id)
            
            # Test leaderboard update
            await self.gamification.update_leaderboards(test_user_id)
            
            # Test achievement creation
            achievement_id = await self.gamification.create_milestone_achievement(
                test_user_id,
                "first_transaction",
                {"amount": 100}
            )
            
            self.test_results[test_name] = {
                "status": "✅ PASSED",
                "message": "All gamification API functions execute successfully",
                "badges_earned": len(badges_earned) if badges_earned else 0,
                "achievement_created": bool(achievement_id)
            }
            
        except Exception as e:
            self.test_results[test_name] = {
                "status": "❌ FAILED",
                "message": f"Gamification API error: {e}",
                "error_type": "API error"
            }
    
    async def test_referral_api_simulation(self):
        """Simulate referral system API calls"""
        test_name = "Referral System API Simulation"
        try:
            # Create test referral program entry
            test_referrer_id = f"test_referrer_{uuid.uuid4().hex[:8]}"
            referral_code = f"TEST{uuid.uuid4().hex[:6].upper()}"
            
            # Test referral program creation
            referral_data = {
                "referrer_id": test_referrer_id,
                "referral_code": referral_code,
                "total_referrals": 0,
                "successful_referrals": 0,
                "total_earnings": 0.0,
                "pending_earnings": 0.0,
                "created_at": datetime.now(timezone.utc)
            }
            
            result = await self.db.referral_programs.insert_one(referral_data)
            
            # Test referral lookup
            found_referral = await self.db.referral_programs.find_one({
                "referral_code": referral_code
            })
            
            # Test earnings creation
            earning_data = {
                "referrer_id": test_referrer_id,
                "referred_user_id": "test_referred_user",
                "earning_type": "signup_bonus",
                "amount": 50.0,
                "description": "Test signup bonus",
                "status": "confirmed",
                "created_at": datetime.now(timezone.utc),
                "confirmed_at": datetime.now(timezone.utc)
            }
            
            await self.db.referral_earnings.insert_one(earning_data)
            
            # Clean up test data
            await self.db.referral_programs.delete_one({"_id": result.inserted_id})
            await self.db.referral_earnings.delete_one({"referrer_id": test_referrer_id})
            
            self.test_results[test_name] = {
                "status": "✅ PASSED",
                "message": "Referral system CRUD operations work correctly",
                "referral_created": bool(result.inserted_id),
                "referral_found": bool(found_referral)
            }
            
        except Exception as e:
            self.test_results[test_name] = {
                "status": "❌ FAILED",
                "message": f"Referral API simulation error: {e}",
                "error_type": "CRUD error"
            }
    
    async def run_all_tests(self):
        """Run all tests and return results"""
        logger.info("🚀 Starting Gamification & Referral System Tests...")
        
        if not await self.setup():
            return {"setup_failed": True}
        
        # Run all tests
        await self.test_gamification_serialization()
        await self.test_referral_collections()
        await self.test_referral_bonus_processing()
        await self.test_gamification_api_endpoints()
        await self.test_referral_api_simulation()
        
        return self.test_results
    
    def print_results(self):
        """Print formatted test results"""
        logger.info("\n" + "="*70)
        logger.info("🧪 GAMIFICATION & REFERRAL SYSTEM TEST RESULTS")
        logger.info("="*70)
        
        passed = 0
        failed = 0
        warnings = 0
        
        for test_name, result in self.test_results.items():
            status = result["status"]
            message = result["message"]
            
            logger.info(f"\n📋 {test_name}")
            logger.info(f"   {status} {message}")
            
            if status.startswith("✅"):
                passed += 1
            elif status.startswith("❌"):
                failed += 1
            elif status.startswith("⚠️"):
                warnings += 1
            
            # Print additional details
            for key, value in result.items():
                if key not in ["status", "message"]:
                    logger.info(f"   📄 {key}: {value}")
        
        logger.info("\n" + "="*70)
        logger.info(f"📊 SUMMARY: {passed} Passed, {failed} Failed, {warnings} Warnings")
        logger.info("="*70)
        
        return {
            "passed": passed,
            "failed": failed, 
            "warnings": warnings,
            "total": len(self.test_results)
        }

async def main():
    """Main test execution"""
    tester = GamificationReferralTester()
    results = await tester.run_all_tests()
    summary = tester.print_results()
    
    # Return exit code based on results
    return 0 if summary["failed"] == 0 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
