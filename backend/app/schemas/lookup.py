"""Response schemas for the lookup endpoints (Sprint 2.11)."""

from pydantic import BaseModel, ConfigDict


class CountryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    phonecode: int


class CurrencyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    symbol: str | None = None
    precision: int
    thousand_separator: str
    decimal_separator: str
    swap_currency_symbol: bool


class TimezoneOut(BaseModel):
    key: str
    label: str


class DateFormatOut(BaseModel):
    carbon_format: str
    moment_format: str
    display: str
