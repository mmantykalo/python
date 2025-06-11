from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.follow import Follow
from app.schemas.follow import FollowCreate, FollowResponse
from sqlalchemy import select

router = APIRouter()

@router.post("/users/{user_id}/follow", response_model=FollowResponse)
async def follow_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if user exists
    result = await db.execute(select(User).filter(User.id == user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already following
    result = await db.execute(
        select(Follow).filter(
            Follow.follower_id == current_user.id,
            Follow.following_id == user_id
        )
    )
    existing_follow = result.scalar_one_or_none()
    if existing_follow:
        raise HTTPException(status_code=400, detail="Already following this user")
    
    # Create follow relationship
    follow = Follow(follower_id=current_user.id, following_id=user_id)
    db.add(follow)
    await db.commit()
    await db.refresh(follow)
    
    return follow

@router.delete("/users/{user_id}/follow")
async def unfollow_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Find and delete follow relationship
    result = await db.execute(
        select(Follow).filter(
            Follow.follower_id == current_user.id,
            Follow.following_id == user_id
        )
    )
    follow = result.scalar_one_or_none()
    if not follow:
        raise HTTPException(status_code=404, detail="Not following this user")
    
    await db.delete(follow)
    await db.commit()
    
    return {"message": "Unfollowed successfully"} 