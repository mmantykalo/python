
from fastapi import APIRouter
from app.api.v1.endpoints import users, posts, likes

router = APIRouter()
router.include_router(users.router, tags=["users"])
router.include_router(posts.router, tags=["posts"])
router.include_router(likes.router, tags=["likes"])
