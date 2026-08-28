from decimal import Decimal

from pydantic import BaseModel
from datetime import datetime


# =========================================================
# DASHBOARD SUMMARY RESPONSE
# =========================================================
# Provides a high-level overview of the inventory system.
#
# This response is designed for:
#
# GET /dashboard/summary
#
# The frontend can use this single response to populate
# dashboard cards and statistics.
class DashboardSummaryResponse(BaseModel):

    # -----------------------------------------------------
    # PRODUCT STATISTICS
    # -----------------------------------------------------

    # Total number of products in the system.
    total_products: int

    # Number of currently active products.
    active_products: int

    # -----------------------------------------------------
    # CUSTOMER STATISTICS
    # -----------------------------------------------------

    # Total number of customers.
    total_customers: int

    # -----------------------------------------------------
    # INVENTORY STATISTICS
    # -----------------------------------------------------

    # Total quantity across all inventory records.
    total_inventory_units: int

    # Number of products whose stock is considered low.
    low_stock_products: int

    # -----------------------------------------------------
    # SALES STATISTICS
    # -----------------------------------------------------

    # Total number of sales, including cancelled sales.
    total_sales: int

    # Number of active sales.
    active_sales: int

    # Number of cancelled sales.
    cancelled_sales: int

    # Revenue generated from active sales only.
    total_revenue: Decimal

# =========================================================
# LOW STOCK PRODUCT RESPONSE
# =========================================================
class LowStockProductResponse(BaseModel):

    # Product ID.
    product_id: int

    # Product name.
    product_name: str

    # Current available quantity.
    quantity: int

    # Product-specific low-stock threshold.
    low_stock_threshold: int

    # Current stock status.
    #
    # OUT_OF_STOCK → quantity is 0
    # LOW_STOCK    → quantity is below threshold
    # IN_STOCK     → quantity is at/above threshold
    stock_status: str

# =========================================================
# RECENT SALE RESPONSE
# =========================================================
class RecentSaleResponse(BaseModel):

    # Sale ID.
    sale_id: int

    # Customer who made the purchase.
    customer_id: int

    # User/staff member who created the sale.
    user_id: int

    # Total amount of the sale.
    total_amount: Decimal

    # Current sale status.
    status: str

    # Date and time when the sale was created.
    sale_date: datetime

# =========================================================
# TOP SELLING PRODUCT RESPONSE
# =========================================================
class TopSellingProductResponse(BaseModel):

    # Product ID.
    product_id: int

    # Product name.
    product_name: str

    # Total quantity sold through active sales.
    total_quantity_sold: int

# =========================================================
# MONTHLY REVENUE RESPONSE
# =========================================================
class MonthlyRevenueResponse(BaseModel):

    # Month in YYYY-MM format.
    month: str

    # Revenue generated from active sales.
    revenue: Decimal