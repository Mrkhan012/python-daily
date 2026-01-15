from datetime import date
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from fastapi import HTTPException, status
from app.models.habit import HabitCreate, HabitInDB, HabitResponse
from app.models.log import LogCreate, LogInDB, LogResponse
from app.models.user import UserInDB

class TrackerController:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.habits_collection = self.db.habits
        self.logs_collection = self.db.logs
        self.users_collection = self.db.users

    # --- Habits ---
    async def get_habits(self, user_id: str) -> List[HabitResponse]:
        habits = []
        async for habit in self.habits_collection.find({"userId": ObjectId(user_id)}):
            habits.append(HabitResponse(**habit))
        return habits

    async def create_habit(self, user_id: str, habit_data: HabitCreate) -> HabitResponse:
        habit_dict = habit_data.model_dump(by_alias=True)
        habit_dict["userId"] = ObjectId(user_id)
        
        new_habit = await self.habits_collection.insert_one(habit_dict)
        created_habit = await self.habits_collection.find_one({"_id": new_habit.inserted_id})
        return HabitResponse(**created_habit)

    async def toggle_habit(self, user_id: str, habit_id: str) -> HabitResponse:
        if not ObjectId.is_valid(habit_id):
             raise HTTPException(status_code=400, detail="Invalid ID format")
             
        habit = await self.habits_collection.find_one({
            "_id": ObjectId(habit_id), 
            "userId": ObjectId(user_id)
        })
        if not habit:
            raise HTTPException(status_code=404, detail="Habit not found")
        
        new_status = not habit.get("isCompleted", False)
        # Update
        await self.habits_collection.update_one(
            {"_id": ObjectId(habit_id)},
            {"$set": {"isCompleted": new_status}}
        )
        
        # Gamification logic: Add XP if completed
        if new_status:
            await self.add_xp(user_id, 10) # 10 XP per habit completion
            
        updated_habit = await self.habits_collection.find_one({"_id": ObjectId(habit_id)})
        return HabitResponse(**updated_habit)

    # --- Logs ---
    async def get_today_log(self, user_id: str) -> LogResponse:
        today_str = date.today().isoformat()
        log = await self.logs_collection.find_one({
            "userId": ObjectId(user_id),
            "date": today_str
        })
        
        if not log:
            # Return empty/default log if not found, or create one? 
            # Controller usually just returns data. Route might handle default.
            # Let's return a default structure but don't save it yet until sync.
            return LogResponse(
                _id=ObjectId(), # Temporary ID
                userId=ObjectId(user_id),
                date=today_str,
                steps=0,
                waterMl=0,
                proteinG=0
            )
        return LogResponse(**log)

    async def get_log_history(self, user_id: str, start_date: str, end_date: str) -> List[LogResponse]:
        # Basic string comparison helper for date range
        logs = []
        async for log in self.logs_collection.find({
            "userId": ObjectId(user_id),
            "date": {"$gte": start_date, "$lte": end_date}
        }).sort("date", 1): # Sort by date ascending
            logs.append(LogResponse(**log))
        return logs

    async def sync_log(self, user_id: str, log_data: LogCreate) -> LogResponse:
        # Upsert: Update if exists, Insert if not
        log_dict = log_data.model_dump(by_alias=True)
        log_dict["userId"] = ObjectId(user_id)
        
        result = await self.logs_collection.update_one(
            {"userId": ObjectId(user_id), "date": log_data.date},
            {"$set": log_dict},
            upsert=True
        )
        
        # Retrieve the updated/inserted doc
        saved_log = await self.logs_collection.find_one({
            "userId": ObjectId(user_id), 
            "date": log_data.date
        })
        return LogResponse(**saved_log)

    # --- Helper: Gamification ---
    async def add_xp(self, user_id: str, amount: int):
        user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return
            
        current_xp = user.get("currentXp", 0) + amount
        max_xp = user.get("maxXp", 1000)
        level = user.get("level", 1)
        
        # Simple level up logic
        if current_xp >= max_xp:
            current_xp = current_xp - max_xp
            level += 1
            max_xp = int(max_xp * 1.2) # Increase difficulty
            
        await self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"currentXp": current_xp, "maxXp": max_xp, "level": level}}
        )
