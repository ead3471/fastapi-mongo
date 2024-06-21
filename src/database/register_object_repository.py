from typing import List, Union

from beanie import PydanticObjectId

from models.register_object_type import RegisterObjectType

register_object_collection = RegisterObjectType


async def retrieve_objects() -> List[RegisterObjectType]:
    objects = await register_object_collection.all().to_list()
    return objects


async def add_object(new_object: RegisterObjectType) -> RegisterObjectType:
    object_type = await new_object.create()
    await object_type.get_motor_collection().create_index({field: 1 for field in object_type.unique_fields},
                                                          unique=True)
    return object_type


async def retrieve_object(id: PydanticObjectId) -> RegisterObjectType:
    object = await register_object_collection.get(id)
    if object:
        return object


async def delete_student(id: PydanticObjectId) -> bool:
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
