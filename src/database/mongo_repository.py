from functools import wraps
from typing import Callable, Type, Iterable, TypeVar, Any, Mapping

from beanie import PydanticObjectId
from fastapi import HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient
from pydantic import ValidationError, BaseModel
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from pymongo.read_concern import ReadConcern

from config.config import get_db, Settings, SETTINGS
from bson import SON


class MongoDataBaseRepository:
    def __init__(self):
        self.db = get_db()

    async def find_one(self, collection_name: str, query: dict,
                       exclude_fields: set = frozenset(),
                       extra_filter: dict | None = None):
        collection = self.db[collection_name]
        projection = {field: 0 for field in exclude_fields}
        if extra_filter:
            projection.update(extra_filter)
        return await collection.find_one(query, projection)

    async def delete_one(self, collection_name: str, query: dict, session=None):
        collection = self.db[collection_name]
        return await collection.delete_one(query, session=session)

    async def bulk_write(self, collection_name: str, operations: list):
        collection = self.db[collection_name]
        return await collection.bulk_write(operations)

    async def insert_one(self, collection_name: str, document: dict, session=None) -> Any:
        """Вставка объекта в бд, возвращается его идентификатор"""
        result = await self.db[collection_name].insert_one(document=document, session=session)
        return result.inserted_id

    async def update_one(self, collection_name: str, query: dict, update: dict):
        """ОБновление одного документа, вне контекста сессий"""
        await self.db[collection_name].update_one(query, update)
        return await self.find_one(collection_name, query)

    async def find_one_and_update(self, collection_name: str, query: dict, update: dict, session=None):
        data = await self.db[collection_name].find_one_and_update(query,
                                                                  update,
                                                                  session=session,
                                                                  return_document=ReturnDocument.AFTER)
        return data

    async def find(self, collection_name: str, query: dict, skip: int = 0, sort: list = None, limit: int = None):
        collection = self.db[collection_name]
        cursor = collection.find(query)

        if skip:
            cursor = cursor.skip(skip)

        if sort:
            cursor = cursor.sort(sort)

        if limit:
            cursor = cursor.limit(limit)

        data = await cursor.to_list(limit)
        return data

    async def create_collection(self, collection_name,
                                json_validation_schema: dict,
                                index_fields_spec: list[tuple[tuple[str, str | int], bool]],
                                level='strict',
                                session=None):
        """Создание коллекции с заданными индексами и валидацией"""
        new_collection = await self.db.create_collection(collection_name,
                                                         validator=json_validation_schema,
                                                         validationLevel=level,
                                                         session=session,
                                                         )

        for index_spec in index_fields_spec:
            await new_collection.create_index(
                index_spec[0],
                unique=index_spec[1],
                session=session)

    async def update_schema(self, collection_name, json_schema: dict, level='strict',
                            session=None):
        await self.db.command({
            'collMod': collection_name,
            'validator': json_schema,
            'validationLevel': level
        }, session=session)

    async def create_composite_index(self, collection_name: str, index_fields: list[str], session=None):
        """
        Создание индекса по переданным полям в коллекции
        Args:
            session: сессия
            collection_name: имя коллекции
            index_fields: список полей
        """

        index_spec = [(index_field, 1) for index_field in sorted(index_fields)]

        await self.db.get_collection(collection_name).create_index(index_spec,
                                                                   unique=True,
                                                                   session=session,
                                                                   )

    async def list_collections(self, session=None, filter: Mapping = None):
        return await self.db.list_collection_names(session, filter)


T = TypeVar('T', bound=BaseModel)


class DataBaseObjectRepository:
    def __init__(self, collection_name: str, model: Type[T]):
        self.collection_name = collection_name
        self._repository = MongoDataBaseRepository()
        self.model = model

    async def find_one(self, query: dict, exclude_fields: set = frozenset()) -> T | None:
        data = await self._repository.find_one(self.collection_name, query, exclude_fields)
        return self.model.model_validate(data) if data else None

    async def find_one_by_id(self, object_id: PydanticObjectId, exclude_fields: set = frozenset()) -> T:
        query = {'_id': object_id}
        register_type_object: T = await self.find_one(query, exclude_fields)
        return register_type_object

    async def delete_one(self, query: dict, session=None) -> bool:
        deletion_result = await self._repository.delete_one(self.collection_name, query, session=session)
        return deletion_result is not None

    async def delete_one_by_id(self, object_id: PydanticObjectId, session=None) -> bool:
        query = {'_id': object_id}
        deletion_result = await self._repository.delete_one(self.collection_name, query, session=session)
        return deletion_result.deleted_count > 0

    async def bulk_write(self, operations: list):
        return await self._repository.bulk_write(self.collection_name, operations)

    async def insert_one(self, document: T, session=None) -> Any:
        data = await self._repository.insert_one(self.collection_name,
                                                 document.model_dump(exclude={'id'}),
                                                 session=session)
        return data

    async def collection_exists(self):
        registered_collections = await self._repository.list_collections()
        return self.collection_name in registered_collections

    async def update_one(self, query: dict, update: dict, session=None) -> T:
        updated_data = await self._repository.update_one(self.collection_name, query, update)
        return self.model.model_validate(updated_data)

    async def find_one_and_update(self, query: dict, update: dict, session=None) -> T:
        updated_data = await self._repository.find_one_and_update(self.collection_name, query, update, session=session)
        return self.model.model_validate(updated_data)

    async def find(self, query: dict = None, skip: int = 0, limit: int = None, sort: list = None) -> Iterable[T]:
        filtered_data = await self._repository.find(self.collection_name, query, skip, sort, limit)
        return (self.model.model_validate(data) for data in filtered_data)
