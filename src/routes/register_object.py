from typing import Optional, Type, Iterable

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Response, status, Depends

from pydantic import BaseModel, ValidationError, create_model

from database.register_object_repository import MongoRegisterRepository
from library.pydantic.fields import PyObjectId
from library.pydantic.models_generator import create_model_from_jsonschema
from models import RegisterObjectTypeModel
from config.config import get_db
from models.register_object import RegisterObjectModel, HistoryRecordModel
from schemas.register_object import CreateRegisterObjectSchema, RegisterObjectNoHistorySchema, \
    UpdateRegisterObjectSchema

router = APIRouter()


def get_repository(slug: str = None) -> MongoRegisterRepository:
    return MongoRegisterRepository(slug)


@router.post("/register/{slug}/",
             description='Добавить объект зарегистрированного типа в реестр',
             name='Добавить объект')
async def create_object(slug: str, register_object_payload: CreateRegisterObjectSchema,
                        repository: MongoRegisterRepository = Depends(get_repository)):
    collection_exists = await repository.collection_exists()
    if not collection_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Register Object type {slug} not found")

    register_object = RegisterObjectModel(**register_object_payload.model_dump(exclude_unset=True))
    result = await repository.insert_one(register_object)

    return Response(status_code=status.HTTP_201_CREATED)


@router.get("/register/{slug}/{object_id}",
            description='Получить объект зарегистрированного типа из реестра',
            name="Получить объект",
            response_model=RegisterObjectNoHistorySchema)
async def get_object(slug: str,
                     object_id: PydanticObjectId,
                     repository: MongoRegisterRepository = Depends(get_repository)):
    result_object: RegisterObjectModel = await repository.find_one_by_id(object_id, {"history"})
    return result_object.model_dump()


@router.get("/register/{slug}/",
            description='Получить объекты зарегистрированного типа из реестра',
            name="Получить объекты",
            response_model=list[RegisterObjectNoHistorySchema])
async def get_objects(slug: str,
                      repository: MongoRegisterRepository = Depends(get_repository)):
    result_objects: Iterable[RegisterObjectModel] = await repository.find()
    return (result_object.model_dump() for result_object in result_objects)


@router.delete("/register/{slug}/{object_id}",
               description='Удалить объект зарегистрированного типа из реестра',
               name="Удалить объект", )
async def delete_object(slug: str,
                        object_id: PydanticObjectId,
                        repository: MongoRegisterRepository = Depends(get_repository)):
    result = await repository.delete_one_by_id(object_id)
    if result:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.patch("/register/{slug}/{object_id}",
              description='Обновить объект зарегистрированного типа из реестра',
              name="Обновить объект", )
async def update_object(slug: str,
                        object_id: PydanticObjectId,
                        update_object_payload: UpdateRegisterObjectSchema,
                        repository: MongoRegisterRepository = Depends(get_repository)):
    result = await repository.update_one(object_id, update_object_payload.model_dump(exclude_unset=True))
    if result:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.get("/register/{slug}/{object_id}/history/",
            description='История объекта',
            name="История объекта",
            response_model=list[HistoryRecordModel])
async def get_object_history(slug: str,
                             object_id: PydanticObjectId,
                             repository: MongoRegisterRepository = Depends(get_repository)):
    result_object: RegisterObjectModel = await repository.find_one_by_id(object_id)
    if result_object:
        return result_object.history
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.get("/register/{slug}/{object_id}/history/{history_id}",
            description='Историческая запись объекта',
            name="Историческая запись объекта",
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
