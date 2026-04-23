"""Static seed data bundled with the backend (Sprint 2.1).

These lists are inserted once by the Alembic migration that creates the
master-data tables, and re-used at runtime by the lookup endpoints
(`GET /api/v1/currencies`, `GET /api/v1/countries`, ...).  Keeping them
as Python data (not a SQL dump) means the same source of truth works
for both paths.
"""

from app.seed_data.countries import COUNTRIES
from app.seed_data.currencies import CURRENCIES
from app.seed_data.date_formats import DATE_FORMATS
from app.seed_data.timezones import TIMEZONES

__all__ = ["COUNTRIES", "CURRENCIES", "TIMEZONES", "DATE_FORMATS"]
