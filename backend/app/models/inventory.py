from datetime import datetime

from sqlalchemy import DateTime, ForeignKey,func
from sqlalchemy.orm import Mapped, mapped_column,relationship

from app.models.base import Base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.product import Product

class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        unique=True,
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
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

    product: Mapped["Product"] = relationship(
    back_populates="inventory"
)