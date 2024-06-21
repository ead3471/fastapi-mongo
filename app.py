from fastapi import FastAPI, Depends

from config.config import initiate_database
from routes.reestr_object import router as ReestrObjectTypeRouter
from routes.reestr import router as ReestrRouter

app = FastAPI()


@app.on_event("startup")
async def start_database():
    await initiate_database()


app.include_router(
    ReestrObjectTypeRouter,
    tags=["Reestr Objects Types"],
    prefix="/reestrtype",
)

app.include_router(
    ReestrRouter,
    tags=["Reestr Objects"],
    prefix="/reestr",
)
