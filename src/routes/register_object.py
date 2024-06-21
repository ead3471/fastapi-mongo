from typing import Optional, Type

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, ValidationError, create_model

from library.pydantic.models_generator import create_model_from_jsonschema
from models import RegisterObjectType
from config.config import get_db

router = APIRouter()


@router.post("/register/{slug}/")
async def create_object(slug: str, obj_data: dict):
    register_type_object = await RegisterObjectType.find_one({"slug": slug})

    if not register_type_object:
        raise HTTPException(status_code=404, detail=f"Register Object type {slug} not found")

    schema = register_type_object.json_schema

    register_object_class: Type[BaseModel] = create_model_from_jsonschema(schema,
                                                                          name=register_type_object.name.strip(" "))

    try:
        validated_obj = register_object_class(**obj_data)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    collection_name = slug.replace("-", "_")
    db = get_db()
    collection = db[collection_name]

    await collection.insert_one(validated_obj.model_dump())

    return Response(status_code=status.HTTP_201_CREATED)
