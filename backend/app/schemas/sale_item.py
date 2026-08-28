from decimal import Decimal

from pydantic import BaseModel, Field


# =========================================================
# SALE ITEM CREATE SCHEMA
# =========================================================
# Represents one product inside a sale.
#
# Example:
#
# {
#     "product_id": 3,
#     "quantity": 2
# }
#
# The client only sends the product and quantity.
# The server will fetch the current product price itself.
class SaleItemCreate(BaseModel):

    # Product that is being sold.
    product_id: int

    # Number of units being sold.
    #
    # Quantity must be greater than zero.
    quantity: int = Field(
        gt=0,
    )


# =========================================================
# SALE ITEM RESPONSE SCHEMA
# =========================================================
# Returned after a sale is created.
class SaleItemResponse(BaseModel):

    id: int

    sale_id: int

    product_id: int

    quantity: int

    # Price of one unit at the time of sale.
    #
    # We store this in the sale item so that future product
    # price changes do not change historical sales.
    unit_price: Decimal