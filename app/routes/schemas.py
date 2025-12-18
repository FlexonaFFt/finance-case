from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8)
    phone: str = Field(min_length=5, max_length=32)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    phone: str | None
    role: str
    created_at: datetime


class InsuranceAccountCreate(BaseModel):
    account_number: str = Field(min_length=4, max_length=32)
    status: str = Field(default="small")


class InsuranceAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_number: str
    balance: Decimal
    status: str
    created_at: datetime


class PolicyCreate(BaseModel):
    user_id: int
    type: str = Field(min_length=3, max_length=50)
    start_date: date
    end_date: date
    premium: Decimal
    account_id: int | None = None


class PolicyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    policy_number: str
    user_id: int
    type: str
    start_date: date
    end_date: date
    premium: Decimal
    status: str
    account_id: int | None
    created_at: datetime


class ClaimCreate(BaseModel):
    policy_id: int
    amount: Decimal
    date_filed: date


class ClaimOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    claim_number: str
    policy_id: int
    date_filed: date
    amount: Decimal
    status: str
    created_at: datetime
