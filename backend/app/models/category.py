from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column,relationship

from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.product import Product
    
class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    products: Mapped[list["Product"]] = relationship(

        back_populates="category"

    )