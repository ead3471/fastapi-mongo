from typing import Optional, Type, Iterable

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Response, status, Depends

from database.register_object_repository import MongoRegisterRepository
from models.register_object import RegisterObjectModel, HistoryRecordModel
from schemas.register_object import CreateRegisterObjectSchema, RegisterObjectNoHistorySchema, \
    UpdateRegisterObjectSchema

router = APIRouter()


def get_repository(slug: str = None) -> MongoRegisterRepository:
    return MongoRegisterRepository(slug)


@router.post("/{slug}/",
             description='Добавить объект зарегистрированного типа в реестр',
             status_code=status.HTTP_201_CREATED,
             name='create_register_object',
             response_model=RegisterObjectNoHistorySchema
             )
async def create_object(slug: str, register_object_payload: CreateRegisterObjectSchema,
                        repository: MongoRegisterRepository = Depends(get_repository)):
    collection_exists = await repository.collection_exists()
    if not collection_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Register Object type {slug} not found")

    register_object = RegisterObjectModel(**register_object_payload.model_dump(exclude_unset=True))
    result: RegisterObjectModel = await repository.insert_one(register_object)

    return result.model_dump()


@router.get("/{slug}/{object_id}",
            description='Получить объект зарегистрированного типа из реестра',
            name="get_register_object",
            response_model=RegisterObjectNoHistorySchema)
async def get_object(slug: str,
                     object_id: PydanticObjectId,
                     repository: MongoRegisterRepository = Depends(get_repository)):
    result_object: RegisterObjectModel = await repository.find_one_by_id(object_id, {"history"})
    if result_object is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Register Object type {slug}/{object_id} not found")

    return result_object.model_dump()


@router.get("/{slug}/",
            description='Получить объекты зарегистрированного типа из реестра',
            name="get_register_objects",
            response_model=list[RegisterObjectNoHistorySchema])
async def get_objects(slug: str,
                      repository: MongoRegisterRepository = Depends(get_repository)):
    result_objects: Iterable[RegisterObjectModel] = await repository.find()
    return (result_object.model_dump() for result_object in result_objects)


@router.delete("/{slug}/{object_id}",
               description='Удалить объект зарегистрированного типа из реестра',
               name="delete_register_object", )
async def delete_object(slug: str,
                        object_id: PydanticObjectId,
                        repository: MongoRegisterRepository = Depends(get_repository)):
    result = await repository.delete_one_by_id(object_id)
    if result:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.patch("/{slug}/{object_id}",
              description='Обновить объект зарегистрированного типа из реестра',
              name="update_register_object",
              response_model=RegisterObjectNoHistorySchema)
async def update_object(slug: str,
                        object_id: PydanticObjectId,
                        update_object_payload: UpdateRegisterObjectSchema,
                        repository: MongoRegisterRepository = Depends(get_repository)):
    result = await repository.update_one(object_id, update_object_payload.model_dump(exclude_unset=True))
    if result:
        return result.model_dump()
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.patch("/{slug}/{object_id}/deactivate",
              description='Деактивировать объект',
              name="deactivate_register_object",
              response_model=RegisterObjectNoHistorySchema)
async def update_object(slug: str,
                        object_id: PydanticObjectId,
                        repository: MongoRegisterRepository = Depends(get_repository)):
    result = await repository.update_one(object_id, {"is_deactivated": True})
    if result:
        return result.model_dump()
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


# TODO: Добавить паджинацию и фильтрацию
@router.get("/{slug}/{object_id}/history/",
            description='История объекта',
            name="get_object_history_records_list",
            response_model=list[HistoryRecordModel])
async def get_object_history(slug: str,
                             object_id: PydanticObjectId,
                             repository: MongoRegisterRepository = Depends(get_repository)):
    result_object: RegisterObjectModel = await repository.find_one_by_id(object_id)
    if result_object:
        return result_object.history
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.get("/{slug}/{object_id}/history/{history_id}",
            description='Историческая запись объекта',
            name="get_object_history_record",
            response_model=HistoryRecordModel)
async def get_object_history_record(slug: str,
                                    object_id: PydanticObjectId,
                                    history_id: PydanticObjectId,
                                    repository: MongoRegisterRepository = Depends(get_repository)):
    result_object: HistoryRecordModel = await repository.get_object_history_record(object_id, history_id)
    if result_object:
        return result_object
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
