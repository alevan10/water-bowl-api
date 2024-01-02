import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Union, cast

import aiofiles
import shortuuid
import tensorflow as tf
from enums import (
    FOOD_BOWL_CROP_WINDOW,
    PICTURES_DIR,
    WATER_BOWL_CROP_WINDOW,
    PictureRetrieveLimits,
    PictureType,
)
from fastapi import UploadFile
from models import PictureUpdateRequest
from postgres.db_models import DBPicture, DBPictureMetadata
from sqlalchemy import and_, false, or_, select, true, update
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

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

    async def create_metadata(self) -> DBPictureMetadata:
        db_picture_metadata = DBPictureMetadata()
        self._db.add(db_picture_metadata)
        await self._db.commit()
        return db_picture_metadata

    async def create_pictures(self, picture: UploadFile, timestamp: float) -> DBPicture:
        waterbowl_picture, food_picture, time = await save_pictures(
            in_file=picture, timestamp=timestamp
        )
        metadata = await self.create_metadata()
        time = datetime.fromtimestamp(timestamp)
        db_picture = DBPicture(
            metadata_id=metadata.id,
            waterbowl_picture=f"{waterbowl_picture}",
            food_picture=f"{food_picture}",
            picture_timestamp=time,
        )
        self._db.add(db_picture)
        await self._db.commit()
        await self._db.refresh(db_picture)
        return db_picture

    async def _get_single_item(
        self, item_type: type, item_id: int
    ) -> Union[DBPicture, DBPictureMetadata]:
        item = await self._db.get(entity=item_type, ident=item_id)
        return item

    async def get_metadata(self, metadata_id: int) -> DBPictureMetadata:
        metadata: DBPictureMetadata = await self._get_single_item(
            item_type=DBPictureMetadata, item_id=metadata_id
        )
        logger.debug("Metadata retrieved", extra=metadata.to_dict())
        return metadata

    async def get_picture(self, picture_id: int) -> DBPicture:
        picture: DBPicture = await self._get_single_item(
            item_type=DBPicture, item_id=picture_id
        )
        if picture:
            logger.debug("Picture retrieved", extra=picture.to_dict())
        else:
            logger.debug("No picture found with id %s", picture_id)
        return picture

    async def get_random_picture(
        self, limit: PictureRetrieveLimits = None
    ) -> Optional[DBPicture]:
        statement = (
            select(DBPicture)
            .order_by(func.random())  # pylint: disable=not-callable
            .limit(1)
        )
        if limit:
            if limit == PictureRetrieveLimits.NO_ANNOTATION:
                statement = (
                    select(DBPicture, DBPictureMetadata)
                    .join(DBPicture.picture_metadata)
                    .filter(
                        and_(
                            DBPictureMetadata.human_water_yes == 0,
                            DBPictureMetadata.human_water_no == 0,
                        )
                    )
                    .order_by(func.random())  # pylint: disable=not-callable
                    .limit(1)
                )
            if limit == PictureRetrieveLimits.HUMAN_ANNOTATED:
                statement = (
                    select(DBPicture, DBPictureMetadata)
                    .join(DBPicture.picture_metadata)
                    .filter(
                        or_(
                            DBPictureMetadata.human_water_yes > 0,
                            DBPictureMetadata.human_water_no > 0,
                        )
                    )
                    .order_by(func.random())  # pylint: disable=not-callable
                    .limit(1)
                )
        result: Result = await self._db.execute(statement)
        if pictures := result.fetchone():
            picture = pictures[0]
            return picture
        return None

    async def update_metadata(
        self, metadata_id: int, updates: PictureUpdateRequest
    ) -> DBPictureMetadata:
        metadata = await self.get_metadata(metadata_id)
        updated_human_water_yes = metadata.human_water_yes + updates.human_water_yes
        updated_human_water_no = metadata.human_water_no + updates.human_water_no
        updated_human_food_yes = metadata.human_food_yes + updates.human_food_yes
        updated_human_food_no = metadata.human_food_no + updates.human_food_no
        updated_human_cat_yes = metadata.human_cat_yes + updates.human_cat_yes
        updated_human_cat_no = metadata.human_cat_no + updates.human_cat_no
        updated_water_in_bowl = updated_human_water_yes > updated_human_water_no
        updated_food_in_bowl = updated_human_food_yes > updated_human_food_no
        updated_cat_at_bowl = updated_human_cat_yes > updated_human_cat_no
        statement = (
            update(DBPictureMetadata)
            .where(DBPictureMetadata.id == metadata_id)
            .values(
                water_in_bowl=updated_water_in_bowl,
                food_in_bowl=updated_food_in_bowl,
                cat_at_bowl=updated_cat_at_bowl,
                human_cat_yes=updated_human_cat_yes,
                human_water_yes=updated_human_water_yes,
                human_food_yes=updated_human_food_yes,
                human_cat_no=updated_human_cat_no,
                human_water_no=updated_human_water_no,
                human_food_no=updated_human_food_no,
            )
        )
        await self._db.execute(statement=statement)
        return metadata

    async def get_annotated_pictures(
        self, limit: int, picture_type: PictureType, picture_class: bool
    ) -> list[DBPicture]:
        if limit < 0:
            limit = None
        if picture_type == PictureType.WATER_BOWL:
            metadata_type = DBPictureMetadata.water_in_bowl
        elif picture_type == PictureType.FOOD_BOWL:
            metadata_type = DBPictureMetadata.food_in_bowl
        else:
            metadata_type = DBPictureMetadata.cat_at_bowl

        if picture_class is True:
            statement = (
                select(DBPicture)
                .join(DBPicture.picture_metadata)
                .filter(metadata_type == true())
                .order_by(func.random())  # pylint: disable=not-callable
                .limit(limit)
            )
        else:
            if picture_type == PictureType.WATER_BOWL:
                metadata_annotation_type = DBPictureMetadata.human_water_no
            elif picture_type == PictureType.FOOD_BOWL:
                metadata_annotation_type = DBPictureMetadata.human_food_no
            else:
                metadata_annotation_type = DBPictureMetadata.human_cat_no
            statement = (
                select(DBPicture)
                .join(DBPicture.picture_metadata)
                .filter(and_(metadata_type == false(), metadata_annotation_type > 0))
                .order_by(func.random())  # pylint: disable=not-callable
                .limit(limit)
            )
        result: Result = await self._db.execute(statement)
        if pictures := result.fetchall():
            pictures = [picture[0] for picture in pictures]
            return cast(list[DBPicture], pictures)
        return []
