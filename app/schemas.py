from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ClientCreate(BaseModel):
    name: str
    email: str
    password: str


class AccountCreate(BaseModel):
    currency: str = "USD"
    initial_balance: int = Field(
        ge=0, default=0, description="Balance in minor units (e.g. cents)"
    )


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Transaction(BaseModel):
    id: str
    account_id: str
    amount_minor: int
    currency: str
    description: str
    occurred_at: datetime


class Account(BaseModel):
    id: str
    client_id: str
    currency: str
    balance_minor: int
    created_at: datetime


class Client(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    created_at: datetime
    accounts: List[Account] = Field(default_factory=list)


class TransactionCreate(BaseModel):
    account_id: str
    amount_minor: int = Field(description="Amount in minor units; positive=deposit, negative=withdraw")
    currency: str
    description: str


class TransferCreate(BaseModel):
    from_account_id: str
    to_account_id: str
    amount_minor: int = Field(gt=0, description="Positive amount in minor units")
    currency: str
    description: str = ""
