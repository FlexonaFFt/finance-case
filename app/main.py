from fastapi import FastAPI

from app.routes import router
from app.dbs import repo

app = FastAPI(title="Finance Tracker API", version="0.2.0")
app.include_router(router)


@app.on_event("startup")
def startup_seed() -> None:
    # Ensure seeded clients have hashed passwords
    repo.ensure_passwords(default_password="12345abc")
