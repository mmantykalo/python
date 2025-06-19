from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment
from app.models.comment_like import CommentLike
from app.schemas.comment import CommentCreateRequest, CommentResponse, CommentUpdate
from app.schemas.comment_like import CommentLikeCreate, CommentLikeResponse
from app.schemas.post import PaginatedResponse

router = APIRouter()

@router.post("/posts/{post_id}/comments", response_model=CommentResponse)
async def create_comment(
    post_id: int,
    comment: CommentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new comment on a post"""
    # Check if post exists
    result = await db.execute(select(Post).filter(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if comments are enabled for this post
    if not post.is_comments_enabled:
        raise HTTPException(status_code=403, detail="Comments are disabled for this post")
    
    # Create comment
    comment_data = comment.model_dump()
    comment_data.update({
        "post_id": post_id,
        "user_id": current_user.id
    })
    
    db_comment = Comment(**comment_data)
    db.add(db_comment)
    await db.commit()
    await db.refresh(db_comment)
    
    # Update post comments count
    post.comments_count = (post.comments_count or 0) + 1
    await db.commit()
    
    return db_comment

@router.get("/posts/{post_id}/comments")
async def get_post_comments(
    post_id: int,
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get comments for a post with pagination"""
    skip = (page - 1) * size
    
    # Check if post exists
    result = await db.execute(select(Post).filter(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Get total count of comments
    total = await db.scalar(
        select(func.count())
        .select_from(Comment)
        .filter(Comment.post_id == post_id)
    )
    
    # Get comments with user info
    result = await db.execute(
        select(Comment)
        .filter(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())  # Show oldest first
        .offset(skip)
        .limit(size)
    )
    comments = result.scalars().all()
    
    return {
        "items": comments,
        "total": total,
        "page": page,
        "size": size
    }

@router.get("/comments/{comment_id}/replies", response_model=List[CommentResponse])
async def get_comment_replies(
    comment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get replies to a specific comment"""
    result = await db.execute(
        select(Comment)
        .filter(Comment.parent_comment_id == comment_id)
        .order_by(Comment.created_at.asc())
    )
    replies = result.scalars().all()
    return replies

@router.post("/comments/{comment_id}/reply", response_model=CommentResponse)
async def reply_to_comment(
    comment_id: int,
    reply: CommentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reply to a specific comment"""
    # Check if parent comment exists
    result = await db.execute(select(Comment).filter(Comment.id == comment_id))
    parent_comment = result.scalar_one_or_none()
    if not parent_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if post allows comments
    result = await db.execute(select(Post).filter(Post.id == parent_comment.post_id))
    post = result.scalar_one_or_none()
    if not post or not post.is_comments_enabled:
        raise HTTPException(status_code=403, detail="Comments are disabled for this post")
    
    # Create reply
    reply_data = reply.model_dump()
    reply_data.update({
        "post_id": parent_comment.post_id,
        "user_id": current_user.id,
        "parent_comment_id": comment_id
    })
    
    db_reply = Comment(**reply_data)
    db.add(db_reply)
    await db.commit()
    await db.refresh(db_reply)
    
    # Update post comments count
    post.comments_count = (post.comments_count or 0) + 1
    await db.commit()
    
    return db_reply

@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    comment_update: CommentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a comment (only by comment author)"""
    # Get comment
    result = await db.execute(select(Comment).filter(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check ownership
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Update comment
    for field, value in comment_update.model_dump(exclude_unset=True).items():
        setattr(comment, field, value)
    
    await db.commit()
    await db.refresh(comment)
    return comment

@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a comment (only by comment author)"""
    # Get comment
    result = await db.execute(select(Comment).filter(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check ownership
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get post to update comments count
    result = await db.execute(select(Post).filter(Post.id == comment.post_id))
    post = result.scalar_one_or_none()
    
    # Delete comment
    await db.delete(comment)
    
    # Update post comments count
    if post:
        post.comments_count = max(0, (post.comments_count or 1) - 1)
    
    await db.commit()
    return {"message": "Comment deleted successfully"}

# =====================
# COMMENT LIKES ENDPOINTS
# =====================

@router.post("/comments/{comment_id}/like", response_model=CommentLikeResponse)
async def like_comment(
    comment_id: int,
    is_like: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Like or dislike a comment"""
    # Check if comment exists
    result = await db.execute(select(Comment).filter(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if user already liked/disliked this comment
    existing_like_result = await db.execute(
        select(CommentLike).filter(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == current_user.id
        )
    )
    existing_like = existing_like_result.scalar_one_or_none()
    
    if existing_like:
        # Update existing like/dislike
        old_is_like = existing_like.is_like
        existing_like.is_like = is_like
        
        # Update comment counters
        if old_is_like != is_like:
            if old_is_like:  # Was like, now dislike
                comment.likes_count = max(0, (comment.likes_count or 1) - 1)
                comment.dislikes_count = (comment.dislikes_count or 0) + 1
            else:  # Was dislike, now like
                comment.dislikes_count = max(0, (comment.dislikes_count or 1) - 1)
                comment.likes_count = (comment.likes_count or 0) + 1
        
        await db.commit()
        await db.refresh(existing_like)
        return existing_like
    else:
        # Create new like/dislike
        new_like = CommentLike(
            comment_id=comment_id,
            user_id=current_user.id,
            is_like=is_like
        )
        db.add(new_like)
        
        # Update comment counters
        if is_like:
            comment.likes_count = (comment.likes_count or 0) + 1
        else:
            comment.dislikes_count = (comment.dislikes_count or 0) + 1
        
        await db.commit()
        await db.refresh(new_like)
        return new_like

@router.delete("/comments/{comment_id}/like")
async def remove_comment_like(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove like/dislike from a comment"""
    # Check if comment exists
    result = await db.execute(select(Comment).filter(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Find existing like
    existing_like_result = await db.execute(
        select(CommentLike).filter(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == current_user.id
        )
    )
    existing_like = existing_like_result.scalar_one_or_none()
    
    if not existing_like:
        raise HTTPException(status_code=404, detail="Like not found")
    
    # Update comment counters
    if existing_like.is_like:
        comment.likes_count = max(0, (comment.likes_count or 1) - 1)
    else:
        comment.dislikes_count = max(0, (comment.dislikes_count or 1) - 1)
    
    # Remove like
    await db.delete(existing_like)
    await db.commit()
    
    return {"message": "Like removed successfully"}

@router.get("/comments/{comment_id}/likes")
async def get_comment_likes(
    comment_id: int,
    like_type: str = "all",  # "likes", "dislikes", "all"
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get likes for a comment"""
    # Check if comment exists
    result = await db.execute(select(Comment).filter(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Build query based on like_type
    query = select(CommentLike).filter(CommentLike.comment_id == comment_id)
    
    if like_type == "likes":
        query = query.filter(CommentLike.is_like == True)
    elif like_type == "dislikes":
        query = query.filter(CommentLike.is_like == False)
    # "all" includes both likes and dislikes
    
    # Get total count
    count_query = select(func.count()).select_from(CommentLike).filter(CommentLike.comment_id == comment_id)
    if like_type == "likes":
        count_query = count_query.filter(CommentLike.is_like == True)
    elif like_type == "dislikes":
        count_query = count_query.filter(CommentLike.is_like == False)
    
    total = await db.scalar(count_query)
    
    # Apply pagination
    skip = (page - 1) * size
    query = query.order_by(CommentLike.created_at.desc()).offset(skip).limit(size)
    
    result = await db.execute(query)
    likes = result.scalars().all()
    
    return {
        "items": likes,
        "total": total,
        "page": page,
        "size": size,
        "like_type": like_type
    } 