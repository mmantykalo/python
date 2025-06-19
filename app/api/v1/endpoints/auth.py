from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.user import UserLogin, UserCreate, UserResponse
from app.schemas.refresh_token import TokenResponse, RefreshRequest, RegisterResponse
from app.services.user import UserService
from app.services.refresh_token import RefreshTokenService
from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.config import settings

# Rate limiter for login attempts
limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


@router.post("/register", response_model=RegisterResponse)
@limiter.limit("3/minute")  # Max 3 registration attempts per minute per IP
async def register(
    request: Request,
    user: UserCreate, 
    db: AsyncSession = Depends(get_db)
):
    """Register a new user with rate limiting"""
    # Check if username already exists
    db_user = await UserService.get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email already exists
    db_user = await UserService.get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_dict = user.model_dump()
    user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
    created_user = await UserService.create_user(db, user_dict)
    
    # Return minimal info - user needs to login to get full access
    return RegisterResponse(
        message="User registered successfully. Please login to continue.",
        username=created_user.username,
        email=created_user.email
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")  # Max 5 login attempts per minute per IP
async def login(
    request: Request,
    user_data: UserLogin, 
    db: AsyncSession = Depends(get_db)
):
    """Login with username/password and receive access + refresh tokens"""
    # Authenticate user
    user = await UserService.authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",  # Secure: don't reveal if user exists
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.username}, user_id=user.id)
    
    # Create refresh token
    device_info = request.headers.get("User-Agent", "Unknown device")
    refresh_token = await RefreshTokenService.create_refresh_token(
        db=db, 
        user_id=user.id, 
        device_info=device_info
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token.token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        user_info=UserResponse.from_orm(user)  # Convert to Pydantic schema
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    refresh_request: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    # Validate refresh token
    refresh_token = await RefreshTokenService.get_valid_refresh_token(
        db=db, 
        token=refresh_request.refresh_token
    )
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user
    user = await UserService.get_user(db, refresh_token.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new access token
    access_token = create_access_token(data={"sub": user.username}, user_id=user.id)
    
    # Create new refresh token (rotate refresh tokens for security)
    device_info = request.headers.get("User-Agent", "Unknown device")
    new_refresh_token = await RefreshTokenService.create_refresh_token(
        db=db, 
        user_id=user.id, 
        device_info=device_info
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token.token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_info=UserResponse.from_orm(user)  # Convert to Pydantic schema
    )


@router.post("/logout")
async def logout(
    refresh_request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Logout and revoke refresh token"""
    success = await RefreshTokenService.revoke_refresh_token(
        db=db, 
        token=refresh_request.refresh_token
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token"
        )
    
    return {"message": "Successfully logged out"}


@router.post("/logout-all")
async def logout_all_devices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Logout from all devices (revoke all refresh tokens)"""
    success = await RefreshTokenService.revoke_all_user_tokens(
        db=db, 
        user_id=current_user.id
    )
    
    return {"message": f"Successfully logged out from all devices. Revoked tokens: {success}"} 