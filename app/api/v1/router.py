from fastapi import APIRouter
from app.api.v1.endpoints import users, posts, likes, comments, settings, auth, public

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["authentication"])
router.include_router(public.router, prefix="/public", tags=["public"])
router.include_router(users.router, tags=["users"])
router.include_router(posts.router, tags=["posts"])
router.include_router(likes.router, tags=["likes"])
router.include_router(comments.router, tags=["comments"])
router.include_router(settings.router, tags=["settings"])
