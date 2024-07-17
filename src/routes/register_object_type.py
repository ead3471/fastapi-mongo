from fastapi import APIRouter, Body, HTTPException, status, Response, Depends
from pymongo.errors import OperationFailure

from database.register_object_type_repository import *
from schemas.register_object_type import RegisterObjectTypeResponseSchema, UpdateRegisterObjectTypeSchema, \
    CreateRegisterObjectTypeSchema

router = APIRouter()


def get_repository() -> MongoRegisterTypeRepository:
    return MongoRegisterTypeRepository()


@router.post(
    "/",
    response_description="Object data added into the database",
    description="Create object type in database",
    response_model=RegisterObjectTypeModel,
    status_code=status.HTTP_201_CREATED,
    name="create_register_object_type",
)
async def add_register_type_object(register_type_object: CreateRegisterObjectTypeSchema = Body(...),
                                   repository: MongoRegisterTypeRepository = Depends(get_repository)):
    domain_object = RegisterObjectTypeModel(**register_type_object.model_dump())
    try:
        new_object = await repository.insert_one(domain_object)
    # TODO: Заменить на не зависящие от монго реализации исключений
    except OperationFailure as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ex.details['errmsg'])
    return new_object


@router.get(
    "/",
    description="Получить все зарегистрированные типы объектов",
    response_model=list[RegisterObjectTypeResponseSchema],
    name="get_register_object_type_list",
)
async def get_all_register_type_objects(repository: MongoRegisterTypeRepository = Depends(get_repository)):
    registers_objects = await repository.find()
    return registers_objects


@router.get(
    "/{object_id}",
    description="Получить объект типа",
    response_model=RegisterObjectTypeResponseSchema,
    name="get_register_object_type"
)
async def get_register_type_data(object_id: PydanticObjectId,
                                 repository: MongoRegisterTypeRepository = Depends(get_repository)):
    register_object = await repository.find_one_by_id(object_id)
    if register_object:
        return register_object
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Object with id {object_id} not found")


@router.delete("/{object_id}",
               description="Удалить объект",
               name="delete_register_object_type")
async def delete_register_type(object_id: PydanticObjectId,
                               repository: MongoRegisterTypeRepository = Depends(get_repository)):
    deleted_object = await repository.delete_one_by_id(object_id)
    if deleted_object:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Object with id {object_id} not found")


@router.patch("/{object_id}", response_model=RegisterObjectTypeModel, name="update_register_object_type")
async def update_register_type_object(object_id: PydanticObjectId, req: UpdateRegisterObjectTypeSchema = Body(...),
                                      repository: MongoRegisterTypeRepository = Depends(get_repository),
                                      ):
    req_dict = req.model_dump(exclude_unset=True)
    updated_object: RegisterObjectTypeModel = await repository.update_one(object_id,
                                                                          req_dict)
    if updated_object:
        return updated_object
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Object with id {object_id} not found")
