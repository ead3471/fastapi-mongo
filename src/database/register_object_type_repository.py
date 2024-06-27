from functools import lru_cache
from types import UnionType
from typing import List, Union, Any

from beanie import PydanticObjectId
from pydantic import BaseModel

from database.mongo_repository import MongoDataBaseRepository, DataBaseObjectRepository
from models.register_object_type import RegisterObjectType

register_object_collection = RegisterObjectType


# TODO: Переписать на другую реализацию кэша
@lru_cache(128)
async def get_object_default_notify_fields(slug: str):
    type_object = await register_object_collection.find_one({"slug": slug})
    return type_object.unique_fields


class MongoRegisterTypeRepository(DataBaseObjectRepository):
    def __init__(self):
        super().__init__('register_type', model=RegisterObjectType)

    def __create_index_specification_from_json_schema(self, json_schema: dict) -> list[tuple[str, int | str]]:
        """
        Создает спецификацию для создания индексов в  MongoDB исходя из переданной json схемы
        Args:
            json_schema: JsonSchema
        Returns:
            лист вида [('int_field_name', 1), (string_field_name, 'text')]
        """
        index_fields_spec = [
            (field, "text" if "str" in str(field_spec) else 1)
            for field, field_spec
            in
            json_schema["$jsonSchema"]['properties'].items()]
        return index_fields_spec

    async def insert_one(self, document: RegisterObjectType, session=None):
        """
        Вставка одной записи типа.
        В транзакции одновременно с созданием записи создается коллекция для данных реестра
        с индексами и схемой валидации
        """
        async with (await self.db.client.start_session() as in_session):
            async with in_session.start_transaction():
                result = await super().insert_one(document,
                                                  session=in_session)
                register_json_schema = document.fields_json_schema()
                index_spec = self.__create_index_specification_from_json_schema(register_json_schema)
                await self.db.create_register_collection(
                    collection_name=document.slug,
                    json_validation_schema=register_json_schema,
                    index_fields_spec=index_spec,
                    level='strict',
                    session=session)
        created_object = await self.find_one({"_id": result})
        return created_object

    async def delete_one(self, query, session=None) -> bool:
        """
        Удаление объекта из БД. Также удаляется связанная коллекция даных объектов реестра
        """
        async with (await self.db.client.start_session() as in_session):
            async with in_session.start_transaction():
                object_type_to_delete: RegisterObjectType = await self.find_one(query)
                register_object_collection_name = object_type_to_delete.slug
                deleted = await super().delete_one(query, session=in_session)

                # TODO: невозможно сбросить коллекцию внутри транзакции:
                await self.db.db[register_object_collection_name].drop()
                return deleted

    async def delete_one_by_id(self, object_id: PydanticObjectId, session=None) -> bool:
        """Удаление объекта и связанной с ним коллекции реестра"""
        deleted = await self.delete_one({'_id': object_id})
        return deleted

    async def find_one_by_id(self, object_id: PydanticObjectId):
        register_type_object: RegisterObjectType = await self.find_one({'_id': object_id})
        return register_type_object

    def __validate_data(self, existing_object: RegisterObjectType, update: dict[str, Any]):
        """Производит валидацию объекта"""
        updated_object_data = existing_object.model_dump(exclude={'id'}, )
        updated_object_data.update(update)
        updated_object: RegisterObjectType = self.model(**updated_object_data)

    async def update_one(self, object_id: PydanticObjectId, update: dict, session=None) -> RegisterObjectType:
        async with (await self.db.client.start_session() as in_session):
            async with in_session.start_transaction():
                query = {"_id": object_id}
                existing_object = await self.find_one_by_id(object_id)
                self.__validate_data(existing_object, update)
                update_spec = {"$set": update}

                updated_object: RegisterObjectType = await super().find_one_and_update(query, update_spec, in_session)

                if 'fields' in update.keys():
                    await self.db.update_schema(updated_object.slug,
                                                updated_object.fields_json_schema())

                return updated_object


async def retrieve_objects_types() -> List[RegisterObjectType]:
    objects = await register_object_collection.all().to_list()
    ss = await register_object_collection.get_motor_collection().options()
    register_object_collection.get_motor_collection().with_options()
    return objects


async def add_object_type(new_object: RegisterObjectType) -> RegisterObjectType:
    object_type = await new_object.create()
    await object_type.get_motor_collection().create_index({field: 1 for field in object_type.unique_fields},
                                                          unique=True)
    return object_type


async def retrieve_object_type(id: PydanticObjectId) -> RegisterObjectType:
    object = await register_object_collection.get(id)
    if object:
        return object


async def delete_object_type(id: PydanticObjectId) -> bool:
    object = await register_object_collection.get(id)
    if object:
        await object.delete()
        return True


async def update_object_data(
        id: PydanticObjectId, data: dict
) -> Union[bool, RegisterObjectType]:
    des_body = {k: v for k, v in data.items() if v is not None}
    update_query = {"$set": {field: value for field, value in des_body.items()}}
    object = await register_object_collection.get(id)
    if object:
        await object.update(update_query)
        return object
    return False
