from enum import Enum

from pydantic import BaseModel, model_validator, Field, constr
from typing_extensions import Self

from library.pydantic.fields import PyObjectId
from models.register_object_type import RegisterField


class UpdateRegisterObjectTypeSchema(BaseModel):
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
                "fields": ["field1", "field2", "field3"],
            }
        }


class RegisterObjectTypeResponseSchema(BaseModel):
    id: PyObjectId
    name: str
    description: str | None
    notify_fields: list[str] | None
    unique_fields: list[str]
    fields: list[RegisterField]
    slug: str


class CreateRegisterObjectTypeSchema(BaseModel):
    name: str
    description: str | None
    slug: constr(pattern=r'^[a-z0-9_]{1,32}$')
    notify_fields: list[str] | None
    unique_fields: list[str]
    fields: list[RegisterField]
