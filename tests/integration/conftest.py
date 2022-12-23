import asyncio
from asyncio import AbstractEventLoop
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator
from unittest import mock
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from fastapi import UploadFile
from sqlalchemy import Table
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from postgres.db_models import Picture, PictureMetadata
from postgres.database import Base
from enums import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_ADDRESS, POSTGRES_DATABASE

database_uri = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_ADDRESS}/{POSTGRES_DATABASE}"
engine = create_async_engine(database_uri)
TestingSession = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(scope='session')
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
        postgres: AsyncSession, test_picture_file: Path, test_data_dir: Path
) -> AsyncGenerator[Picture, None]:
    file = test_picture_file
    files = test_data_dir
    now = datetime.now()
    session = postgres

    async def _add_picture(
            raw_picture_file: Path = file,
            pictures_file: Path = files,
            timestamp: datetime = now,
    ):
        new_metadata = PictureMetadata()
        session.add(new_metadata)
        await session.commit()
        new_picture = Picture(
            metadata_id=new_metadata.id,
            raw_picture_location=f"{raw_picture_file}",
            pictures_location=f"{pictures_file}",
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
        return await session.get(Picture, picture_id)

    yield _get_picture


@pytest.fixture
def picture_upload(test_picture_file):
    with open(test_picture_file, "rb") as file_upload:
        yield UploadFile(filename=test_picture_file.name, file=file_upload)


@pytest.fixture
def mock_picture_service_dirs(test_raw_picture_storage):
    with mock.patch("picture_service.RAW_PICTURES_DIR") as raw_pictures_dir:
        raw_pictures_dir.joinpath = test_raw_picture_storage.joinpath
        yield
