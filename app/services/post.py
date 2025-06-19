from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from app.models.post import Post, PrivacyLevel
from app.models.like import Like
from app.models.follow import Follow
from app.models.user import User
from typing import List, Dict, Any, Optional

class PostService:
    @staticmethod
    async def get_posts(db: AsyncSession, skip: int = 0, limit: int = 10) -> tuple[List[Post], int]:
        # Get total count
        total = await db.scalar(select(func.count()).select_from(Post))
        
        # Get paginated posts with likes count
        result = await db.execute(
            select(
                Post,
                func.count(Like.id).label('likes_count')
            )
            .outerjoin(Like)
            .group_by(Post.id)
            .order_by(Post.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all(), total

    @staticmethod
    async def get_posts_with_filters(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 10,
        current_user_id: Optional[int] = None,
        privacy_filter: bool = True,
        user_id: Optional[int] = None,
        following_only: bool = False
    ) -> tuple[List[Post], int]:
        """
        Get posts with advanced filtering:
        - privacy_filter: Apply privacy level filtering (requires current_user_id)
        - user_id: Filter posts by specific user
        - following_only: Show only posts from users that current user follows
        """
        
        # Base query
        query = select(Post).order_by(Post.created_at.desc())
        count_query = select(func.count()).select_from(Post)
        
        # Filter by specific user
        if user_id:
            query = query.filter(Post.user_id == user_id)
            count_query = count_query.filter(Post.user_id == user_id)
        
        # Filter by following only
        if following_only and current_user_id:
            # Show posts only from users that current user follows
            following_user_ids = select(Follow.following_id).filter(
                Follow.follower_id == current_user_id
            )
            query = query.filter(Post.user_id.in_(following_user_ids))
            count_query = count_query.filter(Post.user_id.in_(following_user_ids))
        
        # Apply privacy filtering
        if privacy_filter and current_user_id:
            privacy_conditions = or_(
                # Show public posts to everyone
                Post.privacy_level == PrivacyLevel.PUBLIC,
                
                # Show user's own posts regardless of privacy level
                Post.user_id == current_user_id,
                
                # Show followers-only posts to followers
                and_(
                    Post.privacy_level == PrivacyLevel.FOLLOWERS,
                    Post.user_id.in_(
                        select(Follow.following_id).filter(
                            Follow.follower_id == current_user_id
                        )
                    )
                )
            )
            query = query.filter(privacy_conditions)
            count_query = count_query.filter(privacy_conditions)
        
        # Get total count
        total = await db.scalar(count_query)
        
        # Get paginated posts
        result = await db.execute(
            query.offset(skip).limit(limit)
        )
        
        return result.scalars().all(), total

    @staticmethod
    async def get_user_posts(
        db: AsyncSession, 
        user_id: int,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Post], int]:
        # Get total count for user
        total = await db.scalar(
            select(func.count())
            .select_from(Post)
            .filter(Post.user_id == user_id)
        )
        
        # Get paginated user posts
        result = await db.execute(
            select(Post)
            .filter(Post.user_id == user_id)
            .order_by(Post.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all(), total

    @staticmethod
    async def get_posts_by_location(
        db: AsyncSession, 
        lat_min: float, 
        lat_max: float, 
        lon_min: float, 
        lon_max: float,
        current_user_id: int
    ) -> List[Post]:
        """
        Get posts in location with privacy filtering:
        - PUBLIC: Show to all authenticated users
        - FOLLOWERS: Show only to followers of the post author
        - PRIVATE: Show only to the post author
        """
        
        # Base query with location filtering and likes/dislikes count
        query = select(
            Post,
            func.count(func.nullif(Like.is_like, False)).label('likes_count'),
            func.count(func.nullif(Like.is_like, True)).label('dislikes_count')
        ).outerjoin(Like).filter(
            Post.latitude.between(lat_min, lat_max),
            Post.longitude.between(lon_min, lon_max)
        ).group_by(Post.id)
        
        # Privacy filtering
        privacy_conditions = or_(
            # Show public posts to everyone
            Post.privacy_level == PrivacyLevel.PUBLIC,
            
            # Show user's own posts regardless of privacy level
            Post.user_id == current_user_id,
            
            # Show followers-only posts to followers
            and_(
                Post.privacy_level == PrivacyLevel.FOLLOWERS,
                Post.user_id.in_(
                    select(Follow.following_id).filter(
                        Follow.follower_id == current_user_id
                    )
                )
            )
        )
        
        query = query.filter(privacy_conditions).order_by(Post.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create_post(db: AsyncSession, post_data: Dict[str, Any], user_id: int) -> Post:
        db_post = Post(**post_data, user_id=user_id)
        db.add(db_post)
        await db.commit()
        await db.refresh(db_post)
        return db_post

    @staticmethod
    async def get_post(db: AsyncSession, post_id: int) -> Optional[Post]:
        result = await db.execute(select(Post).filter(Post.id == post_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_post(
        db: AsyncSession, 
        post_id: int, 
        post_data: Dict[str, Any],
        user_id: int
    ) -> Optional[Post]:
        result = await db.execute(
            select(Post).filter(Post.id == post_id, Post.user_id == user_id)
        )
        post = result.scalar_one_or_none()
        if post:
            for key, value in post_data.items():
                setattr(post, key, value)
            await db.commit()
            await db.refresh(post)
        return post

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
