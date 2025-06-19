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

# Register endpoint moved to /auth/register with rate limiting

# Login endpoint moved to /auth/login with refresh token support

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

# =====================
# FOLLOW/UNFOLLOW ENDPOINTS
# =====================

@router.post("/users/{user_id}/follow")
async def follow_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Follow a user"""
    # Check if trying to follow yourself
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    
    # Check if target user exists
    result = await db.execute(select(User).filter(User.id == user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already following
    existing_follow = await db.execute(
        select(Follow).filter(
            Follow.follower_id == current_user.id,
            Follow.following_id == user_id
        )
    )
    if existing_follow.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already following this user")
    
    # Create follow relationship
    follow = Follow(
        follower_id=current_user.id,
        following_id=user_id
    )
    db.add(follow)
    
    # Update counters
    current_user.following_count = (current_user.following_count or 0) + 1
    target_user.followers_count = (target_user.followers_count or 0) + 1
    
    await db.commit()
    return {"message": f"Now following {target_user.username}"}

@router.delete("/users/{user_id}/follow")
async def unfollow_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unfollow a user"""
    # Check if trying to unfollow yourself
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot unfollow yourself")
    
    # Check if target user exists
    result = await db.execute(select(User).filter(User.id == user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find existing follow relationship
    existing_follow_result = await db.execute(
        select(Follow).filter(
            Follow.follower_id == current_user.id,
            Follow.following_id == user_id
        )
    )
    existing_follow = existing_follow_result.scalar_one_or_none()
    
    if not existing_follow:
        raise HTTPException(status_code=400, detail="Not following this user")
    
    # Remove follow relationship
    await db.delete(existing_follow)
    
    # Update counters
    current_user.following_count = max(0, (current_user.following_count or 1) - 1)
    target_user.followers_count = max(0, (target_user.followers_count or 1) - 1)
    
    await db.commit()
    return {"message": f"Unfollowed {target_user.username}"}

@router.get("/users/{user_id}/followers", response_model=List[UserPublicResponse])
async def get_user_followers(
    user_id: int,
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get public list of user's followers"""
    # Check if user exists
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    skip = (page - 1) * size
    
    # Get followers
    result = await db.execute(
        select(User)
        .join(Follow, Follow.follower_id == User.id)
        .filter(Follow.following_id == user_id)
        .offset(skip)
        .limit(size)
    )
    followers = result.scalars().all()
    return followers

@router.get("/users/{user_id}/following", response_model=List[UserPublicResponse])
async def get_user_following(
    user_id: int,
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get public list of users that this user follows"""
    # Check if user exists
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    skip = (page - 1) * size
    
    # Get following
    result = await db.execute(
        select(User)
        .join(Follow, Follow.following_id == User.id)
        .filter(Follow.follower_id == user_id)
        .offset(skip)
        .limit(size)
    )
    following = result.scalars().all()
    return following
