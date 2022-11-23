from datetime import datetime
from pathlib import Path
from unittest import mock

import pytest
import pytest_asyncio
from fastapi import UploadFile
from sqlalchemy import Table
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncConnection
from sqlalchemy.orm import sessionmaker
from postgres.db_models import Picture, PictureMetadata
from postgres.database import Base
from enums import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_ADDRESS, POSTGRES_DATABASE


@pytest_asyncio.fixture
async def postgres_engine() -> AsyncConnection:
    engine = create_async_engine(
        f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_ADDRESS}/{POSTGRES_DATABASE}",
        echo=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def postgres(postgres_engine: AsyncConnection) -> AsyncSession:
    async_local_session = sessionmaker(postgres_engine, expire_on_commit=False, class_=AsyncSession)
    yield async_local_session()


@pytest_asyncio.fixture
async def postgres_tables(postgres_engine: AsyncConnection) -> tuple[Table, Table]:
    await postgres_engine.run_sync(Base.metadata.reflect)
    yield Base.metadata.tables["test_pictures"], Base.metadata.tables["test_pictures_modeling_data"]


@pytest_asyncio.fixture
async def cleanup(postgres_engine):
    async with postgres_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest_asyncio.fixture
def add_picture(
        postgres: AsyncSession,
        test_picture_file: Path,
        test_data_dir: Path
):
    file = test_picture_file
    files = test_data_dir
    now = datetime.now()
    session = postgres

    async def _add_picture(
            raw_picture_file: Path = file,
            pictures_file: Path = files,
            timestamp: datetime = now
    ):
        new_picture = Picture(
            raw_picture_location=f"{raw_picture_file}",
            pictures_location=f"{pictures_file}",
            picture_timestamp=timestamp,
        )
        session.add(new_picture)
        await session.commit()
        new_picture = await session.refresh(new_picture)
        new_metadata = PictureMetadata(picture_id=new_picture.id)
        session.add(new_metadata)
        await session.commit()
        return new_picture

    yield _add_picture


@pytest_asyncio.fixture
def get_picture(
        postgres_session: AsyncSession,
):
    session = postgres_session

    async def _get_picture(
            picture_id: int
    ):
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


