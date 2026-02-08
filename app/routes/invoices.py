"""
Invoice Management API Routes
"""

import sqlite3
import logging
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from app.database import get_db

router = APIRouter(prefix="/invoices", tags=["invoices"])
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models
# ============================================================================

class InvoiceItemCreate(BaseModel):
    """Schema for creating an invoice item."""
    product_id: int
    quantity: int = Field(default=1, ge=1)


class InvoiceItemUpdate(BaseModel):
    """Schema for updating an invoice item."""
    product_id: int
    quantity: int = Field(ge=1)


class InvoiceCreate(BaseModel):
    """Schema for creating an invoice."""
    client_id: int
    address: Optional[str] = Field(default=None, max_length=500)
    issue_date: date
    due_date: date
    tax: float = Field(default=0.0, ge=0.0, description="Tax amount to apply")
    items: List[InvoiceItemCreate] = Field(..., min_length=1)

    @model_validator(mode='after')
    def validate_dates(self):
        """Ensure due_date is on or after issue_date."""
        if self.due_date < self.issue_date:
            raise ValueError('due_date must be on or after issue_date')
        return self


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""
    client_id: Optional[int] = None
    address: Optional[str] = Field(default=None, max_length=500)
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    tax: Optional[float] = Field(default=None, ge=0.0)
    items: Optional[List[InvoiceItemUpdate]] = Field(default=None, min_length=1)

    @model_validator(mode='after')
    def validate_dates(self):
        """Ensure due_date is on or after issue_date when both are provided."""
        if self.issue_date is not None and self.due_date is not None:
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
    tax: float
    subtotal: float
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
    """Schema for list invoices response with pagination."""
    invoices: List[InvoiceListItem]
    total_count: int
    limit: int
    offset: int


# ============================================================================
# Helper Functions
# ============================================================================

def generate_next_invoice_number(cursor) -> str:
    """
    Generate the next sequential invoice number based on existing invoices.
    """
    cursor.execute("SELECT MAX(CAST(SUBSTR(invoice_no, 5) AS INTEGER)) FROM invoices")
    result = cursor.fetchone()
    next_num = (result[0] or 0) + 1
    return f"INV-{next_num:04d}"


def get_client_by_id(cursor, client_id: int) -> Optional[dict]:
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


def get_product_by_id(cursor, product_id: int) -> Optional[dict]:
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


def calculate_items_and_totals(cursor, items: list, tax: float) -> tuple:
    """
    Validate products and calculate item details and totals.
    Returns: (item_details, subtotal, total)
    Raises HTTPException if any product is invalid.
    """
    subtotal = 0.0
    item_details = []
    
    for item in items:
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
    
    total = subtotal + tax
    return item_details, subtotal, total


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("", response_model=InvoiceListResponse)
def list_invoices(
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of invoices to return"),
    offset: int = Query(default=0, ge=0, description="Number of invoices to skip"),
    client_id: Optional[int] = Query(default=None, description="Filter by client ID"),
    issue_date_from: Optional[date] = Query(default=None, description="Filter by issue date (from)"),
    issue_date_to: Optional[date] = Query(default=None, description="Filter by issue date (to)"),
    due_date_from: Optional[date] = Query(default=None, description="Filter by due date (from)"),
    due_date_to: Optional[date] = Query(default=None, description="Filter by due date (to)"),
):
    """
    List invoices with pagination and filtering.
    
    - **limit**: Maximum number of invoices to return (1-100, default 20)
    - **offset**: Number of invoices to skip for pagination
    - **client_id**: Filter by specific client
    - **issue_date_from/to**: Filter by issue date range
    - **due_date_from/to**: Filter by due date range
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Build dynamic query with filters
            base_query = """
                SELECT 
                    i.id, i.invoice_no, i.issue_date, i.due_date, 
                    i.tax, i.total,
                    c.name as client_name,
                    (SELECT COUNT(*) FROM invoice_items WHERE invoice_id = i.id) as item_count
                FROM invoices i
                JOIN clients c ON i.client_id = c.id
            """
            count_query = """
                SELECT COUNT(*) FROM invoices i
                JOIN clients c ON i.client_id = c.id
            """
            
            # Build WHERE clause
            conditions = []
            params = []
            
            if client_id is not None:
                conditions.append("i.client_id = ?")
                params.append(client_id)
            
            if issue_date_from is not None:
                conditions.append("i.issue_date >= ?")
                params.append(issue_date_from.isoformat())
            
            if issue_date_to is not None:
                conditions.append("i.issue_date <= ?")
                params.append(issue_date_to.isoformat())
            
            if due_date_from is not None:
                conditions.append("i.due_date >= ?")
                params.append(due_date_from.isoformat())
            
            if due_date_to is not None:
                conditions.append("i.due_date <= ?")
                params.append(due_date_to.isoformat())
            
            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)
            
            # Get total count
            cursor.execute(count_query + where_clause, params)
            total_count = cursor.fetchone()[0]
            
            # Get paginated results
            full_query = base_query + where_clause + " ORDER BY i.id DESC LIMIT ? OFFSET ?"
            cursor.execute(full_query, params + [limit, offset])
            rows = cursor.fetchall()
            
            invoices = [
                InvoiceListItem(
                    id=row["id"],
                    invoice_no=row["invoice_no"],
                    issue_date=row["issue_date"],
                    due_date=row["due_date"],
                    client_name=row["client_name"],
                    item_count=row["item_count"],
                    tax=row["tax"],
                    total=row["total"]
                )
                for row in rows
            ]
            
            return InvoiceListResponse(
                invoices=invoices,
                total_count=total_count,
                limit=limit,
                offset=offset
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error listing invoices")
        raise HTTPException(status_code=500, detail="An error occurred while listing invoices")


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
                       i.address, i.tax, i.subtotal, i.total
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
                tax=row["tax"],
                subtotal=row["subtotal"],
                total=row["total"]
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error getting invoice %s", invoice_id)
        raise HTTPException(status_code=500, detail="An error occurred while retrieving the invoice")


@router.post("", status_code=201, response_model=InvoiceResponse)
def create_invoice(invoice: InvoiceCreate):
    """
    Create a new invoice.
    
    - Auto-generates invoice number (INV-0001, INV-0002, etc.)
    - Uses client's address if not provided
    - The 'tax' field is the tax amount to add to the subtotal
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
            
            # Validate products and calculate totals
            item_details, subtotal, total = calculate_items_and_totals(
                cursor, invoice.items, invoice.tax
            )
            
            # Insert invoice with retry for concurrency safety
            max_retries = 5
            invoice_id = None
            invoice_no = None
            
            for attempt in range(max_retries):
                invoice_no = generate_next_invoice_number(cursor)
                try:
                    cursor.execute("""
                        INSERT INTO invoices (
                            invoice_no, issue_date, due_date, client_id, address,
                            tax, subtotal, total
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        invoice_no,
                        invoice.issue_date.isoformat(),
                        invoice.due_date.isoformat(),
                        invoice.client_id,
                        address,
                        invoice.tax,
                        subtotal,
                        total
                    ))
                    invoice_id = cursor.lastrowid
                    break
                except sqlite3.IntegrityError as e:
                    if "UNIQUE constraint failed: invoices.invoice_no" in str(e):
                        conn.rollback()
                        continue
                    raise
            
            if invoice_id is None:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to generate unique invoice number"
                )
            
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
                tax=invoice.tax,
                subtotal=subtotal,
                total=total
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error creating invoice")
        raise HTTPException(status_code=500, detail="An error occurred while creating the invoice")


@router.put("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(invoice_id: int, invoice: InvoiceUpdate):
    """
    Update an existing invoice.
    
    - Only provided fields will be updated
    - If items are provided, they completely replace existing items
    - Invoice number cannot be changed
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if invoice exists
            cursor.execute("""
                SELECT id, invoice_no, issue_date, due_date, client_id, address, tax, subtotal, total
                FROM invoices WHERE id = ?
            """, (invoice_id,))
            existing = cursor.fetchone()
            
            if existing is None:
                raise HTTPException(status_code=404, detail="Invoice not found")
            
            # Build update values
            new_client_id = invoice.client_id if invoice.client_id is not None else existing["client_id"]
            new_issue_date = invoice.issue_date if invoice.issue_date is not None else existing["issue_date"]
            new_due_date = invoice.due_date if invoice.due_date is not None else existing["due_date"]
            new_tax = invoice.tax if invoice.tax is not None else existing["tax"]
            
            # Validate dates
            if isinstance(new_issue_date, str):
                new_issue_date = date.fromisoformat(new_issue_date)
            if isinstance(new_due_date, str):
                new_due_date = date.fromisoformat(new_due_date)
            
            if new_due_date < new_issue_date:
                raise HTTPException(
                    status_code=400,
                    detail="due_date must be on or after issue_date"
                )
            
            # Validate client if changed
            client = get_client_by_id(cursor, new_client_id)
            if client is None:
                raise HTTPException(status_code=400, detail="Client not found")
            
            # Handle address
            if invoice.address is not None:
                new_address = invoice.address
            elif invoice.client_id is not None:
                # Client changed, use new client's address
                new_address = client["address"]
            else:
                new_address = existing["address"]
            
            # Handle items update
            if invoice.items is not None:
                # Validate products and calculate new totals
                item_details, subtotal, total = calculate_items_and_totals(
                    cursor, invoice.items, new_tax
                )
                
                # Delete old items and insert new ones
                cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
                
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
            else:
                # Keep existing items, just recalculate if tax changed
                subtotal = existing["subtotal"]
                total = subtotal + new_tax
            
            # Update invoice
            cursor.execute("""
                UPDATE invoices
                SET issue_date = ?, due_date = ?, client_id = ?, address = ?,
                    tax = ?, subtotal = ?, total = ?
                WHERE id = ?
            """, (
                new_issue_date.isoformat() if isinstance(new_issue_date, date) else new_issue_date,
                new_due_date.isoformat() if isinstance(new_due_date, date) else new_due_date,
                new_client_id,
                new_address,
                new_tax,
                subtotal,
                total,
                invoice_id
            ))
            
            # Fetch and return updated invoice
            items = get_invoice_items(cursor, invoice_id)
            
            return InvoiceResponse(
                id=invoice_id,
                invoice_no=existing["invoice_no"],
                issue_date=new_issue_date,
                due_date=new_due_date,
                client=ClientResponse(**client),
                address=new_address,
                items=[InvoiceItemResponse(**item) for item in items],
                tax=new_tax,
                subtotal=subtotal,
                total=total
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error updating invoice %s", invoice_id)
        raise HTTPException(status_code=500, detail="An error occurred while updating the invoice")


@router.delete("/{invoice_id}", status_code=204)
def delete_invoice(invoice_id: int):
    """
    Delete an invoice by ID.
    Associated invoice items are automatically deleted via CASCADE.
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if invoice exists
            cursor.execute("SELECT id FROM invoices WHERE id = ?", (invoice_id,))
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Invoice not found")
            
            # Delete invoice (items are deleted via ON DELETE CASCADE)
            cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
            
            return None
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error deleting invoice %s", invoice_id)
        raise HTTPException(status_code=500, detail="An error occurred while deleting the invoice")
