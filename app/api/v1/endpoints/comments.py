from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment
from app.schemas.comment import CommentCreateRequest, CommentResponse, CommentUpdate
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