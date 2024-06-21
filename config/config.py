from typing import Optional

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings
import models as models


class Settings(BaseSettings):
    # database configurations
    DATABASE_URL: Optional[str] = None

    # JWT
    secret_key: str = "secret"
    algorithm: str = "HS256"

    class Config:
        env_file = ".env.dev"
        from_attributes = True


client = None
db = None


async def initiate_database():
    global client, db
    client = AsyncIOMotorClient(Settings().DATABASE_URL)
    db = client.get_default_database()
    await init_beanie(database=db, document_models=models.__all__)
