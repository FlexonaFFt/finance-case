from fastapi import FastAPI

from app.config import settings
from app.dbs.db import Base, engine
from app.dbs import models  # noqa: F401
from app.routes import accounts_router, auth_router, transactions_router

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(transactions_router)
