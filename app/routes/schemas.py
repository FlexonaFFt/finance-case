import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    created_at: datetime


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    currency: str = Field(min_length=1, max_length=10)
    balance: Decimal | None = None


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    currency: str | None = Field(default=None, min_length=1, max_length=10)
    balance: Decimal | None = None


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    currency: str
    balance: Decimal
    created_at: datetime


class TransactionCreate(BaseModel):
    account_id: uuid.UUID
    amount: Decimal
    currency: str = Field(min_length=1, max_length=10)
    occurred_at: datetime
    description: str | None = Field(default=None, max_length=255)
    category: str | None = Field(default=None, max_length=120)


class TransactionUpdate(BaseModel):
    account_id: uuid.UUID | None = None
    amount: Decimal | None = None
    currency: str | None = Field(default=None, min_length=1, max_length=10)
    occurred_at: datetime | None = None
    description: str | None = Field(default=None, max_length=255)
    category: str | None = Field(default=None, max_length=120)


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    amount: Decimal
    currency: str
    occurred_at: datetime
    description: str | None
    category: str | None
    created_at: datetime
