from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class CommentLike(Base):
    __tablename__ = "comment_likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=False)
    is_like = Column(Boolean, nullable=False)  # True = like, False = dislike
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")
    comment = relationship("Comment", back_populates="likes")

    __table_args__ = (
        UniqueConstraint('user_id', 'comment_id', name='unique_user_comment_like'),
    ) 