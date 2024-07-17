from typing import Optional, AsyncGenerator

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic_settings import BaseSettings
import models


class Settings(BaseSettings):
    # database configurations
    DATABASE_URL: Optional[str] = None
    DATABASE_NAME: Optional[str] = None

    # JWT
    secret_key: str = "secret"
    algorithm: str = "HS256"

    class Config:
        env_file = ".env"
        from_attributes = True


SETTINGS = Settings()


def get_db() -> AsyncIOMotorDatabase:
    mongo_client = AsyncIOMotorClient(SETTINGS.DATABASE_URL)
    mongo_db = mongo_client.get_database(SETTINGS.DATABASE_NAME)
    return mongo_db


async def a_get_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    mongo_client = AsyncIOMotorClient(SETTINGS.DATABASE_URL)
    mongo_db = mongo_client[SETTINGS.DATABASE_NAME]
    try:
        yield mongo_db
    finally:
        mongo_client.close()
