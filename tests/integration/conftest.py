import asyncio
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator
from unittest import mock

import pytest
import pytest_asyncio
from fastapi import UploadFile
from sqlalchemy import Table
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from postgres.db_models import Pictures, PictureMetadata
from postgres.database import Base
from enums import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_ADDRESS, POSTGRES_DATABASE

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


@pytest_asyncio.fixture(scope="function")
async def postgres_connection() -> AsyncConnection:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        yield conn
        await conn.close()


@pytest_asyncio.fixture(scope="function")
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
) -> AsyncGenerator[Pictures, None]:
    water_bowl = test_water_bowl_picture_file
    food_bowl = test_food_bowl_picture_file
    now = datetime.now()
    session = postgres

    async def _add_picture(
        water_bowl: str = str(water_bowl),
        food_bowl: str = str(food_bowl),
        timestamp: datetime = now,
    ):
        new_metadata = PictureMetadata()
        session.add(new_metadata)
        await session.commit()
        new_picture = Pictures(
            metadata_id=new_metadata.id,
            waterbowl_picture=water_bowl,
            food_picture=food_bowl,
            picture_timestamp=timestamp,
        )
        session.add(new_picture)
        await session.commit()
        await session.refresh(new_picture)
        return new_picture

    yield _add_picture


@pytest.fixture
def get_picture(
    postgres_session: AsyncSession,
):
    session = postgres_session

    async def _get_picture(picture_id: int):
        return await session.get(Pictures, picture_id)

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
