import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
POSTGRES_ADDRESS = os.environ.get("POSTGRES_ADDRESS", "localhost:5432")
POSTGRES_DATABASE = os.environ.get("POSTGRES_DATABASE", "postgres")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
RAW_PICTURES_DIR = Path(
    os.environ.get("RAW_PICTURES_DIR", ROOT_DIR.joinpath("pictures", "raw"))
)
PICTURES_DIR = Path(os.environ.get("PICTURES_DIR", "pictures"))
PICTURES_TABLE = os.environ.get("PICTURES_TABLE", "test_pictures")
PICTURES_MODELING_DATA = os.environ.get(
    "PICTURES_MODELING_DATA", "test_pictures_modeling_data"
)
