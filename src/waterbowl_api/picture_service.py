import logging
from datetime import datetime
from pathlib import Path
from typing import Tuple

import aiofiles
import shortuuid
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from enums import (
    RAW_PICTURES_DIR,
)
from postgres.db_models import Picture, PictureMetadata

# "postgres-svc.postgres.cluster.local"
# "pictures"

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
        raw_picture_path = RAW_PICTURES_DIR.joinpath(filename)
        async with aiofiles.open(raw_picture_path, "w+b") as out_file:
            content = await in_file.read()
            await out_file.write(content)
        return raw_picture_path, time

    async def _create_training_pictures(self):
        pass

    async def create_metadata(self) -> PictureMetadata:
        db_picture_metadata = PictureMetadata()
        self._db.add(db_picture_metadata)
        await self._db.commit()
        return db_picture_metadata

    async def create_picture(self, picture: UploadFile, timestamp: float) -> Picture:
        raw_picture_path, time = await self._save_picture(
            in_file=picture, timestamp=timestamp
        )
        await self._create_training_pictures()
        metadata = await self.create_metadata()
        time = datetime.fromtimestamp(timestamp)
        db_picture = Picture(
            metadata_id=metadata.id,
            raw_picture_location=f"{raw_picture_path}",
            pictures_location=f"{raw_picture_path}",
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
        metadata = await self._get_single_item(item_type=PictureMetadata, item_id=metadata_id)
        return metadata

    async def get_picture(self, picture_id: int) -> Picture:
        picture = await self._get_single_item(item_type=Picture, item_id=picture_id)
        return picture
