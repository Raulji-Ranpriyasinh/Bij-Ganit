"""Currency model (Sprint 2.1)."""

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Currency(Base):
    __tablename__ = "currencies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(16))
    symbol: Mapped[str | None] = mapped_column(String(16), nullable=True)
    precision: Mapped[int] = mapped_column(Integer, default=2)
    thousand_separator: Mapped[str] = mapped_column(String(4), default=",")
    decimal_separator: Mapped[str] = mapped_column(String(4), default=".")
    swap_currency_symbol: Mapped[bool] = mapped_column(Boolean, default=False)
