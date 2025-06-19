from typing import AsyncGenerator
from app.db.base import AsyncSessionLocal

async def get_db() -> AsyncGenerator:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

from fastapi import Depends, HTTPException, status, Header
from jose import JWTError, jwt
from app.core.config import settings
from app.services.user import UserService
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import verify_token
from typing import Optional

def get_authorization_header(x_authorization: Optional[str] = Header(None, alias="X-Authorization")):
    """
    Custom function to extract token from X-Authorization header
    """
    if x_authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if token starts with "Bearer "
    if not x_authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid X-Authorization header format. Must be 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token without "Bearer " prefix
    return x_authorization[7:]

async def get_current_user(token: str = Depends(get_authorization_header), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = await UserService.get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    return user
