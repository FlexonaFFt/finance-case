from fastapi import FastAPI

from app.routes.auth import router as auth_router
from app.config import settings
from app.dbs.db import Base, engine
from app.dbs import models  # noqa: F401

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router)
