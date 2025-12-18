import enum
import random
from decimal import Decimal
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dbs.db import Base


class UserRole(enum.Enum):
    admin = "admin"
    client = "client"


class AccountStatus(enum.Enum):
    small = "small"
    medium = "medium"
    large = "large"


class PolicyStatus(enum.Enum):
    draft = "draft"
    active = "active"
    expired = "expired"
    cancelled = "cancelled"


class ClaimStatus(enum.Enum):
    open = "open"
    approved = "approved"
    rejected = "rejected"
    paid = "paid"


def _random_numeric_id(length: int) -> int:
    start = 10 ** (length - 1)
    end = (10**length) - 1
    return random.randint(start, end)


def random_user_id() -> int:
    return _random_numeric_id(6)


def random_account_id() -> int:
    return _random_numeric_id(5)


def random_policy_id() -> int:
    return _random_numeric_id(5)


def random_claim_id() -> int:
    return _random_numeric_id(9)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, default=random_user_id)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(
        String(320), unique=True, index=True, nullable=False
    )
    phone: Mapped[str | None] = mapped_column(String(32))
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.client, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    policies: Mapped[list["Policy"]] = relationship(back_populates="user")


class InsuranceAccount(Base):
    __tablename__ = "insurance_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, default=random_account_id)
    account_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    balance: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0.00"), nullable=False
    )
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus), default=AccountStatus.small, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(primary_key=True, default=random_policy_id)
    policy_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    premium: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[PolicyStatus] = mapped_column(
        Enum(PolicyStatus), default=PolicyStatus.draft, nullable=False
    )
    account_id: Mapped[int | None] = mapped_column(
        ForeignKey("insurance_accounts.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="policies")
    account: Mapped[InsuranceAccount | None] = relationship()
    claims: Mapped[list["Claim"]] = relationship(back_populates="policy")


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True, default=random_claim_id)
    policy_id: Mapped[int] = mapped_column(
        ForeignKey("policies.id"), nullable=False
    )
    claim_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    date_filed: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[ClaimStatus] = mapped_column(
        Enum(ClaimStatus), default=ClaimStatus.open, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    policy: Mapped[Policy] = relationship(back_populates="claims")
