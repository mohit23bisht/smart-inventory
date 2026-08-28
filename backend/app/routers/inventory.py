from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.inventory import Inventory
from app.models.product import Product
from app.schemas.inventory import (
    InventoryCreate,
    InventoryResponse,
    InventorySummaryResponse,
    InventoryUpdate,
    StockMovement,
)
from app.models.inventory_movement import (

    InventoryMovement,

    MovementType,

)
from app.schemas.inventory_movement import (
    InventoryMovementResponse,
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
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Pagination
    # -----------------------------------------------------
    # skip:
    # Number of records to skip.
    #
    # limit:
    # Maximum number of records to return.
    #
    # Example:
    #
    # /inventory/?skip=0&limit=20
    # → first 20 records
    #
    # /inventory/?skip=20&limit=20
    # → next 20 records

    # Prevent negative pagination values.
    if skip < 0:
        raise HTTPException(
            status_code=400,
            detail="skip cannot be negative",
        )

    # Prevent excessively large responses.
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 100",
        )

    # Fetch only the requested portion of inventory.
    inventory = (
        db.query(Inventory)
        .offset(skip)
        .limit(limit)
        .all()
    )

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
# Adds stock to the inventory AND records the movement
# in inventory_movements for audit/history purposes.
@router.post(
    "/{inventory_id}/stock-in",
    response_model=InventoryResponse,
)
def stock_in(
    inventory_id: int,
    movement: StockMovement,
    db: Session = Depends(get_db),
):
    # Find the inventory record.
    inventory = db.query(Inventory).filter(
        Inventory.id == inventory_id
    ).first()

    # Inventory does not exist.
    if inventory is None:
        raise HTTPException(
            status_code=404,
            detail="Inventory not found",
        )

    # Add the incoming quantity to current stock.
    inventory.quantity += movement.quantity

    # Create a history record for this stock movement.
    movement_record = InventoryMovement(
        inventory_id=inventory.id,
        type=MovementType.IN,
        quantity=movement.quantity,
    )

    # Add the movement record to the same transaction.
    db.add(movement_record)

    # Save BOTH changes together:
    #
    # 1. Updated inventory quantity
    # 2. New movement history record
    db.commit()

    # Reload the inventory with the latest database values.
    db.refresh(inventory)

    return inventory

# =========================================================
# STOCK OUT
# =========================================================

# POST /inventory/{inventory_id}/stock-out
#
# Removes stock from inventory AND records the movement
# in inventory_movements.
@router.post(
    "/{inventory_id}/stock-out",
    response_model=InventoryResponse,
)
def stock_out(
    inventory_id: int,
    movement: StockMovement,
    db: Session = Depends(get_db),
):
    # Find the inventory record.
    inventory = db.query(Inventory).filter(
        Inventory.id == inventory_id
    ).first()

    # Inventory does not exist.
    if inventory is None:
        raise HTTPException(
            status_code=404,
            detail="Inventory not found",
        )

    # Make sure enough stock is available.
    if movement.quantity > inventory.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock",
        )

    # Remove the requested quantity.
    inventory.quantity -= movement.quantity

    # Create a history record for this stock-out operation.
    movement_record = InventoryMovement(
        inventory_id=inventory.id,
        type=MovementType.OUT,
        quantity=movement.quantity,
    )

    # Add the movement record to the transaction.
    db.add(movement_record)

    # Save both:
    # 1. Updated inventory quantity
    # 2. New OUT movement history
    db.commit()

    # Reload the latest database values.
    db.refresh(inventory)

    return inventory

# =========================================================
# INVENTORY SUMMARY
# =========================================================

# GET /inventory/{inventory_id}/summary
#
# Returns:
# - Current stock
# - Total stock added
# - Total stock removed
#
# This endpoint is useful for dashboards and reports.
@router.get(
    "/{inventory_id}/summary",
    response_model=InventorySummaryResponse,
)
def get_inventory_summary(
    inventory_id: int,
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Step 1: Find the inventory record.
    # -----------------------------------------------------
    inventory = db.query(Inventory).filter(
        Inventory.id == inventory_id
    ).first()

    # Inventory does not exist.
    if inventory is None:
        raise HTTPException(
            status_code=404,
            detail="Inventory not found",
        )

    # -----------------------------------------------------
    # Step 2: Calculate total stock IN.
    #
    # Only movements with type = IN are included.
    # -----------------------------------------------------
    total_stock_in = (
        db.query(
            func.coalesce(
                func.sum(InventoryMovement.quantity),
                0,
            )
        )
        .filter(
            InventoryMovement.inventory_id == inventory_id,
            InventoryMovement.type == MovementType.IN,
        )
        .scalar()
    )

    # -----------------------------------------------------
    # Step 3: Calculate total stock OUT.
    #
    # Only movements with type = OUT are included.
    # -----------------------------------------------------
    total_stock_out = (
        db.query(
            func.coalesce(
                func.sum(InventoryMovement.quantity),
                0,
            )
        )
        .filter(
            InventoryMovement.inventory_id == inventory_id,
            InventoryMovement.type == MovementType.OUT,
        )
        .scalar()
    )

    # -----------------------------------------------------
    # Step 4: Return the inventory summary.
    # -----------------------------------------------------
    return InventorySummaryResponse(
        inventory_id=inventory.id,
        product_id=inventory.product_id,
        current_stock=inventory.quantity,
        total_stock_in=total_stock_in,
        total_stock_out=total_stock_out,
    )

# =========================================================
# GET INVENTORY MOVEMENT HISTORY
# =========================================================

# GET /inventory/{inventory_id}/movements
#
# Returns movement history for one inventory record.
#
# Supports:
# - Pagination
# - Filtering by movement type
#
# Examples:
#
# /inventory/1/movements
# /inventory/1/movements?type=IN
# /inventory/1/movements?type=OUT
@router.get(
    "/{inventory_id}/movements",
    response_model=list[InventoryMovementResponse],
)
def get_inventory_movements(
    inventory_id: int,
    skip: int = 0,
    limit: int = 20,
    movement_type: MovementType | None = None,
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Step 1: Check that the inventory exists.
    # -----------------------------------------------------
    inventory = db.query(Inventory).filter(
        Inventory.id == inventory_id
    ).first()

    if inventory is None:
        raise HTTPException(
            status_code=404,
            detail="Inventory not found",
        )

    # -----------------------------------------------------
    # Step 2: Validate pagination.
    # -----------------------------------------------------
    if skip < 0:
        raise HTTPException(
            status_code=400,
            detail="skip cannot be negative",
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 100",
        )

    # -----------------------------------------------------
    # Step 3: Start the movement query.
    # -----------------------------------------------------
    query = db.query(InventoryMovement).filter(
        InventoryMovement.inventory_id == inventory_id
    )

    # -----------------------------------------------------
    # Step 4: Apply movement type filter if provided.
    #
    # movement_type = IN
    #     → only IN records
    #
    # movement_type = OUT
    #     → only OUT records
    #
    # movement_type = None
    #     → all records
    # -----------------------------------------------------
    if movement_type is not None:
        query = query.filter(
            InventoryMovement.type == movement_type
        )

    # -----------------------------------------------------
    # Step 5: Order and paginate the results.
    # -----------------------------------------------------
    movements = (
        query
        .order_by(InventoryMovement.id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return movements