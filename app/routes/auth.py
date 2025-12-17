from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dbs.deps import get_current_user, get_db
from app.dbs.models import Account, AccountType, Client, User
from app.routes.schemas import LoginRequest, RegisterRequest, Token, UserOut
from app.security import create_access_token, get_password_hash, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, email: str, password: str, *, commit: bool = True) -> User:
    user = User(email=email, hashed_password=get_password_hash(password))
    db.add(user)
    if commit:
        db.commit()
        db.refresh(user)
    else:
        db.flush()
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def build_access_token(user: User) -> str:
    return create_access_token(subject=str(user.id))


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> UserOut:
    full_name = payload.email.split("@", maxsplit=1)[0].replace(".", " ").title()
    if not full_name:
        full_name = "Client"
    with db.begin():
        existing = get_user_by_email(db, payload.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        user = create_user(db, payload.email, payload.password, commit=False)
        client = Client(user_id=user.id, full_name=full_name)
        db.add(client)
        db.flush()
        account = Account(
            client_id=client.id,
            name="Main",
            account_type=AccountType.checking,
            currency="RUB",
            balance=Decimal("0.00"),
        )
        db.add(account)
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = build_access_token(user)
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return user
