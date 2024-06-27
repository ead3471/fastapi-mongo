from fastapi import FastAPI, Depends

from routes.register_object import router as register_object_type_router
from routes.register_object_type import router as register_router

app = FastAPI()

app.include_router(
    register_object_type_router,
    tags=["Register Objects Types"],
    prefix="/register_type",
)

app.include_router(
    register_router,
    tags=["Register Objects"],
    prefix="/register",
)
