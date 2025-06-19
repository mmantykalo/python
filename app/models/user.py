from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from app.db.base import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    bio = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    posts = relationship("Post", back_populates="user")
    settings = relationship("UserSettings", back_populates="user", uselist=False)
    followers = relationship("Follow", foreign_keys="Follow.following_id", back_populates="following")
    following = relationship("Follow", foreign_keys="Follow.follower_id", back_populates="follower")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
