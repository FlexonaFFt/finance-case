import random
import logging
from datetime import datetime, timedelta
from typing import List, Optional

import psycopg
from psycopg import errors

from app.dbs.postgres import get_conn
from app.utils.ids import generate_account_id, generate_short_id
from app.core.security import hash_password
from app.dbs.mongo import transfers_collection

logger = logging.getLogger(__name__)


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


def create_account(client_id: str, currency: str, initial_balance: int, seed: bool = True) -> dict:
    for _ in range(10):
        account_id = generate_account_id()
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO accounts (id, client_id, currency, balance_minor, created_at)
                        VALUES (%s, %s, %s, %s, NOW())
                        """,
                        (account_id, client_id, currency, initial_balance),
                    )
                    if seed:
                        _seed_transactions(conn, account_id, currency)
            break
        except errors.UniqueViolation:
            continue
    else:
        raise RuntimeError("Could not generate unique account number after multiple attempts")
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


def create_transaction(account_id: str, amount_minor: int, currency: str, description: str) -> dict:
    tx_id = generate_short_id()
    now = datetime.utcnow()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT currency, balance_minor FROM accounts WHERE id = %s FOR UPDATE",
                (account_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("Account not found")
            account_currency, balance_minor = row
            if account_currency != currency:
                raise ValueError("Currency mismatch")
            new_balance = balance_minor + amount_minor
            cur.execute(
                """
                INSERT INTO transactions (id, account_id, amount_minor, currency, description, occurred_at, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                """,
                (tx_id, account_id, amount_minor, currency, description, now, now),
            )
            cur.execute(
                "UPDATE accounts SET balance_minor = %s WHERE id = %s",
                (new_balance, account_id),
            )
    return {
        "id": tx_id,
        "account_id": account_id,
        "amount_minor": amount_minor,
        "currency": currency,
        "description": description,
        "occurred_at": now,
        "created_at": now,
    }


def create_transfer(from_account_id: str, to_account_id: str, amount_minor: int, currency: str, description: str) -> dict:
    """
    Move money between accounts with same currency. Creates transfer row and two transactions (debit/credit).
    """
    transfer_id = generate_short_id()
    now = datetime.utcnow()
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Lock both accounts
            cur.execute(
                "SELECT id, currency, balance_minor FROM accounts WHERE id IN (%s,%s) ORDER BY id FOR UPDATE",
                (from_account_id, to_account_id),
            )
            rows = cur.fetchall()
            if len(rows) != 2:
                raise ValueError("One of the accounts not found")
            accounts = {r[0]: {"currency": r[1], "balance": r[2]} for r in rows}
            if accounts[from_account_id]["currency"] != accounts[to_account_id]["currency"]:
                raise ValueError("Currency mismatch between accounts")
            if accounts[from_account_id]["currency"] != currency:
                raise ValueError("Currency mismatch with payload")
            new_balance_from = accounts[from_account_id]["balance"] - amount_minor
            new_balance_to = accounts[to_account_id]["balance"] + amount_minor
            # Insert transfer
            cur.execute(
                """
                INSERT INTO transfers (id, from_account_id, to_account_id, amount_minor, currency, description, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                """,
                (transfer_id, from_account_id, to_account_id, amount_minor, currency, description, now),
            )
            # Insert debit and credit transactions
            cur.executemany(
                """
                INSERT INTO transactions (id, account_id, amount_minor, currency, description, occurred_at, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                """,
                [
                    (
                        generate_short_id(),
                        from_account_id,
                        -amount_minor,
                        currency,
                        f"Transfer to {to_account_id}. {description}".strip(),
                        now,
                        now,
                    ),
                    (
                        generate_short_id(),
                        to_account_id,
                        amount_minor,
                        currency,
                        f"Transfer from {from_account_id}. {description}".strip(),
                        now,
                        now,
                    ),
                ],
            )
            # Update balances
            cur.execute(
                "UPDATE accounts SET balance_minor = %s WHERE id = %s",
                (new_balance_from, from_account_id),
            )
            cur.execute(
                "UPDATE accounts SET balance_minor = %s WHERE id = %s",
                (new_balance_to, to_account_id),
            )
    # Log to Mongo (best-effort)
    try:
        transfers_collection.insert_one(
            {
                "_id": transfer_id,
                "from_account_id": from_account_id,
                "to_account_id": to_account_id,
                "amount_minor": amount_minor,
                "currency": currency,
                "description": description,
                "created_at": now,
            }
        )
    except Exception:
        logger.warning("Failed to log transfer %s to Mongo", transfer_id)
    return {
        "id": transfer_id,
        "from_account_id": from_account_id,
        "to_account_id": to_account_id,
        "amount_minor": amount_minor,
        "currency": currency,
        "description": description,
        "created_at": now,
    }
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


def ensure_passwords(default_password: str) -> None:
    """Fill missing password_hash for seeded clients."""
    hashed = hash_password(default_password)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE clients SET password_hash = %s WHERE password_hash IS NULL",
                (hashed,),
            )
