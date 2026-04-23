"""Expose every model so Alembic's autogenerate sees them."""

from app.models.address import Address  # noqa: F401
from app.models.company import Company, UserCompany  # noqa: F401
from app.models.country import Country  # noqa: F401
from app.models.currency import Currency  # noqa: F401
from app.models.customer import Customer  # noqa: F401
from app.models.item import Item  # noqa: F401
from app.models.tax import Tax, TaxType  # noqa: F401
from app.models.unit import Unit  # noqa: F401
from app.models.user import User  # noqa: F401
