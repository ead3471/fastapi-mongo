from enum import Enum

from pydantic import BaseModel, model_validator
from typing_extensions import Self

from library.pydantic.fields import PyObjectId
from models.register_object_type import RegisterField


class UpdateRegisterObjectTypeModel(BaseModel):
    name: str | None = None
    description: str | None = None
    notify_fields: list[str] | None = None
    fields: list[RegisterField] | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Active Directory User!",
                "description": "Active Directory user objects",
                "notify_fields": ["title", "uac", "description", "groups", "is_fired"],
            }
        }


class RegisterObjectTypeResponse(BaseModel):
    id: PyObjectId
    name: str
    description: str | None
    notify_fields: list[str] | None
    json_schema: list[RegisterField]
    unique_fields: list[str]
    slug: str


class RegisterObjectTypeCreate(BaseModel):
    name: str
    description: str | None
    slug: str
    notify_fields: list[str] | None
    unique_fields: list[str]
    fields: list[RegisterField]
