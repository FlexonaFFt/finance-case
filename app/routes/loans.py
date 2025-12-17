import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dbs.deps import get_current_user, get_db
from app.dbs.models import Account, Client, Loan, Transaction, User
from app.routes.schemas import LoanCreate, LoanOut

router = APIRouter(prefix="/loans", tags=["loans"])

DEFAULT_LOAN_LIMIT = Decimal("50000.00")
DEFAULT_LOAN_RATE = Decimal("0.1000")
DEFAULT_TERM_MONTHS = 12


def get_client_by_user(db: Session, user_id) -> Client | None:
    return db.query(Client).filter(Client.user_id == user_id).first()


def get_account_for_user(db: Session, user_id, account_id: uuid.UUID) -> Account | None:
    return (
        db.query(Account)
        .join(Client, Account.client_id == Client.id)
        .filter(Account.id == account_id, Client.user_id == user_id)
        .first()
    )


@router.post("", response_model=LoanOut, status_code=status.HTTP_201_CREATED)
def create_loan(
    payload: LoanCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LoanOut:
    client = get_client_by_user(db, user.id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Create client profile first",
        )

    account = get_account_for_user(db, user.id, payload.account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    if payload.principal <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be positive"
        )

    if payload.principal > DEFAULT_LOAN_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Loan amount exceeds limit",
        )

    rate = payload.rate or DEFAULT_LOAN_RATE
    term = payload.term_months or DEFAULT_TERM_MONTHS
    if payload.currency.upper() != account.currency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Currency mismatch"
        )

    with db.begin():
        loan = Loan(
            client_id=client.id,
            account_id=account.id,
            principal=payload.principal,
            currency=payload.currency.upper(),
            rate=rate,
            term_months=term,
        )
        db.add(loan)
        db.flush()
        account.balance += payload.principal
        db.add(
            Transaction(
                account_id=account.id,
                amount=payload.principal,
                currency=payload.currency.upper(),
                reference_type="loan_disbursement",
                reference_id=loan.id,
                description="Loan disbursement",
            )
        )

    db.refresh(loan)
    return loan


@router.get("", response_model=list[LoanOut])
def list_loans(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[LoanOut]:
    client = get_client_by_user(db, user.id)
    if not client:
        return []
    return db.query(Loan).filter(Loan.client_id == client.id).all()
