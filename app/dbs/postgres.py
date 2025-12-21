"""
Postgres connector using psycopg (simple sync helper).
"""
import os
from dataclasses import dataclass

import psycopg


@dataclass
class PostgresSettings:
    user: str = os.getenv("POSTGRES_USER", "postgres")
    password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    host: str = os.getenv("POSTGRES_HOST", "postgres")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    db: str = os.getenv("POSTGRES_DB", "finance")

    @property
    def dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


settings = PostgresSettings()


def get_conn() -> psycopg.Connection:
    return psycopg.connect(settings.dsn, autocommit=True)
