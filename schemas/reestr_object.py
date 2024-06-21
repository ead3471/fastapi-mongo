from pydantic import BaseModel, EmailStr
from typing import Optional, Any


class UpdateReestrObjectModel(BaseModel):
    name: str | None
    description: str | None
    notify_fields: list[str] | None
    json_schema: dict | None = None
    slug: str | None

    class Collection:
        name = "Reestr objects"

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Active Directory User",
                "description": "Actirv Directory user objects",
                "slug": "ad_user",
                "notify_fields": ["title", "uac", "description", "groups", "is_fired"],
                "json_schema": {
                    "$schema": "http://json-schema.org/draft-07/schema#",
                    "type": "object",
                    "properties": {
                        "samaccountname": {
                            "type": "string",
                            "description": "The SAM account name.",
                            "required": True,
                        },
                        "uac": {
                            "type": "integer",
                            "description": "The User Account Control integer value.",
                            "required": True,
                        },
                        "description": {
                            "type": "string",
                            "description": "A description of the object.",
                            "required": True,
                        },
                        "groups": {
                            "description": "User Groups",
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of group names.",
                        },
                        "is_fired": {
                            "type": "boolean",
                            "description": "Indicates whether the user is fired.",
                            "required": True,
                        },
                        "slug": {
                            "type": "string",
                            "description": "Short slug for reestr.",
                            "required": False,
                        },
                    },
                    "required": ["samaccountname", "description", "is_fired"],
                },
            }
        }


class ReestrObjectResponse(BaseModel):
    status_code: int
    response_type: str
    description: str
    data: Optional[Any]

    class Config:
        json_schema_extra = {
            "example": {
                "status_code": 200,
                "response_type": "success",
                "description": "Operation successful",
                "data": "Sample data",
            }
        }
