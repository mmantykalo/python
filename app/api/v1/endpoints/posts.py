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
    privacy_filter: bool = True,
    user_id: Optional[int] = None,
    following_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get posts with advanced filtering:
    - privacy_filter: Apply privacy level filtering (default: True)
    - user_id: Filter posts by specific user (optional)
    - following_only: Show only posts from followed users (default: False)
    """
    skip = (page - 1) * size
    posts, total = await PostService.get_posts_with_filters(
        db=db,
        skip=skip,
        limit=size,
        current_user_id=current_user.id,
        privacy_filter=privacy_filter,
        user_id=user_id,
        following_only=following_only
    )
    return {
        "items": posts,
        "total": total,
        "page": page,
        "size": size
    }

@router.get("/posts/feed", response_model=PaginatedResponse)
async def get_posts_feed(
    page: int = 1,
    size: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get personalized posts feed: posts from followed users + public posts
    """
    skip = (page - 1) * size
    posts, total = await PostService.get_posts_with_filters(
        db=db,
        skip=skip,
        limit=size,
        current_user_id=current_user.id,
        privacy_filter=True,  # Always apply privacy filtering
        user_id=None,
        following_only=False  # Show all posts with privacy filtering
    )
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
    center_lat: float,
    center_lon: float,
    radius_km: float = 30.0,  # Default 30km radius
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.utils.geo import get_bounding_box
    
    # Convert center + radius to bounding box for database query
    lat_min, lat_max, lon_min, lon_max = get_bounding_box(center_lat, center_lon, radius_km)
    
    return await PostService.get_posts_by_location(db, lat_min, lat_max, lon_min, lon_max, current_user.id)

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
    privacy_level: str = Form("PUBLIC"),
    is_comments_enabled: bool = Form(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Upload image to cloudinary
    result = cloudinary.uploader.upload(image.file)
    
    # Create post data
    post_data = {
        "image_url": result["secure_url"],
        "comment": comment,
        "latitude": latitude,
        "longitude": longitude,
        "privacy_level": privacy_level,
        "is_comments_enabled": is_comments_enabled
    }
    
    return await PostService.create_post(db, post_data, current_user.id)

@router.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    db: AsyncSession = Depends(get_db)
):
    post = await PostService.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.put("/posts/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    post: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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
    # Check if post exists and belongs to user
    existing_post = await PostService.get_post(db, post_id)
    if not existing_post:
        raise HTTPException(status_code=404, detail="Post not found")
    if existing_post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    post = await PostService.delete_post(db, post_id, current_user.id)
    return post
