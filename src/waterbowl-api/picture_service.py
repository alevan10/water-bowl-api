import logging
from datetime import datetime
from pathlib import Path
from typing import Tuple

import aiofiles
import shortuuid
from fastapi import UploadFile
from sqlalchemy import Table, Column, Integer, String, DateTime, Identity, MetaData
from sqlalchemy.exc import UnboundExecutionError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession

from enums import POSTGRES_ADDRESS, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_PICTURES_TABLE, RAW_PICTURES_DIR
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

    async def _save_picture(self, in_file: UploadFile, timestamp: float) -> Tuple[Path, datetime]:
        filename = f"{timestamp}_{shortuuid.uuid()}.jpeg"
        time = datetime.fromtimestamp(timestamp)
        raw_picture_path = RAW_PICTURES_DIR.joinpath(filename)
        async with aiofiles.open(raw_picture_path, 'w+b') as out_file:
            content = await in_file.read()
            await out_file.write(content)
        return raw_picture_path, time

    async def create_picture(self, picture: UploadFile, timestamp: float) -> Picture:
        raw_picture_path, time = await self._save_picture(in_file=picture, timestamp=timestamp)
        time = datetime.fromtimestamp(timestamp)
        db_picture = Picture(
            raw_picture_location=f"{raw_picture_path}",
            pictures_location=f"{raw_picture_path}",
            picture_timestamp=time,
        )
        self._db.add(db_picture)
        await self._db.commit()
        await self._db.refresh(db_picture)
        db_picture_metadata = PictureMetadata(picture_id=db_picture.id)
        self._db.add(db_picture_metadata)
        await self._db.commit()
        await self._db.refresh(db_picture_metadata)
        await self._db.refresh(db_picture)
        return db_picture
