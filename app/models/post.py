from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
import enum

class PrivacyLevel(enum.Enum):
    PUBLIC = "PUBLIC"
    FOLLOWERS = "FOLLOWERS"
    PRIVATE = "PRIVATE"

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String, nullable=False)
    comment = Column(String)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    privacy_level = Column(Enum(PrivacyLevel), default=PrivacyLevel.PUBLIC)
    comments_count = Column(Integer, default=0)
    is_comments_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="posts")
    likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
