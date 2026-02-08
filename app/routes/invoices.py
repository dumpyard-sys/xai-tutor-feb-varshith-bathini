"""
Invoice Management API Routes
"""

from datetime import date
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from app.database import get_db

router = APIRouter(prefix="/invoices", tags=["invoices"])


# ============================================================================
# Pydantic Models
# ============================================================================

class InvoiceItemCreate(BaseModel):
    """Schema for creating an invoice item."""
    product_id: int
    quantity: int = Field(default=1, ge=1)


class InvoiceCreate(BaseModel):
    """Schema for creating an invoice."""
    client_id: int
    address: Optional[str] = None  # If not provided, uses client's address
    issue_date: date
    due_date: date
    # Accept both 'tax' and 'tax_percentage' - spec says 'tax', we treat as percentage
    tax: float = Field(default=0.0, ge=0.0, le=100.0, alias="tax_percentage")
    items: List[InvoiceItemCreate] = Field(..., min_length=1)

    model_config = {"populate_by_name": True}  # Allow both field name and alias

    @model_validator(mode='after')
    def validate_dates(self):
        """Ensure due_date is on or after issue_date."""
        if self.due_date < self.issue_date:
            raise ValueError('due_date must be on or after issue_date')
        return self


class InvoiceItemResponse(BaseModel):
    """Schema for invoice item in response."""
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    line_total: float


class ClientResponse(BaseModel):
    """Schema for client in response."""
    id: int
    name: str
    address: str
    company_registration_no: str


class InvoiceResponse(BaseModel):
    """Schema for full invoice response."""
    id: int
    invoice_no: str
    issue_date: date
    due_date: date
    client: ClientResponse
    address: str
    items: List[InvoiceItemResponse]
    tax: float  # Required field per spec
    total: float


class InvoiceListItem(BaseModel):
    """Schema for invoice in list view."""
    id: int
    invoice_no: str
    issue_date: date
    due_date: date
    client_name: str
    item_count: int
    tax: float
    total: float


class InvoiceListResponse(BaseModel):
    """Schema for list invoices response."""
    invoices: List[InvoiceListItem]


# ============================================================================
# Helper Functions
# ============================================================================

def generate_invoice_number(cursor) -> str:
    """
    Generate a unique sequential invoice number.
    Simple approach: get max existing number and increment.
    UNIQUE constraint on invoice_no column ensures no duplicates.
    """
    cursor.execute("SELECT MAX(CAST(SUBSTR(invoice_no, 5) AS INTEGER)) FROM invoices")
    result = cursor.fetchone()
    next_num = (result[0] or 0) + 1
    return f"INV-{next_num:04d}"


def get_client_by_id(cursor, client_id: int) -> dict:
    """Fetch a client by ID."""
    cursor.execute(
        "SELECT id, name, address, company_registration_no FROM clients WHERE id = ?",
        (client_id,)
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return {
        "id": row["id"],
        "name": row["name"],
        "address": row["address"],
        "company_registration_no": row["company_registration_no"]
    }


def get_product_by_id(cursor, product_id: int) -> dict:
    """Fetch a product by ID."""
    cursor.execute("SELECT id, name, price FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    if row is None:
        return None
    return {"id": row["id"], "name": row["name"], "price": row["price"]}


def get_invoice_items(cursor, invoice_id: int) -> list:
    """Fetch all items for an invoice."""
    cursor.execute("""
        SELECT ii.id, ii.product_id, p.name as product_name, ii.quantity, 
               ii.unit_price, ii.line_total
        FROM invoice_items ii
        JOIN products p ON ii.product_id = p.id
        WHERE ii.invoice_id = ?
        ORDER BY ii.id
    """, (invoice_id,))
    rows = cursor.fetchall()
    return [
        {
            "id": row["id"],
            "product_id": row["product_id"],
            "product_name": row["product_name"],
            "quantity": row["quantity"],
            "unit_price": row["unit_price"],
            "line_total": row["line_total"]
        }
        for row in rows
    ]


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("", response_model=InvoiceListResponse)
def list_invoices():
    """
    List all invoices with summary information.
    Returns invoice list with client name, item count, and total.
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    i.id, i.invoice_no, i.issue_date, i.due_date, 
                    i.tax_amount, i.total,
                    c.name as client_name,
                    (SELECT COUNT(*) FROM invoice_items WHERE invoice_id = i.id) as item_count
                FROM invoices i
                JOIN clients c ON i.client_id = c.id
                ORDER BY i.id DESC
            """)
            rows = cursor.fetchall()
            invoices = [
                InvoiceListItem(
                    id=row["id"],
                    invoice_no=row["invoice_no"],
                    issue_date=row["issue_date"],
                    due_date=row["due_date"],
                    client_name=row["client_name"],
                    item_count=row["item_count"],
                    tax=row["tax_amount"],
                    total=row["total"]
                )
                for row in rows
            ]
            return InvoiceListResponse(invoices=invoices)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: int):
    """
    Get a single invoice by ID with full details.
    Includes client information and all line items.
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Fetch invoice
            cursor.execute("""
                SELECT i.id, i.invoice_no, i.issue_date, i.due_date, i.client_id,
                       i.address, i.tax_amount, i.total
                FROM invoices i
                WHERE i.id = ?
            """, (invoice_id,))
            row = cursor.fetchone()
            
            if row is None:
                raise HTTPException(status_code=404, detail="Invoice not found")
            
            # Fetch client
            client = get_client_by_id(cursor, row["client_id"])
            
            # Fetch items
            items = get_invoice_items(cursor, invoice_id)
            
            return InvoiceResponse(
                id=row["id"],
                invoice_no=row["invoice_no"],
                issue_date=row["issue_date"],
                due_date=row["due_date"],
                client=ClientResponse(**client),
                address=row["address"],
                items=[InvoiceItemResponse(**item) for item in items],
                tax=row["tax_amount"],
                total=row["total"]
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("", status_code=201, response_model=InvoiceResponse)
def create_invoice(invoice: InvoiceCreate):
    """
    Create a new invoice.
    - Auto-generates invoice number (INV-0001, INV-0002, etc.)
    - Calculates tax and total automatically
    - Uses client's address if not provided
    - Accepts 'tax' or 'tax_percentage' as input (percentage value)
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Validate client exists
            client = get_client_by_id(cursor, invoice.client_id)
            if client is None:
                raise HTTPException(status_code=400, detail="Client not found")
            
            # Use client's address if not provided
            address = invoice.address if invoice.address else client["address"]
            
            # Validate all products exist and calculate totals
            subtotal = 0.0
            item_details = []
            
            for item in invoice.items:
                product = get_product_by_id(cursor, item.product_id)
                if product is None:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Product with id {item.product_id} not found"
                    )
                
                line_total = product["price"] * item.quantity
                subtotal += line_total
                item_details.append({
                    "product_id": item.product_id,
                    "product_name": product["name"],
                    "quantity": item.quantity,
                    "unit_price": product["price"],
                    "line_total": line_total
                })
            
            # Calculate tax and total (invoice.tax is the percentage)
            tax_amount = subtotal * (invoice.tax / 100)
            total = subtotal + tax_amount
            
            # Generate invoice number
            invoice_no = generate_invoice_number(cursor)
            
            # Insert invoice
            cursor.execute("""
                INSERT INTO invoices (
                    invoice_no, issue_date, due_date, client_id, address,
                    tax_percentage, tax_amount, subtotal, total
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_no,
                invoice.issue_date.isoformat(),
                invoice.due_date.isoformat(),
                invoice.client_id,
                address,
                invoice.tax,
                tax_amount,
                subtotal,
                total
            ))
            invoice_id = cursor.lastrowid
            
            # Insert invoice items
            items_response = []
            for detail in item_details:
                cursor.execute("""
                    INSERT INTO invoice_items (
                        invoice_id, product_id, quantity, unit_price, line_total
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    invoice_id,
                    detail["product_id"],
                    detail["quantity"],
                    detail["unit_price"],
                    detail["line_total"]
                ))
                items_response.append(InvoiceItemResponse(
                    id=cursor.lastrowid,
                    product_id=detail["product_id"],
                    product_name=detail["product_name"],
                    quantity=detail["quantity"],
                    unit_price=detail["unit_price"],
                    line_total=detail["line_total"]
                ))
            
            return InvoiceResponse(
                id=invoice_id,
                invoice_no=invoice_no,
                issue_date=invoice.issue_date,
                due_date=invoice.due_date,
                client=ClientResponse(**client),
                address=address,
                items=items_response,
                tax=tax_amount,
                total=total
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete("/{invoice_id}", status_code=204)
def delete_invoice(invoice_id: int):
    """
    Delete an invoice by ID.
    Also deletes all associated invoice items (cascade).
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if invoice exists
            cursor.execute("SELECT id FROM invoices WHERE id = ?", (invoice_id,))
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Invoice not found")
            
            # Delete invoice items first (explicit delete for safety)
            cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
            
            # Delete invoice
            cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
            
            return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
