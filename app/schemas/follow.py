from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from .user import UserPublicResponse

class FollowBase(BaseModel):
    following_id: int

class FollowCreate(FollowBase):
    pass

class FollowResponse(FollowBase):
    id: int
    follower_id: int
    created_at: datetime

    class Config:
        from_attributes = True 