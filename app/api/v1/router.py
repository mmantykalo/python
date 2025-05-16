
from fastapi import APIRouter
from app.api.v1.endpoints import users, posts

router = APIRouter()
router.include_router(users.router, tags=["users"])
router.include_router(posts.router, tags=["posts"])
