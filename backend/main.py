from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def home():
    return {"message": "Smart Inventory API is running"}

@app.get("/products")

def get_products():

    return [

        {"id": 1, "name": "Laptop", "price": 60000},

        {"id": 2, "name": "Mouse", "price": 800},

        {"id": 3, "name": "Keyboard", "price": 1500},

    ]