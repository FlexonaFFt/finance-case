import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dbs.deps import get_current_admin, get_db
from app.dbs.models import InsuranceAccount, Policy, PolicyStatus, User
from app.routes.schemas import PolicyCreate, PolicyOut

router = APIRouter(prefix="/policies", tags=["policies"])


def generate_policy_number() -> str:
    return f"POL-{uuid.uuid4().hex[:8].upper()}"


@router.post("", response_model=PolicyOut, status_code=status.HTTP_201_CREATED)
def create_policy(
    payload: PolicyCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> PolicyOut:
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    account = None
    if payload.account_id:
        account = db.get(InsuranceAccount, payload.account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Insurance account not found"
            )

    if payload.end_date <= payload.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be after start_date",
        )

    policy = Policy(
        policy_number=generate_policy_number(),
        user_id=user.id,
        type=payload.type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        premium=payload.premium,
        status=PolicyStatus.active if payload.start_date <= date.today() else PolicyStatus.draft,
        account_id=account.id if account else None,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


@router.get("", response_model=list[PolicyOut])
def list_policies(
    user_id: int | None = Query(default=None),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[PolicyOut]:
    query = db.query(Policy)
    if user_id:
        query = query.filter(Policy.user_id == user_id)
    return query.order_by(Policy.created_at.desc()).all()
