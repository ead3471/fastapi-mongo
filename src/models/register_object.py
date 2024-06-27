from datetime import datetime

from pydantic import BaseModel, Extra


class HistoryRecord(BaseModel):
    history_datetime: datetime
    notify_fields: list[str]

    class Config:
        extra = Extra.allow


class RegisterObject(BaseModel):
    history: list[HistoryRecord]
    notify_fields: list[str]

    class Config:
        extra = Extra.allow
