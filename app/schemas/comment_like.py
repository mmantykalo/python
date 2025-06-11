from pydantic import BaseModel
from datetime import datetime

class CommentLikeBase(BaseModel):
    comment_id: int
    is_like: bool  # True = like, False = dislike

class CommentLikeCreate(CommentLikeBase):
    pass

class CommentLikeUpdate(BaseModel):
    is_like: bool

class CommentLikeResponse(CommentLikeBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True 