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

class CommentUpdate(BaseModel):
    content: Optional[str] = None

class CommentResponse(CommentBase):
    id: int
    user_id: int
    user: Optional[UserPublicResponse] = None
    likes_count: int = 0
    dislikes_count: int = 0
    created_at: datetime
    updated_at: datetime
    replies: Optional[List['CommentResponse']] = []

    class Config:
        from_attributes = True

# Update forward reference
CommentResponse.model_rebuild() 