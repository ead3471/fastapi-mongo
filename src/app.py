from fastapi import FastAPI, Depends
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError, OperationFailure
from starlette.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_409_CONFLICT

from routes.register_object import router as register_router
from routes.register_object_type import router as register_object_type_router

app = FastAPI()

app.include_router(
    register_object_type_router,
    tags=["Зарегистрированные типы объектов рестра"],
    prefix="/register_type",
)

app.include_router(
    register_router,
    tags=["Объекты реестра"],
    prefix="/register",
)


@app.exception_handler(ValidationError)
async def validation_error_exception_handler(request, exc: ValidationError):
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": [error['msg'] for error in exc.errors()]},
    )


@app.exception_handler(ValueError)
async def value_error_exception_handler(request, exc: ValueError):
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.args},
    )


@app.exception_handler(OperationFailure)
async def value_error_exception_handler(request, exc: OperationFailure):
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.details['errInfo']['details']},
    )


@app.exception_handler(DuplicateKeyError)
async def duplicate_key_exception_handler(request, exc: DuplicateKeyError):
    return JSONResponse(
        status_code=HTTP_409_CONFLICT,
        content={"detail": "Insertion error. Object with same unique parameters already exists."},
    )
