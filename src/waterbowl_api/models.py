from datetime import datetime

from pydantic import BaseModel


class Picture(BaseModel):
    id: int
    picture_location: str
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
