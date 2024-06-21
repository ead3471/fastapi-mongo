import re
from typing import List, Optional, Any

from beanie import Document
from pydantic import BaseModel, field_validator


class ReestrObject(Document):
    name: str
    description: str
    notify_fields: List[str]

    slug: str

    @field_validator("slug")
    def validate_slug(cls, v):
        pattern = re.compile(r"^[\w-]+$")
        if not pattern.match(v):
            raise ValueError("Invalid slug")
        return v

    json_schema: Optional[dict] = None

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
                            "required": True,
                        },
                    },
                    "required": ["samaccountname", "description", "is_fired", "slug"],
                },
            }
        }

    class Settings:
        name = "reestr_object"
