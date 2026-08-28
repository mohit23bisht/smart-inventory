from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


if TYPE_CHECKING:
    from app.models.inventory import Inventory


# =========================================================
# INVENTORY MOVEMENT TYPE
# =========================================================
# Defines the only two types of stock movement allowed.
#
# IN  → Stock was added.
# OUT → Stock was removed.
#
# Using Enum prevents random values such as "hello",
# "add", or "remove" from being used as movement types.
class MovementType(str, Enum):

    IN = "IN"
    OUT = "OUT"


# =========================================================
# INVENTORY MOVEMENT MODEL
# =========================================================
# Stores the history of every stock movement.
#
# Example:
#
# Stock In:
# inventory_id = 1
# type = IN
# quantity = 20
#
# Stock Out:
# inventory_id = 1
# type = OUT
# quantity = 5
class InventoryMovement(Base):

    __tablename__ = "inventory_movements"

    # -----------------------------------------------------
    # Primary Key
    # -----------------------------------------------------
    # PostgreSQL automatically generates this ID.
    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    # -----------------------------------------------------
    # Inventory ID
    # -----------------------------------------------------
    # Connects this movement to an inventory record.
    #
    # Example:
    # inventory_id = 1
    #
    # means this movement belongs to Inventory #1.
    inventory_id: Mapped[int] = mapped_column(
        ForeignKey("inventory.id"),
        nullable=False,
    )

    # -----------------------------------------------------
    # Movement Type
    # -----------------------------------------------------
    # Stores whether stock was added or removed.
    #
    # Only:
    # IN
    # OUT
    #
    # are allowed.
    type: Mapped[MovementType] = mapped_column(
        SQLEnum(MovementType),
        nullable=False,
    )

    # -----------------------------------------------------
    # Quantity
    # -----------------------------------------------------
    # Number of units involved in this movement.
    #
    # This must always be positive.
    #
    # Example:
    # IN  +20 → quantity = 20
    # OUT -5  → quantity = 5
    #
    # We store the direction separately in "type".
    quantity: Mapped[int] = mapped_column(
        nullable=False,
    )

    # -----------------------------------------------------
    # Created At
    # -----------------------------------------------------
    # Records when this stock movement happened.
    #
    # PostgreSQL automatically sets the current timestamp.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # -----------------------------------------------------
    # Relationship to Inventory
    # -----------------------------------------------------
    # Allows us to access the inventory associated with
    # this movement through:
    #
    # movement.inventory
    inventory: Mapped["Inventory"] = relationship(
        back_populates="movements"
    )