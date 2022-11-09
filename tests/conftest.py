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
