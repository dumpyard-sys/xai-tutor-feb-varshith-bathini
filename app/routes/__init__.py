from app.routes.health import router as health_router
from app.routes.items import router as items_router
from app.routes.invoices import router as invoices_router
from app.routes.products import router as products_router
from app.routes.clients import router as clients_router

__all__ = [
    "health_router",
    "items_router",
    "invoices_router",
    "products_router",
    "clients_router",
]
