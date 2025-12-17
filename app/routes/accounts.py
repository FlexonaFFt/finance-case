import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dbs.deps import get_current_user, get_db
from app.dbs.models import Account, AccountType, Client, User
from app.routes.schemas import AccountCreate, AccountOut

router = APIRouter(prefix="/accounts", tags=["accounts"])


def get_client_by_user(db: Session, user_id) -> Client | None:
    return db.query(Client).filter(Client.user_id == user_id).first()


def get_account_for_user(db: Session, user_id, account_id) -> Account | None:
    return (
        db.query(Account)
        .join(Client, Account.client_id == Client.id)
        .filter(Account.id == account_id, Client.user_id == user_id)
        .first()
    )


def parse_account_type(value: str) -> AccountType:
    try:
        return AccountType(value.lower())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid account_type",
        ) from exc


@router.post("", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccountOut:
    client = get_client_by_user(db, user.id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Create client profile first",
        )
    account_type = parse_account_type(payload.account_type)
    balance = payload.initial_balance or Decimal("0.00")
    if balance < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Initial balance must be non-negative",
        )
    account = Account(
        client_id=client.id,
        name=payload.name,
        account_type=account_type,
        currency=payload.currency.upper(),
        balance=balance,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("", response_model=list[AccountOut])
def list_accounts(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[AccountOut]:
    client = get_client_by_user(db, user.id)
    if not client:
        return []
    return db.query(Account).filter(Account.client_id == client.id).all()


@router.get("/{account_id}", response_model=AccountOut)
def get_account(
    account_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccountOut:
    account = get_account_for_user(db, user.id, account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account
