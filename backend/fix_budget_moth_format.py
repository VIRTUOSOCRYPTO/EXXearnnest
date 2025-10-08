#!/usr/bin/env python3
"""
Budget Month Format Migration Script

This script fixes the month format inconsistency in the budget collection.
It converts budgets with separate month/year fields to the standard "YYYY-MM" format.
"""

import asyncio
import sys
from datetime import datetime, timezone
from database import get_database

async def migrate_budget_month_format():
    """Migrate budget month format from separate month/year to YYYY-MM format"""
    print("🔧 Starting budget month format migration...")
    
    db = await get_database()
    
    # Find budgets with old format (month as number and separate year field)
    old_format_budgets = await db.budgets.find({
        "$and": [
            {"month": {"$type": "number"}},  # month is a number
            {"year": {"$exists": True}}      # year field exists
        ]
    }).to_list(None)
    
    print(f"📊 Found {len(old_format_budgets)} budgets with old format")
    
    if len(old_format_budgets) == 0:
        print("✅ No budgets need migration")
        return
    
    migrated_count = 0
    error_count = 0
    
    for budget in old_format_budgets:
        try:
            # Convert month/year to YYYY-MM format
            month = budget["month"]
            year = budget.get("year", datetime.now(timezone.utc).year)
            
            # Ensure month is 1-12
            if not (1 <= month <= 12):
                print(f"⚠️  Skipping budget {budget['_id']} - invalid month: {month}")
                error_count += 1
                continue
            
            # Format as YYYY-MM
            new_month_format = f"{year}-{month:02d}"
            
            # Update the budget
            result = await db.budgets.update_one(
                {"_id": budget["_id"]},
                {
                    "$set": {"month": new_month_format},
                    "$unset": {"year": ""}  # Remove the separate year field
                }
            )
            
            if result.modified_count > 0:
                print(f"✅ Migrated budget {budget['_id']}: {month}/{year} → {new_month_format}")
                migrated_count += 1
            else:
                print(f"⚠️  Failed to update budget {budget['_id']}")
                error_count += 1
                
        except Exception as e:
            print(f"❌ Error migrating budget {budget['_id']}: {str(e)}")
            error_count += 1
    
    print(f"\n📈 Migration complete:")
    print(f"   ✅ Successfully migrated: {migrated_count}")
    print(f"   ❌ Errors: {error_count}")
    print(f"   📊 Total processed: {len(old_format_budgets)}")
    
    # Verify migration
    remaining_old_format = await db.budgets.count_documents({
        "$and": [
            {"month": {"$type": "number"}},
            {"year": {"$exists": True}}
        ]
    })
    
    if remaining_old_format == 0:
        print("🎉 All budgets successfully migrated to new format!")
    else:
        print(f"⚠️  {remaining_old_format} budgets still need migration")

async def verify_budget_consistency():
    """Verify that all budgets now use consistent month format"""
    print("\n🔍 Verifying budget month format consistency...")
    
    db = await get_database()
    
    # Count budgets by month format
    total_budgets = await db.budgets.count_documents({})
    string_format_budgets = await db.budgets.count_documents({"month": {"$type": "string"}})
    number_format_budgets = await db.budgets.count_documents({"month": {"$type": "number"}})
    
    print(f"📊 Budget format summary:")
    print(f"   Total budgets: {total_budgets}")
    print(f"   String format (YYYY-MM): {string_format_budgets}")
    print(f"   Number format (old): {number_format_budgets}")
    
    if number_format_budgets == 0:
        print("✅ All budgets use consistent string format!")
    else:
        print(f"⚠️  {number_format_budgets} budgets still use old format")
    
    # Sample some budget data to verify
    sample_budgets = await db.budgets.find({}).limit(5).to_list(None)
    if sample_budgets:
        print("\n📝 Sample budget month formats:")
        for budget in sample_budgets:
            month_value = budget.get("month", "N/A")
            month_type = type(month_value).__name__
            print(f"   Budget {budget['_id'][:8]}...: month='{month_value}' ({month_type})")

if __name__ == "__main__":
    async def main():
        try:
            await migrate_budget_month_format()
            await verify_budget_consistency()
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            sys.exit(1)
    
    asyncio.run(main())
