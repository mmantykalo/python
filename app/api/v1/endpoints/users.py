
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.api.deps import get_db
from app.schemas.user import User, UserCreate, UserUpdate
from app.services.user import UserService

router = APIRouter()

@router.get("/users/", response_model=List[User])
async def get_users(db: AsyncSession = Depends(get_db)):
    return await UserService.get_users(db)

@router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await UserService.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/users/", response_model=User)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    return await UserService.create_user(db, user)

@router.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user: UserUpdate, db: AsyncSession = Depends(get_db)):
    updated_user = await UserService.update_user(db, user_id, user)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.delete("/users/{user_id}", response_model=User)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    deleted_user = await UserService.delete_user(db, user_id)
    if not deleted_user:
        raise HTTPException(status_code=404, detail="User not found")
    return deleted_user
