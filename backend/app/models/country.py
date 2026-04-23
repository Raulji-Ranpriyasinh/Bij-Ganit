"""Country model (Sprint 2.1).

The reference schema has no timestamps on this table — it is static reference
data seeded once by the migration.
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(8))
    name: Mapped[str] = mapped_column(String(255))
    phonecode: Mapped[int] = mapped_column(Integer, default=0)
