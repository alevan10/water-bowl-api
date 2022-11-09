from datetime import datetime

import pytest

from picture_service import PictureService
from postgres.db_models import Picture


@pytest.fixture
def now():
    yield datetime.now()


@pytest.mark.asyncio
async def test_add_picture(now, postgres, picture_upload, test_picture_file, test_data_dir):
    picture_svc = PictureService(db=postgres)
    expected_picture = Picture(
        raw_picture_location=str(test_picture_file),
        pictures_location=str(test_data_dir),
        picture_timestamp=now
    )
    test_picture = await picture_svc.create_picture(picture=picture_upload, timestamp=now.timestamp())
    assert expected_picture.raw_picture_location == test_picture.raw_picture_location
    assert expected_picture.pictures_location == test_picture.pictures_location
    assert expected_picture.picture_timestamp == test_picture.picture_timestamp
    assert test_picture.id == 1
