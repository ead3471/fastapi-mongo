from pydantic import BaseModel, EmailStr, Json, Field
from typing import Optional, Any

from library.pydantic.fields import PyObjectId


class UpdateRegisterObjectTypeModel(BaseModel):
    name: str
    description: str | None
    notify_fields: list[str] | None
    json_schema: dict | None = None
    slug: str

    class Collection:
        name = "Register objects types"

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Active Directory User!",
                "description": "Active Directory user objects",
                "slug": "ad_user",
                "notify_fields": ["title", "uac", "description", "groups", "is_fired"],
                "unique_fields": ["samaccountname", ],

                "json_schema": {
                    "$schema": "some_url",
                    "type": "object",
                    "properties": {
                        "samaccountname": {
                            "type": "string",
                            "description": "The SAM account name."
                        },
                        "uac": {
                            "type": "integer",
                            "description": "The User Account Control integer value."
                        },
                        "description": {
                            "type": "string",
                            "description": "A description of the register type object."
                        },
                        "groups": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of group names.",
                        },
                        "is_fired": {
                            "type": "boolean",
                            "description": "Indicates whether the user is fired.",
                        },
                    },
                    "required": ["samaccountname", ],
                },
            }
        }


class RegisterObjectTypeResponse(BaseModel):
    id: PyObjectId
    name: str
    description: str | None
    notify_fields: list[str] | None
    json_schema: dict | None
    unique_fields: list[str]
    slug: str
