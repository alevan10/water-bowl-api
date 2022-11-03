import os

from sqlalchemy import Table, Column, Integer, String, DateTime, Identity, MetaData, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from enums import PICTURES_TABLE, PICTURES_MODELING_DATA
from postgres.database import Base


class Picture(Base):
    __tablename__ = PICTURES_TABLE

    id = Column(Integer, Identity(start=1, cycle=True), primary_key=True, index=True)
    raw_picture_location = Column(String)
    pictures_location = Column(String)
    picture_timestamp = Column(DateTime)

    picture_metadata = relationship("PictureMetadata", back_populates="picture")


class PictureMetadata(Base):
    __tablename__ = PICTURES_MODELING_DATA

    id = Column(Integer, Identity(start=1, cycle=True), primary_key=True, index=True)
    picture_id = Column(Integer, ForeignKey(f"{PICTURES_TABLE}.id"))
    water_in_bowl = Column(Boolean, default=False)
    cat_at_bowl = Column(Boolean, default=False)
    human_cat_yes = Column(Integer, default=0)
    human_water_yes = Column(Integer, default=0)
    human_cat_no = Column(Integer, default=0)
    human_water_no = Column(Integer, default=0)

    picture = relationship("Picture", back_populates="picture_metadata")



