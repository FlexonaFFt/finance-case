from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.security import JWT_ALGORITHM, JWT_SECRET, create_access_token, verify_password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_client(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        client_id: str = payload.get("sub")
        if client_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    from app.dbs.repo import get_client_by_id

    client = get_client_by_id(client_id)
    if client is None:
        raise credentials_exception
    return client
