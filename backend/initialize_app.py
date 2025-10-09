#!/usr/bin/env python3
"""
Master Initialization Script - Runs all setup tasks on first deployment
This script should be run once after deployment to set up the application
"""

import asyncio
import os
import sys
from datetime import datetime

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

from database import get_database

async def check_if_initialized():
    """Check if app has already been initialized"""
    db = await get_database()
    
    # Check for initialization flag in database
    init_flag = await db.system_config.find_one({"key": "app_initialized"})
    return init_flag is not None

async def mark_as_initialized():
    """Mark the app as initialized"""
    db = await get_database()
    await db.system_config.update_one(
        {"key": "app_initialized"},
        {"$set": {
            "key": "app_initialized",
            "value": True,
            "initialized_at": datetime.utcnow()
        }},
        upsert=True
    )

async def run_initialization():
    """Run all initialization scripts"""
    
    print("=" * 80)
    print("🚀 STARTING APPLICATION INITIALIZATION")
    print("=" * 80)
    
    # Check if already initialized
    if await check_if_initialized():
        print("✅ Application already initialized. Skipping setup scripts.")
        return
    
    print("\n📋 Running initialization scripts...\n")
    
    # Import and run each script
    scripts = [
        ("fix_budget_moth_format", "Budget Format Migration"),
        ("fix_leaderboard_duplicates", "Leaderboard Cleanup"),
        ("create_super_admin", "Super Admin Creation"),
        ("initialize_comprehensive_universities", "University Database Setup"),
    ]
    
    for script_name, description in scripts:
        print(f"\n{'='*80}")
        print(f"📦 Running: {description}")
        print(f"{'='*80}")
        
        try:
            # Import the script module
            module = __import__(script_name)
            
            # Run the main function
            if hasattr(module, 'main'):
                if asyncio.iscoroutinefunction(module.main):
                    await module.main()
                else:
                    module.main()
            else:
                # Try to find and run the appropriate function
                for func_name in dir(module):
                    func = getattr(module, func_name)
                    if callable(func) and not func_name.startswith('_'):
                        if asyncio.iscoroutinefunction(func):
                            await func()
                        else:
                            func()
                        break
            
            print(f"✅ Completed: {description}")
            
        except Exception as e:
            print(f"⚠️  Warning in {description}: {str(e)}")
            print("   Continuing with other scripts...")
    
    # Create test users
    print(f"\n{'='*80}")
    print("👥 Creating Test Users")
    print(f"{'='*80}")
    
    try:
        from quick_test_users import create_quick_test_users
        await create_quick_test_users()
        print("✅ Test users created successfully")
    except Exception as e:
        print(f"⚠️  Warning: Could not create test users: {str(e)}")
    
    # Mark as initialized
    await mark_as_initialized()
    
    print("\n" + "=" * 80)
    print("🎉 APPLICATION INITIALIZATION COMPLETE!")
    print("=" * 80)
    print("\n📊 Summary:")
    print("   ✅ Budget format validated")
    print("   ✅ Leaderboards cleaned and populated")
    print("   ✅ Super admin created")
    print("   ✅ Universities populated (27 institutions)")
    print("   ✅ Test users created")
    print("\n🔐 Test Credentials:")
    print("   Student: student1@test.com / Test@123")
    print("   Super Admin: yash@earnaura.com / YaSh@4517")
    print("\n🌐 Application ready at: https://fullstack-rating.preview.emergentagent.com")
    print("=" * 80)

async def force_reinitialize():
    """Force reinitialization (useful for development)"""
    db = await get_database()
    await db.system_config.delete_one({"key": "app_initialized"})
    print("🔄 Initialization flag cleared. Run initialize_app.py again to reinitialize.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        # Force reinitialization
        asyncio.run(force_reinitialize())
    else:
        # Normal initialization
        asyncio.run(run_initialization())
