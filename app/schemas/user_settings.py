from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserSettingsBase(BaseModel):
    search_radius: int = 30000  # Default 30km in meters
    is_private: bool = False
    allow_comments: bool = True

class UserSettingsCreate(UserSettingsBase):
    pass

class UserSettingsUpdate(BaseModel):
    search_radius: Optional[int] = None
    is_private: Optional[bool] = None
    allow_comments: Optional[bool] = None

class UserSettingsResponse(UserSettingsBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 