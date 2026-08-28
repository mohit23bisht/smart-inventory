from decimal import Decimal
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db

from app.models.customer import Customer
from app.models.inventory import Inventory
from app.models.inventory_movement import (
    InventoryMovement,
    MovementType,
)
from app.models.product import Product
from app.models.sale import Sale, SaleStatus
from app.models.sale_item import SaleItem

from app.schemas.sale import (
    SaleCreate,
    SaleResponse,
    SaleSummaryResponse,
    SaleRevenueResponse,
)


router = APIRouter(
    prefix="/sales",
    tags=["Sales"],
)


# =========================================================
# CREATE SALE
# =========================================================
# Creates a sale and automatically:
#
# 1. Validates the customer.
# 2. Validates every product.
# 3. Checks available inventory.
# 4. Calculates the total amount.
# 5. Creates the Sale record.
# 6. Creates SaleItem records.
# 7. Reduces inventory.
# 8. Creates OUT movement records.
#
# All changes are saved in one database transaction.
@router.post(
    "/",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sale(
    sale_data: SaleCreate,
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Step 1: Check that the customer exists.
    # -----------------------------------------------------
    customer = db.query(Customer).filter(
        Customer.id == sale_data.customer_id
    ).first()

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    # -----------------------------------------------------
    # Step 2: Validate every sale item.
    # -----------------------------------------------------
    total_amount = Decimal("0.00")

    validated_items = []

    for item in sale_data.items:

        # Find the product.
        product = db.query(Product).filter(
            Product.id == item.product_id,
            Product.is_active == True,
        ).first()

        if product is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Product {item.product_id} "
                    "not found or inactive"
                ),
            )

        # Find the inventory record.
        inventory = db.query(Inventory).filter(
            Inventory.product_id == product.id,
        ).first()

        if inventory is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Inventory not found for "
                    f"product {product.id}"
                ),
            )

        # Make sure enough stock is available.
        if item.quantity > inventory.quantity:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Insufficient stock for product "
                    f"{product.id}. "
                    f"Available: {inventory.quantity}, "
                    f"Requested: {item.quantity}"
                ),
            )

        # Calculate this item's subtotal.
        subtotal = product.price * item.quantity

        # Add subtotal to the complete sale total.
        total_amount += subtotal

        # Keep validated data for the transaction.
        validated_items.append(
            {
                "product": product,
                "inventory": inventory,
                "quantity": item.quantity,
            }
        )

    # -----------------------------------------------------
    # Step 3: Create the Sale record.
    # -----------------------------------------------------
    sale = Sale(
        customer_id=sale_data.customer_id,
        user_id=sale_data.user_id,
        total_amount=total_amount,
        status=SaleStatus.ACTIVE,
    )

    db.add(sale)

    # Flush gives us sale.id before committing.
    db.flush()

    # -----------------------------------------------------
    # Step 4: Create SaleItems and update inventory.
    # -----------------------------------------------------
    for item_data in validated_items:

        product = item_data["product"]
        inventory = item_data["inventory"]
        quantity = item_data["quantity"]

        # Create the sale item using the product price
        # fetched from the database.
        sale_item = SaleItem(
            sale_id=sale.id,
            product_id=product.id,
            quantity=quantity,
            unit_price=product.price,
        )

        db.add(sale_item)

        # Reduce current inventory.
        inventory.quantity -= quantity

        # Create an OUT movement for audit/history.
        movement = InventoryMovement(
            inventory_id=inventory.id,
            type=MovementType.OUT,
            quantity=quantity,
        )

        db.add(movement)

    # -----------------------------------------------------
    # Step 5: Commit the complete transaction.
    # -----------------------------------------------------
    db.commit()

    # Reload the sale with its database-generated values.
    db.refresh(sale)

    return sale





# =========================================================
# GET ALL SALES
# =========================================================
# Returns a paginated list of sales.
#
# Optional filters:
# - customer_id
# - user_id
# - status
# - from_date
# - to_date
#
# Examples:
#
# /sales/
# /sales/?customer_id=1
# /sales/?user_id=2
# /sales/?status=ACTIVE
# /sales/?status=CANCELLED
# /sales/?customer_id=1&status=CANCELLED
# /sales/?from_date=2026-08-28T00:00:00
@router.get(
    "/",
    response_model=list[SaleResponse],
)
def get_sales(
    skip: int = 0,
    limit: int = 20,
    customer_id: int | None = None,
    user_id: int | None = None,
    status: str | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Step 1: Validate pagination.
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
    # Step 2: Start the sales query.
    # -----------------------------------------------------
    query = db.query(Sale)

    # -----------------------------------------------------
    # Step 3: Filter by customer if provided.
    # -----------------------------------------------------
    if customer_id is not None:
        query = query.filter(
            Sale.customer_id == customer_id
        )

    # -----------------------------------------------------
    # Step 4: Filter by user if provided.
    # -----------------------------------------------------
    if user_id is not None:
        query = query.filter(
            Sale.user_id == user_id
        )

    # -----------------------------------------------------
    # Step 5: Filter by sale status if provided.
    # -----------------------------------------------------
    if status is not None:

        # Only these statuses are supported.
        if status not in {
            SaleStatus.ACTIVE.value,
            SaleStatus.CANCELLED.value,
        }:
            raise HTTPException(
                status_code=400,
                detail="Invalid sale status",
            )

        # Convert string into SaleStatus enum.
        query = query.filter(
            Sale.status == SaleStatus(status)
        )

    # -----------------------------------------------------
    # Step 6: Filter sales from a specific date/time.
    # -----------------------------------------------------
    if from_date is not None:
        query = query.filter(
            Sale.sale_date >= from_date
        )

    # -----------------------------------------------------
    # Step 7: Filter sales up to a specific date/time.
    # -----------------------------------------------------
    if to_date is not None:
        query = query.filter(
            Sale.sale_date <= to_date
        )

    # -----------------------------------------------------
    # Step 8: Sort newest sales first.
    # -----------------------------------------------------
    sales = (
        query
        .order_by(Sale.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return sales


# =========================================================
# CANCEL SALE
# =========================================================
# POST /sales/{sale_id}/cancel
#
# Cancelling a sale:
#
# 1. Checks that the sale exists.
# 2. Checks that the sale is currently ACTIVE.
# 3. Restores inventory for every sale item.
# 4. Creates an IN movement for every restored quantity.
# 5. Changes sale status to CANCELLED.
#
# All changes happen in one database transaction.
@router.post(
    "/{sale_id}/cancel",
    response_model=SaleResponse,
)
def cancel_sale(
    sale_id: int,
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Step 1: Find the sale.
    # -----------------------------------------------------
    sale = db.query(Sale).filter(
        Sale.id == sale_id
    ).first()

    if sale is None:
        raise HTTPException(
            status_code=404,
            detail="Sale not found",
        )

    # -----------------------------------------------------
    # Step 2: Prevent cancelling the same sale twice.
    # -----------------------------------------------------
    if sale.status == SaleStatus.CANCELLED:
        raise HTTPException(
            status_code=400,
            detail="Sale is already cancelled",
        )

    # -----------------------------------------------------
    # Step 3: Restore inventory for every sale item.
    # -----------------------------------------------------
    for item in sale.items:

        # Find inventory for this product.
        inventory = db.query(Inventory).filter(
            Inventory.product_id == item.product_id
        ).first()

        if inventory is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Inventory not found for product "
                    f"{item.product_id}"
                ),
            )

        # Return the sold quantity to inventory.
        inventory.quantity += item.quantity

        # Record the inventory restoration.
        movement = InventoryMovement(
            inventory_id=inventory.id,
            type=MovementType.IN,
            quantity=item.quantity,
        )

        db.add(movement)

    # -----------------------------------------------------
    # Step 4: Mark the sale as cancelled.
    # -----------------------------------------------------
    sale.status = SaleStatus.CANCELLED

    # -----------------------------------------------------
    # Step 5: Commit everything together.
    # -----------------------------------------------------
    db.commit()

    # Reload the sale from the database.
    db.refresh(sale)

    return sale

# =========================================================
# SALES SUMMARY
# =========================================================
# GET /sales/summary
#
# Provides basic sales statistics:
#
# - Total number of sales
# - Number of active sales
# - Number of cancelled sales
# - Total revenue from active sales
#
# Cancelled sales are excluded from revenue because the
# customer transaction has been cancelled.
@router.get(
    "/summary",
    response_model=SaleSummaryResponse,
)
def get_sales_summary(
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Total number of sales.
    # -----------------------------------------------------
    total_sales = (
        db.query(Sale)
        .count()
    )

    # -----------------------------------------------------
    # Number of active sales.
    # -----------------------------------------------------
    active_sales = (
        db.query(Sale)
        .filter(
            Sale.status == SaleStatus.ACTIVE
        )
        .count()
    )

    # -----------------------------------------------------
    # Number of cancelled sales.
    # -----------------------------------------------------
    cancelled_sales = (
        db.query(Sale)
        .filter(
            Sale.status == SaleStatus.CANCELLED
        )
        .count()
    )

    # -----------------------------------------------------
    # Total revenue from active sales only.
    #
    # coalesce makes sure we get 0 instead of NULL when
    # there are no active sales.
    # -----------------------------------------------------
    total_revenue = (
        db.query(
            func.coalesce(
                func.sum(Sale.total_amount),
                Decimal("0.00"),
            )
        )
        .filter(
            Sale.status == SaleStatus.ACTIVE
        )
        .scalar()
    )

    return {
        "total_sales": total_sales,
        "active_sales": active_sales,
        "cancelled_sales": cancelled_sales,
        "total_revenue": total_revenue,
    }

# =========================================================
# SALES REVENUE BY DATE RANGE
# =========================================================

@router.get(
    "/revenue",
    response_model=SaleRevenueResponse,
)
def get_sales_revenue(
    from_date: datetime,
    to_date: datetime,
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Validate the date range.
    # -----------------------------------------------------
    if from_date > to_date:
        raise HTTPException(
            status_code=400,
            detail="from_date cannot be after to_date",
        )

    # -----------------------------------------------------
    # Count active sales in the requested period.
    # -----------------------------------------------------
    total_sales = (
        db.query(Sale)
        .filter(
            Sale.status == SaleStatus.ACTIVE,
            Sale.sale_date >= from_date,
            Sale.sale_date <= to_date,
        )
        .count()
    )

    # -----------------------------------------------------
    # Calculate active revenue.
    #
    # Cancelled sales are excluded.
    # -----------------------------------------------------
    total_revenue = (
        db.query(
            func.coalesce(
                func.sum(Sale.total_amount),
                Decimal("0.00"),
            )
        )
        .filter(
            Sale.status == SaleStatus.ACTIVE,
            Sale.sale_date >= from_date,
            Sale.sale_date <= to_date,
        )
        .scalar()
    )

    return {
        "from_date": from_date,
        "to_date": to_date,
        "total_sales": total_sales,
        "total_revenue": total_revenue,
    }

# =========================================================
# GET SINGLE SALE
# =========================================================
# GET /sales/{sale_id}
#
# Returns one sale along with all of its sale items.
@router.get(
    "/{sale_id}",
    response_model=SaleResponse,
)
def get_sale(
    sale_id: int,
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Find the requested sale.
    # -----------------------------------------------------
    sale = db.query(Sale).filter(
        Sale.id == sale_id
    ).first()

    # -----------------------------------------------------
    # Sale does not exist.
    # -----------------------------------------------------
    if sale is None:
        raise HTTPException(
            status_code=404,
            detail="Sale not found",
        )

    # -----------------------------------------------------
    # Return the sale.
    #
    # Sale.items is a SQLAlchemy relationship, so the
    # associated sale items are included in the response.
    # -----------------------------------------------------
    return sale