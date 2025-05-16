
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.like import LikeResponse
from app.services.like import LikeService

router = APIRouter()

@router.post("/posts/{post_id}/like", response_model=LikeResponse)
async def like_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    like = await LikeService.create_like(db, post_id, current_user.id)
    if not like:
        raise HTTPException(status_code=400, detail="Already liked or post not found")
    return like

@router.delete("/posts/{post_id}/like", status_code=204)
async def unlike_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = await LikeService.delete_like(db, post_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Like not found")

@router.get("/posts/{post_id}/likes", response_model=List[LikeResponse])
async def get_post_likes(
    post_id: int,
    page: int = 1,
    size: int = 10,
    db: AsyncSession = Depends(get_db)
):
    skip = (page - 1) * size
    likes = await LikeService.get_post_likes(db, post_id, skip, size)
    return likes
