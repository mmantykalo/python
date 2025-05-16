
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class PostBase(BaseModel):
    image_url: str
    comment: Optional[str] = None
    latitude: float
    longitude: float

class PostCreate(PostBase):
    pass

class PostResponse(PostBase):
    id: int
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
