import json
import logging
import os
from typing import Optional

import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession

import models
from enums import PictureType, PictureRetrieveLimits
from picture_service import PictureService

from fastapi import APIRouter, Depends, Form, File, UploadFile, Path
from fastapi.responses import FileResponse
from postgres.database import get_db, engine, Base
from postgres.db_models import DBPicture

waterbowl_router = APIRouter()

logging.basicConfig(
    level=logging.DEBUG if os.environ.get("DEBUG") == "true" else logging.INFO
)
logger = logging.getLogger(__name__)


@waterbowl_router.on_event("startup")
async def init_models():
    async with engine.begin() as conn:
        if os.environ.get("LOCAL"):
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@waterbowl_router.get("/health")
async def health_endpoint() -> str:
    return "pong"


@waterbowl_router.post("/pictures/", response_model=models.Picture)
async def add_pictures_endpoint(
    db: AsyncSession = Depends(get_db),
    picture: UploadFile = File(),
    timestamp: float = Form(),
) -> models.Picture:
    picture_service = PictureService(db=db)
    db_picture = await picture_service.create_pictures(
        picture=picture, timestamp=timestamp
    )
    return db_picture


@waterbowl_router.get("/pictures/", response_class=FileResponse)
async def get_random_picture_endpoint(
    db: AsyncSession = Depends(get_db),
    picture_type: Optional[PictureType] = PictureType.WATER_BOWL,
    limit: Optional[PictureRetrieveLimits] = PictureRetrieveLimits.NO_ANNOTATION,
) -> FileResponse:
    picture_service = PictureService(db=db)
    random_picture: DBPicture = await picture_service.get_random_picture(limit=limit)
    file = (
        random_picture.waterbowl_picture
        if picture_type == PictureType.WATER_BOWL
        else random_picture.food_picture
    )
    return FileResponse(
        file, headers={"PictureMetadata": json.dumps(random_picture.to_dict())}
    )


@waterbowl_router.get("/pictures/{picture_id}/", response_model=models.Picture)
async def get_picture_endpoint(
    picture_id: int = Path(), db: AsyncSession = Depends(get_db)
) -> models.Picture:
    picture_service = PictureService(db=db)
    picture: DBPicture = await picture_service.get_picture(picture_id)
    return picture


@waterbowl_router.patch(
    "/pictures/{metadata_id}/", response_model=models.PictureMetadata
)
async def update_picture_endpoint(
    update_request: models.PictureUpdateRequest,
    metadata_id: int = Path(),
    db: AsyncSession = Depends(get_db),
) -> models.PictureMetadata:
    picture_service = PictureService(db=db)
    picture: DBPicture = await picture_service.update_metadata(
        metadata_id, updates=update_request
    )
    return picture.picture_metadata
