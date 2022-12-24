import logging
from datetime import datetime
from pathlib import Path
from typing import Tuple
import tensorflow as tf
import aiofiles
import shortuuid
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from enums import PICTURES_DIR
from postgres.db_models import Picture, PictureMetadata


logger = logging.getLogger(__name__)


class PostgresException(Exception):
    def __init__(self, message):
        super.__init__(message)


class PictureService:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def _save_picture(
        self, in_file: UploadFile, timestamp: float
    ) -> Tuple[Path, datetime]:
        filename = f"{timestamp}_{shortuuid.uuid()}.jpeg"
        time = datetime.fromtimestamp(timestamp)
        raw_picture_path = PICTURES_DIR.joinpath(filename)
        async with aiofiles.open(raw_picture_path, "w+b") as out_file:
            content = await in_file.read()
            decoded_image = tf.image.decode_and_crop_jpeg(
                contents=content, crop_window=[350, 450, 1000, 1400], channels=1
            )
            new_jpg = tf.image.encode_jpeg(
                decoded_image, format="grayscale", quality=100
            )
            tf.io.write_file(filename=out_file.name, contents=new_jpg)
        return raw_picture_path, time

    async def create_metadata(self) -> PictureMetadata:
        db_picture_metadata = PictureMetadata()
        self._db.add(db_picture_metadata)
        await self._db.commit()
        return db_picture_metadata

    async def create_picture(self, picture: UploadFile, timestamp: float) -> Picture:
        picture_path, time = await self._save_picture(
            in_file=picture, timestamp=timestamp
        )
        metadata = await self.create_metadata()
        time = datetime.fromtimestamp(timestamp)
        db_picture = Picture(
            metadata_id=metadata.id,
            picture_location=f"{picture_path}",
            picture_timestamp=time,
        )
        self._db.add(db_picture)
        await self._db.commit()
        await self._db.refresh(db_picture)
        return db_picture

    async def _get_single_item(self, item_type: type, item_id: int):
        item = await self._db.get(entity=item_type, ident=item_id)
        return item

    async def get_metadata(self, metadata_id: int) -> PictureMetadata:
        metadata = await self._get_single_item(
            item_type=PictureMetadata, item_id=metadata_id
        )
        logger.debug("Metadata retrieved", extra=metadata.to_dict())
        return metadata

    async def get_picture(self, picture_id: int) -> Picture:
        picture = await self._get_single_item(item_type=Picture, item_id=picture_id)
        logger.debug("Picture retrieved", extra=picture.to_dict())
        return picture
