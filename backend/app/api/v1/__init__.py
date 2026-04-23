"""v1 API router aggregation."""

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    companies,
    customers,
    items,
    lookups,
    tax_types,
    units,
    users,
)

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(auth.router)
api_v1_router.include_router(companies.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(customers.router)
api_v1_router.include_router(items.router)
api_v1_router.include_router(units.router)
api_v1_router.include_router(tax_types.router)
api_v1_router.include_router(lookups.router)
