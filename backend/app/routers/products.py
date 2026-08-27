from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Product
from app.schemas.product import (
    ProductCreate,
    ProductPatch,
    ProductResponse,
    ProductUpdate,
)


# ---------------------------------------------------------
# Product Router
# ---------------------------------------------------------
# All endpoints in this router will start with /products.
#
# Example:
# @router.get("/")
# becomes:
# GET /products/

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


# =========================================================
# CREATE PRODUCT
# =========================================================

# POST /products/
#
# Creates a new product in the database.

@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
):
    # Convert the validated Pydantic request object
    # into a SQLAlchemy Product object.
    db_product = Product(
        name=product.name,
        price=product.price,
        category_id=product.category_id,
    )

    # Add the new product to the current database transaction.
    db.add(db_product)

    # Permanently save the transaction in PostgreSQL.
    db.commit()

    # Refresh the object so that database-generated values
    # such as the ID are available in db_product.
    db.refresh(db_product)

    # Return the newly created product.
    # ProductResponse controls the response structure.
    return db_product


# =========================================================
# GET ALL PRODUCTS
# =========================================================

# GET /products/
#
# Returns only active products.
#
# Soft-deleted products are kept in the database for
# historical/reference purposes but are hidden from the
# normal product listing.

@router.get(
    "/",
    response_model=list[ProductResponse],
)
def get_products(
    db: Session = Depends(get_db),
):
    # Fetch all products whose is_active value is True.
    #
    # Conceptually this becomes:
    #
    # SELECT *
    # FROM products
    # WHERE is_active = true;
    products = db.query(Product).filter(
        Product.is_active == True
    ).all()

    return products


# =========================================================
# GET SINGLE PRODUCT
# =========================================================

# GET /products/{product_id}
#
# Returns one active product using its ID.

@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    # Find the product whose ID matches the URL parameter.
    #
    # We also check is_active=True because a soft-deleted
    # product should not be visible through the normal API.
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_active == True,
    ).first()

    # If no active product exists with this ID,
    # return HTTP 404 instead of returning None.
    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product


# =========================================================
# UPDATE PRODUCT - PUT
# =========================================================

# PUT /products/{product_id}
#
# Performs a complete update.
# The client must send all ProductUpdate fields.

@router.put(
    "/{product_id}",
    response_model=ProductResponse,
)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
):
    # Find the existing product.
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    # Product does not exist.
    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    # Replace the existing values with the new values.
    product.name = product_data.name
    product.price = product_data.price
    product.category_id = product_data.category_id
    product.is_active = product_data.is_active

    # Save changes to PostgreSQL.
    db.commit()

    # Reload the object with the latest database values.
    db.refresh(product)

    return product


# =========================================================
# PARTIAL UPDATE PRODUCT - PATCH
# =========================================================

# PATCH /products/{product_id}
#
# Performs a partial update.
#
# Example:
# {
#     "price": 90000
# }
#
# Only the price will be changed.

@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
)
def patch_product(
    product_id: int,
    product_data: ProductPatch,
    db: Session = Depends(get_db),
):
    # Find the existing product.
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    # Return 404 if the product does not exist.
    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    # Update only the fields that were actually provided.
    if product_data.name is not None:
        product.name = product_data.name

    if product_data.price is not None:
        product.price = product_data.price

    if product_data.category_id is not None:
        product.category_id = product_data.category_id

    if product_data.is_active is not None:
        product.is_active = product_data.is_active

    # Save the changes.
    db.commit()

    # Reload the updated product from the database.
    db.refresh(product)

    return product


# =========================================================
# DELETE PRODUCT - SOFT DELETE
# =========================================================

# DELETE /products/{product_id}
#
# IMPORTANT:
# We do NOT physically delete the database row.
#
# Instead, we mark the product as inactive.
# This is called a SOFT DELETE.
#
# Why?
# Historical sales may still reference this product.
# Keeping the row preserves historical data.

@router.delete(
    "/{product_id}",
    response_model=ProductResponse,
)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    # Find the product by ID.
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    # Product does not exist.
    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    # Instead of DELETE FROM products,
    # simply mark the product as inactive.
    product.is_active = False

    # Save the change.
    db.commit()

    # Reload the updated object.
    db.refresh(product)

    return product