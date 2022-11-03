import asyncio
import os

from blueprint import waterbowl_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from postgres.database import Base, engine

default_origins = [
    "http://levan.home",
    "https://levan.home",
    "http://localhost",
    "http://localhost:8080",
]


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def create_app() -> FastAPI:
    picture_app = FastAPI()
    picture_app.include_router(waterbowl_router)
    default_origins.extend(os.environ.get("ALLOWED_ORIGINS", []))
    picture_app.add_middleware(
        CORSMiddleware,
        allow_origins=default_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return picture_app


app = create_app()
