# Implementation Details

This document describes the design decisions, architecture, and implementation details for the invoicing system.

## Database Schema

### Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌──────────────────┐
│   clients   │       │  products   │       │    invoices      │
├─────────────┤       ├─────────────┤       ├──────────────────┤
│ id (PK)     │       │ id (PK)     │       │ id (PK)          │
│ name        │       │ name        │       │ invoice_no (UK)  │
│ address     │       │ price       │       │ issue_date       │
│ company_    │       └─────────────┘       │ due_date         │
│ registration│              │              │ client_id (FK)───┼──┐
│ _no         │              │              │ address          │  │
└─────────────┘              │              │ tax_percentage   │  │
       │                     │              │ tax_amount       │  │
       │                     │              │ subtotal         │  │
       │                     │              │ total            │  │
       │                     │              │ created_at       │  │
       │                     │              └──────────────────┘  │
       │                     │                      │             │
       │                     │              ┌───────┴────────┐    │
       │                     │              │                │    │
       │                     ▼              ▼                │    │
       │              ┌──────────────────────┐               │    │
       │              │   invoice_items      │               │    │
       │              ├──────────────────────┤               │    │
       │              │ id (PK)              │               │    │
       │              │ invoice_id (FK)──────┼───────────────┘    │
       │              │ product_id (FK)──────┘                    │
       │              │ quantity                                  │
       │              │ unit_price                                │
       │              │ line_total                                │
       └──────────────┴──────────────────────┘◄───────────────────┘
```

### Design Decisions

1. **Separate `invoice_items` table**: Allows multiple products per invoice with quantities, following standard invoice design patterns.

2. **Stored calculations**: `tax_amount` and `total` are calculated at creation time and stored. This ensures historical accuracy even if product prices change later.

3. **Unit price snapshot**: The `unit_price` in `invoice_items` captures the product price at invoice creation time, protecting historical data integrity.

4. **Auto-generated invoice numbers**: Sequential format `INV-0001`, `INV-0002` ensures unique, human-readable identifiers.

5. **Foreign key enforcement**: SQLite foreign keys are explicitly enabled via `PRAGMA foreign_keys = ON` on each connection.

## API Design

### RESTful Conventions

| Operation | HTTP Method | Status Code |
|-----------|-------------|-------------|
| Create | POST | 201 Created |
| Read (list) | GET | 200 OK |
| Read (single) | GET | 200 OK |
| Delete | DELETE | 204 No Content |
| Not Found | - | 404 Not Found |
| Validation Error | - | 400 Bad Request |
| Schema Validation | - | 422 Unprocessable Entity |

### Request Validation

- **Pydantic models** for type safety and automatic validation
- **Custom validation** for business rules:
  - Client must exist
  - All products must exist
  - `due_date` must be on or after `issue_date`
  - At least one item required
- **Clear error messages** that indicate what went wrong

## Invoice Response Fields

Per the specification, the invoice response includes:

| Field | Description |
|-------|-------------|
| `invoice_no` | Auto-generated unique identifier |
| `issue_date` | Date the invoice was issued |
| `due_date` | Payment due date |
| `client` | Full client information |
| `address` | Billing address |
| `items` | List of invoice line items |
| `tax` | Calculated tax amount |
| `total` | Final invoice total |

## Code Organization

### Following Existing Patterns

The implementation follows the patterns established in the starter code:

1. **Raw SQL queries** - No ORM, direct SQLite queries
2. **Router-based structure** - Separate files per resource
3. **Migration system** - Database changes via migration scripts
4. **Context manager for DB** - Automatic connection handling

### File Structure

```
app/
├── routes/
│   ├── health.py     # Health check endpoint
│   └── invoices.py   # Invoice CRUD operations
└── database.py       # DB connection with FK enforcement
```

## Testing Strategy

### Test Coverage

- **Integration tests**: Full request/response cycle via TestClient
- **Validation tests**: Invalid inputs, missing fields
- **Business logic tests**: Date validation, calculation verification
- **Edge cases**: Empty results, not found scenarios

### Test Count: 19 tests

| Category | Tests |
|----------|-------|
| Invoice Create | 11 (including validation) |
| Invoice List | 2 |
| Invoice Get | 2 |
| Invoice Delete | 3 |
| Health | 1 |

## Concurrency Safety

Invoice number generation handles concurrent requests by:
1. Querying the max existing invoice number
2. Attempting to use the next sequential number
3. Retrying with incremented number if collision detected
4. Fallback to timestamp-based number as last resort

## What Was NOT Implemented (Per Spec)

The specification explicitly states "For products and clients, do not create APIs—use seed data." Therefore:

- No `/products` endpoints
- No `/clients` endpoints

Products and clients are only accessible via seed data IDs when creating invoices.
