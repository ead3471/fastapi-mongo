from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel, ValidationError
from motor.motor_asyncio import AsyncIOMotorClient
from bson.json_util import dumps, loads
from models import (
    ReestrObject,
)  # Adjust the import path according to your project structure
from config.config import db


router = APIRouter()


def create_dynamic_model(schema: dict):
    """
    Creates a Pydantic model dynamically based on the provided JSON schema.
    This is a simplified example and might need adjustments based on your schema's complexity.
    """
    fields = {}
    for key, value in schema["properties"].items():
        field_type_map = {
            "string": str,
            "number": float,
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        fields[key] = field_type_map.get(value["type"], lambda: ...)

    return type("DynamicModel", (BaseModel,), fields)


@router.post("/reestr/{slug}/")
async def create_object(slug: str, obj_data: dict):
    reestr_object = await ReestrObject.find_one({"slug": slug})

    if not reestr_object:
        raise HTTPException(status_code=404, detail="ReestrObject not found")

    # Assuming `json_schema` is stored as a stringified JSON in MongoDB
    # schema = loads(
    #     reestr_object.json_schema
    # )  # Convert BSON to Python dict if necessary

    # # Simplified dynamic model creation and validation
    # DynamicModel = create_dynamic_model(schema)

    # try:
    #     validated_obj = DynamicModel(**obj_data)
    # except ValidationError as e:
    #     raise HTTPException(status_code=422, detail=str(e))

    collection_name = slug.replace(
        "-", "_"
    )  # Sanitize the slug for use as a collection name
    collection = db[collection_name]

    # Convert Pydantic model to dictionary and insert
    await collection.insert_one(obj_data)

    return {"detail": f"Object created in collection '{collection_name}'"}
