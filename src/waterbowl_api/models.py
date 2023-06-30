from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Picture(BaseModel):
    id: int
    waterbowl_picture: str
    food_picture: str
    picture_timestamp: datetime

    class Config:
        orm_mode = True


class PictureMetadata(BaseModel):
    id: int
    picture_id: int
    water_in_bowl: bool
    food_in_bowl: bool
    cat_at_bowl: bool
    human_cat_yes: int
    human_water_yes: int
    human_food_yes: int
    human_cat_no: int
    human_water_no: int
    human_food_no: int

    class Config:
        orm_mode = True


class PictureUpdateRequest(BaseModel):
    human_cat_yes: Optional[int] = 0
    human_water_yes: Optional[int] = 0
    human_food_yes: Optional[int] = 0
    human_cat_no: Optional[int] = 0
    human_water_no: Optional[int] = 0
    human_food_no: Optional[int] = 0
