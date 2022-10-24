import logging
import os
from picture_service import PictureService

from fastapi import APIRouter, Depends

waterbowl_router = APIRouter()

logging.basicConfig(
    level=logging.DEBUG if os.environ.get("DEBUG") == "true" else logging.INFO
)
logger = logging.getLogger(__name__)


@waterbowl_router.get("/health")
async def health_endpoint() -> str:
    return "pong"


@waterbowl_router.post("/pictures")
async def pictures_endpoint():
    service = PictureService()
    return "success"
