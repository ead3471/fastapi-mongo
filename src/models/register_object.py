from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel, Extra, Field

from library.pydantic.fields import PyObjectId


class HistoryRecordModel(BaseModel):
    history_id: PyObjectId = Field(default_factory=PyObjectId)
    history_datetime: datetime
    notify_fields: list[str]
    is_deactivated: bool = False

    class Config:
        json_encoders = {ObjectId: str}
        extra = 'allow'


class RegisterObjectModel(BaseModel):
    id: PyObjectId = Field(alias='_id', default=None, serialization_alias='id')
    notify_fields: list[str] = []
    history: list[HistoryRecordModel] = []
    is_deactivated: bool = False

    class Config:
        extra = 'allow'
