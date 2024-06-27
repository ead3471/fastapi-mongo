import dataclasses

from config.config import get_db
from database.mongo_repository import MongoDataBaseRepository, DataBaseObjectRepository
from models.register_object import RegisterObject


class MongoRegisterRepository(DataBaseObjectRepository):
    def __init__(self, collection_name: str, ):
        super().__init__(collection_name, model=RegisterObject)
