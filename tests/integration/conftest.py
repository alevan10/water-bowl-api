import asyncio
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator
from unittest import mock

import pytest
import pytest_asyncio
from enums import POSTGRES_ADDRESS, POSTGRES_DATABASE, POSTGRES_PASSWORD, POSTGRES_USER
from fastapi import UploadFile
from postgres.database import Base
from postgres.db_models import DBPicture, DBPictureMetadata
from sqlalchemy import Table
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

database_uri = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_ADDRESS}/{POSTGRES_DATABASE}"
engine = create_async_engine(database_uri)
TestingSession = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(scope="session")
def event_loop():
    """
    Creates an instance of the default event loop for the test session.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def postgres_connection() -> AsyncConnection:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        yield conn
        await conn.close()


@pytest_asyncio.fixture
async def postgres(postgres_connection) -> AsyncSession:
    db = TestingSession(bind=postgres_connection)
    yield db
    await db.close()


@pytest.fixture
@pytest.mark.asyncio
async def postgres_tables(postgres_engine: AsyncConnection) -> tuple[Table, Table]:
    await postgres_engine.run_sync(Base.metadata.reflect)
    yield Base.metadata.tables["test_pictures"], Base.metadata.tables[
        "test_pictures_modeling_data"
    ]


@pytest.fixture
def add_picture(
    postgres: AsyncSession,
    test_water_bowl_picture_file: Path,
    test_food_bowl_picture_file: Path,
) -> AsyncGenerator[DBPicture, None]:
    water_bowl = test_water_bowl_picture_file
    food_bowl = test_food_bowl_picture_file
    now = datetime.now()
    session = postgres
    created_pictures = []

    async def _add_picture(
        water_bowl: str = str(water_bowl),
        food_bowl: str = str(food_bowl),
        timestamp: datetime = now,
        water_in_bowl: bool = False,
        food_in_bowl: bool = False,
        cat_at_bowl: bool = False,
        human_cat_yes: int = 0,
        human_water_yes: int = 0,
        human_food_yes: int = 0,
        human_cat_no: int = 0,
        human_water_no: int = 0,
        human_food_no: int = 0,
    ):
        new_metadata = DBPictureMetadata(
            water_in_bowl=water_in_bowl,
            food_in_bowl=food_in_bowl,
            cat_at_bowl=cat_at_bowl,
            human_cat_yes=human_cat_yes,
            human_water_yes=human_water_yes,
            human_food_yes=human_food_yes,
            human_cat_no=human_cat_no,
            human_water_no=human_water_no,
            human_food_no=human_food_no,
        )
        session.add(new_metadata)
        await session.commit()
        new_picture = DBPicture(
            metadata_id=new_metadata.id,
            waterbowl_picture=water_bowl,
            food_picture=food_bowl,
            picture_timestamp=timestamp,
        )
        created_pictures.append(new_picture)
        session.add(new_picture)
        await session.commit()
        await session.refresh(new_picture)
        return new_picture

    yield _add_picture
    if created_pictures:
        for picture in created_pictures:
            session.sync_session.delete(picture)


@pytest.fixture
def add_multiple_pictures(
    postgres: AsyncSession,
    test_water_bowl_picture_file: Path,
    test_food_bowl_picture_file: Path,
) -> AsyncGenerator[list[DBPicture], None]:
    water_bowl = test_water_bowl_picture_file
    food_bowl = test_food_bowl_picture_file
    now = datetime.now()
    session = postgres
    created_pictures = []

    async def _add_pictures(
        water_bowl: str = str(water_bowl),
        food_bowl: str = str(food_bowl),
        timestamp: datetime = now,
        num_pictures: int = 5,
    ):
        new_pictures = []
        for i in range(0, num_pictures):
            new_metadata = DBPictureMetadata()
            session.add(new_metadata)
            await session.commit()
            new_picture = DBPicture(
                metadata_id=new_metadata.id,
                waterbowl_picture=water_bowl,
                food_picture=food_bowl,
                picture_timestamp=timestamp,
            )
            created_pictures.append(new_picture)
            session.add(new_picture)
            await session.commit()
            await session.refresh(new_picture)
            new_pictures.append(new_picture)
        return new_pictures

    yield _add_pictures
    if created_pictures:
        for picture in created_pictures:
            session.sync_session.delete(picture)


@pytest.fixture
def get_picture(
    postgres_session: AsyncSession,
):
    session = postgres_session

    async def _get_picture(picture_id: int):
        return await session.get(DBPicture, picture_id)

    yield _get_picture


@pytest.fixture
def picture_upload(test_raw_picture_file):
    with open(test_raw_picture_file, "rb") as file_upload:
        yield UploadFile(filename=test_raw_picture_file.name, file=file_upload)


@pytest.fixture
def mock_picture_service_dirs(test_picture_storage):
    with mock.patch("picture_service.PICTURES_DIR") as pictures_dir:
        pictures_dir.joinpath = test_picture_storage.joinpath
        yield
