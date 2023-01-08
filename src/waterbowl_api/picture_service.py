import logging
from datetime import datetime
from pathlib import Path
from typing import Tuple
import tensorflow as tf
import aiofiles
import shortuuid
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from enums import PICTURES_DIR, WATER_BOWL_CROP_WINDOW, FOOD_BOWL_CROP_WINDOW
from postgres.db_models import Pictures, PictureMetadata


logger = logging.getLogger(__name__)


class PostgresException(Exception):
    def __init__(self, message):
        super.__init__(message)


async def save_pictures(
    in_file: UploadFile, timestamp: float
) -> Tuple[Path, Path, datetime]:
    new_images: list[Path] = []
    in_file_data = await in_file.read()
    for crop_window in [WATER_BOWL_CROP_WINDOW, FOOD_BOWL_CROP_WINDOW]:
        file_suffix = f"{timestamp}_{shortuuid.uuid()}.jpeg"
        filename = (
            f"water_{file_suffix}"
            if crop_window == WATER_BOWL_CROP_WINDOW
            else f"food_{file_suffix}"
        )
        time = datetime.fromtimestamp(timestamp)
        raw_picture_path = PICTURES_DIR.joinpath(filename)
        async with aiofiles.open(raw_picture_path, "w+b") as out_file:
            decoded_image = tf.image.decode_and_crop_jpeg(
                contents=in_file_data, crop_window=crop_window, channels=1
            )
            new_jpg = tf.image.encode_jpeg(
                decoded_image, format="grayscale", quality=100
            )
            tf.io.write_file(filename=out_file.name, contents=new_jpg)
        new_images.append(raw_picture_path)
    return *new_images, time


class PictureService:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create_metadata(self) -> PictureMetadata:
        db_picture_metadata = PictureMetadata()
        self._db.add(db_picture_metadata)
        await self._db.commit()
        return db_picture_metadata

    async def create_pictures(self, picture: UploadFile, timestamp: float) -> Pictures:
        waterbowl_picture, food_picture, time = await save_pictures(
            in_file=picture, timestamp=timestamp
        )
        metadata = await self.create_metadata()
        time = datetime.fromtimestamp(timestamp)
        db_pictures = Pictures(
            metadata_id=metadata.id,
            waterbowl_picture=f"{waterbowl_picture}",
            food_picture=f"{food_picture}",
            picture_timestamp=time,
        )
        self._db.add(db_pictures)
        await self._db.commit()
        await self._db.refresh(db_pictures)
        return db_pictures

    async def _get_single_item(self, item_type: type, item_id: int):
        item = await self._db.get(entity=item_type, ident=item_id)
        return item

    async def get_metadata(self, metadata_id: int) -> PictureMetadata:
        metadata = await self._get_single_item(
            item_type=PictureMetadata, item_id=metadata_id
        )
        logger.debug("Metadata retrieved", extra=metadata.to_dict())
        return metadata

    async def get_picture(self, picture_id: int) -> Pictures:
        picture = await self._get_single_item(item_type=Pictures, item_id=picture_id)
        logger.debug("Picture retrieved", extra=picture.to_dict())
        return picture
