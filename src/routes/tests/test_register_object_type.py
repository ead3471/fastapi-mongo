"""Интеграционные тесты регистрации типов данных в реестре"""
import pytest
from deepdiff import DeepDiff
from http import HTTPStatus

from app import app
from fastapi.testclient import TestClient

from database.register_object_repository import MongoRegisterRepository
from database.register_object_type_repository import MongoRegisterTypeRepository
from models import RegisterObjectTypeModel


@pytest.mark.asyncio
async def test_create_new_type(test_client: TestClient, register_type_all_fields: dict):
    create_url = app.url_path_for("create_register_object_type")
    response = test_client.post(create_url, json=register_type_all_fields)
    assert response.status_code == HTTPStatus.CREATED

    types_repository = MongoRegisterTypeRepository()

    # 1. Проверка того, что создалась коллекция для зарегистрированных типов
    assert await types_repository.collection_exists()
    # 2. Проверка наличия записи и ее соответствия запросу
    registered_types_records = iter(await types_repository.find())
    registered_type: RegisterObjectTypeModel = next(registered_types_records)
    assert DeepDiff(registered_type.model_dump(exclude='id'), register_type_all_fields,
                    ignore_order=True) == {}
    # Проверка соответствия ответа исходным данным
    assert DeepDiff(response.json(), registered_type.model_dump(), ignore_order=True) == {}
    # 3.Проверка того, что создалась всего одна запись
    with pytest.raises(StopIteration):
        next(registered_types_records)

    register_object_repository = MongoRegisterRepository(registered_type.slug)
    # 4.Проверка того, что создалась коллекция для сущности
    assert register_object_repository.collection_exists()
    # 5. Проверка того, что она пустая
    assert len(list(await register_object_repository.find())) == 0


@pytest.mark.asyncio
async def test_create_same_new_type_twice(test_client: TestClient, register_type_all_fields: dict):
    """Проверка ошибки при содании одного и того же типа данных"""
    create_url = app.url_path_for("create_register_object_type")
    response = test_client.post(create_url, json=register_type_all_fields)
    assert response.status_code == HTTPStatus.CREATED

    # Начальная проверка того, что есть коллекции под типы и данные и в коллекции типов есть одна запись
    types_repository = MongoRegisterTypeRepository()
    assert len(list(await types_repository.find())) == 1
    register_object_repository = MongoRegisterRepository(register_type_all_fields["slug"])
    assert register_object_repository.collection_exists()

    response = test_client.post(create_url, json=register_type_all_fields)
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_create_new_type_with_bad_schema_value(test_client: TestClient, register_type_all_fields: dict):
    """Проверка ошибки при содании типа данных из не валидных данных"""
    create_url = app.url_path_for("create_register_object_type")
    register_type_all_fields['slug'] = 'bad collection name'
    response = test_client.post(create_url, json=register_type_all_fields)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_type(test_client: TestClient, register_type_all_fields):
    """Проверка обработки запроса на получение существующего объекта"""
    types_repository = MongoRegisterTypeRepository()
    created: RegisterObjectTypeModel = await types_repository.insert_one(
        RegisterObjectTypeModel(**register_type_all_fields))
    registered_types_records = list(await types_repository.find())
    assert len(registered_types_records) == 1

    get_url = app.url_path_for("get_register_object_type", object_id=created.id)
    response = test_client.get(get_url)

    assert response.status_code == HTTPStatus.OK
    assert DeepDiff(created.model_dump(), response.json(),
                    ignore_order=True) == {}


@pytest.mark.asyncio
async def test_get_type_list(test_client: TestClient, register_type_all_fields):
    """Проверка обработки запроса на получение списка существующих объектов"""
    types_repository = MongoRegisterTypeRepository()
    created_objects = []
    base_object = RegisterObjectTypeModel(**register_type_all_fields)
    for index in range(4):
        type_object = RegisterObjectTypeModel(**base_object.model_dump(exclude={'slug', 'name'}),
                                              slug=f'test_slug_{index}',
                                              name=f"test_name_{index}")
        created: RegisterObjectTypeModel = await types_repository.insert_one(type_object)
        created_objects.append(created.model_dump())
    registered_types_records = list(await types_repository.find())
    assert len(registered_types_records) == 4

    get_url = app.url_path_for("get_register_object_type_list")
    response = test_client.get(get_url)

    assert response.status_code == HTTPStatus.OK
    assert DeepDiff(created_objects, response.json(),
                    ignore_order=True) == {}


@pytest.mark.asyncio
async def test_get_non_existing_type(test_client: TestClient, register_type_all_fields):
    """Проверка обработки запроса на получение не существующего объекта"""
    types_repository = MongoRegisterTypeRepository()
    created: RegisterObjectTypeModel = await types_repository.insert_one(
        RegisterObjectTypeModel(**register_type_all_fields))
    registered_types_records = list(await types_repository.find())
    assert len(registered_types_records) == 1

    get_url = app.url_path_for("get_register_object_type", object_id='667a803fa2dd9bced33dda55')
    response = test_client.get(get_url)
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_delete_type(test_client: TestClient, register_type_all_fields):
    """Проверка обработки запроса на удаление существующего объекта"""
    existing_type = RegisterObjectTypeModel(**register_type_all_fields)

    types_repository = MongoRegisterTypeRepository()
    created: RegisterObjectTypeModel = await types_repository.insert_one(existing_type)
    registered_types_records = list(await types_repository.find())
    assert len(registered_types_records) == 1

    delete_url = app.url_path_for("delete_register_object_type", object_id=created.id)
    response = test_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert len(list(await types_repository.find())) == 0

    register_object_repository = MongoRegisterRepository(created.slug)
    assert not (await register_object_repository.collection_exists())


@pytest.mark.asyncio
async def test_delete_non_existing_type(test_client: TestClient, register_type_all_fields):
    """Проверка обработки запроса на удаление не существующего объекта"""
    existing_type = RegisterObjectTypeModel(**register_type_all_fields)

    types_repository = MongoRegisterTypeRepository()
    created: RegisterObjectTypeModel = await types_repository.insert_one(existing_type)
    registered_types_records = list(await types_repository.find())
    assert len(registered_types_records) == 1

    delete_url = app.url_path_for("delete_register_object_type", object_id='667a803fa2dd9bced33dda55')
    response = test_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert len(list(await types_repository.find())) == 1

    register_object_repository = MongoRegisterRepository(created.slug)
    assert await register_object_repository.collection_exists()


@pytest.mark.asyncio
async def test_update_object(test_client: TestClient, register_type_all_fields):
    """Проверка обработки запроса на обновления существующего объекта"""
    existing_type = RegisterObjectTypeModel(**register_type_all_fields)

    types_repository = MongoRegisterTypeRepository()
    created: RegisterObjectTypeModel = await types_repository.insert_one(existing_type)
    registered_types_records = list(await types_repository.find())
    assert len(registered_types_records) == 1

    update_url = app.url_path_for("update_register_object_type", object_id=created.id)
    response = test_client.patch(update_url, json={"description": "new description"})
    assert response.status_code == HTTPStatus.OK
    updated_object_in_database = await types_repository.find_one_by_id(created.id)

    assert updated_object_in_database.description == "new description"


# TODO: Move to unit tests
@pytest.mark.asyncio
async def test_update_object_with_bad_notify_fields(test_client: TestClient, register_type_all_fields):
    """Проверка обработки запроса обновления существующего объекта  c установкой нотификации по несуществующим полям"""
    existing_type = RegisterObjectTypeModel(**register_type_all_fields)

    types_repository = MongoRegisterTypeRepository()
    created: RegisterObjectTypeModel = await types_repository.insert_one(existing_type)
    registered_types_records = list(await types_repository.find())
    assert len(registered_types_records) == 1

    update_url = app.url_path_for("update_register_object_type", object_id=created.id)
    response = test_client.patch(update_url, json={"notify_fields": ["non_existing_field"]})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


# TODO: Move to unit tests
@pytest.mark.asyncio
async def test_update_object_with_bad_new_fields_list(test_client: TestClient, register_type_all_fields):
    """Проверка обработки запроса обновления существующего объекта  c обновлением списка полей,
    исключающим существующие уникальные поля
    Исходный объект содержит уникальные поля: int_field, string_field
    Предпринимается попытка убрать все поля и оставить только bool_field"""
    existing_type = RegisterObjectTypeModel(**register_type_all_fields)

    types_repository = MongoRegisterTypeRepository()
    created: RegisterObjectTypeModel = await types_repository.insert_one(existing_type)
    registered_types_records = list(await types_repository.find())
    assert len(registered_types_records) == 1

    update_url = app.url_path_for("update_register_object_type", object_id=created.id)
    response = test_client.patch(update_url, json={"fields": [{
        "name": "bool_field",
        "optional": False,
        "type": "bool"
    }, ]})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
