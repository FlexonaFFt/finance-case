from fastapi import FastAPI

from app.routes.auth import router as auth_router
from app.routes.accounts import router as accounts_router
from app.routes.clients import router as clients_router
from app.routes.loans import router as loans_router
from app.routes.transactions import router as transactions_router
from app.routes.transfers import router as transfers_router
from app.config import settings
from app.dbs.db import Base, SessionLocal, engine
from app.dbs import models  # noqa: F401
from app.dbs.seed import seed_database

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    if settings.seed_data:
        db = SessionLocal()
        try:
            seed_database(db)
        finally:
            db.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(clients_router)
app.include_router(accounts_router)
app.include_router(transfers_router)
app.include_router(transactions_router)
app.include_router(loans_router)
