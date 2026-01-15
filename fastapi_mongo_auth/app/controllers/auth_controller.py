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
        try:
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
                **user.model_dump(),
                hashed_password=hashed_password
            )
            
            # Insert into DB
            # Use model_dump instead of dict for V2
            user_dict = user_in_db.model_dump(by_alias=True, exclude={"id"})
            # Explicitly ensure _id is not None in the dict sent to Mongo
            if "_id" in user_dict and user_dict["_id"] is None:
                del user_dict["_id"]

            print(f"Attempting to insert user: {user_dict}")
            new_user = await self.collection.insert_one(user_dict)
            print(f"User inserted with ID: {new_user.inserted_id}")
            
            # Return created user
            created_user = await self.collection.find_one({"_id": new_user.inserted_id})
            return UserInDB(**created_user)
        except Exception as e:
            print(f"CRITICAL ERROR in create_user: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e

    async def authenticate_user(self, email: str, password: str):
        user = await self.collection.find_one({"email": email})
        if not user:
            return None
        if not verify_password(password, user["hashed_password"]):
            return None
        return UserInDB(**user)
