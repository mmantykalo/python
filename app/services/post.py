
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.post import Post
from typing import List, Dict, Any, Optional

class PostService:
    @staticmethod
    async def get_posts(db: AsyncSession) -> List[Post]:
        result = await db.execute(select(Post).order_by(Post.created_at.desc()))
        return result.scalars().all()

    @staticmethod
    async def get_posts_by_location(
        db: AsyncSession, 
        lat_min: float, 
        lat_max: float, 
        lon_min: float, 
        lon_max: float
    ) -> List[Post]:
        result = await db.execute(
            select(Post)
            .filter(Post.latitude.between(lat_min, lat_max))
            .filter(Post.longitude.between(lon_min, lon_max))
            .order_by(Post.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def create_post(db: AsyncSession, post_data: Dict[str, Any], user_id: int) -> Post:
        db_post = Post(**post_data, user_id=user_id)
        db.add(db_post)
        await db.commit()
        await db.refresh(db_post)
        return db_post

    @staticmethod
    async def delete_post(db: AsyncSession, post_id: int, user_id: int) -> Optional[Post]:
        result = await db.execute(
            select(Post).filter(Post.id == post_id, Post.user_id == user_id)
        )
        post = result.scalar_one_or_none()
        if post:
            await db.delete(post)
            await db.commit()
        return post
