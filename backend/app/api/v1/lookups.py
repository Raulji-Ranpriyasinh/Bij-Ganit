"""Static-lookup endpoints (Sprint 2.11).

These simply echo bundled seed data and do not require authentication — the
Laravel reference also makes them public because the login screen itself
populates its country/currency dropdowns from them.
"""

from fastapi import APIRouter

from app.schemas.lookup import CountryOut, CurrencyOut, DateFormatOut, TimezoneOut
from app.seed_data import COUNTRIES, CURRENCIES, DATE_FORMATS, TIMEZONES

router = APIRouter(tags=["lookups"])


@router.get("/countries", response_model=list[CountryOut])
async def list_countries() -> list[dict]:
    return COUNTRIES


@router.get("/currencies", response_model=list[CurrencyOut])
async def list_currencies() -> list[dict]:
    # Inject synthetic ids matching the order the migration inserted them so
    # the frontend can key dropdowns by id.
    return [{"id": idx + 1, **entry} for idx, entry in enumerate(CURRENCIES)]


@router.get("/timezones", response_model=list[TimezoneOut])
async def list_timezones() -> list[dict]:
    return TIMEZONES


@router.get("/date/formats", response_model=list[DateFormatOut])
async def list_date_formats() -> list[dict]:
    return DATE_FORMATS
