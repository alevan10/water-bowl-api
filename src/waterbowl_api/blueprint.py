import json
import logging
import os
from pathlib import Path as FilePath
from typing import Optional

import models
from enums import PictureRetrieveLimits, PictureType
from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, UploadFile
from fastapi.responses import FileResponse

from packaging_service import ZipPackager
from picture_service import PictureService
from postgres.database import Base, engine, get_db
from postgres.db_models import DBPicture, DBPictureMetadata
from sqlalchemy.ext.asyncio import AsyncSession

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
    if random_picture:
        file = (
            FilePath(random_picture.waterbowl_picture)
            if picture_type == PictureType.WATER_BOWL
            else FilePath(random_picture.food_picture)
        )
        if file.exists():
            return FileResponse(
                file, headers={"PictureMetadata": json.dumps(random_picture.to_dict())}
            )
        raise HTTPException(
            status_code=404, detail="No picture file associated with this picture ID."
        )
    raise HTTPException(status_code=404, detail="No items found with given limit.")


@waterbowl_router.get("/pictures/{picture_id}/", response_model=models.Picture)
async def get_picture_endpoint(
    picture_id: int = Path(), db: AsyncSession = Depends(get_db)
) -> models.Picture:
    picture_service = PictureService(db=db)
    picture: DBPicture = await picture_service.get_picture(picture_id)
    if picture:
        return picture
    raise HTTPException(status_code=404, detail="Item not found")


@waterbowl_router.get(
    "/pictures/{picture_id}/metadata/", response_model=models.PictureMetadata
)
async def get_picture_metadata(
    picture_id: int = Path(), db: AsyncSession = Depends(get_db)
) -> models.PictureMetadata:
    picture_service = PictureService(db=db)
    picture: DBPicture = await picture_service.get_picture(picture_id)
    if picture:
        picture_metadata: DBPictureMetadata = await picture_service.get_metadata(
            picture.metadata_id
        )
        return picture_metadata.to_api_return(picture_id)
    raise HTTPException(status_code=404, detail="Item not found")


@waterbowl_router.patch("/pictures/{picture_id}/", response_model=models.Picture)
async def update_picture_endpoint(
    update_request: models.PictureUpdateRequest,
    picture_id: int = Path(),
    db: AsyncSession = Depends(get_db),
) -> models.Picture:
    picture_service = PictureService(db=db)
    picture: DBPicture = await picture_service.get_picture(picture_id=picture_id)
    if picture:
        await picture_service.update_metadata(
            picture.metadata_id, updates=update_request
        )
        return picture
    raise HTTPException(status_code=404, detail="Item not found")


@waterbowl_router.get("/pictures/annotated-batch/")
async def get_batch_picture_endpoint(
    db: AsyncSession = Depends(get_db),
    picture_type: Optional[PictureType] = PictureType.WATER_BOWL,
    picture_class: Optional[bool] = None,
    limit: Optional[int] = 100,
) -> FileResponse:
    """
    Returns a .zip file containing a directory of classified images split between positive and negative classes,
    and a json file with image information.
    """
    picture_service = PictureService(db=db)
    positive_pictures: list[DBPicture] = []
    negative_pictures: list[DBPicture] = []
    if picture_class is True or picture_class is None:
        positive_pictures = await picture_service.get_annotated_pictures(
            limit=limit, picture_type=picture_type, picture_class=True
        )
    if picture_class is False or picture_class is None:
        negative_pictures = await picture_service.get_annotated_pictures(
            limit=limit, picture_type=picture_type, picture_class=False
        )
    if not positive_pictures and not negative_pictures:
        raise HTTPException(status_code=404, detail="No items found with given limit.")
    picture_metadata = {}
    for picture in [*positive_pictures, *negative_pictures]:
        file = (
            FilePath(picture.waterbowl_picture)
            if picture_type == PictureType.WATER_BOWL
            else FilePath(picture.food_picture)
        )
        if file.exists():
            picture_metadata[file.name] = json.dumps(picture.to_dict())
    async with ZipPackager.generate_dataset_zip(
            positive_picture_files=positive_pictures,
            negative_picture_files=negative_pictures,
            picture_metadata=picture_metadata,
            class_name=picture_type
    ) as zip_package:
        return FileResponse(zip_package)
