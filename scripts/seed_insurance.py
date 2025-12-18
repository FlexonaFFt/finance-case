#!/usr/bin/env python
"""Seed insurance demo data.

Usage:
  python scripts/seed_insurance.py

Respects env vars from app.config (DATABASE_URL, etc.).
"""
from app.config import settings
from app.dbs.db import Base, SessionLocal, engine
from app.dbs.seed import seed_database


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
        print("Seed completed")
    finally:
        db.close()


if __name__ == "__main__":
    main()
