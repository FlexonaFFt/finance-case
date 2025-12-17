from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dbs.deps import get_current_user, get_db
from app.dbs.models import Client, User
from app.routes.schemas import ClientCreate, ClientOut

router = APIRouter(prefix="/clients", tags=["clients"])


def get_client_by_user(db: Session, user_id) -> Client | None:
    return db.query(Client).filter(Client.user_id == user_id).first()


@router.post("/me", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(
    payload: ClientCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClientOut:
    existing = get_client_by_user(db, user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Client profile already exists",
        )
    client = Client(user_id=user.id, full_name=payload.full_name, phone=payload.phone)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/me", response_model=ClientOut)
def get_me(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ClientOut:
    client = get_client_by_user(db, user.id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client
