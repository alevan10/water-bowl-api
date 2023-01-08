import os
import shutil
from pathlib import Path
from unittest import mock

import pytest


@pytest.fixture
def project_root() -> Path:
    yield Path(__file__).parent.parent


@pytest.fixture
def test_dir(project_root) -> Path:
    yield project_root.joinpath("tests")


@pytest.fixture
def test_data_dir(test_dir) -> Path:
    yield test_dir.joinpath("test_data")


@pytest.fixture
def test_raw_picture_file(test_data_dir) -> Path:
    yield test_data_dir.joinpath("waterbowl-test.jpg")


@pytest.fixture
def test_water_bowl_picture_file(test_data_dir) -> Path:
    yield test_data_dir.joinpath("water-bowl.jpg")


@pytest.fixture
def test_food_bowl_picture_file(test_data_dir) -> Path:
    yield test_data_dir.joinpath("food-bowl.jpg")


@pytest.fixture
def test_picture_storage(test_data_dir) -> Path:
    picture_storage = test_data_dir.joinpath("test-pictures")
    if not picture_storage.exists():
        picture_storage.mkdir()
    yield picture_storage
    shutil.rmtree(picture_storage)


@pytest.fixture
def mock_picture_locations(test_picture_storage):
    with mock.patch.dict(os.environ, {"PICTURES_DIR": str(test_picture_storage)}):
        yield
