# Smart Inventory & Sales Analytics — Technical Reference

## 1. Project Overview

**Project type:** Single-company inventory, sales, analytics, and machine-learning application

**Primary goal:** Build a production-ready Python full-stack application while learning backend development, databases, APIs, frontend integration, data analysis, and machine learning step by step.

**Current scope:** Beginner-friendly single-company application. Multi-tenant SaaS is intentionally out of scope for now and may be considered later.

**Cost constraint:** All services and tools used for the project should be free or have a permanent free tier. Paid services must not be introduced without explicit approval.

---

## 2. Technology Stack

### Backend
- Python 3.14.5
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL
- JWT-based authentication
- Password hashing

### Frontend
- React
- TypeScript
- Tailwind CSS
- React Router
- API integration

### Data Science / ML
- Pandas
- NumPy
- Scikit-learn
- SQL for analytical data extraction
- Data visualization

### Development / Production
- Git
- GitHub
- Docker
- Nginx
- Environment variables
- Automated testing
- Logging
- Error handling
- Free-tier deployment options only

---

## 3. Product Vision

The application will allow a company to manage:

- Users/employees
- Customers
- Categories
- Products
- Inventory
- Sales
- Sale items

Later, the same transactional data will support:

- Sales analytics
- Product performance analysis
- Customer analysis
- Sales forecasting
- Customer segmentation
- Product recommendations

---

## 4. Development Philosophy

The project will be built incrementally.

Rule:

> Understand → Implement → Test → Commit → Move to the next feature.

We will avoid introducing production complexity too early. First build a working simple version, then progressively add production practices.

---

## 5. Current Database Design

### Customer

| Column | Purpose |
|---|---|
| id | Primary key; unique customer identifier |
| name | Customer name |
| email | Customer email; currently planned as UNIQUE |
| phone | Contact number |
| address | Customer address |
| is_active | Allows deactivation without deleting historical records |
| created_at | Record creation timestamp |
| updated_at | Last modification timestamp |

### Category

| Column | Purpose |
|---|---|
| id | Primary key |
| name | Category name |

### Product

| Column | Purpose |
|---|---|
| id | Primary key |
| name | Product name |
| price | Current selling price |
| category_id | Foreign key to Category |
| is_active | Deactivate discontinued products without breaking history |
| created_at | Record creation timestamp |
| updated_at | Last modification timestamp |

### Inventory

| Column | Purpose |
|---|---|
| id | Primary key |
| product_id | Foreign key to Product; UNIQUE because current scope has one inventory record per product |
| quantity | Current available stock |
| created_at | Record creation timestamp |
| updated_at | Last modification timestamp |

### Sale

| Column | Purpose |
|---|---|
| id | Primary key |
| customer_id | Foreign key to Customer |
| user_id | Foreign key to the employee/user who created the sale |
| sale_date | Business date/time of the sale |
| total_amount | Final sale total |
| created_at | Record creation timestamp |
| updated_at | Last modification timestamp |

### SaleItem

| Column | Purpose |
|---|---|
| id | Primary key |
| sale_id | Foreign key to Sale |
| product_id | Foreign key to Product |
| quantity | Number of units sold in this particular sale |
| unit_price | Historical selling price at the time of sale |
| created_at | Record creation timestamp |
| updated_at | Last modification timestamp |

---

## 6. Important Relationships

- Category 1 → N Product
- Product 1 → 1 Inventory (current single-location scope)
- Customer 1 → N Sale
- User 1 → N Sale
- Sale 1 → N SaleItem
- Product 1 → N SaleItem

Conceptual flow:

```text
Category
   |
   | 1:N
   v
Product -------- 1:1 -------- Inventory
   |
   | 1:N
   v
SaleItem
   ^
   |
   | N:1
   |
Sale -------- N:1 -------- Customer
 |
 N:1
 |
User
```

---

## 7. Why Sale and SaleItem Are Separate

A single sale can contain multiple products.

Example:

```text
Sale #101
Customer: Rahul

Laptop × 2
Mouse × 3
Keyboard × 1
```

`Sale` stores information about the overall transaction.

`SaleItem` stores each product line inside that transaction.

This avoids repeating sale-level information and follows relational database normalization principles.

---

## 8. Quantity Rules

Two different quantities exist:

### SaleItem.quantity
How many units were sold in one specific sale.

Example:

```text
Laptop × 3
```

### Inventory.quantity
How many units are currently available.

Example:

```text
Current stock = 47
```

They must not be confused.

### Stock validation rule

If available stock is 5 and an employee attempts to sell 8:

```text
Requested: 8
Available: 5
```

The sale should be rejected.

Negative inventory is not allowed in the current project scope.

---

## 9. Why unit_price Exists in SaleItem

`Product.price` represents the current product price.

`SaleItem.unit_price` represents the historical price used in that transaction.

Example:

```text
25 Aug
Laptop product price = ₹60,000
Sale #101 unit_price = ₹60,000

1 Sep
Laptop product price = ₹65,000
```

The old sale must continue to show ₹60,000, not the new current price.

---

## 10. Why is_active Exists

Products and customers should generally not be hard-deleted when historical records depend on them.

Instead:

```text
is_active = false
```

This preserves historical references.

Example:

```text
Product #10
Laptop
is_active = false
```

The product can no longer be used for normal new operations, but old sales can still reference it.

---

## 11. Timestamps

Important records will use:

- `created_at` — when the record was created
- `updated_at` — when the record was last modified

Use timestamp names rather than vague names such as `date_created`.

Example:

```text
created_at = 2026-08-27 10:30:00
updated_at = 2026-08-27 14:45:00
```

---

## 12. Normalization Principles Used

### 1NF
Each cell contains one atomic value.

Bad:

```text
products = "Laptop, Mouse, Keyboard"
```

Better: separate `SaleItem` rows.

### 2NF
Non-key data should depend on the complete key/record identity.

Sale-level information belongs to `Sale`; product-line information belongs to `SaleItem`.

### 3NF
Avoid storing data that depends on another non-key attribute.

For example, do not duplicate `category_name` in Product when `category_id` identifies the category.

---

## 13. Backend API Direction

The backend will expose REST APIs.

Typical operations:

```text
GET     /products
POST    /products
GET     /products/{id}
PUT     /products/{id}
PATCH   /products/{id}
DELETE  /products/{id}
```

Similar resource APIs will later exist for:

```text
/customers
/categories
/inventory
/sales
/users
```

---

## 14. Current FastAPI Status

The first FastAPI application is already working.

Current concept:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Smart Inventory API is running"}
```

A temporary `/products` endpoint was also created using hard-coded data.

FastAPI development documentation is available through:

```text
/docs
```

---

## 15. Development Environment Status

Python version confirmed:

```text
Python 3.14.5
```

A Python virtual environment is being used:

```text
backend/
└── .venv/
```

The project uses Git from the beginning.

Important `.gitignore` entries include:

```text
.venv/
__pycache__/
*.pyc
.env
.DS_Store
```

`.env` must not be committed because it may contain secrets or database credentials.

---

## 16. Planned Project Structure

```text
smart-inventory/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── middleware/
│   │   └── main.py
│   │
│   ├── tests/
│   ├── alembic/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── types/
│   │
│   ├── Dockerfile
│   └── package.json
│
├── nginx/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

This is the target structure; not every directory needs to be created immediately.

---

## 17. Planned Authentication

Initial roles:

### Admin
- Manage products
- Manage customers
- Manage inventory
- View sales
- Manage users
- View reports

### Employee
- View products
- Manage customers
- Create sales
- View inventory
- View dashboard

Planned security:

- Password hashing
- JWT access token
- Authentication
- Role-based authorization
- Environment-based secrets

---

## 18. Planned Data Science Layer

Once the transactional application works:

### Data Analysis
- Extract data using SQL
- Load data with Pandas
- Clean data
- Handle missing values
- Explore distributions
- Analyze sales trends
- Analyze product performance
- Analyze customer behavior

### Machine Learning

First planned ML feature:

**Sales Forecasting**

```text
Historical Sales
      ↓
Data Cleaning
      ↓
Feature Engineering
      ↓
Model Training
      ↓
Model Evaluation
      ↓
Future Sales Prediction
```

Later:

- Customer segmentation using RFM features and clustering
- Product recommendation
- Business analytics

---

## 19. Production Goals

Before calling the project production-ready, we will progressively add:

- Input validation
- Database constraints
- Transactions
- Authentication
- Authorization
- Secure configuration
- Error handling
- Logging
- Automated tests
- Database migrations
- API documentation
- Docker
- Nginx
- CI/CD
- Deployment
- Monitoring appropriate to free-tier constraints

---

## 20. Current Roadmap

```text
Phase 1  Project planning                 [IN PROGRESS]
Phase 2  Database design                  [MOSTLY COMPLETE]
Phase 3  PostgreSQL setup
Phase 4  SQLAlchemy + Alembic
Phase 5  FastAPI project structure
Phase 6  User authentication
Phase 7  Product + Category APIs
Phase 8  Customer APIs
Phase 9  Inventory
Phase 10 Sales + SaleItem
Phase 11 React frontend
Phase 12 Dashboard
Phase 13 Data analysis
Phase 14 Machine learning
Phase 15 ML API integration
Phase 16 Testing
Phase 17 Docker
Phase 18 Security hardening
Phase 19 Deployment
```

---

## 21. Current Next Step

The next practical task is:

**Set up PostgreSQL locally and create the first real database.**

After that:

```text
PostgreSQL
    ↓
SQLAlchemy
    ↓
FastAPI
```

The temporary hard-coded `/products` data will eventually be replaced by real database-backed data.

---

## 22. Project Rules / Decisions Log

1. Project is currently single-company, not SaaS.
2. Beginner-friendly implementation first; production practices added progressively.
3. External services must be free/permanent-free-tier unless explicitly approved.
4. Sale and SaleItem are separate entities.
5. SaleItem stores quantity sold for a specific sale.
6. Inventory stores current available stock.
7. Negative inventory is not allowed.
8. Product price is current price.
9. SaleItem unit_price preserves historical transaction price.
10. Important entities use created_at and updated_at.
11. Product/customer deactivation should preserve historical references.
12. Inventory.product_id is UNIQUE under the current single-location model.
13. Multi-warehouse inventory is out of scope for now.
14. Multi-tenancy/SaaS is out of scope for now.
15. Database and business rules should be understood before implementation.

---

## 23. Learning Goal

By the end of this project, the target is not just to have an application.

The goal is to understand the complete flow:

```text
Business Problem
      ↓
Database Design
      ↓
SQL
      ↓
Python
      ↓
FastAPI
      ↓
REST API
      ↓
React
      ↓
Data Analysis
      ↓
Machine Learning
      ↓
ML API
      ↓
Testing
      ↓
Docker
      ↓
Deployment
```

This project should therefore serve as both a portfolio project and a long-term technical reference.
