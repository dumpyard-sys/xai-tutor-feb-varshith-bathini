# Invoicing System API

A RESTful API for managing invoices, built with FastAPI and SQLite.

## Quick Start

```bash
docker-compose up --build
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs (Swagger)**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## API Endpoints

### Health Check
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check endpoint |

### Invoices
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/invoices` | List all invoices |
| GET | `/invoices/{id}` | Get invoice by ID |
| POST | `/invoices` | Create a new invoice |
| DELETE | `/invoices/{id}` | Delete an invoice |

### Products (Read-only)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/products` | List all products |
| GET | `/products/{id}` | Get product by ID |

### Clients (Read-only)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/clients` | List all clients |
| GET | `/clients/{id}` | Get client by ID |

## Creating an Invoice

```bash
curl -X POST http://localhost:8000/invoices \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "issue_date": "2026-02-08",
    "due_date": "2026-03-08",
    "tax_percentage": 10.0,
    "items": [
      {"product_id": 1, "quantity": 2},
      {"product_id": 2, "quantity": 1}
    ]
  }'
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `client_id` | integer | Yes | ID of the client |
| `issue_date` | string (date) | Yes | Invoice issue date (YYYY-MM-DD) |
| `due_date` | string (date) | Yes | Invoice due date (YYYY-MM-DD) |
| `tax_percentage` | float | No | Tax percentage (default: 0) |
| `address` | string | No | Billing address (defaults to client's address) |
| `items` | array | Yes | List of invoice items (min 1) |
| `items[].product_id` | integer | Yes | ID of the product |
| `items[].quantity` | integer | No | Quantity (default: 1) |

### Response

```json
{
  "id": 1,
  "invoice_no": "INV-0001",
  "issue_date": "2026-02-08",
  "due_date": "2026-03-08",
  "client": {
    "id": 1,
    "name": "Acme Corporation",
    "address": "123 Business Ave, Suite 100, New York, NY 10001",
    "company_registration_no": "REG-2024-ACME-001"
  },
  "address": "123 Business Ave, Suite 100, New York, NY 10001",
  "items": [
    {
      "id": 1,
      "product_id": 1,
      "product_name": "Web Development Service",
      "quantity": 2,
      "unit_price": 1500.0,
      "line_total": 3000.0
    }
  ],
  "subtotal": 3500.0,
  "tax_percentage": 10.0,
  "tax_amount": 350.0,
  "total": 3850.0
}
```

## Running Tests

```bash
# Install test dependencies
pip install pytest

# Run all tests
pytest tests/ -v

# Run with coverage (if pytest-cov installed)
pytest tests/ -v --cov=app
```

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # Database connection handling
│   └── routes/
│       ├── __init__.py
│       ├── health.py        # Health check endpoint
│       ├── invoices.py      # Invoice CRUD endpoints
│       ├── products.py      # Products read endpoint
│       └── clients.py       # Clients read endpoint
├── migrations/
│   ├── 001_create_items_table.py
│   └── 002_create_invoicing_tables.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Test fixtures
│   ├── test_health.py
│   ├── test_invoices.py
│   ├── test_products.py
│   └── test_clients.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── migrate.py               # Migration runner
├── ASSESSMENT.md            # Original assessment instructions
├── IMPLEMENTATION.md        # Implementation details
└── README.md                # This file
```

## Manual Setup (Without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python migrate.py upgrade

# Start server
uvicorn app.main:app --reload
```

## Database Migrations

```bash
# Apply migrations
python migrate.py upgrade

# Revert migrations
python migrate.py downgrade

# List migration status
python migrate.py list
```

## Seed Data

The application comes with pre-seeded data:

### Products (8 items)
- Web Development Service ($1,500)
- Logo Design ($500)
- Mobile App Development ($3,000)
- SEO Optimization ($750)
- Content Writing ($200)
- UI/UX Design ($1,200)
- Server Maintenance ($400)
- Database Administration ($800)

### Clients (5 companies)
- Acme Corporation
- TechStart Inc.
- Global Solutions Ltd.
- Creative Media Group
- DataFlow Systems

## License

This project was created as part of a backend assessment.
