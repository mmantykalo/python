from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional
from app.api.deps import get_db
from app.models.post import Post, PrivacyLevel
from app.schemas.post import PostResponse, PaginatedResponse
from app.utils.geo import haversine_distance
import math

router = APIRouter()


@router.get("/posts", response_model=PaginatedResponse)
async def get_public_posts(
    page: int = 1,
    size: int = 10,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius: Optional[int] = 30000,  # 30km default
    db: AsyncSession = Depends(get_db)
):
    """
    Get public posts without authentication (guest mode)
    Only shows posts with privacy_level = 'public'
    """
    skip = (page - 1) * size
    
    # Base query - only public posts
    query = select(Post).filter(Post.privacy_level == PrivacyLevel.PUBLIC)
    
    # Apply geo filtering if coordinates provided
    if lat is not None and lon is not None:
        # Get all posts within approximate bounding box first (for performance)
        lat_radius_deg = radius / 111000  # roughly 111km per degree
        lon_radius_deg = radius / (111000 * math.cos(math.radians(lat)))
        
        query = query.filter(
            and_(
                Post.latitude.between(lat - lat_radius_deg, lat + lat_radius_deg),
                Post.longitude.between(lon - lon_radius_deg, lon + lon_radius_deg)
            )
        )
    
    # Execute query with pagination
    result = await db.execute(query.offset(skip).limit(size))
    posts = result.scalars().all()
    
    # Apply precise geo filtering if coordinates provided
    if lat is not None and lon is not None:
        filtered_posts = []
        for post in posts:
            distance = haversine_distance(lat, lon, post.latitude, post.longitude) * 1000  # Convert km to meters
            if distance <= radius:
                filtered_posts.append(post)
        posts = filtered_posts
    
    # Get total count for pagination
    count_result = await db.execute(
        select(Post).filter(Post.privacy_level == PrivacyLevel.PUBLIC)
    )
    total = len(count_result.scalars().all())
    
    return {
        "items": posts,
        "total": total,
        "page": page,
        "size": size
    }


@router.get("/posts/map", response_model=list[PostResponse])
async def get_public_posts_map(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"), 
    radius: int = Query(30000, description="Search radius in meters"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get public posts for map display (guest mode)
    Only shows posts with privacy_level = 'public'
    """
    # Approximate bounding box for performance
    lat_radius_deg = radius / 111000
    lon_radius_deg = radius / (111000 * math.cos(math.radians(lat)))
    
    # Get posts within bounding box
    result = await db.execute(
        select(Post)
        .filter(
            and_(
                Post.privacy_level == PrivacyLevel.PUBLIC,
                Post.latitude.between(lat - lat_radius_deg, lat + lat_radius_deg),
                Post.longitude.between(lon - lon_radius_deg, lon + lon_radius_deg)
            )
        )
    )
    posts = result.scalars().all()
    
    # Apply precise distance filtering
    filtered_posts = []
    for post in posts:
        distance = haversine_distance(lat, lon, post.latitude, post.longitude) * 1000  # Convert km to meters
        if distance <= radius:
            filtered_posts.append(post)
    
    return filtered_posts


@router.get("/posts/{post_id}", response_model=PostResponse)
async def get_public_post(
    post_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific public post (guest mode)
    Only allows access to posts with privacy_level = 'public'
    """
    result = await db.execute(
        select(Post).filter(
            and_(
                Post.id == post_id,
                Post.privacy_level == PrivacyLevel.PUBLIC
            )
        )
    )
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(
            status_code=404, 
            detail="Post not found or not public"
        )
    
    return post 