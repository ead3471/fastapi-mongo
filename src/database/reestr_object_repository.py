from typing import List, Union

from beanie import PydanticObjectId

from models.reestr_object import ReestrObject


reestr_object_collection = ReestrObject


async def retrieve_objects() -> List[ReestrObject]:
    objects = await reestr_object_collection.all().to_list()
    return objects


async def add_object(new_object: ReestrObject) -> ReestrObject:
    object = await new_object.create()
    return object


async def retrieve_object(id: PydanticObjectId) -> ReestrObject:
    object = await reestr_object_collection.get(id)
    if object:
        return object


async def delete_student(id: PydanticObjectId) -> bool:
    object = await reestr_object_collection.get(id)
    if object:
        await object.delete()
        return True


async def update_object_data(
    id: PydanticObjectId, data: dict
) -> Union[bool, ReestrObject]:
    des_body = {k: v for k, v in data.items() if v is not None}
    update_query = {"$set": {field: value for field, value in des_body.items()}}
    object = await reestr_object_collection.get(id)
    if object:
        await object.update(update_query)
        return object
    return False
