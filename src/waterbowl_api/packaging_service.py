import json
import os
import shutil
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

import aiofiles
from enums import PictureType


class ZipPackager:
    @classmethod
    @asynccontextmanager
    async def generate_dataset_zip(
        cls,
        positive_picture_files: Optional[list[Path]],
        negative_picture_files: Optional[list[Path]],
        picture_metadata: dict[str, Any],
        class_name: PictureType,
        dataset_name: str = "dataset",
    ) -> Path:
        async with aiofiles.tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir_path = Path(tmp_dir)
            if positive_picture_files:
                positive_class_dir = tmp_dir_path.joinpath(f"{class_name}_true")
                os.mkdir(positive_class_dir)
            else:
                positive_picture_files = []
            if negative_picture_files:
                negative_class_dir = tmp_dir_path.joinpath(f"{class_name}_false")
                os.mkdir(negative_class_dir)
            else:
                negative_picture_files = []
            for picture_file in positive_picture_files:
                shutil.copyfile(
                    picture_file, positive_class_dir.joinpath(picture_file.name)
                )
            for picture_file in negative_picture_files:
                shutil.copyfile(
                    picture_file, negative_class_dir.joinpath(picture_file.name)
                )
            async with aiofiles.open(
                tmp_dir_path.joinpath("picture_data.json"), "w+"
            ) as data_file:
                await data_file.write(json.dumps(picture_metadata))
            archive = Path(
                shutil.make_archive(
                    base_name=dataset_name, format="zip", root_dir=tmp_dir_path
                )
            )
            yield archive
            archive.unlink(missing_ok=True)
