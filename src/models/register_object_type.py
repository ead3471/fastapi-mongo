import re
from enum import Enum
from typing import Self, TypeVar, Optional

import jsonschema
from beanie import Document
from bson import ObjectId
from pydantic import field_validator, BaseModel, model_validator, Field, constr

from library.pydantic.fields import PyObjectId

T = TypeVar('T', bound='SupportedTypes')


class SupportedTypes(str, Enum):
    INT = 'int'
    BOOL = 'bool'
    FLOAT = 'float'
    STRING = 'str'
    LIST_OF_INTS = 'list_of_int'
    LIST_OF_BOOLS = 'list_of_bool'
    LIST_OF_FLOAT = 'list_of_float'
    LIST_OF_STRING = 'list_of_str'

    def __repr__(self) -> str:
        return str.__repr__(self.value)

    def json_schema(self):
        if not hasattr(self, "__json_spec"):
            self.__json_spec = {
                SupportedTypes.INT: {"bsonType": "int"},
                SupportedTypes.BOOL: {"bsonType": "bool"},
                SupportedTypes.FLOAT: {"bsonType": "double"},
                SupportedTypes.STRING: {"bsonType": "string"},
                SupportedTypes.LIST_OF_INTS: {
                    "bsonType": "array",
                    "items": {"bsonType": "int"}
                },
                SupportedTypes.LIST_OF_BOOLS: {
                    "bsonType": "array",
                    "items": {"bsonType": "bool"}
                },
                SupportedTypes.LIST_OF_FLOAT: {
                    "bsonType": "array",
                    "items": {"bsonType": "double"}
                },
                SupportedTypes.LIST_OF_STRING: {
                    "bsonType": "array",
                    "items": {"bsonType": "string"}
                }
            }

        return self.__json_spec[self]


class RegisterField(BaseModel):
    name: str
    optional: bool = False
    type: SupportedTypes


# TODO: Генерация индексов по уникальным  slug и name
class RegisterObjectTypeModel(BaseModel):
    id: PyObjectId = Field(alias='_id', default=None, serialization_alias='id')
    name: str
    description: str | None
    slug: constr(pattern=r'^[a-z_0-9]{1,32}$')
    notify_fields: list[str] | None
    unique_fields: list[str]
    fields: list[RegisterField]

    @model_validator(mode='after')
    def check_notify_and_unique_fields(self) -> Self:
        fields = {field.name for field in self.fields}
        if extra_fields := set(self.unique_fields) - fields:
            raise ValueError(f"Unique fields list contains unknown fields:{extra_fields}")

        if extra_fields := set(self.notify_fields) - fields:
            raise ValueError(f"Notify fields list contains unknown fields:{extra_fields}")

        return self

    def fields_json_schema(self):
        base_properties = {field.name: field.type.json_schema() for field in self.fields}
        base_properties["_id"] = {
            "bsonType": "objectId"
        }
        base_properties["notify_fields"] = {
            "bsonType": "array",
            "items": {
                "bsonType": "string"
            }
        }
        base_properties["is_deactivated"] = {
            "bsonType": "bool"
        }
        # TODO: более точная спецификация истории?
        base_properties["history"] = {
            "bsonType": "array"
        }
        return {
            "$jsonSchema": {"bsonType": "object",
                            "required": [field.name for field in self.fields if not field.optional],
                            "properties": base_properties,
                            "additionalProperties": False
                            }

        }
