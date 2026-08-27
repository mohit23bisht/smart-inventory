from fastapi import FastAPI

from app.routers.products import router as products_router
from app.routers.categories import router as categories_router

app = FastAPI()

app.include_router(categories_router)
app.include_router(products_router)