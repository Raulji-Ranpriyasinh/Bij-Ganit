"""Item model (Sprint 2.5).

Prices are stored as BigInt (cents of the item's currency, matching the
reference Crater convention of `unsignedBigInteger price`).
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.currency import Currency
    from app.models.tax import Tax
    from app.models.unit import Unit


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    price: Mapped[int] = mapped_column(BigInteger, default=0)
    tax_per_item: Mapped[bool] = mapped_column(Boolean, default=False)

    unit_id: Mapped[int | None] = mapped_column(
        ForeignKey("units.id", ondelete="SET NULL"), nullable=True
    )
    currency_id: Mapped[int | None] = mapped_column(
        ForeignKey("currencies.id", ondelete="SET NULL"), nullable=True
    )
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=True
    )
    creator_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    unit: Mapped["Unit | None"] = relationship("Unit", lazy="selectin")
    currency: Mapped["Currency | None"] = relationship("Currency", lazy="selectin")
    taxes: Mapped[list["Tax"]] = relationship(
        "Tax",
        back_populates="item",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
