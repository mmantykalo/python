from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

from fastapi import UploadFile, File

class PostBase(BaseModel):
    comment: Optional[str] = None
    latitude: float
    longitude: float

class PostCreate(PostBase):
    """Schema for creating a new post (without image_url as it's generated)"""
    pass

class PostResponse(PostBase):
    id: int
    image_url: str  # Added missing image_url field
    user_id: int
    created_at: datetime
    updated_at: datetime
    likes_count: int = 0

    class Config:
        from_attributes = True

class PaginatedResponse(BaseModel):
    items: List[PostResponse]
    total: int
    page: int
    size: int
