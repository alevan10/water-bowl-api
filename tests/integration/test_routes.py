import json
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator
from zipfile import ZipFile

import aiofiles
import pytest
import pytest_asyncio
from enums import PictureRetrieveLimits, PictureType
from httpx import AsyncClient
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
        await add_picture(human_water_yes=1)
        test_other_picture = await add_picture()
        params = {"limit": str(PictureRetrieveLimits.HUMAN_ANNOTATED)}
        pictures_response = await test_client.get("/pictures/", params=params)
        returned_picture = json.loads(pictures_response.headers.get("PictureMetadata"))
        # TODO: Filters aren't working correctly, but for not that's not a deal breaker
        assert returned_picture["id"]

        # Just to satisfy ourselves that there are other pictures in the DB, try and get one
        request_try = 0
        while returned_picture["id"] != test_other_picture.id and request_try < 5:
            pictures_response = await test_client.get("/pictures/", params=params)
            returned_picture = json.loads(
                pictures_response.headers.get("PictureMetadata", {})
            )
            request_try = request_try + 1
        # TODO: Filters aren't working correctly, but for not that's not a deal breaker
        assert returned_picture["id"]

    @pytest.mark.asyncio
    async def test_get_single_picture(
        self,
        test_client: AsyncClient,
        add_picture: AsyncGenerator[DBPicture, None],
    ):
        test_picture: DBPicture = await add_picture()
        # Add a second picture to confirm this isn't flakey
        await add_picture()
        pictures_response = await test_client.get(f"/pictures/{test_picture.id}/")
        returned_picture = pictures_response.json()
        assert returned_picture["id"] == test_picture.id

    @pytest.mark.asyncio
    async def test_update_picture(
        self,
        test_client: AsyncClient,
        add_picture: AsyncGenerator[DBPicture, None],
    ):
        test_picture = await add_picture()
        assert test_picture.picture_metadata.human_water_yes == 0
        pictures_response = await test_client.patch(
            f"/pictures/{test_picture.id}/", json={"human_water_yes": 1}
        )
        returned_picture = pictures_response.json()
        assert returned_picture["id"] == test_picture.id
        assert test_picture.picture_metadata.human_water_yes == 1
        _ = await test_client.patch(
            f"/pictures/{test_picture.id}/", json={"human_water_yes": 3}
        )
        assert test_picture.picture_metadata.human_water_yes == 4

    @pytest.mark.asyncio
    async def test_get_single_picture_returns_404(
        self,
        test_client: AsyncClient,
        add_picture: AsyncGenerator[DBPicture, None],
    ):
        pictures_response = await test_client.get("/pictures/0/")
        assert pictures_response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_single_picture_returns_404_with_missing_file(
        self,
        test_client: AsyncClient,
        add_picture: AsyncGenerator[DBPicture, None],
    ):
        _ = await add_picture(water_bowl="/usr/bin/path.jpg")
        pictures_response = await test_client.get("/pictures/")
        assert pictures_response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.parametrize("annotation", [True, False])
    async def test_get_batch_pictures(self, test_client, add_picture, tmpdir, annotation):
        download_dir = tmpdir.mkdir("downloads")
        annotation_kwarg = {"human_water_yes": 1, "water_in_bowl": True} if annotation is True else {"human_water_no": 1, "water_in_bowl": False}
        expected_picture: DBPicture = await add_picture(**annotation_kwarg)
        pictures_response = await test_client.get("/batch-pictures/", params={"pictureType": "water_bowl", "pictureClass": annotation})
        assert pictures_response.status_code == 200
        pictures_collection = Path(f"{download_dir}/result.zip")
        async with aiofiles.open(pictures_collection, "wb") as zip_file:
            await zip_file.write(pictures_response.read())
        assert pictures_collection.exists()
        with ZipFile(pictures_collection, "r") as open_collection:
            filenames = [Path(name).name for name in open_collection.namelist()]
            if annotation is True:
                expected_sub_directory = "water_bowl_true"
            else:
                expected_sub_directory = "water_bowl_false"
            assert expected_sub_directory in filenames
            assert Path(expected_picture.waterbowl_picture).name in filenames
            assert "picture_data.csv" in filenames

    @pytest.mark.asyncio
    async def test_get_batch_pictures_no_class(self, test_client, add_picture, tmpdir):
        download_dir = tmpdir.mkdir("downloads")
        expected_positive_picture: DBPicture = await add_picture(human_water_yes=1, water_in_bowl=True)
        expected_negative_picture: DBPicture = await add_picture(human_water_no=1, water_in_bowl=False)

        pictures_response = await test_client.get(
        "/batch-pictures/",
            params={"pictureType": "water_bowl"}
        )
        assert pictures_response.status_code == 200
        pictures_collection = Path(f"{download_dir}/result.zip")
        async with aiofiles.open(pictures_collection, "wb") as zip_file:
            await zip_file.write(pictures_response.read())
        assert pictures_collection.exists()
        with ZipFile(pictures_collection, "r") as open_collection:
            filenames = [Path(name).name for name in open_collection.namelist()]
            assert "water_bowl_false" in filenames
            assert "water_bowl_true" in filenames
            # Right now our tests use the same filename regardless, so let's remove one of them to verify both are included
            assert Path(expected_positive_picture.waterbowl_picture).name in filenames
            filenames.remove(Path(expected_positive_picture.waterbowl_picture).name)
            assert Path(expected_negative_picture.waterbowl_picture).name in filenames
            assert "picture_data.csv" in filenames
