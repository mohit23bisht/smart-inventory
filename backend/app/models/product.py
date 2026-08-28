from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column,relationship

from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:

    from app.models.category import Category
    from app.models.inventory import Inventory
    from app.models.sale_item import SaleItem

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    low_stock_threshold: Mapped[int] = mapped_column(
    nullable=False,
    default=10,
)

    category: Mapped["Category"] = relationship(

        back_populates="products"

    )
    inventory: Mapped["Inventory"] = relationship(
    back_populates="product",
    uselist=False,
)
    sale_items: Mapped[list["SaleItem"]] = relationship(
    back_populates="product"
)