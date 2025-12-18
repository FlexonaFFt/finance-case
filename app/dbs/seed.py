from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.dbs.models import (
    AccountStatus,
    InsuranceAccount,
    Policy,
    PolicyStatus,
    User,
    UserRole,
)
from app.security import get_password_hash

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"
CLIENT_PASSWORD = "password123"
CLIENT_COUNT = 5
ACCOUNT_COUNT = 3


def seed_database(db: Session) -> None:
    seeded = False

    if db.query(User).count() == 0:
        admin = User(
            name="Admin",
            email=ADMIN_EMAIL,
            phone="+70000000000",
            role=UserRole.admin,
            hashed_password=get_password_hash(ADMIN_PASSWORD),
        )
        db.add(admin)
        clients: list[User] = []
        for i in range(1, CLIENT_COUNT + 1):
            user = User(
                name=f"Client {i}",
                email=f"client{i}@example.com",
                phone=f"+790000000{i:02d}",
                role=UserRole.client,
                hashed_password=get_password_hash(CLIENT_PASSWORD),
            )
            db.add(user)
            clients.append(user)
        db.flush()
        seeded = True
    else:
        clients = db.query(User).filter(User.role == UserRole.client).all()

    if db.query(InsuranceAccount).count() == 0:
        statuses = [AccountStatus.small, AccountStatus.medium, AccountStatus.large]
        balances = {
            AccountStatus.small: Decimal("50000.00"),
            AccountStatus.medium: Decimal("200000.00"),
            AccountStatus.large: Decimal("1000000.00"),
        }
        for i in range(1, ACCOUNT_COUNT + 1):
            status = statuses[(i - 1) % len(statuses)]
            account = InsuranceAccount(
                account_number=f"ACC-{i:04d}",
                balance=balances[status],
                status=status,
            )
            db.add(account)
        db.flush()
        seeded = True

    if db.query(Policy).count() == 0 and clients:
        accounts = db.query(InsuranceAccount).all()
        today = date.today()
        for idx, client in enumerate(clients, start=1):
            account = accounts[(idx - 1) % len(accounts)] if accounts else None
            policy = Policy(
                policy_number=f"POL-SEED-{idx:04d}",
                user_id=client.id,
                type="health" if idx % 2 == 0 else "auto",
                start_date=today,
                end_date=today + timedelta(days=365),
                premium=Decimal("12000.00") + Decimal(idx * 500),
                status=PolicyStatus.active,
                account_id=account.id if account else None,
            )
            db.add(policy)
        seeded = True

    if seeded:
        db.commit()
