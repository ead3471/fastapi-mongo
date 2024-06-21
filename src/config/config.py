from typing import Optional

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic_settings import BaseSettings
import models


class Settings(BaseSettings):
    # database configurations
    DATABASE_URL: Optional[str] = None

    # JWT
    secret_key: str = "secret"
    algorithm: str = "HS256"

    class Config:
        env_file = ".env.dev"
        from_attributes = True


def get_db() -> AsyncIOMotorDatabase:
    mongo_client = AsyncIOMotorClient(Settings().DATABASE_URL)
    mondo_db = mongo_client.get_default_database()
    return mondo_db


async def initiate_database():
    await init_beanie(database=get_db(), document_models=models.__all__)
