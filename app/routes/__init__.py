from app.routes.auth import router as auth_router
from app.routes.insurance_accounts import router as insurance_accounts_router
from app.routes.policies import router as policies_router

__all__ = [
    "auth_router",
    "insurance_accounts_router",
    "policies_router",
]
