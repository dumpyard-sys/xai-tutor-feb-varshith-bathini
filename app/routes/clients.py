"""
Clients API Routes (Read-only - seed data)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_db

router = APIRouter(prefix="/clients", tags=["clients"])


class ClientResponse(BaseModel):
    """Schema for client response."""
    id: int
    name: str
    address: str
    company_registration_no: str


@router.get("")
def list_clients():
    """
    List all available clients.
    Clients are seed data and cannot be modified via API.
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, address, company_registration_no FROM clients ORDER BY id"
            )
            rows = cursor.fetchall()
            clients = [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "address": row["address"],
                    "company_registration_no": row["company_registration_no"]
                }
                for row in rows
            ]
            return {"clients": clients}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(client_id: int):
    """
    Get a single client by ID.
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, address, company_registration_no FROM clients WHERE id = ?",
                (client_id,)
            )
            row = cursor.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Client not found")
            return {
                "id": row["id"],
                "name": row["name"],
                "address": row["address"],
                "company_registration_no": row["company_registration_no"]
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
