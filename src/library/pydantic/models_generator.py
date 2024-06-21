from typing import Optional, Type

from pydantic import create_model, BaseModel


def get_field_type(json_type):
    if json_type == 'string':
        return str
    elif json_type == 'integer':
        return int
    elif json_type == 'boolean':
        return bool
    elif json_type == 'array':
        return list
    elif json_type == 'object':
        return dict
    else:
        raise ValueError(f"Unsupported JSON schema type: {json_type}")


def create_model_from_jsonschema(schema: dict, name='DynamicModel') -> Type[BaseModel]:
    """
    Создает Pydantic BaseModel  класс из переданной JsonSchema
    Args:
        schema: схема
        name: имя модели
    """
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    annotations = {}
    defaults = {}

    for prop_name, prop_schema in properties.items():
        prop_type = prop_schema.get("type", "string")
        field_type = get_field_type(prop_type)

        if prop_name in required:
            annotations[prop_name] = field_type
            defaults[prop_name] = ...
        else:
            annotations[prop_name] = Optional[field_type]
            defaults[prop_name] = None

    return create_model(name, **{k: (annotations[k], defaults[k]) for k in annotations})
