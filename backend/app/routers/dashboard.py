from decimal import Decimal
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db

from app.models.customer import Customer
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.sale import Sale, SaleStatus
from app.models.sale_item import SaleItem


from app.schemas.dashboard import (
    DashboardSummaryResponse,
    LowStockProductResponse,
    RecentSaleResponse,
    TopSellingProductResponse,
    MonthlyRevenueResponse,
)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


# =========================================================
# DASHBOARD SUMMARY
# =========================================================
# GET /dashboard/summary
#
# Returns a complete overview of the inventory system.
#
# This endpoint combines information from:
#
# - Products
# - Customers
# - Inventory
# - Sales
#
# The frontend can use this single API response to build
# dashboard cards and statistics.
@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
)
def get_dashboard_summary(
    db: Session = Depends(get_db),
):
    # =====================================================
    # PRODUCT STATISTICS
    # =====================================================

    # Total number of products.
    total_products = (
        db.query(Product)
        .count()
    )

    # Number of active products.
    active_products = (
        db.query(Product)
        .filter(
            Product.is_active == True
        )
        .count()
    )

    # =====================================================
    # CUSTOMER STATISTICS
    # =====================================================

    # Total number of customers.
    total_customers = (
        db.query(Customer)
        .count()
    )

    # =====================================================
    # INVENTORY STATISTICS
    # =====================================================

    # Total quantity across all inventory records.
    total_inventory_units = (
        db.query(
            func.coalesce(
                func.sum(Inventory.quantity),
                0,
            )
        )
        .scalar()
    )

    # -----------------------------------------------------
    # Low-stock threshold.
    #
    # For the first version of the dashboard we consider
    # stock below 10 units as low stock.
    # -----------------------------------------------------
    low_stock_products = (
    db.query(Inventory)
    .join(
        Product,
        Product.id == Inventory.product_id,
    )
    .filter(
        Inventory.quantity < Product.low_stock_threshold
    )
    .count()
)

    # =====================================================
    # SALES STATISTICS
    # =====================================================

    # Total number of sales, including cancelled sales.
    total_sales = (
        db.query(Sale)
        .count()
    )

    # Number of active sales.
    active_sales = (
        db.query(Sale)
        .filter(
            Sale.status == SaleStatus.ACTIVE
        )
        .count()
    )

    # Number of cancelled sales.
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
    # Cancelled sales are excluded from revenue.
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

    # =====================================================
    # RETURN DASHBOARD DATA
    # =====================================================

    return {
        "total_products": total_products,
        "active_products": active_products,
        "total_customers": total_customers,
        "total_inventory_units": total_inventory_units,
        "low_stock_products": low_stock_products,
        "total_sales": total_sales,
        "active_sales": active_sales,
        "cancelled_sales": cancelled_sales,
        "total_revenue": total_revenue,
    }

# =========================================================
# LOW STOCK PRODUCTS
# =========================================================
# GET /dashboard/low-stock
#
# Returns products whose current inventory is below their
# configured low-stock threshold.
@router.get(
    "/low-stock",
    response_model=list[LowStockProductResponse],
)
def get_low_stock_products(
    db: Session = Depends(get_db),
):
    results = (
        db.query(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            Inventory.quantity,
            Product.low_stock_threshold,
        )
        .join(
            Inventory,
            Inventory.product_id == Product.id,
        )
        .filter(
            Product.is_active == True,
            Inventory.quantity < Product.low_stock_threshold,
        )
        .order_by(
            Inventory.quantity.asc()
        )
        .all()
    )

    return [
        {
            "product_id": row.product_id,
            "product_name": row.product_name,
            "quantity": row.quantity,
            "low_stock_threshold": row.low_stock_threshold,
            "stock_status": (
                "OUT_OF_STOCK"
                if row.quantity == 0
                else "LOW_STOCK"
            ),
        }
        for row in results
    ]

# =========================================================
# RECENT SALES
# =========================================================
# GET /dashboard/recent-sales
#
# Returns the latest sales first.
@router.get(
    "/recent-sales",
    response_model=list[RecentSaleResponse],
)

def get_recent_sales(
    limit: int = 10,
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Validate limit
    # -----------------------------------------------------

    if limit < 1 or limit > 50:

        raise HTTPException(

            status_code=400,

            detail="limit must be between 1 and 50",

        )

    # -----------------------------------------------------
    # Get recent sales
    # -----------------------------------------------------
    sales = (
        db.query(Sale)
        .order_by(
            Sale.sale_date.desc()
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "sale_id": sale.id,
            "customer_id": sale.customer_id,
            "user_id": sale.user_id,
            "total_amount": sale.total_amount,
            "status": sale.status,
            "sale_date": sale.sale_date,
        }
        for sale in sales
    ]

# =========================================================
# TOP SELLING PRODUCTS
# =========================================================
# GET /dashboard/top-products
#
# Returns the products with the highest total quantity sold.
#
# Cancelled sales are excluded because cancelled items
# should not contribute to sales performance.
@router.get(
    "/top-products",
    response_model=list[TopSellingProductResponse],
)
def get_top_selling_products(
    limit: int = 10,
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Validate limit
    # -----------------------------------------------------

    if limit < 1 or limit > 50:

        raise HTTPException(

            status_code=400,

            detail="limit must be between 1 and 50",

        )

    # -----------------------------------------------------

    # Query top-selling products

    # -----------------------------------------------------
    results = (
        db.query(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            func.sum(SaleItem.quantity).label(
                "total_quantity_sold"
            ),
        )
        .join(
            SaleItem,
            SaleItem.product_id == Product.id,
        )
        .join(
            Sale,
            Sale.id == SaleItem.sale_id,
        )
        .filter(
            Sale.status == SaleStatus.ACTIVE,
        )
        .group_by(
            Product.id,
            Product.name,
        )
        .order_by(
            func.sum(SaleItem.quantity).desc()
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "product_id": row.product_id,
            "product_name": row.product_name,
            "total_quantity_sold": row.total_quantity_sold,
        }
        for row in results
    ]
# =========================================================
# MONTHLY REVENUE
# =========================================================
# GET /dashboard/monthly-revenue
#
# Returns active-sale revenue grouped by month for the
# current year.
@router.get(
    "/monthly-revenue",
    response_model=list[MonthlyRevenueResponse],
)
def get_monthly_revenue(
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Current year.
    # -----------------------------------------------------
    current_year = datetime.now().year

    # -----------------------------------------------------
    # Group sales by year and month.
    #
    # We use EXTRACT for grouping instead of DATE_TRUNC
    # so PostgreSQL does not encounter different bound
    # parameters for the grouping expression.
    # -----------------------------------------------------
    results = (
        db.query(
            func.extract(
                "month",
                Sale.sale_date,
            ).label("month"),
            func.sum(
                Sale.total_amount
            ).label("revenue"),
        )
        .filter(
            Sale.status == SaleStatus.ACTIVE,
            func.extract(
                "year",
                Sale.sale_date,
            ) == current_year,
        )
        .group_by(
            func.extract(
                "month",
                Sale.sale_date,
            )
        )
        .order_by(
            func.extract(
                "month",
                Sale.sale_date,
            )
        )
        .all()
    )

    # -----------------------------------------------------
    # Convert query result into API response.
    # -----------------------------------------------------
    return [
        {
            "month": f"{current_year}-{int(row.month):02d}",
            "revenue": row.revenue,
        }
        for row in results
    ]