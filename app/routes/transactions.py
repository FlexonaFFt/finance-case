import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dbs.deps import get_current_user, get_db
from app.dbs.models import Account, Client, Transaction, User
from app.routes.schemas import TransactionOut

router = APIRouter(prefix="/transactions", tags=["transactions"])


def get_client_by_user(db: Session, user_id) -> Client | None:
    return db.query(Client).filter(Client.user_id == user_id).first()


@router.get("", response_model=list[TransactionOut])
def list_transactions(
    account_id: uuid.UUID | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TransactionOut]:
    client = get_client_by_user(db, user.id)
    if not client:
        return []

    query = (
        db.query(Transaction)
        .join(Account, Transaction.account_id == Account.id)
        .filter(Account.client_id == client.id)
        .order_by(Transaction.created_at.desc())
    )
    if account_id:
        account = (
            db.query(Account)
            .filter(Account.id == account_id, Account.client_id == client.id)
            .first()
        )
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
            )
        query = query.filter(Transaction.account_id == account_id)

    return query.all()
