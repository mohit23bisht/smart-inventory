from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.customer import Customer
from app.schemas.customer import (
    CustomerCreate,
    CustomerPatch,
    CustomerResponse,
    CustomerUpdate,
)


# =========================================================
# CUSTOMER ROUTER
# =========================================================
# All customer endpoints will start with /customers.
#
# Examples:
# POST   /customers/
# GET    /customers/
# GET    /customers/1
# PUT    /customers/1
# PATCH  /customers/1
# DELETE /customers/1
router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


# =========================================================
# CREATE CUSTOMER
# =========================================================

# POST /customers/
#
# Creates a new customer in the database.
@router.post(
    "/",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
):
    # Create a SQLAlchemy Customer object from the
    # validated Pydantic request data.
    db_customer = Customer(
        name=customer_data.name,
        email=customer_data.email,
        phone=customer_data.phone,
        address=customer_data.address,
    )

    # Add the customer to the current database transaction.
    db.add(db_customer)

    try:
        # Commit the transaction so the new customer is saved.
        #
        # PostgreSQL checks the UNIQUE(email) constraint here.
        db.commit()

    except IntegrityError:
        # The database rejected the operation.
        # This can happen when another customer already uses
        # the same email address.
        
        # Roll back the failed transaction so that the current
        # database session can be safely used again.
        db.rollback()

        # Convert the database error into a meaningful HTTP response.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A customer with this email already exists",
        )

    # Reload the object so database-generated values such as
    # id and timestamps are available.

    db.refresh(db_customer)

    return db_customer


# =========================================================
# GET ALL CUSTOMERS
# =========================================================

# GET /customers/
#
# Returns all active customers.
#
# Soft-deleted customers remain in the database but are
# hidden from the normal customer listing.
@router.get(
    "/",
    response_model=list[CustomerResponse],
)
def get_customers(
    db: Session = Depends(get_db),
):
    # Fetch only customers that are currently active.
    customers = db.query(Customer).filter(
        Customer.is_active == True
    ).all()

    return customers


# =========================================================
# GET SINGLE CUSTOMER
# =========================================================

# GET /customers/{customer_id}
#
# Returns one active customer using its ID.
@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
):
    # Search for an active customer with the requested ID.
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.is_active == True,
    ).first()

    # If the customer does not exist or is inactive,
    # return HTTP 404.
    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return customer


# =========================================================
# UPDATE CUSTOMER - PUT
# =========================================================

# PUT /customers/{customer_id}
#
# Performs a complete update of the customer.
@router.put(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
):
    # Find the customer by ID.
    customer = db.query(Customer).filter(
        Customer.id == customer_id
    ).first()

    # Customer does not exist.
    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    # Replace the existing customer information
    # with the new information supplied by the client.
    customer.name = customer_data.name
    customer.email = customer_data.email
    customer.phone = customer_data.phone
    customer.address = customer_data.address
    customer.is_active = customer_data.is_active

    # Save changes to PostgreSQL.
    db.commit()

    # Reload the updated customer.
    db.refresh(customer)

    return customer


# =========================================================
# PARTIAL UPDATE CUSTOMER - PATCH
# =========================================================

# PATCH /customers/{customer_id}
#
# Allows the client to change only the fields it provides.
#
# Example:
# {
#     "email": "newemail@gmail.com"
# }
#
# Only the email will be updated.
@router.patch(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def patch_customer(
    customer_id: int,
    customer_data: CustomerPatch,
    db: Session = Depends(get_db),
):
    # Find the existing customer.
    customer = db.query(Customer).filter(
        Customer.id == customer_id
    ).first()

    # Customer does not exist.
    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    # Update only fields that were provided by the client.
    if customer_data.name is not None:
        customer.name = customer_data.name

    if customer_data.email is not None:
        customer.email = customer_data.email

    if customer_data.phone is not None:
        customer.phone = customer_data.phone

    if customer_data.address is not None:
        customer.address = customer_data.address

    if customer_data.is_active is not None:
        customer.is_active = customer_data.is_active

    # Save changes to PostgreSQL.
    db.commit()

    # Reload the latest database values.
    db.refresh(customer)

    return customer



# =========================================================
# DELETE CUSTOMER - SOFT DELETE
# =========================================================

# DELETE /customers/{customer_id}
#
# We do NOT physically delete the customer.
#
# Instead, we set is_active=False.
#
# This preserves customer information for historical
# sales and other records.
@router.delete(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
):
    # Find the customer.
    customer = db.query(Customer).filter(
        Customer.id == customer_id
    ).first()

    # Customer does not exist.
    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    # Soft delete:
    # Keep the database row but mark the customer inactive.
    customer.is_active = False

    # Save the change.
    db.commit()

    # Reload the updated customer.
    db.refresh(customer)

    return customer