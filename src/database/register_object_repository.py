from datetime import datetime, tzinfo, UTC
from typing import Any

from beanie import PydanticObjectId

from database.mongo_repository import DataBaseObjectRepository, T
from database.register_object_type_repository import get_object_default_notify_fields, get_object_unique_fields

from models.register_object import RegisterObjectModel, HistoryRecordModel


class MongoRegisterRepository(DataBaseObjectRepository):
    def __init__(self, collection_name: str, ):
        super().__init__(collection_name, model=RegisterObjectModel)

    async def insert_one(self, document: RegisterObjectModel, session=None) -> Any:
        if 'notify_fields' not in document.model_dump(exclude_unset=True):
            document.notify_fields = await get_object_default_notify_fields(self.collection_name)

        history_record = HistoryRecordModel(
            history_datetime=datetime.now(tz=UTC),
            **document.model_dump(exclude={'history', 'id'})
        )
        document.history = [history_record]

        document_dump = document.model_dump(exclude={
            'id': True,
            "history": {
                "__all__": {"history_id"}
            }})
        document_dump["history"][0]["history_id"] = document.history[0].history_id

        result_id = await self._repository.insert_one(self.collection_name,
                                                      document_dump,
                                                      session=session)
        return await self.find_one_by_id(result_id, exclude_fields={'history'})

    async def get_object_history_record(self, object_id: PydanticObjectId, history_id: PydanticObjectId):
        data = await self._repository.find_one(self.collection_name,
                                               query={"_id": object_id},
                                               extra_filter={"history": {"$elemMatch": {"history_id": history_id}}}
                                               )
        if data and data["history"]:
            return HistoryRecordModel(**data["history"][0])

    async def update_one(self, object_id: PydanticObjectId, update_data: dict, session=None) -> RegisterObjectModel:
        existing_object: RegisterObjectModel = await self.find_one_by_id(object_id, exclude_fields={"history"})
        object_unique_fields = await get_object_unique_fields(self.collection_name)
        if set(object_unique_fields).intersection(set(update_data.keys())):
            raise ValueError("Object unique fields cant be updated")
        history_object_data = existing_object.model_dump(exclude={"history", "id"})
        history_object_data.update(update_data)
        history_object = HistoryRecordModel(**history_object_data, history_datetime=datetime.now(UTC))
        history_object_dump = history_object.model_dump(exclude={'history_id'})
        history_object_dump['history_id'] = history_object.history_id

        query = {"_id": object_id}
        update_data = {"$set": update_data,
                       "$push": {"history": history_object_dump}}

        data = await super().find_one_and_update(query, update_data, session)
        return data
