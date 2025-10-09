"""
Startup tasks that run when FastAPI server starts
These tasks ensure the application is properly initialized
"""

import asyncio
import logging
from datetime import datetime
from database import get_database

logger = logging.getLogger(__name__)

async def check_and_initialize():
    """
    Check if app needs initialization and run setup tasks if needed
    This runs automatically when FastAPI starts
    """
    try:
        db = await get_database()
        
        # Check if already initialized
        init_flag = await db.system_config.find_one({"key": "app_initialized"})
        
        if init_flag:
            logger.info("✅ Application already initialized")
            return
        
        logger.info("🚀 First-time initialization detected - Running setup scripts...")
        
        # Run initialization scripts
        await run_all_initialization_scripts()
        
        # Mark as initialized
        await db.system_config.update_one(
            {"key": "app_initialized"},
            {"$set": {
                "key": "app_initialized",
                "value": True,
                "initialized_at": datetime.utcnow()
            }},
            upsert=True
        )
        
        logger.info("🎉 First-time initialization complete!")
        
    except Exception as e:
        logger.error(f"⚠️  Error during initialization: {str(e)}")
        logger.info("Continuing with server startup...")

async def run_all_initialization_scripts():
    """Run all initialization scripts in sequence"""
    
    # Budget format check
    try:
        from fix_budget_moth_format import main as fix_budgets
        await fix_budgets()
        logger.info("✅ Budget format validated")
    except Exception as e:
        logger.warning(f"Budget format check: {str(e)}")
    
    # Leaderboard cleanup
    try:
        from fix_leaderboard_duplicates import main as fix_leaderboards
        await fix_leaderboards()
        logger.info("✅ Leaderboards cleaned")
    except Exception as e:
        logger.warning(f"Leaderboard cleanup: {str(e)}")
    
    # Create super admin
    try:
        from create_super_admin import create_super_admin
        await create_super_admin()
        logger.info("✅ Super admin created")
    except Exception as e:
        logger.warning(f"Super admin creation: {str(e)}")
    
    # Initialize universities
    try:
        from initialize_comprehensive_universities import main as init_universities
        await init_universities()
        logger.info("✅ Universities initialized")
    except Exception as e:
        logger.warning(f"University initialization: {str(e)}")
    
    # Create test users
    try:
        from quick_test_users import create_quick_test_users
        await create_quick_test_users()
        logger.info("✅ Test users created")
    except Exception as e:
        logger.warning(f"Test user creation: {str(e)}")

def register_startup_tasks(app):
    """
    Register startup tasks with FastAPI app
    Call this function in your main server.py
    """
    
    @app.on_event("startup")
    async def startup_event():
        """Runs when FastAPI server starts"""
        logger.info("🚀 Running startup tasks...")
        await check_and_initialize()
        logger.info("✅ Startup tasks complete")
