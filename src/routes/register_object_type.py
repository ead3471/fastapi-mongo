from fastapi import APIRouter, Body, HTTPException, status, Response

from database.register_object_repository import *
from schemas.register_object_type import RegisterObjectTypeResponse, UpdateRegisterObjectTypeModel

router = APIRouter()


@router.get(
    "/",
    response_description="Register objects retrieved",
    response_model=list[RegisterObjectTypeResponse]
)
async def get_all_register_type_objects():
    objects = await retrieve_objects()
    return objects


@router.get(
    "/{id}",
    response_description="Object data retrieved",
    response_model=RegisterObjectTypeResponse,
)
async def get_register_type_data(id: PydanticObjectId):
    object = await retrieve_object(id)
    if object:
        return object
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Object with id {id} not found")


@router.post(
    "/",
    response_description="Object data added into the database",
    description="Create object type in database",
    response_model=RegisterObjectTypeResponse,
)
async def add_register_type_object(register_type_object: RegisterObjectType = Body(...)):
    new_object = await add_object(register_type_object)
    return new_object


@router.delete("/{id}", response_description="Register data deleted from the database")
async def delete_register_type(id: PydanticObjectId):
    deleted_student = await delete_student(id)
    if deleted_student:
        return Response(status=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Object with id {id} not found")


@router.put("/{id}", response_model=RegisterObjectTypeResponse)
async def update_register_type_object(id: PydanticObjectId, req: UpdateRegisterObjectTypeModel = Body(...)):
    updated_student = await update_object_data(id, req.dict())
    if updated_student:
        return updated_student
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Object with id {id} not found")
