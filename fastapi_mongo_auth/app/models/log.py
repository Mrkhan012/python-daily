from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict
from app.models.user import PyObjectId

class LogBase(BaseModel):
    date: str  # YYYY-MM-DD
    steps: int = 0
    water_ml: int = Field(default=0, alias="waterMl")
    protein_g: int = Field(default=0, alias="proteinG")

class LogCreate(LogBase):
    pass

class LogInDB(LogBase):
    id: Annotated[PyObjectId, Field(alias="_id", default=None)]
    user_id: Annotated[PyObjectId, Field(alias="userId")]

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

class LogResponse(LogInDB):
    pass
