from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.user_settings import UserSettings
from app.schemas.user_settings import UserSettingsCreate, UserSettingsUpdate, UserSettingsResponse

router = APIRouter()

@router.get("/me/settings", response_model=UserSettingsResponse)
async def get_user_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's settings"""
    result = await db.execute(
        select(UserSettings).filter(UserSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create default settings if none exist
        settings = UserSettings(
            user_id=current_user.id,
            search_radius=30000,  # 30km default
            is_private=False,
            allow_comments=True
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    
    return settings

@router.put("/me/settings", response_model=UserSettingsResponse)
async def update_user_settings(
    settings_update: UserSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update current user's settings"""
    result = await db.execute(
        select(UserSettings).filter(UserSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create settings if none exist
        settings_data = settings_update.model_dump(exclude_unset=True)
        settings_data.update({
            "user_id": current_user.id,
            "search_radius": settings_data.get("search_radius", 30000),
            "is_private": settings_data.get("is_private", False),
            "allow_comments": settings_data.get("allow_comments", True)
        })
        settings = UserSettings(**settings_data)
        db.add(settings)
    else:
        # Update existing settings
        for field, value in settings_update.model_dump(exclude_unset=True).items():
            setattr(settings, field, value)
    
    await db.commit()
    await db.refresh(settings)
    return settings

@router.put("/me/settings/privacy", response_model=UserSettingsResponse)
async def update_privacy_settings(
    is_private: bool,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update privacy settings"""
    result = await db.execute(
        select(UserSettings).filter(UserSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create settings if none exist
        settings = UserSettings(
            user_id=current_user.id,
            search_radius=30000,
            is_private=is_private,
            allow_comments=True
        )
        db.add(settings)
    else:
        settings.is_private = is_private
    
    await db.commit()
    await db.refresh(settings)
    return settings

@router.put("/me/settings/search-radius", response_model=UserSettingsResponse)
async def update_search_radius(
    radius: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update search radius (in meters)"""
    # Validate radius (min 100m, max 100km)
    if radius < 100 or radius > 100000:
        raise HTTPException(
            status_code=400, 
            detail="Search radius must be between 100 meters and 100 kilometers"
        )
    
    result = await db.execute(
        select(UserSettings).filter(UserSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create settings if none exist
        settings = UserSettings(
            user_id=current_user.id,
            search_radius=radius,
            is_private=False,
            allow_comments=True
        )
        db.add(settings)
    else:
        settings.search_radius = radius
    
    await db.commit()
    await db.refresh(settings)
    return settings

@router.put("/me/settings/comments", response_model=UserSettingsResponse)
async def update_comment_settings(
    allow_comments: bool,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update comment settings"""
    result = await db.execute(
        select(UserSettings).filter(UserSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create settings if none exist
        settings = UserSettings(
            user_id=current_user.id,
            search_radius=30000,
            is_private=False,
            allow_comments=allow_comments
        )
        db.add(settings)
    else:
        settings.allow_comments = allow_comments
    
    await db.commit()
    await db.refresh(settings)
    return settings 