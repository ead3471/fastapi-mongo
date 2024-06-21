import re
from typing import List, Optional, Any

import jsonschema
from beanie import Document
from pydantic import field_validator, validator

from library.pydantic.fields import SlugField, JsonSchemaField


class RegisterObjectType(Document):
    name: str
    description: str | None
    notify_fields: list[str] | None
    unique_fields: list[str]
    slug: str
    json_schema: dict | None = None

    @field_validator('json_schema')
    def validate_json_schema(cls, v):
        try:
            jsonschema.Draft7Validator.check_schema(v)
        except jsonschema.exceptions.SchemaError as e:
            raise ValueError(f"Invalid JSON schema: {e}")
        return v

    @field_validator('slug')
    def validate_slug(cls, v):
        if not re.match(r'^[a-z0-9_]{3,}$', v):
            raise ValueError(
                ('Invalid slug format. Must be at least 3 characters long and '
                 'contain only lowercase letters and numbers.'))
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Active Directory User!!",
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
                    "required": ["samaccountname"],
                },
            }
        }

    class Settings:
        name = "register_object_type"
