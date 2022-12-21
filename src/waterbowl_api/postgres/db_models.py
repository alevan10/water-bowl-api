from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Identity,
    Boolean,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from enums import PICTURES_TABLE, PICTURES_MODELING_DATA
from postgres.database import Base


class PictureMetadata(Base):
    __tablename__ = PICTURES_MODELING_DATA
    __table_args__ = {"keep_existing": True}
    __mapper_args__ = {"eager_defaults": True}

    id = Column(Integer, Identity(start=1, cycle=True), primary_key=True, index=True)
    water_in_bowl = Column(Boolean, default=False)
    cat_at_bowl = Column(Boolean, default=False)
    human_cat_yes = Column(Integer, default=0)
    human_water_yes = Column(Integer, default=0)
    human_cat_no = Column(Integer, default=0)
    human_water_no = Column(Integer, default=0)


class Picture(Base):
    __tablename__ = PICTURES_TABLE
    __table_args__ = {"keep_existing": True}
    __mapper_args__ = {"eager_defaults": True}

    id = Column(Integer, Identity(start=1, cycle=True), primary_key=True, index=True)
    metadata_id = Column(Integer, ForeignKey(f"{PICTURES_MODELING_DATA}.id"))
    raw_picture_location = Column(String)
    pictures_location = Column(String)
    picture_timestamp = Column(DateTime)

    picture_metadata = relationship("PictureMetadata", foreign_keys=[metadata_id])
