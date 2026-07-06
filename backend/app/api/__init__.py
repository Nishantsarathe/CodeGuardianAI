"""API package — HTTP routers are exposed from here."""
from .routes.auth import router as auth_router
from .routes.projects import router as projects_router
from .routes.analyses import router as analyses_router
from .routes.agents import router as agents_router
from .routes.chat import router as chat_router
from .routes.reports import router as reports_router
from .routes.uploads import router as uploads_router
from .routes.dashboard import router as dashboard_router
from .routes.users import router as users_router

__all__ = [
    "auth_router",
    "projects_router",
    "analyses_router",
    "agents_router",
    "chat_router",
    "reports_router",
    "uploads_router",
    "dashboard_router",
    "users_router",
]
