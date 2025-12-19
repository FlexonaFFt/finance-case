from fastapi import FastAPI

from app.routes import router

app = FastAPI(title="Finance Tracker API", version="0.2.0")
app.include_router(router)


@app.on_event("startup")
def startup_seed() -> None:
    # DB is seeded via Postgres init scripts; no in-memory seed needed.
    return None
