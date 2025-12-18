from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dbs.deps import get_current_admin, get_db
from app.dbs.models import AccountStatus, InsuranceAccount, User
from app.routes.schemas import InsuranceAccountCreate, InsuranceAccountOut

router = APIRouter(prefix="/insurance-accounts", tags=["insurance_accounts"])

STATUS_BALANCES = {
    AccountStatus.small: Decimal("50000.00"),
    AccountStatus.medium: Decimal("200000.00"),
    AccountStatus.large: Decimal("1000000.00"),
}


@router.post("", response_model=InsuranceAccountOut, status_code=status.HTTP_201_CREATED)
def create_insurance_account(
    payload: InsuranceAccountCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> InsuranceAccountOut:
    existing = (
        db.query(InsuranceAccount)
        .filter(InsuranceAccount.account_number == payload.account_number)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account number already exists",
        )

    try:
        status_value = AccountStatus(payload.status.lower())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid status, choose small|medium|large",
        ) from exc

    balance = STATUS_BALANCES[status_value]

    account = InsuranceAccount(
        account_number=payload.account_number,
        balance=balance,
        status=status_value,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("", response_model=list[InsuranceAccountOut])
def list_insurance_accounts(
    admin: User = Depends(get_current_admin), db: Session = Depends(get_db)
) -> list[InsuranceAccountOut]:
    return db.query(InsuranceAccount).order_by(InsuranceAccount.created_at.desc()).all()
