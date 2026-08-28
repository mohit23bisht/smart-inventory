from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.inventory import Inventory
from app.models.product import Product
from app.schemas.inventory import (
    InventoryCreate,
    InventoryResponse,
    InventoryUpdate,
    StockMovement,
)


# =========================================================
# INVENTORY ROUTER
# =========================================================
# All inventory endpoints will start with /inventory.
#
# Examples:
# POST /inventory/
# GET  /inventory/
# GET  /inventory/1
# PUT  /inventory/1
router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"],
)


# =========================================================
# CREATE INVENTORY
# =========================================================

# POST /inventory/
#
# Creates an inventory record for a product.
#
# Important:
# - Product must exist.
# - Product must be active.
# - One product can have only one inventory record.
@router.post(
    "/",
    response_model=InventoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory(
    inventory_data: InventoryCreate,
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Step 1: Check whether the product exists and is active.
    # -----------------------------------------------------
    product = db.query(Product).filter(
        Product.id == inventory_data.product_id,
        Product.is_active == True,
    ).first()

    # If the product does not exist or is inactive,
    # inventory cannot be created for it.
    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Active product not found",
        )

    # -----------------------------------------------------
    # Step 2: Create the inventory object.
    # -----------------------------------------------------
    db_inventory = Inventory(
        product_id=inventory_data.product_id,
        quantity=inventory_data.quantity,
    )

    # Add the new inventory record to the transaction.
    db.add(db_inventory)

    try:
        # Save the inventory record to PostgreSQL.
        #
        # PostgreSQL will check the UNIQUE(product_id)
        # constraint here.
        db.commit()

    except IntegrityError:
        # The product already has an inventory record,
        # so the UNIQUE constraint failed.
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Inventory already exists for this product",
        )

    # Reload database-generated values such as id
    # and timestamps.
    db.refresh(db_inventory)

    return db_inventory


# =========================================================
# GET ALL INVENTORY
# =========================================================

# GET /inventory/
#
# Returns all inventory records.
@router.get(
    "/",
    response_model=list[InventoryResponse],
)
def get_inventory(
    db: Session = Depends(get_db),
):
    # Fetch all inventory records from PostgreSQL.
    inventory = db.query(Inventory).all()

    return inventory


# =========================================================
# GET SINGLE INVENTORY
# =========================================================

# GET /inventory/{inventory_id}
#
# Returns one inventory record using its ID.
@router.get(
    "/{inventory_id}",
    response_model=InventoryResponse,
)
def get_inventory_item(
    inventory_id: int,
    db: Session = Depends(get_db),
):
    # Search for the inventory record by its ID.
    inventory = db.query(Inventory).filter(
        Inventory.id == inventory_id
    ).first()

    # Return 404 if the inventory record does not exist.
    if inventory is None:
        raise HTTPException(
            status_code=404,
            detail="Inventory not found",
        )

    return inventory


# =========================================================
# UPDATE INVENTORY
# =========================================================

# PUT /inventory/{inventory_id}
#
# Updates the product and quantity of an inventory record.
#
# Note:
# Later, when we build stock-in/stock-out operations,
# direct quantity updates will become less important.
@router.put(
    "/{inventory_id}",
    response_model=InventoryResponse,
)
def update_inventory(
    inventory_id: int,
    inventory_data: InventoryUpdate,
    db: Session = Depends(get_db),
):
    # Find the existing inventory record.
    inventory = db.query(Inventory).filter(
        Inventory.id == inventory_id
    ).first()

    # Inventory record does not exist.
    if inventory is None:
        raise HTTPException(
            status_code=404,
            detail="Inventory not found",
        )

    # Make sure the new product exists and is active.
    product = db.query(Product).filter(
        Product.id == inventory_data.product_id,
        Product.is_active == True,
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Active product not found",
        )

    # Update the inventory values.
    inventory.product_id = inventory_data.product_id
    inventory.quantity = inventory_data.quantity

    try:
        # Save the changes.
        #
        # UNIQUE(product_id) will be checked here.
        db.commit()

    except IntegrityError:
        # Roll back if another inventory record already
        # belongs to this product.
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Inventory already exists for this product",
        )

    # Reload the updated database values.
    db.refresh(inventory)

    return inventory

# =========================================================
# STOCK IN
# =========================================================

# POST /inventory/{inventory_id}/stock-in
#
# Adds new stock to an existing inventory record.
#
# Example:
# Current stock = 75
# Stock in     = 20
# New stock    = 95
@router.post(
    "/{inventory_id}/stock-in",
    response_model=InventoryResponse,
)
def stock_in(
    inventory_id: int,
    movement: StockMovement,
    db: Session = Depends(get_db),
):
    # Find the inventory record using its ID.
    inventory = db.query(Inventory).filter(
        Inventory.id == inventory_id
    ).first()

    # If inventory does not exist, return 404.
    if inventory is None:
        raise HTTPException(
            status_code=404,
            detail="Inventory not found",
        )

    # Add the incoming stock to the current quantity.
    #
    # Example:
    # 75 + 20 = 95
    inventory.quantity += movement.quantity

    # Save the new quantity to PostgreSQL.
    db.commit()

    # Reload the inventory so updated_at and other
    # database values are refreshed.
    db.refresh(inventory)

    return inventory

# =========================================================
# STOCK OUT
# =========================================================

# POST /inventory/{inventory_id}/stock-out
#
# Removes stock from an inventory record.
#
# Example:
# Current stock = 95
# Stock out    = 15
# New stock    = 80
@router.post(
    "/{inventory_id}/stock-out",
    response_model=InventoryResponse,
)
def stock_out(
    inventory_id: int,
    movement: StockMovement,
    db: Session = Depends(get_db),
):
    # Find the inventory record using its ID.
    inventory = db.query(Inventory).filter(
        Inventory.id == inventory_id
    ).first()

    # If inventory does not exist, return 404.
    if inventory is None:
        raise HTTPException(
            status_code=404,
            detail="Inventory not found",
        )

    # Make sure we have enough stock before removing it.
    #
    # Example:
    # Current stock = 10
    # Requested out = 15
    #
    # 15 > 10 → Not enough stock ❌
    if movement.quantity > inventory.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock",
        )

    # Remove the requested quantity from current stock.
    inventory.quantity -= movement.quantity

    # Save the updated quantity.
    db.commit()

    # Reload the latest database values.
    db.refresh(inventory)

    return inventory