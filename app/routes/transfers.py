import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, aliased

from app.dbs.deps import get_current_user, get_db
from app.dbs.models import (
    Account,
    Client,
    Transaction,
    TransferRequest,
    TransferStatus,
    User,
)
from app.routes.schemas import TransferRequestCreate, TransferRequestOut

router = APIRouter(prefix="/transfers", tags=["transfers"])

DEFAULT_TRANSFER_LIMIT = Decimal("50000.00")


def get_client_by_user(db: Session, user_id) -> Client | None:
    return db.query(Client).filter(Client.user_id == user_id).first()


def get_account(db: Session, account_id: uuid.UUID) -> Account | None:
    return db.query(Account).filter(Account.id == account_id).first()


def validate_currency(*values: str) -> None:
    normalized = {value.upper() for value in values}
    if len(normalized) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Currency mismatch",
        )


@router.post("/requests", response_model=TransferRequestOut, status_code=201)
def create_transfer_request(
    payload: TransferRequestCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransferRequestOut:
    client = get_client_by_user(db, user.id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Create client profile first",
        )

    from_account = get_account(db, payload.from_account_id)
    to_account = get_account(db, payload.to_account_id)
    if not from_account or not to_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    owns_from = from_account.client_id == client.id
    owns_to = to_account.client_id == client.id
    if not (owns_from or owns_to):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    if payload.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be positive"
        )

    validate_currency(from_account.currency, to_account.currency, payload.currency)

    transfer_limit = from_account.transfer_limit or DEFAULT_TRANSFER_LIMIT
    if payload.amount > transfer_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transfer amount exceeds limit",
        )

    transfer_request = TransferRequest(
        from_account_id=from_account.id,
        to_account_id=to_account.id,
        requested_by_client_id=client.id,
        amount=payload.amount,
        currency=payload.currency.upper(),
        status=TransferStatus.pending,
    )
    db.add(transfer_request)
    db.commit()
    db.refresh(transfer_request)
    return transfer_request


@router.get("/requests", response_model=list[TransferRequestOut])
def list_transfer_requests(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[TransferRequestOut]:
    client = get_client_by_user(db, user.id)
    if not client:
        return []

    from_account = aliased(Account)
    to_account = aliased(Account)
    return (
        db.query(TransferRequest)
        .join(from_account, TransferRequest.from_account_id == from_account.id)
        .join(to_account, TransferRequest.to_account_id == to_account.id)
        .filter(or_(from_account.client_id == client.id, to_account.client_id == client.id))
        .order_by(TransferRequest.created_at.desc())
        .all()
    )


def get_transfer_request(db: Session, transfer_id: uuid.UUID) -> TransferRequest | None:
    return db.query(TransferRequest).filter(TransferRequest.id == transfer_id).first()


@router.post("/requests/{transfer_id}/approve", response_model=TransferRequestOut)
def approve_transfer(
    transfer_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransferRequestOut:
    client = get_client_by_user(db, user.id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Create client profile first",
        )

    transfer_request = get_transfer_request(db, transfer_id)
    if not transfer_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if transfer_request.status != TransferStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Request already processed"
        )

    from_account = get_account(db, transfer_request.from_account_id)
    to_account = get_account(db, transfer_request.to_account_id)
    if not from_account or not to_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    if from_account.client_id != client.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    transfer_limit = from_account.transfer_limit or DEFAULT_TRANSFER_LIMIT
    if transfer_request.amount > transfer_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transfer amount exceeds limit",
        )

    if from_account.balance < transfer_request.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds"
        )

    with db.begin():
        from_account.balance -= transfer_request.amount
        to_account.balance += transfer_request.amount
        transfer_request.status = TransferStatus.approved
        transfer_request.approved_at = datetime.utcnow()
        db.add(
            Transaction(
                account_id=from_account.id,
                amount=-transfer_request.amount,
                currency=transfer_request.currency,
                reference_type="transfer",
                reference_id=transfer_request.id,
                description="Transfer out",
            )
        )
        db.add(
            Transaction(
                account_id=to_account.id,
                amount=transfer_request.amount,
                currency=transfer_request.currency,
                reference_type="transfer",
                reference_id=transfer_request.id,
                description="Transfer in",
            )
        )

    db.refresh(transfer_request)
    return transfer_request


@router.post("/requests/{transfer_id}/decline", response_model=TransferRequestOut)
def decline_transfer(
    transfer_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransferRequestOut:
    client = get_client_by_user(db, user.id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Create client profile first",
        )

    transfer_request = get_transfer_request(db, transfer_id)
    if not transfer_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if transfer_request.status != TransferStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Request already processed"
        )

    from_account = get_account(db, transfer_request.from_account_id)
    if not from_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    if from_account.client_id != client.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    transfer_request.status = TransferStatus.declined
    db.commit()
    db.refresh(transfer_request)
    return transfer_request
