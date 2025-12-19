import random
from datetime import datetime, timedelta
from typing import List, Optional

import psycopg

from app.dbs.postgres import get_conn
from app.utils.ids import generate_short_id


def create_client(name: str, email: str, password_hash: str) -> dict:
    client_id = generate_short_id()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO clients (id, name, email, password_hash, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                """,
                (client_id, name, email, password_hash),
            )
    return get_client_by_id(client_id)


def get_client_by_email(email: str) -> Optional[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, email, password_hash, created_at FROM clients WHERE email = %s",
                (email,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "password_hash": row[3],
                "created_at": row[4],
            }


def get_client_by_id(client_id: str) -> Optional[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, email, password_hash, created_at FROM clients WHERE id = %s",
                (client_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "password_hash": row[3],
                "created_at": row[4],
            }


def list_accounts_by_client(client_id: str) -> List[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, client_id, currency, balance_minor, created_at
                FROM accounts
                WHERE client_id = %s
                ORDER BY created_at DESC
                """,
                (client_id,),
            )
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "client_id": r[1],
                    "currency": r[2],
                    "balance_minor": r[3],
                    "created_at": r[4],
                }
                for r in rows
            ]


def create_account(client_id: str, currency: str, initial_balance: int) -> dict:
    account_id = generate_short_id()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO accounts (id, client_id, currency, balance_minor, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                """,
                (account_id, client_id, currency, initial_balance),
            )
            _seed_transactions(conn, account_id, currency)
    return get_account_by_id(account_id)


def get_account_by_id(account_id: str) -> Optional[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, client_id, currency, balance_minor, created_at
                FROM accounts WHERE id = %s
                """,
                (account_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "client_id": row[1],
                "currency": row[2],
                "balance_minor": row[3],
                "created_at": row[4],
            }


def list_transactions(account_id: str) -> List[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, account_id, amount_minor, currency, description, occurred_at, created_at
                FROM transactions
                WHERE account_id = %s
                ORDER BY occurred_at DESC
                """,
                (account_id,),
            )
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "account_id": r[1],
                    "amount_minor": r[2],
                    "currency": r[3],
                    "description": r[4],
                    "occurred_at": r[5],
                    "created_at": r[6],
                }
                for r in rows
            ]


def _seed_transactions(conn: psycopg.Connection, account_id: str, currency: str) -> None:
    txs = []
    for _ in range(random.randint(1, 3)):
        txs.append(
            (
                generate_short_id(),
                account_id,
                random.randint(-20000, 20000),
                currency,
                random.choice(
                    ["Groceries", "Coffee", "Subscription", "Salary", "Transfer", "Utilities"]
                ),
                datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                datetime.utcnow(),
            )
        )
    if not txs:
        return
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO transactions (id, account_id, amount_minor, currency, description, occurred_at, created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            txs,
        )
