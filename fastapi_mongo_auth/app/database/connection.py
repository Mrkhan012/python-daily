from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class Database:
    client: AsyncIOMotorClient = None

    def connect(self):
        url = settings.MONGO_URL
        masked_url = url.split("@")[-1] if "@" in url else "..." 
        print(f"Attempting to connect to MongoDB at: ...@{masked_url}")
        # Fix for Vercel SSL Error: TLSV1_ALERT_INTERNAL_ERROR
        self.client = AsyncIOMotorClient(
            url,
            tls=True,
            tlsAllowInvalidCertificates=True
        )
        print("Connected to MongoDB client created")

    def disconnect(self):
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")

    def get_db(self):
        return self.client[settings.DB_NAME]

db = Database()

async def get_database():
    return db.get_db()
