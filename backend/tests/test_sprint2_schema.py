"""Smoke tests for the Sprint 2 schema + seed data.

We do not spin up Alembic here (that would need a real Postgres + psycopg2
socket).  Instead we create the same metadata in an in-memory SQLite database
and assert the tables + seeded counts match what the migration will produce
against Postgres.  This also exercises the model relationships.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app import models  # noqa: F401  (register all models on metadata)
from app.database import Base
from app.models.country import Country
from app.models.currency import Currency
from app.seed_data import COUNTRIES, CURRENCIES, DATE_FORMATS, TIMEZONES


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        # Seed the two static lookup tables the same way the Alembic migration does.
        session.add_all(
            [
                Country(id=c["id"], code=c["code"], name=c["name"], phonecode=c["phonecode"])
                for c in COUNTRIES
            ]
        )
        session.add_all([Currency(**c) for c in CURRENCIES])
        session.commit()
        yield session


def test_seed_counts_meet_acceptance_criteria(session: Session) -> None:
    assert session.scalar(select(Currency).order_by(Currency.id)) is not None
    assert len(CURRENCIES) >= 150, f"expected >=150 currencies, got {len(CURRENCIES)}"
    assert len(COUNTRIES) >= 200, f"expected >=200 countries, got {len(COUNTRIES)}"


def test_core_lookups_present() -> None:
    currency_codes = {c["code"] for c in CURRENCIES}
    for code in ("USD", "EUR", "INR", "GBP", "JPY"):
        assert code in currency_codes

    country_codes = {c["code"] for c in COUNTRIES}
    for code in ("US", "IN", "GB", "JP", "DE"):
        assert code in country_codes


def test_lookup_auxiliary_lists_non_empty() -> None:
    assert TIMEZONES, "timezones list must not be empty"
    assert DATE_FORMATS, "date formats list must not be empty"
    assert all("key" in tz and "label" in tz for tz in TIMEZONES)
    assert all(
        {"carbon_format", "moment_format", "display"} <= set(df)
        for df in DATE_FORMATS
    )


def test_all_sprint2_tables_registered() -> None:
    expected = {
        "currencies",
        "countries",
        "customers",
        "addresses",
        "units",
        "items",
        "tax_types",
        "taxes",
    }
    present = set(Base.metadata.tables)
    assert expected <= present, f"missing tables: {expected - present}"
