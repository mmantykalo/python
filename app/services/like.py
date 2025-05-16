
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.like import Like
from app.models.post import Post
from typing import Optional

class LikeService:
    @staticmethod
    async def create_like(db: AsyncSession, post_id: int, user_id: int) -> Optional[Like]:
        db_like = Like(post_id=post_id, user_id=user_id)
        db.add(db_like)
        try:
            await db.commit()
            await db.refresh(db_like)
            return db_like
        except:
            await db.rollback()
            return None

    @staticmethod
    async def delete_like(db: AsyncSession, post_id: int, user_id: int) -> bool:
        result = await db.execute(
            select(Like).filter(
                Like.post_id == post_id,
                Like.user_id == user_id
            )
        )
        like = result.scalar_one_or_none()
        if like:
            await db.delete(like)
            await db.commit()
            return True
        return False

    @staticmethod
    async def get_post_likes_count(db: AsyncSession, post_id: int) -> int:
        result = await db.execute(
            select(func.count(Like.id)).filter(Like.post_id == post_id)
        )
        return result.scalar_one()

    @staticmethod
    async def has_user_liked_post(db: AsyncSession, post_id: int, user_id: int) -> bool:
        result = await db.execute(
            select(Like).filter(
                Like.post_id == post_id,
                Like.user_id == user_id
            )
        )
        return result.scalar_one_or_none() is not None
