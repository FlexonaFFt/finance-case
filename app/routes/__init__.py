from app.routes.auth import router as auth_router
from app.routes.accounts import router as accounts_router
from app.routes.clients import router as clients_router
from app.routes.loans import router as loans_router
from app.routes.transactions import router as transactions_router
from app.routes.transfers import router as transfers_router

__all__ = [
    "auth_router",
    "clients_router",
    "accounts_router",
    "transfers_router",
    "transactions_router",
    "loans_router",
]
