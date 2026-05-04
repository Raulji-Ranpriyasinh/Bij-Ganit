from fastapi import APIRouter

from app.api.v1 import (
    auth,
    companies,
    customers,
    items,
    invoices,
    estimates,
    payments,
    expenses,
    lookups,
    tax_types,
    units,
    users,
    dashboard,
    cron,
    custom_fields,
    pdf,
)

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(auth.router)
api_v1_router.include_router(companies.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(customers.router)
api_v1_router.include_router(items.router)
api_v1_router.include_router(invoices.router)
api_v1_router.include_router(estimates.router)
api_v1_router.include_router(payments.router)
api_v1_router.include_router(expenses.router)
api_v1_router.include_router(expenses.categories_router)
api_v1_router.include_router(units.router)
api_v1_router.include_router(tax_types.router)
api_v1_router.include_router(lookups.router)
api_v1_router.include_router(dashboard.router)
api_v1_router.include_router(cron.router)
api_v1_router.include_router(custom_fields.router)
api_v1_router.include_router(pdf.router)
api_v1_router.include_router(pdf.public_router)