from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

class UserResponse(UserBase):
    id: int
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserPublicResponse(BaseModel):
    """Public user info (for use in posts, comments etc.)"""
    id: int
    username: str
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True
