from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_comment_id = Column(Integer, ForeignKey("comments.id"), nullable=True)  # For nested comments
    likes_count = Column(Integer, default=0)
    dislikes_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    post = relationship("Post", back_populates="comments")
    user = relationship("User")
    parent_comment = relationship("Comment", remote_side=[id])
    replies = relationship("Comment", back_populates="parent_comment")
    likes = relationship("CommentLike", back_populates="comment", cascade="all, delete-orphan") 