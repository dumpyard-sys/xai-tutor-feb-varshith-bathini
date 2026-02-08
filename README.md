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
| GET | `/invoices` | List invoices (with pagination & filtering) |
| GET | `/invoices/{id}` | Get invoice by ID |
| POST | `/invoices` | Create a new invoice |
| PUT | `/invoices/{id}` | Update an existing invoice |
| DELETE | `/invoices/{id}` | Delete an invoice |

#### Query Parameters for GET `/invoices`
| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | int | Max results (1-100, default: 20) |
| `offset` | int | Skip N results (default: 0) |
| `client_id` | int | Filter by client |
| `issue_date_from` | date | Filter by issue date (from) |
| `issue_date_to` | date | Filter by issue date (to) |
| `due_date_from` | date | Filter by due date (from) |
| `due_date_to` | date | Filter by due date (to) |

## Creating an Invoice

```bash
curl -X POST http://localhost:8000/invoices \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "issue_date": "2026-02-08",
    "due_date": "2026-03-08",
    "tax": 350.0,
    "items": [
      {"product_id": 1, "quantity": 2},
      {"product_id": 2, "quantity": 1}
    ]
  }'
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `client_id` | integer | Yes | ID of the client (from seed data) |
| `issue_date` | string (date) | Yes | Invoice issue date (YYYY-MM-DD) |
| `due_date` | string (date) | Yes | Invoice due date (must be >= issue_date) |
| `tax` | float | No | Tax amount to add (default: 0) |
| `address` | string | No | Billing address (defaults to client's address) |
| `items` | array | Yes | List of invoice items (min 1) |
| `items[].product_id` | integer | Yes | ID of the product (from seed data) |
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
  "tax": 350.0,
  "subtotal": 3000.0,
  "total": 3350.0
}
```

## Running Tests

```bash
# Install test dependencies
pip install pytest httpx

# Run all tests
pytest tests/ -v
```

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # Database connection handling
│   ├── schema.py            # Shared database schema definitions
│   └── routes/
│       ├── __init__.py
│       ├── health.py        # Health check endpoint
│       └── invoices.py      # Invoice CRUD endpoints
├── migrations/
│   └── 001_create_invoicing_tables.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Test fixtures
│   ├── test_health.py
│   └── test_invoices.py
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

Products and clients are pre-seeded and accessed by ID when creating invoices.

### Products (8 items)
| ID | Name | Price |
|----|------|-------|
| 1 | Web Development Service | $1,500 |
| 2 | Logo Design | $500 |
| 3 | Mobile App Development | $3,000 |
| 4 | SEO Optimization | $750 |
| 5 | Content Writing | $200 |
| 6 | UI/UX Design | $1,200 |
| 7 | Server Maintenance | $400 |
| 8 | Database Administration | $800 |

### Clients (5 companies)
| ID | Name | Registration No. |
|----|------|------------------|
| 1 | Acme Corporation | REG-2024-ACME-001 |
| 2 | TechStart Inc. | REG-2024-TECH-002 |
| 3 | Global Solutions Ltd. | REG-2024-GLOB-003 |
| 4 | Creative Media Group | REG-2024-CREA-004 |
| 5 | DataFlow Systems | REG-2024-DATA-005 |

## License

This project was created as part of a backend assessment.
