"""Customer model (Sprint 2.2)."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.address import Address
    from app.models.currency import Currency
    from app.models.user import User


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    enable_portal: Mapped[bool] = mapped_column(Boolean, default=False)

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

    currency: Mapped["Currency | None"] = relationship("Currency", lazy="selectin")
    creator: Mapped["User | None"] = relationship(
        "User", foreign_keys=[creator_id], lazy="selectin"
    )
    addresses: Mapped[list["Address"]] = relationship(
        "Address",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
