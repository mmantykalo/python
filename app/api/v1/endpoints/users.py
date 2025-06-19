from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.follow import Follow
from app.schemas.user import UserResponse, UserCreate, UserLogin, UserPublicResponse
from app.services.user import UserService
from app.core.security import get_password_hash, create_access_token, verify_password

router = APIRouter()

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    user = await UserService.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await UserService.get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    db_user = await UserService.get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_dict = user.model_dump()
    user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
    return await UserService.create_user(db, user_dict)

@router.post("/login")
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await UserService.authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_user_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_user_me(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_dict = user_data.model_dump()
    user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
    updated_user = await UserService.update_user(db, current_user.id, user_dict)
    return updated_user

@router.post("/me/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not verify_password(old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    
    user_dict = {"hashed_password": get_password_hash(new_password)}
    await UserService.update_user(db, current_user.id, user_dict)
    return {"message": "Password updated successfully"}

@router.get("/me/followers", response_model=List[UserPublicResponse])
async def get_my_followers(
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of users who follow current user"""
    skip = (page - 1) * size
    
    # Get followers: users who have follow relationship where following_id = current_user.id
    result = await db.execute(
        select(User)
        .join(Follow, Follow.follower_id == User.id)
        .filter(Follow.following_id == current_user.id)
        .offset(skip)
        .limit(size)
    )
    followers = result.scalars().all()
    return followers

@router.get("/me/following", response_model=List[UserPublicResponse])
async def get_my_following(
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of users that current user follows"""
    skip = (page - 1) * size
    
    # Get following: users who are followed by current user (follower_id = current_user.id)
    result = await db.execute(
        select(User)
        .join(Follow, Follow.following_id == User.id)
        .filter(Follow.follower_id == current_user.id)
        .offset(skip)
        .limit(size)
    )
    following = result.scalars().all()
    return following

@router.get("/users/{user_id}/public-info", response_model=UserPublicResponse)
async def get_user_public_info(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get public information about any user (no auth required in future)"""
    user = await UserService.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
