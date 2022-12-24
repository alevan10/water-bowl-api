from datetime import datetime

import pytest

from picture_service import PictureService


@pytest.fixture
def now():
    yield datetime.now()


@pytest.mark.usefixtures("mock_picture_service_dirs")
class TestPictureService:
    @pytest.mark.asyncio
    async def test_add_picture(
        self,
        now,
        postgres,
        picture_upload,
        test_picture_file,
        test_data_dir,
        test_picture_storage,
    ):
        picture_svc = PictureService(db=postgres)
        test_picture = await picture_svc.create_picture(
            picture=picture_upload, timestamp=now.timestamp()
        )

        stored_pictures = list(test_picture_storage.glob("*.jpeg"))
        assert len(stored_pictures) == 1
        stored_picture = stored_pictures[0]
        assert str(stored_picture) == test_picture.picture_location
        assert now == test_picture.picture_timestamp
        assert test_picture.id == 1

    @pytest.mark.asyncio
    async def test_get_picture(
        self,
        now,
        add_picture,
        postgres,
        picture_upload,
        test_picture_file,
        test_data_dir,
    ):
        test_picture = await add_picture(timestamp=now)

        picture_svc = PictureService(db=postgres)
        returned_picture = await picture_svc.get_picture(picture_id=test_picture.id)

        assert test_picture.id == returned_picture.id
        assert test_picture.metadata_id == returned_picture.metadata_id
        assert test_picture.picture_metadata == returned_picture.picture_metadata
