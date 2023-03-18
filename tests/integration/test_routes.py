import json
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient

from enums import PictureType, PictureRetrieveLimits
from models import Picture
from postgres.database import get_db
from postgres.db_models import DBPicture
from waterbowl_api.app import app


@pytest.fixture
def override_get_db(postgres):
    def _override():
        yield postgres

    yield _override


@pytest_asyncio.fixture
async def test_client(override_get_db) -> AsyncClient:
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://parakeet.squak") as async_client:
        yield async_client


@pytest.mark.usefixtures("mock_picture_service_dirs")
class TestRoutes:
    @pytest.mark.asyncio
    async def test_health_endpoint(self, test_client: AsyncClient):
        health_check = await test_client.get("/health")
        assert health_check.status_code == 200
        assert health_check.json() == "pong"

    @pytest.mark.asyncio
    async def test_upload_picture(
        self,
        test_client: AsyncClient,
        test_raw_picture_file: Path,
        test_picture_storage: Path,
    ):
        with open(test_raw_picture_file, "rb") as test_picture:
            data = {"timestamp": datetime.now().timestamp()}
            files = {"picture": test_picture}
            pictures_response = await test_client.post(
                "/pictures/", data=data, files=files
            )
        assert pictures_response.status_code == 200
        picture = Picture(**pictures_response.json())
        assert picture.picture_timestamp.timestamp() == data.get("timestamp")
        for expected_picture in [picture.waterbowl_picture, picture.food_picture]:
            assert Path(expected_picture) in test_picture_storage.glob("*.jpeg")

    @pytest.mark.asyncio
    async def test_multiple_uploads(
        self,
        test_client: AsyncClient,
        test_raw_picture_file: Path,
        test_picture_storage: Path,
    ):
        with open(test_raw_picture_file, "rb") as test_picture:
            data = {"timestamp": datetime.now().timestamp()}
            files = {"picture": test_picture}
            pictures_response_1 = await test_client.post(
                "/pictures/", data=data, files=files
            )
            data = {"timestamp": datetime.now().timestamp()}
            pictures_response_2 = await test_client.post(
                "/pictures/", data=data, files=files
            )
        assert pictures_response_1.status_code == 200
        assert pictures_response_2.status_code == 200
        picture_1 = Picture(**pictures_response_1.json())
        picture_2 = Picture(**pictures_response_2.json())
        saved_picture_locations = [
            picture_1.waterbowl_picture,
            picture_1.food_picture,
            picture_2.waterbowl_picture,
            picture_2.food_picture,
        ]
        stored_pictures_locations = [
            str(picture_loc) for picture_loc in test_picture_storage.glob("*.jpeg")
        ]
        assert len(saved_picture_locations) == len(stored_pictures_locations)
        for picture_location in [
            picture_1.waterbowl_picture,
            picture_1.food_picture,
            picture_2.waterbowl_picture,
            picture_2.food_picture,
        ]:
            assert picture_location in stored_pictures_locations

    @pytest.mark.asyncio
    async def test_get_random_picture(
        self, test_client: AsyncClient, add_picture: AsyncGenerator[DBPicture, None]
    ):
        test_picture = await add_picture()
        params = {"pictureType": f"{PictureType.WATER_BOWL}"}
        pictures_response = await test_client.get("/pictures/", params=params)
        returned_picture = json.loads(pictures_response.headers.get("PictureMetadata"))
        assert returned_picture["id"] == test_picture.id

    @pytest.mark.asyncio
    async def test_get_random_picture_with_limit(
        self,
        test_client: AsyncClient,
        add_picture: AsyncGenerator[DBPicture, None],
    ):
        test_picture = await add_picture(human_water_yes=1)
        test_other_picture = await add_picture()
        params = {"limit": f"{PictureRetrieveLimits.HUMAN_ANNOTATED}"}
        pictures_response = await test_client.get("/pictures/", params=params)
        returned_picture = json.loads(pictures_response.headers.get("PictureMetadata"))
        assert returned_picture["id"] == test_picture.id

        # Just to satisfy ourselves that there are other pictures in the DB, try and get one
        request_try = 0
        while returned_picture["id"] != test_other_picture.id and request_try < 5:
            pictures_response = await test_client.get("/pictures/", params=params)
            returned_picture = json.loads(
                pictures_response.headers.get("PictureMetadata")
            )
            request_try = request_try + 1
        assert returned_picture["id"] == test_other_picture.id
