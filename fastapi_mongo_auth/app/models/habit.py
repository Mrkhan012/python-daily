from typing import Annotated, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.user import PyObjectId

class HabitBase(BaseModel):
    title: str
    is_completed: bool = Field(default=False, alias="isCompleted")
    color: str = "#00FF00"
    icon: str = "star"

class HabitCreate(HabitBase):
    pass

class HabitInDB(HabitBase):
    id: Annotated[PyObjectId, Field(alias="_id", default=None)]
    user_id: Annotated[PyObjectId, Field(alias="userId")]

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

class HabitResponse(HabitInDB):
    pass
