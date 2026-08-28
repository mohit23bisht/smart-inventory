from pydantic import BaseModel, ConfigDict, EmailStr, Field


# =========================================================
# CUSTOMER CREATE SCHEMA
# =========================================================
# Used when creating a new customer.
#
# Endpoint:
# POST /customers/
#
# The client must provide:
# - name
# - email
#
# phone and address are optional.

class CustomerCreate(BaseModel):

    # Customer's name.
    # Minimum 1 character and maximum 150 characters.
    name: str = Field(
        min_length=1,
        max_length=150,
    )

    # EmailStr validates that the value has a valid
    # email address format.
    #
    # Example:
    # "mohit@gmail.com"       -> valid
    # "mohit@gmail"           -> invalid
    email: EmailStr

    # Phone number is optional.
    phone: str | None = Field(
        default=None,
        max_length=20,
    )

    # Address is optional.
    address: str | None = Field(
        default=None,
        max_length=255,
    )


# =========================================================
# CUSTOMER UPDATE SCHEMA
# =========================================================
# Used by:
# PUT /customers/{customer_id}
#
# PUT means complete update, therefore all fields are
# required except the fields that are inherently optional.

class CustomerUpdate(BaseModel):

    name: str = Field(
        min_length=1,
        max_length=150,
    )

    email: EmailStr

    phone: str | None = Field(
        default=None,
        max_length=20,
    )

    address: str | None = Field(
        default=None,
        max_length=255,
    )

    is_active: bool


# =========================================================
# CUSTOMER PATCH SCHEMA
# =========================================================
# Used by:
# PATCH /customers/{customer_id}
#
# PATCH allows the client to update only the fields
# it wants to change.
#
# Example:
# {
#     "email": "newemail@gmail.com"
# }
#
# Only the email will be changed.

class CustomerPatch(BaseModel):

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    email: EmailStr | None = None

    phone: str | None = Field(
        default=None,
        max_length=20,
    )

    address: str | None = Field(
        default=None,
        max_length=255,
    )

    is_active: bool | None = None


# =========================================================
# CUSTOMER RESPONSE SCHEMA
# =========================================================
# Used when sending customer information back to the client.
#
# The client does NOT send this schema.
# FastAPI uses it to control the API response.

class CustomerResponse(BaseModel):

    # Allows Pydantic to read data directly from
    # SQLAlchemy Customer objects.
    model_config = ConfigDict(from_attributes=True)

    id: int

    name: str

    email: EmailStr

    phone: str | None

    address: str | None

    is_active: bool