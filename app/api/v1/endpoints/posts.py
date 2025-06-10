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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get posts feed - requires authentication"""
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's posts - with privacy check"""
    # For now, only allow access to own posts (will be enhanced with privacy settings later)
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied - can only view own posts")
    
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get posts on map - requires authentication"""
    return await PostService.get_posts_by_location(db, lat_min, lat_max, lon_min, lon_max)

from fastapi import UploadFile, File, Form
import cloudinary
import cloudinary.uploader
from app.core.config import settings

# Initialize cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)

@router.post("/posts/", response_model=PostResponse)
async def create_post(
    image: UploadFile = File(...),
    comment: str = Form(None),
    latitude: float = Form(...),
    longitude: float = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new post - requires authentication"""
    # Upload image to cloudinary
    result = cloudinary.uploader.upload(image.file)
    
    # Create post data
    post_data = {
        "image_url": result["secure_url"],
        "comment": comment,
        "latitude": latitude,
        "longitude": longitude
    }
    
    return await PostService.create_post(db, post_data, current_user.id)

@router.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific post - requires authentication"""
    post = await PostService.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # For now, all authenticated users can view posts (will be enhanced with privacy levels later)
    return post

@router.put("/posts/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    post: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update post - only owner can edit"""
    # Check if post exists and belongs to user
    existing_post = await PostService.get_post(db, post_id)
    if not existing_post:
        raise HTTPException(status_code=404, detail="Post not found")
    if existing_post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    updated_post = await PostService.update_post(
        db, 
        post_id, 
        post.model_dump(),
        current_user.id
    )
    return updated_post

@router.delete("/posts/{post_id}", response_model=PostResponse)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete post - only owner can delete"""
    # Check if post exists and belongs to user
    existing_post = await PostService.get_post(db, post_id)
    if not existing_post:
        raise HTTPException(status_code=404, detail="Post not found")
    if existing_post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    post = await PostService.delete_post(db, post_id, current_user.id)
    return post
