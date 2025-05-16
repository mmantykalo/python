
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.post import PostCreate, PostResponse, PaginatedResponse
from app.services.post import PostService

router = APIRouter()

@router.get("/posts/", response_model=PaginatedResponse)
async def get_posts(
    page: int = 1,
    size: int = 10,
    db: AsyncSession = Depends(get_db)
):
    skip = (page - 1) * size
    posts, total = await PostService.get_posts(db, skip, size)
    return {
        "items": posts,
        "total": total,
        "page": page,
        "size": size
    }

@router.get("/users/{user_id}/posts", response_model=PaginatedResponse)
async def get_user_posts(
    user_id: int,
    page: int = 1,
    size: int = 10,
    db: AsyncSession = Depends(get_db)
):
    skip = (page - 1) * size
    posts, total = await PostService.get_user_posts(db, user_id, skip, size)
    return {
        "items": posts,
        "total": total,
        "page": page,
        "size": size
    }

@router.get("/posts/map", response_model=List[PostResponse])
async def get_posts_by_location(
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
    db: AsyncSession = Depends(get_db)
):
    return await PostService.get_posts_by_location(db, lat_min, lat_max, lon_min, lon_max)

@router.post("/posts/", response_model=PostResponse)
async def create_post(
    post: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await PostService.create_post(db, post.model_dump(), current_user.id)

@router.delete("/posts/{post_id}", response_model=PostResponse)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = await PostService.delete_post(db, post_id, current_user.id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post
