from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from .user import UserPublicResponse

class CommentBase(BaseModel):
    content: str
    post_id: int
    parent_comment_id: Optional[int] = None

class CommentCreate(CommentBase):
    pass

class CommentCreateRequest(BaseModel):
    """Schema for creating comment via API (post_id comes from URL)"""
    content: str
    parent_comment_id: Optional[int] = None

class CommentUpdate(BaseModel):
    content: Optional[str] = None

class CommentResponse(CommentBase):
    id: int
    user_id: int
    likes_count: int = 0
    dislikes_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Update forward reference
CommentResponse.model_rebuild() 