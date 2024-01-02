import csv
import json
import shutil
from pathlib import Path

import aiofiles.tempfile
import pytest
from enums import PictureType
from packaging_service import ZipPackager


@pytest.mark.asyncio
@pytest.mark.parametrize("image_class", [True, False])
async def test_generate_single_class_archive(
    image_class: bool, test_water_bowl_picture_file
):
    positive_pictures = []
    negative_pictures = []
    if image_class is True:
        positive_pictures = [test_water_bowl_picture_file]
    if image_class is False:
        negative_pictures = [test_water_bowl_picture_file]
    picture_metadata = [{"filename": test_water_bowl_picture_file.name, "some": "metadata"}]
    async with ZipPackager.generate_dataset_zip(
        positive_picture_files=positive_pictures,
        negative_picture_files=negative_pictures,
        picture_metadata=picture_metadata,
        class_name=PictureType.WATER_BOWL,
    ) as dataset:
        async with aiofiles.tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            shutil.unpack_archive(str(dataset), tmp_path, "zip")
            files = tmp_path.glob("*")
            assert len(list(files)) == 2
            for file in files:
                if file.is_dir():
                    assert (
                        file.name == f"{PictureType.WATER_BOWL}_" + "true"
                        if image_class is True
                        else "false"
                    )
                    class_files = list(file.glob("*"))
                    assert len(class_files) == 1
                    assert class_files[0].name == test_water_bowl_picture_file.name
                else:
                    assert test_water_bowl_picture_file.name in file.read_text()


@pytest.mark.asyncio
async def test_generate_multiple_class_archive(test_water_bowl_picture_file: Path):
    async with aiofiles.tempfile.TemporaryDirectory() as copy_tmp_dir:
        copy_tmp_path = Path(copy_tmp_dir)
        positive_picture = shutil.copy(
            test_water_bowl_picture_file,
            copy_tmp_path.joinpath(f"true_{test_water_bowl_picture_file.name}"),
        )
        negative_picture = shutil.copy(
            test_water_bowl_picture_file,
            copy_tmp_path.joinpath(f"false_{test_water_bowl_picture_file.name}"),
        )
        picture_metadata = [
            {"filename": positive_picture.name, "some": "metadata"},
            {"filename": negative_picture.name, "some": "metadata"}
        ]
        async with ZipPackager.generate_dataset_zip(
            positive_picture_files=[positive_picture],
            negative_picture_files=[negative_picture],
            picture_metadata=picture_metadata,
            class_name=PictureType.WATER_BOWL,
        ) as dataset:
            async with aiofiles.tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
                shutil.unpack_archive(str(dataset), tmp_path, "zip")
                files = list(tmp_path.glob("*"))
                assert len(files) == 3
                csv_file = Path(
                    next(file for file in files if file.name.endswith("csv"))
                )
                with open(csv_file, 'r') as file:
                    csv_reader = csv.DictReader(file)
                    csv_data = [row for row in csv_reader]
                assert list(csv_data[0].keys()) == ["filename", "some"]
                positive_dir = Path(
                    next(file for file in files if file.name.endswith("true"))
                )
                negative_dir = Path(
                    next(file for file in files if file.name.endswith("false"))
                )

                class_files = list(positive_dir.glob("*"))
                assert len(class_files) == 1
                picture_file = class_files[0]
                assert picture_file.name == positive_picture.name
                assert csv_data[0] == {"filename": positive_picture.name, "some": "metadata"}

                class_files = list(negative_dir.glob("*"))
                assert len(class_files) == 1
                picture_file = class_files[0]
                assert picture_file.name == negative_picture.name
                assert csv_data[1] == {"filename": negative_picture.name, "some": "metadata"}
