import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

async def list_users():
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.DB_NAME]
    collection = db.users
    
    print(f"Checking database: {settings.DB_NAME}")
    
    # Count users
    count = await collection.count_documents({})
    print(f"Total Users Found: {count}")
    
    # List users
    async for user in collection.find():
        print("\n" + "-"*30)
        print(f"ID: {user.get('_id')}")
        print(f"Name: {user.get('first_name')} {user.get('last_name')}")
        print(f"Email: {user.get('email')}")
        print(f"Mobile: {user.get('mobile')}")
    
    print("\n" + "-"*30)
    client.close()

if __name__ == "__main__":
    print("Connecting to MongoDB...")
    asyncio.run(list_users())
