from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum

from fastapi import UploadFile, File

class PrivacyLevel(str, Enum):
    PUBLIC = "PUBLIC"
    FOLLOWERS = "FOLLOWERS" 
    PRIVATE = "PRIVATE"

class PostBase(BaseModel):
    comment: Optional[str] = None
    latitude: float
    longitude: float
    privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC
    is_comments_enabled: bool = True

class PostCreate(PostBase):
    """Schema for creating a new post (without image_url as it's generated)"""
    pass

class PostUpdate(BaseModel):
    comment: Optional[str] = None
    privacy_level: Optional[PrivacyLevel] = None
    is_comments_enabled: Optional[bool] = None

class PostResponse(PostBase):
    id: int
    image_url: str
    user_id: int
    comments_count: int = 0
    created_at: datetime
    updated_at: datetime
    likes_count: int = 0
    dislikes_count: int = 0

    class Config:
        from_attributes = True

class PaginatedResponse(BaseModel):
    items: List[PostResponse]
    total: int
    page: int
    size: int
