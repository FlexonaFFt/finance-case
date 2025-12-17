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


class ClientCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=32)


class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    phone: str | None
    kyc_status: str
    created_at: datetime


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    account_type: str = Field(default="checking", max_length=32)
    currency: str = Field(default="RUB", min_length=3, max_length=3)
    initial_balance: Decimal | None = Field(default=Decimal("0.00"))


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    name: str
    account_type: str
    currency: str
    balance: Decimal
    status: str
    transfer_limit: Decimal
    created_at: datetime


class TransferRequestCreate(BaseModel):
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    amount: Decimal
    currency: str = Field(default="RUB", min_length=3, max_length=3)


class TransferRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    requested_by_client_id: uuid.UUID | None
    amount: Decimal
    currency: str
    status: str
    created_at: datetime
    approved_at: datetime | None


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    amount: Decimal
    currency: str
    reference_type: str
    reference_id: uuid.UUID | None
    description: str | None
    created_at: datetime


class LoanCreate(BaseModel):
    account_id: uuid.UUID
    principal: Decimal
    currency: str = Field(default="RUB", min_length=3, max_length=3)
    rate: Decimal | None = None
    term_months: int | None = None


class LoanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    account_id: uuid.UUID
    principal: Decimal
    currency: str
    rate: Decimal
    term_months: int
    status: str
    created_at: datetime
