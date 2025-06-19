from fastapi import APIRouter
from app.api.v1.endpoints import users, posts, likes, follow, comments

router = APIRouter()
router.include_router(users.router, tags=["users"])
router.include_router(posts.router, tags=["posts"])
router.include_router(likes.router, tags=["likes"])
router.include_router(follow.router, tags=["follow"])
router.include_router(comments.router, tags=["comments"])
