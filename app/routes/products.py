"""
Products API Routes (Read-only - seed data)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_db

router = APIRouter(prefix="/products", tags=["products"])


class ProductResponse(BaseModel):
    """Schema for product response."""
    id: int
    name: str
    price: float


@router.get("")
def list_products():
    """
    List all available products.
    Products are seed data and cannot be modified via API.
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, price FROM products ORDER BY id")
            rows = cursor.fetchall()
            products = [
                {"id": row["id"], "name": row["name"], "price": row["price"]}
                for row in rows
            ]
            return {"products": products}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int):
    """
    Get a single product by ID.
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, price FROM products WHERE id = ?",
                (product_id,)
            )
            row = cursor.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Product not found")
            return {"id": row["id"], "name": row["name"], "price": row["price"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
