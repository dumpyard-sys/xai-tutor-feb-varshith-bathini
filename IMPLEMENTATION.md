# Implementation Details

This document describes the design decisions, architecture, and bonus features implemented in this invoicing system.

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

2. **Stored calculations**: `subtotal`, `tax_amount`, and `total` are calculated at creation time and stored. This ensures historical accuracy even if product prices change later.

3. **Unit price snapshot**: The `unit_price` in `invoice_items` captures the product price at invoice creation time, protecting historical data integrity.

4. **Auto-generated invoice numbers**: Sequential format `INV-0001`, `INV-0002` ensures unique, human-readable identifiers.

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
- **Custom validation** for business rules (e.g., client exists, product exists)
- **Clear error messages** that indicate what went wrong

## Bonus Features Implemented

### Beyond Requirements

| Feature | Description | Why It's Valuable |
|---------|-------------|-------------------|
| **Read-only Products API** | `GET /products` and `GET /products/{id}` | Helps API consumers discover available products |
| **Read-only Clients API** | `GET /clients` and `GET /clients/{id}` | Helps API consumers discover available clients |
| **Quantity Support** | Each invoice item can have a quantity | Standard invoice behavior |
| **Subtotal Field** | Separate from total | Better invoice breakdown |
| **Line Totals** | Pre-calculated per item | Reduces client-side computation |
| **Address Override** | Custom billing address option | Flexibility for different billing scenarios |
| **Created Timestamp** | `created_at` on invoices | Audit trail |
| **Integration Tests** | Full test coverage | Quality assurance |

### Calculation Logic

```
subtotal = Σ (quantity × unit_price) for each item
tax_amount = subtotal × (tax_percentage / 100)
total = subtotal + tax_amount
```

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
│   ├── invoices.py   # ~300 lines - Invoice CRUD with helpers
│   ├── products.py   # ~50 lines - Simple read endpoints
│   └── clients.py    # ~60 lines - Simple read endpoints
```

## Testing Strategy

### Test Coverage

- **Unit-style tests**: Individual endpoint behavior
- **Integration tests**: Full request/response cycle
- **Edge cases**: Invalid inputs, empty results, not found scenarios
- **Business logic**: Calculation verification

### Test Categories

| Category | Tests |
|----------|-------|
| Invoice CRUD | 14 tests |
| Products | 4 tests |
| Clients | 4 tests |
| Health | 1 test |
| **Total** | **23 tests** |

## Performance Considerations

While performance testing is machine-dependent and not included, here are considerations for production:

### Current Implementation
- **In-memory for tests**: Fast test execution
- **File-based SQLite for production**: Simple deployment
- **No connection pooling**: Acceptable for single-user system

### For Scale (Future)
- Consider PostgreSQL for concurrent access
- Add connection pooling
- Implement pagination on list endpoints
- Add database indexes on frequently queried columns

## Security Notes

This is a single-user system without authentication as per requirements. For production:

- Add authentication (JWT, OAuth, etc.)
- Implement rate limiting
- Add input sanitization (currently handled by Pydantic)
- Use HTTPS in production

## Future Enhancements

If this were a production system, consider:

1. **Invoice Updates** - PATCH endpoint to modify invoices
2. **Invoice Status** - Draft, Sent, Paid, Overdue
3. **PDF Generation** - Export invoices as PDF
4. **Email Integration** - Send invoices to clients
5. **Payment Tracking** - Record payments against invoices
6. **Recurring Invoices** - Automated invoice generation
7. **Multi-currency** - Support different currencies
8. **Audit Log** - Track all changes
