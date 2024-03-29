from datetime import datetime
from pathlib import Path

import pytest
from enums import PictureRetrieveLimits, PictureType
from models import PictureUpdateRequest
from picture_service import PictureService
from postgres.db_models import DBPicture


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
        test_data_dir,
        test_picture_storage,
    ):
        picture_svc = PictureService(db=postgres)
        test_picture = await picture_svc.create_pictures(
            picture=picture_upload, timestamp=now.timestamp()
        )

        stored_pictures = list(test_picture_storage.glob("*.jpeg"))
        assert len(stored_pictures) == 2
        for expected_picture in [
            Path(test_picture.waterbowl_picture),
            Path(test_picture.food_picture),
        ]:
            assert expected_picture in stored_pictures
        assert now == test_picture.picture_timestamp
        assert test_picture.id == 1

    @pytest.mark.asyncio
    async def test_get_picture(
        self,
        now,
        add_picture,
        postgres,
        picture_upload,
        test_data_dir,
    ):
        test_picture = await add_picture(timestamp=now)

        picture_svc = PictureService(db=postgres)
        returned_picture = await picture_svc.get_picture(picture_id=test_picture.id)

        assert test_picture.id == returned_picture.id
        assert test_picture.metadata_id == returned_picture.metadata_id
        assert test_picture.picture_metadata == returned_picture.picture_metadata

    @pytest.mark.asyncio
    async def test_get_random_picture_no_limit(
        self,
        now,
        add_multiple_pictures,
        postgres,
        picture_upload,
        test_data_dir,
    ):
        await add_multiple_pictures(timestamp=now)

        picture_svc = PictureService(db=postgres)
        returned_picture_1 = await picture_svc.get_random_picture()
        returned_picture_2 = returned_picture_1
        while returned_picture_2 == returned_picture_1:
            returned_picture_2 = await picture_svc.get_random_picture()
        assert returned_picture_1.id != returned_picture_2.id
        assert returned_picture_1.metadata_id != returned_picture_2.metadata_id
        assert (
            returned_picture_1.picture_metadata != returned_picture_2.picture_metadata
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "limit",
        [PictureRetrieveLimits.HUMAN_ANNOTATED, PictureRetrieveLimits.NO_ANNOTATION],
    )
    async def test_get_random_picture_with_limits(
        self,
        now,
        add_picture,
        add_multiple_pictures,
        postgres,
        picture_upload,
        test_data_dir,
        limit,
    ):
        unannotated_picture = await add_picture(timestamp=now, human_water_yes=0)
        annotated_picture = await add_picture(timestamp=now, human_water_yes=1)

        picture_svc = PictureService(db=postgres)
        returned_picture = await picture_svc.get_random_picture(limit=limit)
        if limit == PictureRetrieveLimits.NO_ANNOTATION:
            assert unannotated_picture.id == returned_picture.id
        else:
            assert annotated_picture.id == returned_picture.id

    @pytest.mark.asyncio
    async def test_update_picture(
        self,
        now,
        add_picture,
        postgres,
        picture_upload,
        test_data_dir,
    ):
        test_picture: DBPicture = await add_picture(timestamp=now)
        picture_svc = PictureService(db=postgres)
        test_metadata = await picture_svc.get_metadata(
            metadata_id=test_picture.metadata_id
        )

        # ORM changes object instance values, so let's capture the current state of the metdata
        test_metadata_dict = test_metadata.to_dict()

        update_request = PictureUpdateRequest(human_cat_yes=1, human_water_yes=1)
        updated_metadata = await picture_svc.update_metadata(
            metadata_id=test_metadata.id, updates=update_request
        )

        # Should be the same
        assert test_metadata_dict.get("id") == updated_metadata.id
        assert (
            test_metadata_dict.get("human_food_yes") == updated_metadata.human_food_yes
        )
        assert test_metadata_dict.get("human_cat_no") == updated_metadata.human_cat_no
        assert (
            test_metadata_dict.get("human_water_no") == updated_metadata.human_water_no
        )
        assert test_metadata_dict.get("human_food_no") == updated_metadata.human_food_no
        assert test_metadata_dict.get("food_in_bowl") == updated_metadata.food_in_bowl

        # Should be different
        assert test_metadata_dict.get("human_cat_yes") != updated_metadata.human_cat_yes
        assert updated_metadata.human_cat_yes == 1
        assert (
            test_metadata_dict.get("human_water_yes")
            != updated_metadata.human_water_yes
        )
        assert updated_metadata.human_water_yes == 1
        assert test_metadata_dict.get("water_in_bowl") != updated_metadata.water_in_bowl
        assert updated_metadata.water_in_bowl is True
        assert test_metadata_dict.get("cat_at_bowl") != updated_metadata.cat_at_bowl
        assert updated_metadata.cat_at_bowl is True

    @pytest.mark.asyncio
    async def test_get_picture_none_available(
        self,
        postgres,
    ):
        picture_svc = PictureService(db=postgres)
        returned_picture = await picture_svc.get_picture(picture_id=0)
        assert returned_picture is None

    @pytest.mark.asyncio
    @pytest.mark.parametrize("annotation", [True, False])
    async def test_get_annotated_pictures(self, add_picture, postgres, annotation):
        annotation_kwarg = (
            {"human_water_yes": 1} if annotation is True else {"human_water_no": 1}
        )
        test_picture: DBPicture = await add_picture(
            water_in_bowl=annotation, **annotation_kwarg
        )
        picture_svc = PictureService(db=postgres)
        returned_pictures = await picture_svc.get_annotated_pictures(
            limit=-1, picture_type=PictureType.WATER_BOWL, picture_class=annotation
        )
        assert returned_pictures is not None
        assert len(returned_pictures) == 1
        returned_picture = returned_pictures[0]
        assert returned_picture.id == test_picture.id
        assert returned_picture.picture_metadata.water_in_bowl is annotation
        for key, value in annotation_kwarg.items():
            assert getattr(returned_picture.picture_metadata, key) == value

    @pytest.mark.asyncio
    @pytest.mark.parametrize("annotation", [True, False])
    async def test_get_human_annotation_pictures_mixed_with_computer_annotated_pictures(
        self, add_multiple_pictures, postgres, annotation
    ):
        # Add 10 human annotated pictures:
        annotation_kwarg = (
            {"human_water_yes": 1} if annotation is True else {"human_water_no": 1}
        )
        human_annotated = await add_multiple_pictures(
            water_in_bowl=annotation, num_pictures=10, **annotation_kwarg
        )

        # Add 5 machine annotated pictures
        computer_annotated = await add_multiple_pictures(water_in_bowl=annotation)

        picture_svc = PictureService(db=postgres)
        returned_pictures = await picture_svc.get_annotated_pictures(
            limit=-1, picture_type=PictureType.WATER_BOWL, picture_class=annotation
        )

        assert len(returned_pictures) != len(computer_annotated)
        assert len(returned_pictures) == len(human_annotated)
        returned_pictures.sort(key=lambda picture: picture.id)
        human_annotated.sort(key=lambda picture: picture.id)

        computer_annotated_picture_ids = [picture.id for picture in computer_annotated]

        for expected, human in zip(returned_pictures, human_annotated):
            assert expected == human
            assert human.id not in computer_annotated_picture_ids
