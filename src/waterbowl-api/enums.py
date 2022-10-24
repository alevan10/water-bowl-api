import os

POSTGRES_ADDRESS = os.environ.get("POSTGRES_ADDRESS", "localhost:5432/postgres")
POSTGRES_PICTURES_TABLE = os.environ.get("POSTGRES_PICTURES_TABLE", "test-pictures")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
