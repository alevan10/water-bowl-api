from datetime import datetime

from pydantic import BaseModel


class PictureMetadata(BaseModel):
    id: int
    picture_id: int
    water_in_bowl: bool
    cat_at_bowl: bool
    human_cat_yes: int
    human_water_yes: int
    human_cat_no: int
    human_water_no: int

    class Config:
        orm_mode = True


class Picture(BaseModel):
    id: int
    raw_picture_location: str
    pictures_location: str
    picture_timestamp: datetime
    picture_metadata: PictureMetadata

    class Config:
        orm_mode = True
