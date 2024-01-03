from enums import PICTURES_MODELING_DATA, PICTURES_TABLE
from models import PictureMetadata
from postgres.database import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Identity, Integer, String
from sqlalchemy.orm import relationship


class DBPictureMetadata(Base):
    __tablename__ = PICTURES_MODELING_DATA
    __table_args__ = {"keep_existing": True}
    __mapper_args__ = {"eager_defaults": True}

    id = Column(Integer, Identity(start=1, cycle=True), primary_key=True, index=True)
    water_in_bowl = Column(Boolean, default=False)
    food_in_bowl = Column(Boolean, default=False)
    cat_at_bowl = Column(Boolean, default=False)
    human_cat_yes = Column(Integer, default=0)
    human_water_yes = Column(Integer, default=0)
    human_food_yes = Column(Integer, default=0)
    human_cat_no = Column(Integer, default=0)
    human_water_no = Column(Integer, default=0)
    human_food_no = Column(Integer, default=0)

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, DBPictureMetadata):
            return self.to_dict() == other.to_dict()
        return False

    def to_dict(self):
        return {
            "id": self.id,
            "water_in_bowl": self.water_in_bowl,
            "food_in_bowl": self.food_in_bowl,
            "cat_at_bowl": self.cat_at_bowl,
            "human_cat_yes": self.human_cat_yes,
            "human_water_yes": self.human_water_yes,
            "human_food_yes": self.human_food_yes,
            "human_cat_no": self.human_cat_no,
            "human_water_no": self.human_water_no,
            "human_food_no": self.human_food_no,
        }

    def to_api_return(self, picture_id: int) -> PictureMetadata:
        return PictureMetadata(**self.to_dict(), picture_id=picture_id)


class DBPicture(Base):
    __tablename__ = PICTURES_TABLE
    __table_args__ = {"keep_existing": True}
    __mapper_args__ = {"eager_defaults": True}

    id = Column(Integer, Identity(start=1, cycle=True), primary_key=True, index=True)
    metadata_id = Column(Integer, ForeignKey(f"{PICTURES_MODELING_DATA}.id"))
    waterbowl_picture = Column(String)
    food_picture = Column(String)
    picture_timestamp = Column(DateTime)

    picture_metadata = relationship(
        "DBPictureMetadata", foreign_keys=[metadata_id], lazy="joined"
    )

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, DBPicture):
            return self.to_dict() == other.to_dict()
        return False

    def to_dict(self, flat: bool = False):
        base_dict = {
            "id": self.id,
            "metadata_id": self.metadata_id,
            "waterbowl_picture": self.waterbowl_picture,
            "food_picture": self.food_picture,
            "picture_timestamp": str(self.picture_timestamp),
        }
        if flat:
            base_dict.update(self.picture_metadata.to_dict())
        else:
            base_dict.update({"picture_metadata": self.picture_metadata.to_dict()})
        return base_dict
