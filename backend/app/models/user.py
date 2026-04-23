"""User model (Sprint 1.1 + 1.4).

Mirrors the core fields from the reference Laravel `users` table while
staying idiomatic for SQLAlchemy 2.0.  Extra Crater fields (oauth ids,
portal toggle, etc.) are intentionally omitted in this sprint and will be
added as feature work requires them.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.company import Company


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="user")

    # Self-referential: who created this user (admin that invited them).
    creator_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # Current/primary company the user is operating in.  Nullable because the
    # very first admin exists before any company does.
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    companies: Mapped[list["Company"]] = relationship(
        "Company",
        secondary="user_company",
        back_populates="users",
        lazy="selectin",
    )
    owned_companies: Mapped[list["Company"]] = relationship(
        "Company",
        back_populates="owner",
        foreign_keys="Company.owner_id",
    )
    creator: Mapped["User | None"] = relationship(
        "User", remote_side="User.id", foreign_keys=[creator_id]
    )
