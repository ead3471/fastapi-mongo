import typing
from typing import Any, Literal

from pydantic import BaseModel, Field
from pydantic.main import IncEx
from pydantic_core import PydanticUndefined

from library.pydantic.fields import PyObjectId


class CreateRegisterObjectSchema(BaseModel):
    notify_fields: list[str] | None = []

    class Config:
        extra = 'allow'


class UpdateRegisterObjectSchema(BaseModel):
    notify_fields: list[str] | None = []

    class Config:
        extra = 'allow'


class RegisterObjectNoHistorySchema(BaseModel):
    id: PyObjectId
    notify_fields: list[str] | None = []
    history: Any = Field(exclude=True)  # Прописано здесь с exclude тк необходимо разрешить дополнительные поля
    is_deactivated: bool

    class Config:
        extra = 'allow'
