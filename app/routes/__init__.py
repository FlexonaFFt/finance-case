from app.routes.accounts import router as accounts_router
from app.routes.auth import router as auth_router
from app.routes.transactions import router as transactions_router

__all__ = ["accounts_router", "auth_router", "transactions_router"]
