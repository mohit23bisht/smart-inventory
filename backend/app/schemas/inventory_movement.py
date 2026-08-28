from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.inventory_movement import MovementType


# =========================================================
# INVENTORY MOVEMENT CREATE SCHEMA
# =========================================================
# Used when creating a stock movement.
#
# Example:
#
# {
#     "type": "IN",
#     "quantity": 20
# }
#
# type:
#     IN  -> Stock is added
#     OUT -> Stock is removed
#
# quantity must always be greater than zero.
class InventoryMovementCreate(BaseModel):

    # Determines whether stock is coming IN or going OUT.
    #
    # Because this field uses MovementType, Pydantic will
    # reject values other than IN and OUT.
    type: MovementType

    # Number of units involved in this movement.
    #
    # We store the quantity as a positive number.
    # The "type" field determines whether it is added
    # or removed from inventory.
    quantity: int = Field(
        gt=0,
    )


# =========================================================
# INVENTORY MOVEMENT RESPONSE SCHEMA
# =========================================================
# Used when returning movement history to the client.
class InventoryMovementResponse(BaseModel):

    # Allows Pydantic to read data directly from the
    # SQLAlchemy InventoryMovement object.
    model_config = ConfigDict(from_attributes=True)

    id: int

    inventory_id: int

    type: MovementType

    quantity: int

    created_at: datetime