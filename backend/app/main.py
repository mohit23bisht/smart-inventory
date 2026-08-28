from fastapi import FastAPI

from app.routers.products import router as products_router
from app.routers.categories import router as categories_router
from app.routers.customers import router as customers_router
from app.routers.inventory import router as inventory_router
from app.routers.sales import router as sales_router

app = FastAPI()

app.include_router(categories_router)
app.include_router(products_router)
app.include_router(customers_router)
app.include_router(inventory_router)
app.include_router(sales_router)