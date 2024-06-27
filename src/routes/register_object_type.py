from fastapi import APIRouter, Body, HTTPException, status, Response

from database.register_object_type_repository import *
from schemas.register_object_type import RegisterObjectTypeResponse, UpdateRegisterObjectTypeModel, \
    RegisterObjectTypeCreate

router = APIRouter()

register_type_repository = MongoRegisterTypeRepository()


@router.post(
    "/",
    response_description="Object data added into the database",
    description="Create object type in database",
    response_model=RegisterObjectType,
)
async def add_register_type_object(register_type_object: RegisterObjectTypeCreate = Body(...)):
    domain_object = RegisterObjectType(**register_type_object.model_dump())
    new_object = await register_type_repository.insert_one(domain_object)
    return new_object


@router.get(
    "/",
    description="Получить все зарегистрированные типы объектов",
    response_model=list[RegisterObjectType]
)
async def get_all_register_type_objects():
    registers_objects = await register_type_repository.find()
    return registers_objects


@router.get(
    "/{object_id}",
    description="Получить объект типа",
    response_model=RegisterObjectTypeResponse,
)
async def get_register_type_data(object_id: PydanticObjectId):
    register_object = await register_type_repository.find_one_by_id(object_id)
    if register_object:
        return register_object
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Object with id {object_id} not found")


@router.delete("/{object_id}", description="Удалеить объект")
async def delete_register_type(object_id: PydanticObjectId):
    deleted_object = await register_type_repository.delete_one_by_id(object_id)
    if deleted_object:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Object with id {object_id} not found")


@router.put("/{object_id}", response_model=RegisterObjectType)
async def update_register_type_object(type_id: PydanticObjectId, req: UpdateRegisterObjectTypeModel = Body(...)):
    req_dict = req.model_dump(exclude_unset=True)
    updated_object: RegisterObjectType = await register_type_repository.update_one(type_id,
                                                                                   req_dict)
    if updated_object:
        return updated_object
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Object with id {type_id} not found")
