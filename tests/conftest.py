import os
import shutil
from unittest import mock

import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    yield Path(__file__).parent.parent


@pytest.fixture
def test_dir(project_root):
    yield project_root.joinpath("tests")


@pytest.fixture
def test_data_dir(test_dir):
    yield test_dir.joinpath("test_data")


@pytest.fixture
def test_picture_file(test_data_dir):
    yield test_data_dir.joinpath("waterbowl-test.jpg")


@pytest.fixture
def test_picture_storage(test_data_dir):
    picture_storage = test_data_dir.joinpath("test-pictures")
    if not picture_storage.exists():
        picture_storage.mkdir()
    yield picture_storage


@pytest.fixture
def test_raw_picture_storage(test_picture_storage):
    raw_picture_storage = test_picture_storage.joinpath("test-raw")
    if raw_picture_storage.exists():
        shutil.rmtree(raw_picture_storage)
    raw_picture_storage.mkdir(parents=True)
    yield raw_picture_storage


@pytest.fixture
def mock_picture_locations(test_picture_storage, test_raw_picture_storage):
    with mock.patch.dict(
        os.environ, {"RAW_PICTURES_DIR": str(test_raw_picture_storage)}
    ):
        with mock.patch.dict(os.environ, {"PICTURES_DIR": str(test_picture_storage)}):
            yield
