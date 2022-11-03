import logging
import os

from sqlalchemy.ext.asyncio import AsyncSession

import models
from picture_service import PictureService

from fastapi import APIRouter, Depends, Form, File, UploadFile

from postgres.database import get_db, engine, Base

waterbowl_router = APIRouter()

logging.basicConfig(
    level=logging.DEBUG if os.environ.get("DEBUG") == "true" else logging.INFO
)
logger = logging.getLogger(__name__)


@waterbowl_router.on_event("startup")
async def init_models():
    async with engine.begin() as conn:
        if os.environ.get("TESTING"):
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@waterbowl_router.get("/health")
async def health_endpoint() -> str:
    return "pong"


@waterbowl_router.post("/pictures", response_model=models.Picture)
async def pictures_endpoint(
        db: AsyncSession = Depends(get_db),
        picture: UploadFile = File(),
        timestamp: float = Form(),
):
    picture_service = PictureService(db=db)
    picture = await picture_service.create_picture(picture=picture, timestamp=timestamp)
    return picture
