import asyncio
import sys
import os

# Add parent dir to path so we can import from database and sheets
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.supabase_client import db

async def test():
    print("Testing Google Sheets Database Adapter...")
    try:
        # 1. Fetch drinks
        drinks = await db.get_all_drinks(123)
        print(f"Fetch successful! Found {len(drinks)} drinks:")
        for d in drinks:
            print(f" - {d['name']} ({d['calories_per_100ml']} kcal/100ml)")
            
        # 2. Fetch purchases
        purchases = await db.get_purchases(123, limit=5)
        print(f"Fetch successful! Found {len(purchases)} recent purchases:")
        for p in purchases:
            drink_name = p['drinks']['name'] if isinstance(p.get('drinks'), dict) else p.get('drink_id')
            print(f" - {p['purchase_date']}: {drink_name} ({p['volume_ml']}ml, {p.get('price_rub', 0)} rub)")
            
        print("✅ Test complete. Basic reads are working!")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
