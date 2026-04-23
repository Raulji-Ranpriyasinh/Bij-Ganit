"""TaxType + Tax models (Sprint 2.7).

`Tax` has polymorphic (nullable) FKs to invoice/estimate/item.  Invoice and
estimate tables do not yet exist (they will land in later sprints); for now
the columns are plain nullable Integers without a real DB-level FK, so the
migration stays runnable.  Once the parent tables land we can add the
constraints via a follow-up migration.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.item import Item


class TaxType(Base):
    __tablename__ = "tax_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    compound_tax: Mapped[bool] = mapped_column(Boolean, default=False)
    collective_tax: Mapped[bool] = mapped_column(Boolean, default=False)
    type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Tax(Base):
    __tablename__ = "taxes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    amount: Mapped[int] = mapped_column(BigInteger, default=0)
    percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    compound_tax: Mapped[bool] = mapped_column(Boolean, default=False)

    tax_type_id: Mapped[int | None] = mapped_column(
        ForeignKey("tax_types.id", ondelete="CASCADE"), nullable=True
    )
    # Polymorphic parent references.  Only one of (invoice_id, estimate_id,
    # item_id) is typically populated.  FKs for invoice/estimate are added in
    # a later sprint when those tables exist.
    invoice_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimate_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    item_id: Mapped[int | None] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), nullable=True
    )
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    tax_type: Mapped["TaxType | None"] = relationship("TaxType", lazy="selectin")
    item: Mapped["Item | None"] = relationship("Item", back_populates="taxes")
