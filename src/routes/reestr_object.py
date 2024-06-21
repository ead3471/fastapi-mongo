from fastapi import APIRouter, Body


from database.reestr_object_repository import *
from schemas.reestr_object import ReestrObjectResponse, UpdateReestrObjectModel


router = APIRouter()


@router.get(
    "/",
    response_description="Reestr objects retrieved",
    response_model=ReestrObjectResponse,
)
async def get_all_reestr_objects():
    objects = await retrieve_objects()
    return {
        "status_code": 200,
        "response_type": "success",
        "description": "Reestr data retrieved successfully",
        "data": objects,
    }


@router.get(
    "/{id}",
    response_description="Object data retrieved",
    response_model=ReestrObjectResponse,
)
async def get_reestr_data(id: PydanticObjectId):
    object = await retrieve_object(id)
    if object:
        return {
            "status_code": 200,
            "response_type": "success",
            "description": "Object data retrieved successfully",
            "data": object,
        }
    return {
        "status_code": 404,
        "response_type": "error",
        "description": "Object doesn't exist",
    }


@router.post(
    "/",
    response_description="Object data added into the database",
    response_model=ReestrObjectResponse,
)
async def add_reestr_object(reestr_object: ReestrObject = Body(...)):
    new_object = await add_object(reestr_object)
    return {
        "status_code": 200,
        "response_type": "success",
        "description": "Reestr object created successfully",
        "data": new_object,
    }


@router.delete("/{id}", response_description="Reestr data deleted from the database")
async def delete_reestr_data(id: PydanticObjectId):
    deleted_student = await delete_student(id)
    if deleted_student:
        return {
            "status_code": 200,
            "response_type": "success",
            "description": "Reestr object with ID: {} removed".format(id),
            "data": deleted_student,
        }
    return {
        "status_code": 404,
        "response_type": "error",
        "description": "Reestr object with id {0} doesn't exist".format(id),
        "data": False,
    }


@router.put("/{id}", response_model=ReestrObjectResponse)
async def update_reestr_object(
    id: PydanticObjectId, req: UpdateReestrObjectModel = Body(...)
):
    updated_student = await update_object_data(id, req.dict())
    if updated_student:
        return {
            "status_code": 200,
            "response_type": "success",
            "description": "Reestr object with ID: {} updated".format(id),
            "data": updated_student,
        }
    return {
        "status_code": 404,
        "response_type": "error",
        "description": "An error occurred. Reestr object with ID: {} not found".format(
            id
        ),
        "data": False,
    }
