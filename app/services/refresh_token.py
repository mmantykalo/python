from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from app.models.refresh_token import RefreshToken
from app.core.security import create_refresh_token, get_refresh_token_expire_time
from datetime import datetime
from typing import Optional


class RefreshTokenService:
    @staticmethod
    async def create_refresh_token(
        db: AsyncSession, 
        user_id: int, 
        device_info: Optional[str] = None
    ) -> RefreshToken:
        """Create a new refresh token for user"""
        # Deactivate all existing refresh tokens for the user
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(is_active=False)
        )
        
        # Create new refresh token
        token_value = create_refresh_token()
        expires_at = get_refresh_token_expire_time()
        
        refresh_token = RefreshToken(
            user_id=user_id,
            token=token_value,
            expires_at=expires_at,
            device_info=device_info
        )
        
        db.add(refresh_token)
        await db.commit()
        await db.refresh(refresh_token)
        return refresh_token
    
    @staticmethod
    async def get_valid_refresh_token(
        db: AsyncSession, 
        token: str
    ) -> Optional[RefreshToken]:
        """Get valid refresh token by token value"""
        result = await db.execute(
            select(RefreshToken)
            .where(
                and_(
                    RefreshToken.token == token,
                    RefreshToken.is_active == True,
                    RefreshToken.expires_at > datetime.utcnow()
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def revoke_refresh_token(db: AsyncSession, token: str) -> bool:
        """Revoke a specific refresh token"""
        result = await db.execute(
            update(RefreshToken)
            .where(RefreshToken.token == token)
            .values(is_active=False)
        )
        await db.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def revoke_all_user_tokens(db: AsyncSession, user_id: int) -> bool:
        """Revoke all refresh tokens for a user"""
        result = await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(is_active=False)
        )
        await db.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def cleanup_expired_tokens(db: AsyncSession) -> int:
        """Remove expired refresh tokens from database"""
        result = await db.execute(
            select(RefreshToken)
            .where(RefreshToken.expires_at <= datetime.utcnow())
        )
        expired_tokens = result.scalars().all()
        
        for token in expired_tokens:
            await db.delete(token)
        
        await db.commit()
        return len(expired_tokens) 