from datetime import date, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.connection import get_database
from app.controllers.tracker_controller import TrackerController
from app.models.user import UserInDB, UserResponse
from app.models.habit import HabitCreate, HabitResponse
from app.models.log import LogCreate, LogResponse
from app.core.deps import get_current_user

router = APIRouter(tags=["Tracker"])

def get_tracker_controller(db: AsyncIOMotorDatabase = Depends(get_database)) -> TrackerController:
    return TrackerController(db)

# --- Profile ---
@router.get("/user/profile", response_model=UserResponse)
async def get_profile(
    current_user: UserInDB = Depends(get_current_user)
):
    # current_user already has the latest data from get_current_user dependency 
    # (assuming get_current_user fetches from DB).
    # If get_current_user uses decoded token data only, we might need to fetch fresh from DB.
    # checking app/core/deps.py -> it fetches from DB. So we are good.
    return current_user

# --- Habits ---
@router.get("/habits", response_model=List[HabitResponse])
async def get_habits(
    current_user: UserInDB = Depends(get_current_user),
    controller: TrackerController = Depends(get_tracker_controller)
):
    return await controller.get_habits(str(current_user.id))

@router.post("/habits", response_model=HabitResponse)
async def create_habit(
    habit: HabitCreate,
    current_user: UserInDB = Depends(get_current_user),
    controller: TrackerController = Depends(get_tracker_controller)
):
    return await controller.create_habit(str(current_user.id), habit)

@router.post("/habits/{habit_id}/toggle", response_model=HabitResponse)
async def toggle_habit(
    habit_id: str,
    current_user: UserInDB = Depends(get_current_user),
    controller: TrackerController = Depends(get_tracker_controller)
):
    return await controller.toggle_habit(str(current_user.id), habit_id)

# --- Logs ---
@router.get("/logs/today", response_model=LogResponse)
async def get_today_log(
    current_user: UserInDB = Depends(get_current_user),
    controller: TrackerController = Depends(get_tracker_controller)
):
    return await controller.get_today_log(str(current_user.id))

@router.get("/logs/history", response_model=List[LogResponse])
async def get_log_history(
    startDate: str = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: str = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: UserInDB = Depends(get_current_user),
    controller: TrackerController = Depends(get_tracker_controller)
):
    return await controller.get_log_history(str(current_user.id), startDate, endDate)

@router.post("/logs/sync", response_model=LogResponse)
async def sync_log(
    log: LogCreate,
    current_user: UserInDB = Depends(get_current_user),
    controller: TrackerController = Depends(get_tracker_controller)
):
    return await controller.sync_log(str(current_user.id), log)
