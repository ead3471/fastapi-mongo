from fastapi import FastAPI, Depends
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from routes.register_object import router as register_object_type_router
from routes.register_object_type import router as register_router

app = FastAPI()

app.include_router(
    register_object_type_router,
    tags=["Объекты реестра"],
    prefix="/register_type",
)

app.include_router(
    register_router,
    tags=["Зарегистрированные типы объектов рестра"],
    prefix="/register",
)


@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc: ValidationError):
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": [error['msg'] for error in exc.errors()]},
    )
