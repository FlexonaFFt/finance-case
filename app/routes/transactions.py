import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dbs.deps import get_current_user, get_db
from app.dbs.models import Account, Transaction, User
from app.routes.schemas import TransactionCreate, TransactionOut, TransactionUpdate

router = APIRouter(prefix="/transactions", tags=["transactions"])


def get_user_transaction(db: Session, user: User, transaction_id: uuid.UUID) -> Transaction | None:
    return (
        db.query(Transaction)
        .join(Account, Transaction.account_id == Account.id)
        .filter(Transaction.id == transaction_id, Account.user_id == user.id)
        .first()
    )


def get_user_account(db: Session, user: User, account_id: uuid.UUID) -> Account | None:
    return (
        db.query(Account)
        .filter(Account.id == account_id, Account.user_id == user.id)
        .first()
    )


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TransactionOut:
    account = get_user_account(db, user, payload.account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    transaction = Transaction(
        account_id=payload.account_id,
        amount=payload.amount,
        currency=payload.currency,
        occurred_at=payload.occurred_at,
        description=payload.description,
        category=payload.category,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("", response_model=list[TransactionOut])
def list_transactions(
    account_id: uuid.UUID | None = None,
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    category: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TransactionOut]:
    query = (
        db.query(Transaction)
        .join(Account, Transaction.account_id == Account.id)
        .filter(Account.user_id == user.id)
    )
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    if from_date:
        query = query.filter(Transaction.occurred_at >= from_date)
    if to_date:
        query = query.filter(Transaction.occurred_at <= to_date)
    if category:
        query = query.filter(Transaction.category == category)

    transactions = (
        query.order_by(Transaction.occurred_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return transactions


@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction_detail(
    transaction_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TransactionOut:
    transaction = get_user_transaction(db, user, transaction_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return transaction


@router.patch("/{transaction_id}", response_model=TransactionOut)
def update_transaction(
    transaction_id: uuid.UUID,
    payload: TransactionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TransactionOut:
    transaction = get_user_transaction(db, user, transaction_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    data = payload.model_dump(exclude_unset=True)
    if "account_id" in data:
        account = get_user_account(db, user, data["account_id"])
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
            )

    for field, value in data.items():
        setattr(transaction, field, value)

    db.commit()
    db.refresh(transaction)
    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    transaction = get_user_transaction(db, user, transaction_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    db.delete(transaction)
    db.commit()
    return None
