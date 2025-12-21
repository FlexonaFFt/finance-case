import random
from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import create_access_token, get_current_client, verify_password
from app.core.security import hash_password
from app import dbs as repo
from app.schemas import (
    Account,
    AccountCreate,
    Client,
    ClientCreate,
    LoginRequest,
    TokenResponse,
    Transaction,
    TransactionCreate,
)

router = APIRouter()


@router.post("/clients/login", response_model=TokenResponse, tags=["auth"])
def login(payload: LoginRequest) -> TokenResponse:
    client = repo.get_client_by_email(payload.email)
    if client is None:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if not verify_password(payload.password, client.get("password_hash") or ""):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token({"sub": client["id"]})
    return TokenResponse(access_token=token)


@router.post("/clients/register", response_model=Client, tags=["clients"])
def create_client(payload: ClientCreate) -> Client:
    if payload.email and repo.get_client_by_email(payload.email):
        raise HTTPException(status_code=400, detail="Email already exists")
    password_hash = hash_password(payload.password)
    client = repo.create_client(name=payload.name, email=payload.email, password_hash=password_hash)
    # Auto-create 1-3 accounts with random balances
    for _ in range(random.randint(1, 3)):
        repo.create_account(
            client_id=client["id"],
            currency=random.choice(["USD", "EUR", "GBP"]),
            initial_balance=random.randint(5_000, 200_000),
        )
    accounts = [Account(**acc) for acc in repo.list_accounts_by_client(client["id"])]
    return Client(**client, accounts=accounts)


@router.get("/clients/me", response_model=Client, tags=["clients"])
def get_me(current=Depends(get_current_client)) -> Client:
    accounts = [Account(**acc) for acc in repo.list_accounts_by_client(current["id"])]
    return Client(**current, accounts=accounts)


@router.post("/clients/{client_id}/accounts", response_model=Account, tags=["accounts"])
def add_account(client_id: str, payload: AccountCreate, current=Depends(get_current_client)) -> Account:
    if current["id"] != client_id:
        raise HTTPException(status_code=403, detail="Can only create accounts for yourself")
    account = repo.create_account(client_id, payload.currency, payload.initial_balance)
    return Account(**account)


@router.get("/accounts/{account_id}/transactions", response_model=list[Transaction], tags=["accounts"])
def list_transactions(account_id: str, current=Depends(get_current_client)) -> list[Transaction]:
    account = repo.get_account_by_id(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    if account["client_id"] != current["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    txs = repo.list_transactions(account_id)
    return [Transaction(**tx) for tx in txs]


@router.post("/transactions", response_model=Transaction, tags=["accounts"])
def create_transaction(payload: TransactionCreate, current=Depends(get_current_client)) -> Transaction:
    account = repo.get_account_by_id(payload.account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    if account["client_id"] != current["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    if account["currency"] != payload.currency:
        raise HTTPException(status_code=400, detail="Currency mismatch")
    signed_amount = payload.amount_minor
    tx = repo.create_transaction(
        account_id=payload.account_id,
        amount_minor=signed_amount,
        currency=payload.currency,
        description=payload.description,
    )
    return Transaction(**tx)
