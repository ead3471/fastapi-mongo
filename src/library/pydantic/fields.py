import re
from typing import Any

import jsonschema
from bson import ObjectId
from pydantic_core import core_schema


class JsonSchemaField(dict[str, dict]):
    """Поле, содержащее словарь типа JsonSchema"""

    @classmethod
    def validate_schema(cls, v):
        try:
            jsonschema.Draft7Validator.check_schema(v)
        except jsonschema.exceptions.SchemaError as e:
            raise ValueError(f"Invalid JSON schema: {e}")
        return v


class SlugField(str):
    """Slug поле минимум 3 символа без '-'"""

    @classmethod
    def validate_slug(cls, v):
        if not re.match(r'^[a-z0-9]{3,}$', v):
            raise ValueError(
                'Invalid slug format. Must be at least 3 characters long and contain only lowercase letters and numbers.')
        return v


class PyObjectId(ObjectId):
    # @classmethod
    # def __get_pydantic_core_schema__(
    #         cls, _source_type: Any, _handler: Any
    # ) -> core_schema.CoreSchema:
    #     return core_schema.json_or_python_schema(
    #         json_schema=core_schema.str_schema(),
    #         python_schema=core_schema.union_schema(
    #             [
    #                 core_schema.is_instance_schema(ObjectId),
    #                 core_schema.chain_schema(
    #                     [
    #                         core_schema.str_schema(),
    #                         core_schema.no_info_plain_validator_function(cls.validate),
    #                     ]
    #                 ),
    #             ]
    #         ),
    #         serialization=core_schema.plain_serializer_function_ser_schema(
    #             lambda x: str(x)
    #         ),
    #     )

    @classmethod
    def __get_pydantic_core_schema__(
            cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(ObjectId),
                    core_schema.chain_schema(
                        [
                            core_schema.str_schema(),
                            core_schema.no_info_plain_validator_function(cls.validate),
                        ]
                    ),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, value) -> ObjectId:
        if isinstance(value, ObjectId):
            return value
        if isinstance(value, str) and ObjectId.is_valid(value):
            return ObjectId(value)
        raise ValueError("Invalid ObjectId")
