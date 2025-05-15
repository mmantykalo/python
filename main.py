
import asyncio
from fastapi import FastAPI
from app.db.base import Base, engine
from app.api.v1.router import router
import uvicorn

app = FastAPI(title="User Management API")

@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
