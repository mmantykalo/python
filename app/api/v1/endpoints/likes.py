from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.post import Post
from app.models.like import Like
from app.schemas.like import LikeResponse

router = APIRouter()

@router.post("/posts/{post_id}/like", response_model=LikeResponse)
async def like_post(
    post_id: int,
    is_like: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Like or dislike a post"""
    # Check if post exists
    result = await db.execute(select(Post).filter(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if user already liked/disliked this post
    existing_like_result = await db.execute(
        select(Like).filter(
            Like.post_id == post_id,
            Like.user_id == current_user.id
        )
    )
    existing_like = existing_like_result.scalar_one_or_none()
    
    if existing_like:
        # Update existing like/dislike
        old_is_like = existing_like.is_like
        existing_like.is_like = is_like
        
        # Update post counters only if changed
        if old_is_like != is_like:
            if old_is_like:  # Was like, now dislike
                post.likes_count = max(0, (post.likes_count or 1) - 1)
                post.dislikes_count = (post.dislikes_count or 0) + 1
            else:  # Was dislike, now like
                post.dislikes_count = max(0, (post.dislikes_count or 1) - 1)
                post.likes_count = (post.likes_count or 0) + 1
        
        await db.commit()
        await db.refresh(existing_like)
        return existing_like
    else:
        # Create new like/dislike
        new_like = Like(
            post_id=post_id,
            user_id=current_user.id,
            is_like=is_like
        )
        db.add(new_like)
        
        # Update post counters
        if is_like:
            post.likes_count = (post.likes_count or 0) + 1
        else:
            post.dislikes_count = (post.dislikes_count or 0) + 1
        
        await db.commit()
        await db.refresh(new_like)
        return new_like

@router.delete("/posts/{post_id}/like")
async def remove_post_like(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove like/dislike from a post"""
    # Check if post exists
    result = await db.execute(select(Post).filter(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Find existing like
    existing_like_result = await db.execute(
        select(Like).filter(
            Like.post_id == post_id,
            Like.user_id == current_user.id
        )
    )
    existing_like = existing_like_result.scalar_one_or_none()
    
    if not existing_like:
        raise HTTPException(status_code=404, detail="Like not found")
    
    # Update post counters
    if existing_like.is_like:
        post.likes_count = max(0, (post.likes_count or 1) - 1)
    else:
        post.dislikes_count = max(0, (post.dislikes_count or 1) - 1)
    
    # Remove like
    await db.delete(existing_like)
    await db.commit()
    
    return {"message": "Like removed successfully"}

@router.get("/posts/{post_id}/likes")
async def get_post_likes(
    post_id: int,
    like_type: str = "all",  # "likes", "dislikes", "all"
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get likes for a post"""
    # Check if post exists
    result = await db.execute(select(Post).filter(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Build query based on like_type
    query = select(Like).filter(Like.post_id == post_id)
    
    if like_type == "likes":
        query = query.filter(Like.is_like == True)
    elif like_type == "dislikes":
        query = query.filter(Like.is_like == False)
    elif like_type != "all":
        raise HTTPException(status_code=400, detail="like_type must be 'likes', 'dislikes', or 'all'")
    
    # Get total count
    count_query = select(func.count()).select_from(Like).filter(Like.post_id == post_id)
    if like_type == "likes":
        count_query = count_query.filter(Like.is_like == True)
    elif like_type == "dislikes":
        count_query = count_query.filter(Like.is_like == False)
    
    total = await db.scalar(count_query)
    
    # Apply pagination
    skip = (page - 1) * size
    query = query.order_by(Like.created_at.desc()).offset(skip).limit(size)
    
    result = await db.execute(query)
    likes = result.scalars().all()
    
    return {
        "items": likes,
        "total": total,
        "page": page,
        "size": size,
        "like_type": like_type
    }

@router.get("/posts/{post_id}/my-like", response_model=LikeResponse)
async def get_my_post_like(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's like/dislike for a post"""
    # Check if post exists
    result = await db.execute(select(Post).filter(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Find user's like
    existing_like_result = await db.execute(
        select(Like).filter(
            Like.post_id == post_id,
            Like.user_id == current_user.id
        )
    )
    existing_like = existing_like_result.scalar_one_or_none()
    
    if not existing_like:
        raise HTTPException(status_code=404, detail="No like found")
    
    return existing_like
