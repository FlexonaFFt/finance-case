from fastapi import FastAPI

from app.config import settings
from app.dbs.db import Base, SessionLocal, engine
from app.dbs import models  # noqa: F401
from app.dbs.seed import seed_database
from app.routes.auth import router as auth_router
from app.routes.insurance_accounts import router as insurance_accounts_router
from app.routes.policies import router as policies_router

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
app.include_router(insurance_accounts_router)
app.include_router(policies_router)
