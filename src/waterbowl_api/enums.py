import os
from enum import StrEnum
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
POSTGRES_ADDRESS = os.environ.get("POSTGRES_ADDRESS", "localhost:5432")
POSTGRES_DATABASE = os.environ.get("POSTGRES_DATABASE", "postgres")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
PICTURES_DIR = Path(os.environ.get("PICTURES_DIR", "pictures"))
PICTURES_TABLE = os.environ.get("PICTURES_TABLE", "test_pictures")
PICTURES_MODELING_DATA = os.environ.get(
    "PICTURES_MODELING_DATA", "test_pictures_modeling_data"
)
FOOD_BOWL_CROP_WINDOW = [
    250,
    450,
    700,
    700,
]  # [crop_y, crop_x, crop_height, crop_width]
WATER_BOWL_CROP_WINDOW = [
    600,
    1200,
    700,
    700,
]  # [crop_y, crop_x, crop_height, crop_width]


class PictureType(StrEnum):
    WATER_BOWL = "water_bowl"
    FOOD_BOWL = "food_bowl"


class PictureRetrieveLimits(StrEnum):
    HUMAN_ANNOTATED = "human_annotated"
    NO_ANNOTATION = "no_annotation"

    def __str__(self) -> str:
        return str(self.value)
