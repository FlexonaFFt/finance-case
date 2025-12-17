from decimal import Decimal

from sqlalchemy.orm import Session

from app.dbs.models import Account, AccountType, Client, TreasuryAccount, User
from app.security import get_password_hash

SEED_USERS_COUNT = 10
SEED_TREASURY_COUNT = 10
SEED_PASSWORD = "password123"


def seed_database(db: Session) -> None:
    seeded = False
    clients: list[Client] = []

    if db.query(Client).count() == 0:
        users: list[User] = []
        for i in range(1, SEED_USERS_COUNT + 1):
            user = User(
                email=f"user{i}@example.com",
                hashed_password=get_password_hash(SEED_PASSWORD),
            )
            db.add(user)
            users.append(user)
        db.flush()

        for i, user in enumerate(users, start=1):
            client = Client(
                user_id=user.id,
                full_name=f"Client {i}",
                phone=f"+790000000{i:02d}",
            )
            db.add(client)
            clients.append(client)
        db.flush()
        seeded = True

    if db.query(Account).count() == 0:
        if not clients:
            clients = (
                db.query(Client).order_by(Client.created_at).limit(SEED_USERS_COUNT).all()
            )
        for i, client in enumerate(clients, start=1):
            balance = Decimal("10000.00") * i
            account = Account(
                client_id=client.id,
                name=f"Main Account {i}",
                account_type=AccountType.checking,
                currency="RUB",
                balance=balance,
            )
            db.add(account)
        seeded = True

    if db.query(TreasuryAccount).count() == 0:
        for i in range(1, SEED_TREASURY_COUNT + 1):
            balance = Decimal("1000000.00") * i
            treasury = TreasuryAccount(
                name=f"Treasury Account {i}",
                currency="RUB",
                balance=balance,
                purpose="seed",
            )
            db.add(treasury)
        seeded = True

    if seeded:
        db.commit()
