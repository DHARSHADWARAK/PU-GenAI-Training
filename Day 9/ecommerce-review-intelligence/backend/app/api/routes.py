# app/api/routes.py
from fastapi import APIRouter
from app.services.product_service import PRODUCT_DATA

router = APIRouter()

@router.get("/products")
def get_products():
    return PRODUCT_DATA

@router.get("/products/{name}")
def get_product(name: str):
    return PRODUCT_DATA.get(name, {"error": "Product not found"})