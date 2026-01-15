from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.user import UserCreate, UserInDB
from app.core.security import get_password_hash, verify_password
from bson import ObjectId

class AuthController:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = self.db.users

    async def create_user(self, user: UserCreate) -> UserInDB:
        # Check if user already exists
        existing_user = await self.collection.find_one({"email": user.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Prepare data
        hashed_password = get_password_hash(user.password)
        user_in_db = UserInDB(
            **user.dict(),
            hashed_password=hashed_password
        )
        
        # Insert into DB
        new_user = await self.collection.insert_one(user_in_db.dict(by_alias=True, exclude={"id"}))
        
        # Return created user
        created_user = await self.collection.find_one({"_id": new_user.inserted_id})
        return UserInDB(**created_user)

    async def authenticate_user(self, email: str, password: str):
        user = await self.collection.find_one({"email": email})
        if not user:
            return None
        if not verify_password(password, user["hashed_password"]):
            return None
        return UserInDB(**user)
