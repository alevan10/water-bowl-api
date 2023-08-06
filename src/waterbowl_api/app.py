import os

from blueprint import waterbowl_router
from enums import PICTURES_DIR
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

default_origins = [
    "http://levan.home",
    "https://levan.home",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:8081"
]


def setup_local_files() -> None:
    if not PICTURES_DIR.exists():
        PICTURES_DIR.mkdir(parents=True)


def create_app() -> FastAPI:
    setup_local_files()
    picture_app = FastAPI()
    picture_app.include_router(waterbowl_router)
    default_origins.extend(os.environ.get("ALLOWED_ORIGINS", []))
    picture_app.add_middleware(
        CORSMiddleware,
        allow_origins=default_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["PictureMetadata"]
    )
    return picture_app


app = create_app()
