from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column,relationship

from app.models.base import Base
from app.models.user import User
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.sale_item import SaleItem

class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    sale_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    customer: Mapped["Customer"] = relationship(
    back_populates="sales"
)
    user: Mapped["User"] = relationship(
    back_populates="sales"
)
    items: Mapped[list["SaleItem"]] = relationship(
    back_populates="sale",
    cascade="all, delete-orphan",
)