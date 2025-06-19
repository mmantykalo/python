from pydantic import BaseModel
from datetime import datetime
from typing import Optional, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.schemas.user import UserResponse


class RefreshTokenCreate(BaseModel):
    user_id: int
    token: str
    expires_at: datetime
    device_info: Optional[str] = None


class RefreshTokenResponse(BaseModel):
    id: int
    user_id: int
    token: str
    expires_at: datetime
    is_active: bool
    created_at: datetime
    device_info: Optional[str] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires
    user_info: Any  # Use Any to avoid circular import, will be UserResponse at runtime


class RefreshRequest(BaseModel):
    refresh_token: str


class RegisterResponse(BaseModel):
    """Minimal response for registration - just success confirmation"""
    message: str
    username: str
    email: str 