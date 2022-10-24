import logging

from sqlalchemy import Table, Column, Integer, String, DateTime, Identity, MetaData
from sqlalchemy.exc import UnboundExecutionError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

from enums import POSTGRES_ADDRESS, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_PICTURES_TABLE

# "postgres-svc.postgres.cluster.local"
# "pictures"

logger = logging.getLogger(__name__)

pictures_table_columns = [
    Column("id", Integer, Identity(start=0, cycle=True), primary_key=True),
    Column("picture_location", String),
    Column("picture_timestamp", DateTime),
    Column("human_cat_yes", Integer, default=0),
    Column("human_water_yes", Integer, default=0),
    Column("human_cat_no", Integer, default=0),
    Column("human_water_no", Integer, default=0),
]


class PostgresException(Exception):

    def __init__(self, message):
        super.__init__(message)


class PictureService:

    def __init__(self):
        self._url = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_ADDRESS}"
        self._engine: AsyncEngine = create_async_engine(self._url, echo=True, future=True)
        if not self._check_for_table(POSTGRES_PICTURES_TABLE):
            raise PostgresException("Could not connect to Postgres.")

    def _check_for_table(self, table) -> bool:
        try:
            with self._engine.sync_engine.begin() as connection:
                if not self._engine.dialect.has_table(connection=connection, table_name=table):
                    metadata = MetaData(self._engine)
                    Table(table, metadata, *pictures_table_columns)
                    metadata.create_all()
            return True
        except UnboundExecutionError:
            logger.error(
                f"Failed to connect to postgres instance at {self._url}. "
            )
            return False

