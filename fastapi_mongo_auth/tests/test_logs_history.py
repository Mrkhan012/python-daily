import asyncio
import httpx
from datetime import date, timedelta

# Configuration
BASE_URL = "http://127.0.0.1:8000"

async def test_logs_history():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # 1. Register/Login a new user to ensure clean state
        import time
        email = f"test_history_{int(time.time())}@example.com"
        password = "password123"
        user_data = {
            "first_name": "History",
            "last_name": "Tester",
            "email": email,
            "mobile": "9999999999",
            "city": "TestCity",
            "dob": "1990-01-01",
            "daily_goal_name": "Steps",
            "daily_goal_target": "10000",
            "password": password
        }

        print(f"1. Registering/Logging in user: {email}")
        resp = await client.post("/auth/register", json=user_data)
        if resp.status_code != 200 and resp.status_code != 400:
             print(f"Failed to register: {resp.text}")
             return

        # Login to get token
        login_data = {"username": email, "password": password}
        resp = await client.post("/auth/login", data=login_data)
        if resp.status_code != 200:
            print(f"Failed to login: {resp.text}")
            return
        
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("   Logged in successfully.")

        # 2. Seed Data
        # We will seed data for Today and Today-2. Today-1 should be missing.
        today = date.today()
        day_minus_2 = today - timedelta(days=2)
        
        log_today = {
            "date": today.isoformat(),
            "steps": 5000,
            "waterMl": 2000,
            "proteinG": 100
        }
        log_day_minus_2 = {
            "date": day_minus_2.isoformat(),
            "steps": 3000,
            "waterMl": 1500,
            "proteinG": 80
        }

        print("2. Seeding Logs...")
        # Using sync endpoint to seed
        await client.post("/logs/sync", json=log_today, headers=headers)
        await client.post("/logs/sync", json=log_day_minus_2, headers=headers)
        print("   Logs seeded.")

        # 3. Query History
        start_date = day_minus_2.isoformat()
        end_date = today.isoformat() # ranges are inclusive
        
        print(f"3. Querying History from {start_date} to {end_date}...")
        resp = await client.get(f"/logs/history?startDate={start_date}&endDate={end_date}", headers=headers)
        
        if resp.status_code != 200:
            print(f"   Error: {resp.status_code} - {resp.text}")
            return

        history = resp.json()
        print(f"   Received {len(history)} items.")
        
        # 4. Analyze Results
        found_dates = {item["date"]: item for item in history}
        
        # Check Day -2 (Should exist with data)
        if start_date in found_dates:
            print(f"   [PASS] {start_date} found: {found_dates[start_date]}")
        else:
            print(f"   [FAIL] {start_date} MISSING!")

        # Check Day -1 (Should exist with ZERO data - GAP FILL CHECK)
        day_minus_1 = (today - timedelta(days=1)).isoformat()
        if day_minus_1 in found_dates:
            item = found_dates[day_minus_1]
            if item["steps"] == 0 and item["waterMl"] == 0:
                print(f"   [PASS] {day_minus_1} found (Gap Filled): {item}")
            else:
                print(f"   [FAIL] {day_minus_1} found but has data? {item}")
        else:
            print(f"   [FAIL] {day_minus_1} MISSING (Gap not filled)!")

        # Check Today (Should exist)
        if end_date in found_dates:
            print(f"   [PASS] {end_date} found: {found_dates[end_date]}")
        else:
            print(f"   [FAIL] {end_date} MISSING!")

        # Check Schema (No IDs)
        if len(history) > 0:
            first_item = history[0]
            if "_id" in first_item or "userId" in first_item or "id" in first_item:
                print(f"   [FAIL] Response contains internal IDs: {first_item.keys()}")
            else:
                print("   [PASS] Response schema is clean.")

if __name__ == "__main__":
    asyncio.run(test_logs_history())
