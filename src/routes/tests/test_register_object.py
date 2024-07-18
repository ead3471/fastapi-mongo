"""Интеграционные тесты регистрации типов данных в реестре"""
import pytest
from deepdiff import DeepDiff
from http import HTTPStatus

from app import app
from fastapi.testclient import TestClient

from database.register_object_repository import MongoRegisterRepository
from database.register_object_type_repository import MongoRegisterTypeRepository
from models import RegisterObjectTypeModel
from models.register_object import RegisterObjectModel


@pytest.mark.asyncio
async def test_create_new_object(test_client: TestClient, register_type_object_all_fields_object,
                                 register_object_all_fields_data: dict):
    """Проверка записи объекта в бд
    Ожидается добавление нового объекта в коллекцию со значениями, специфицированными во входной фикстуре"""
    collection_name = register_type_object_all_fields_object.slug
    create_url = app.url_path_for("create_register_object", slug=collection_name)
    response = test_client.post(create_url, json=register_object_all_fields_data)
    assert response.status_code == HTTPStatus.CREATED

    objects_repository = MongoRegisterRepository(collection_name)
    objects: list[RegisterObjectModel] = list(await objects_repository.find())
    assert len(objects) == 1
    created_object = objects[0]

    # Поля созданного объекта соответствуют запросу
    assert DeepDiff(created_object.model_dump(exclude={'id', 'history', 'notify_fields', 'is_deactivated'}),
                    register_object_all_fields_data,
                    ignore_order=True) == {}

    # notify_fields установились по умолчанию
    assert DeepDiff(register_type_object_all_fields_object.model_dump()["notify_fields"],
                    response.json()["notify_fields"],
                    ignore_order=True) == {}

    # Ответ соответствует данным в бд
    assert DeepDiff(created_object.model_dump(exclude={'history'}), response.json(),
                    ignore_order=True) == {}

    # Создалась одна историческая запись и она соответствует текущему состоянию
    assert len(created_object.model_dump()['history']) == 1
    prepared_history_record = created_object.history[0].model_dump(exclude={'history_id', 'history_datetime'})
    assert DeepDiff(prepared_history_record, response.json(), exclude_paths=["root['id']"],
                    ignore_order=True) == {}


@pytest.mark.asyncio
async def test_create_new_object_with_same_unique_fields(test_client: TestClient,
                                                         register_type_object_all_fields_object,
                                                         register_object_all_fields):
    """Проверка обработки создания объекта с существующими уникальными полями"""
    collection_name = register_type_object_all_fields_object.slug
    create_url = app.url_path_for("create_register_object", slug=collection_name)
    response = test_client.post(create_url, json=register_object_all_fields.model_dump(exclude={"id", "history"}))
    assert response.status_code == HTTPStatus.CONFLICT


@pytest.mark.asyncio
async def test_get_object(test_client: TestClient, register_object_all_fields, register_type_object_all_fields_object):
    """Проверка получения объекта из бд"""
    collection_name = register_type_object_all_fields_object.slug
    get_url = app.url_path_for("get_register_object", slug=collection_name, object_id=register_object_all_fields.id)
    response = test_client.get(get_url)
    assert response.status_code == HTTPStatus.OK

    # Все поля соответствуют исхдному объекту
    assert DeepDiff(register_object_all_fields.model_dump(), response.json(), ignore_order=True,
                    exclude_paths=["root['history']",
                                   "root['notify_fields'"]) == {}

    assert DeepDiff(register_type_object_all_fields_object.model_dump()["notify_fields"],
                    response.json()["notify_fields"], ignore_order=True,
                    ) == {}


# TODO: Добавить паджинацию
@pytest.mark.asyncio
async def test_get_objects(test_client: TestClient, register_object_all_fields, register_type_object_all_fields_object):
    """Проверка получения списка объектов из бд"""

    collection_name = register_type_object_all_fields_object.slug
    repository = MongoRegisterRepository(collection_name)

    base_data = register_object_all_fields.model_dump(exclude={"id", "history", "notify_fields", 'int_field'})
    for index in range(4):
        new_object = RegisterObjectModel(**base_data, int_field=index)
        await repository.insert_one(new_object)

    get_url = app.url_path_for("get_register_objects", slug=collection_name)
    response = test_client.get(get_url)
    assert response.status_code == HTTPStatus.OK

    # Все поля соответствуют исхдному объекту
    assert len(list(await repository.find())) == 5


@pytest.mark.asyncio
async def test_get_non_existing_object(test_client: TestClient, register_object_all_fields,
                                       register_type_object_all_fields_object):
    """Проверка получения не существующего объекта из бд"""
    collection_name = register_type_object_all_fields_object.slug
    get_url = app.url_path_for("get_register_object", slug=collection_name, object_id='667a803fa2dd9bced33dda55')
    response = test_client.get(get_url)
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_delete_object(test_client: TestClient, register_object_all_fields,
                             register_type_object_all_fields_object):
    """Проверка полного удаления объекта из бд"""
    collection_name = register_type_object_all_fields_object.slug
    delete_url = app.url_path_for("delete_register_object",
                                  slug=collection_name,
                                  object_id=register_object_all_fields.id)
    response = test_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NO_CONTENT

    repository = MongoRegisterRepository(collection_name)

    # Проверка того, что объект удалился из базы
    assert await repository.find_one_by_id(register_object_all_fields.id) is None


@pytest.mark.asyncio
async def test_delete_object(test_client: TestClient, register_object_all_fields,
                             register_type_object_all_fields_object):
    """Проверка полного удаления не существующего объекта из бд"""
    collection_name = register_type_object_all_fields_object.slug
    delete_url = app.url_path_for("delete_register_object",
                                  slug=collection_name,
                                  object_id="667a803fa2dd9bced33dda55")
    response = test_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND

    repository = MongoRegisterRepository(collection_name)

    # Проверка того, что объект не удалился из базы
    assert await repository.find_one_by_id(register_object_all_fields.id)


async def test_update_object(test_client: TestClient, register_object_all_fields,
                             register_type_object_all_fields_object):
    """Проверка обновления объекта. Ожидается изменение свойств и новая историческая запись"""
    collection_name = register_type_object_all_fields_object.slug
    update_url = app.url_path_for("update_register_object",
                                  slug=collection_name,
                                  object_id=register_object_all_fields.id)
    response = test_client.patch(update_url, json={"float_field": 42.0})
    assert response.status_code == HTTPStatus.OK

    repository = MongoRegisterRepository(collection_name)

    updated_object: RegisterObjectModel = await repository.find_one_by_id(register_object_all_fields.id)
    # Обновленый объект соответствует новым данным
    assert DeepDiff(updated_object.model_dump(), response.json(),
                    ignore_order=True, exclude_paths=["root['float_field']", "root['history']"]) == {}
    assert updated_object.float_field == 42.0
    # Создалась новая историческая запись соответствующая обновленным данным
    assert len(updated_object.history) == 2
    last_history_record = updated_object.history[-1]
    assert DeepDiff(last_history_record.model_dump(), updated_object.model_dump(), ignore_order=True,
                    exclude_paths=["root['history']", "root['history_id']", "root['history_datetime']",
                                   "root['id']"]) == {}


async def test_update_object_unique_field_error(test_client: TestClient, register_object_all_fields,
                                                register_type_object_all_fields_object):
    """Проверка обновления уникаьного поля объекта. Ожидается 422 статус в ответе"""
    collection_name = register_type_object_all_fields_object.slug
    update_url = app.url_path_for("update_register_object",
                                  slug=collection_name,
                                  object_id=register_object_all_fields.id)
    response = test_client.patch(update_url, json={"int_field": 123})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_update_object_field_error(test_client: TestClient, register_object_all_fields,
                                         register_type_object_all_fields_object):
    """Проверка обновления поля объекта не валидными данными. Ожидается 422 статус в ответе"""
    collection_name = register_type_object_all_fields_object.slug
    update_url = app.url_path_for("update_register_object",
                                  slug=collection_name,
                                  object_id=register_object_all_fields.id)
    response = test_client.patch(update_url, json={"float_field": 42})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_deactivate_object(test_client: TestClient, register_object_all_fields,
                                 register_type_object_all_fields_object):
    """Проверка деактивации объекта. Ожидается изменение свойства is_deactivated и новая историческая запись"""
    collection_name = register_type_object_all_fields_object.slug
    update_url = app.url_path_for("deactivate_register_object",
                                  slug=collection_name,
                                  object_id=register_object_all_fields.id)
    response = test_client.patch(update_url)
    assert response.status_code == HTTPStatus.OK

    repository = MongoRegisterRepository(collection_name)

    updated_object: RegisterObjectModel = await repository.find_one_by_id(register_object_all_fields.id)
    # Обновленый объект соответствует новым данным
    assert DeepDiff(updated_object.model_dump(), response.json(),
                    ignore_order=True, exclude_paths=["root['history']"]) == {}
    assert updated_object.is_deactivated == True
    # Создалась новая историческая запись соответствующая обновленным данным
    assert len(updated_object.history) == 2
    last_history_record = updated_object.history[-1]
    assert DeepDiff(last_history_record.model_dump(), updated_object.model_dump(), ignore_order=True,
                    exclude_paths=["root['history']", "root['history_id']", "root['history_datetime']",
                                   "root['id']"]) == {}


@pytest.mark.asyncio
async def test_get_object_history_record(test_client: TestClient, register_object_all_fields,
                                         register_type_object_all_fields_object):
    """Проверка получения исторической записи объекта. Создается обект, обновляется 4 раза.
    Проверяется что по запросу последней исторической записи возвращаются верные данные"""

    collection_name = register_type_object_all_fields_object.slug

    repository = MongoRegisterRepository(collection_name)

    for float_value in [1.0, 2.0, 3.0, 4.0]:
        await repository.update_one(register_object_all_fields.id, {"float_field": float_value})

    registry_object: RegisterObjectModel = await repository.find_one(register_object_all_fields.id)
    last_history_record = registry_object.history[-1]

    get_url = app.url_path_for("get_object_history_record", slug=collection_name,
                               object_id=register_object_all_fields.id,
                               history_id=last_history_record.history_id)
    response = test_client.get(get_url)
    assert response.status_code == HTTPStatus.OK
    assert last_history_record.float_field == response.json()['float_field'] == float_value


@pytest.mark.asyncio
async def test_get_object_history_records(test_client: TestClient, register_object_all_fields,
                                          register_type_object_all_fields_object):
    """Проверка получения всех исторических записей объекта. Создается обект, обновляется 4 раза.
    Проверяется что по запросу всех записей возвращается 5 объектов"""

    collection_name = register_type_object_all_fields_object.slug

    repository = MongoRegisterRepository(collection_name)

    for float_value in [1.0, 2.0, 3.0, 4.0]:
        await repository.update_one(register_object_all_fields.id, {"float_field": float_value})

    get_url = app.url_path_for("get_object_history_records_list", slug=collection_name,
                               object_id=register_object_all_fields.id, )
    response = test_client.get(get_url)
    assert response.status_code == HTTPStatus.OK
    assert len(response.json()) == 5
