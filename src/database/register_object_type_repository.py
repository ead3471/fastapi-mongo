import asyncio
from functools import lru_cache
from types import UnionType
from async_lru import alru_cache
from typing import List, Union, Any, Iterable

from beanie import PydanticObjectId
from pydantic import BaseModel
from cachetools import cached, TTLCache

from database.mongo_repository import MongoDataBaseRepository, DataBaseObjectRepository
from models.register_object_type import RegisterObjectTypeModel

register_object_collection = RegisterObjectTypeModel


# TODO: Переписать на другую реализацию кэша
@alru_cache(maxsize=1024)
async def get_object_default_notify_fields(slug: str):
    type_object: RegisterObjectTypeModel = await MongoRegisterTypeRepository().find_one({"slug": slug})
    return type_object.notify_fields


@alru_cache(maxsize=1024)
async def get_object_unique_fields(slug: str):
    type_object = await MongoRegisterTypeRepository().find_one({"slug": slug})
    return type_object.unique_fields


class MongoRegisterTypeRepository(DataBaseObjectRepository):
    def __init__(self):
        super().__init__('register_type', model=RegisterObjectTypeModel)

    def __create_index_specification_from_json_schema(self, json_schema: dict, unique_fields: Iterable[str]) -> list[
        tuple[str, int | str]]:
        """
        Создает спецификацию для создания индексов в  MongoDB исходя из переданной json схемы
        Args:
            json_schema: JsonSchema
        Returns:
            лист вида [('int_field_name', 1), (string_field_name, 'text')]
        """

        index_fields_spec = [
            (field, "text" if "str" in str(json_schema["$jsonSchema"]['properties'][field]) else 1)
            for field
            in
            unique_fields]
        # Текстовые поля в индексе должны быть смежными в спецификации индекса, поэтому применена сортировка
        return sorted(index_fields_spec, key=lambda x: x[1] != 1)

    async def insert_one(self, document: RegisterObjectTypeModel, session=None):
        """
        Вставка одной записи типа.
        В транзакции одновременно с созданием записи создается коллекция для данных реестра
        с индексами и схемой валидации
        """
        async with (await self._repository.db.client.start_session() as in_session):
            async with in_session.start_transaction():
                result = await super().insert_one(document,
                                                  session=in_session)
                register_json_schema = document.fields_json_schema()
                index_spec = [(self.__create_index_specification_from_json_schema(register_json_schema,
                                                                                  document.unique_fields), True),
                              ]
                history_index = ((('_id', 1), ('history.history_id', 1)), True)
                index_spec.append(history_index)

                await self._repository.create_collection(
                    collection_name=document.slug,
                    json_validation_schema=register_json_schema,
                    index_fields_spec=index_spec,
                    level='strict',
                    session=in_session)
        created_object = await self.find_one({"_id": result})
        return created_object

    async def delete_one(self, query, session=None) -> bool:
        """
        Удаление объекта из БД. Также удаляется связанная коллекция даных объектов реестра
        """
        async with (await self._repository.db.client.start_session() as in_session):
            async with in_session.start_transaction():
                object_type_to_delete: RegisterObjectTypeModel = await self.find_one(query)
                if not object_type_to_delete:
                    return False
                register_object_collection_name = object_type_to_delete.slug
                deleted = await super().delete_one(query, session=in_session)

                # невозможно сбросить коллекцию внутри транзакции,
                # но в случае ошибки при сбросе коллекции сделанные выше изменения откатсятся:
                await self._repository.db[register_object_collection_name].drop()
                return True

    async def delete_one_by_id(self, object_id: PydanticObjectId, session=None) -> bool:
        """Удаление объекта и связанной с ним коллекции реестра"""
        deleted = await self.delete_one({'_id': object_id})
        return deleted

    def __validate_data(self, existing_object: RegisterObjectTypeModel, update: dict[str, Any]):
        """Производит валидацию объекта"""
        updated_object_data = existing_object.model_dump(exclude={'id'}, )
        updated_object_data.update(update)
        updated_object: RegisterObjectTypeModel = self.model(**updated_object_data)

    async def update_one(self, object_id: PydanticObjectId, update: dict, session=None) -> RegisterObjectTypeModel:
        async with (await self._repository.db.client.start_session() as in_session):
            async with in_session.start_transaction():
                query = {"_id": object_id}
                existing_object = await self.find_one_by_id(object_id)
                self.__validate_data(existing_object, update)
                update_spec = {"$set": update}

                updated_object: RegisterObjectTypeModel = await super().find_one_and_update(query, update_spec,
                                                                                            in_session)

                if 'fields' in update.keys():
                    # невозможно обновить схему коллекции внутри транзакции,
                    # но в случае ошибки при сбросе коллекции сделанные выше изменения откатсятся:
                    await self._repository.update_schema(updated_object.slug,
                                                         updated_object.fields_json_schema())

                return updated_object
