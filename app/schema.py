"""
Shared database schema definitions.
This module provides schema creation functions used by both migrations and tests.
"""

# Seed data for products
PRODUCTS_SEED_DATA = [
    ("Web Development Service", 1500.00),
    ("Logo Design", 500.00),
    ("Mobile App Development", 3000.00),
    ("SEO Optimization", 750.00),
    ("Content Writing", 200.00),
    ("UI/UX Design", 1200.00),
    ("Server Maintenance", 400.00),
    ("Database Administration", 800.00),
]

# Seed data for clients
CLIENTS_SEED_DATA = [
    ("Acme Corporation", "123 Business Ave, Suite 100, New York, NY 10001", "REG-2024-ACME-001"),
    ("TechStart Inc.", "456 Innovation Blvd, San Francisco, CA 94102", "REG-2024-TECH-002"),
    ("Global Solutions Ltd.", "789 Enterprise Way, Chicago, IL 60601", "REG-2024-GLOB-003"),
    ("Creative Media Group", "321 Design Street, Los Angeles, CA 90001", "REG-2024-CREA-004"),
    ("DataFlow Systems", "555 Analytics Road, Seattle, WA 98101", "REG-2024-DATA-005"),
]


def create_tables(cursor):
    """
    Create all application tables.
    This function is idempotent - safe to call multiple times.
    """
    # Create products table with CHECK constraint for positive prices
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL CHECK(price > 0)
        )
    """)
    
    # Create clients table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            company_registration_no TEXT NOT NULL
        )
    """)
    
    # Create invoices table with CHECK constraints
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT NOT NULL UNIQUE,
            issue_date DATE NOT NULL,
            due_date DATE NOT NULL,
            client_id INTEGER NOT NULL,
            address TEXT NOT NULL,
            tax REAL NOT NULL DEFAULT 0 CHECK(tax >= 0),
            subtotal REAL NOT NULL DEFAULT 0 CHECK(subtotal >= 0),
            total REAL NOT NULL DEFAULT 0 CHECK(total >= 0),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
    """)
    
    # Create indexes for frequently queried fields
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_client_id ON invoices(client_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_issue_date ON invoices(issue_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_due_date ON invoices(due_date)")
    
    # Create invoice_items table with CHECK constraints
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1 CHECK(quantity > 0),
            unit_price REAL NOT NULL CHECK(unit_price > 0),
            line_total REAL NOT NULL CHECK(line_total > 0),
            FOREIGN KEY (invoice_id) REFERENCES invoices (id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)
    
    # Create index on invoice_items for faster joins
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice_id ON invoice_items(invoice_id)")


def drop_tables(cursor):
    """
    Drop all application tables in correct order (respecting foreign keys).
    """
    # Drop indexes first
    cursor.execute("DROP INDEX IF EXISTS idx_invoices_client_id")
    cursor.execute("DROP INDEX IF EXISTS idx_invoices_issue_date")
    cursor.execute("DROP INDEX IF EXISTS idx_invoices_due_date")
    cursor.execute("DROP INDEX IF EXISTS idx_invoice_items_invoice_id")
    
    # Drop tables in reverse order (respecting foreign keys)
    cursor.execute("DROP TABLE IF EXISTS invoice_items")
    cursor.execute("DROP TABLE IF EXISTS invoices")
    cursor.execute("DROP TABLE IF EXISTS clients")
    cursor.execute("DROP TABLE IF EXISTS products")


def seed_data(cursor):
    """
    Insert seed data for products and clients.
    """
    cursor.executemany(
        "INSERT INTO products (name, price) VALUES (?, ?)",
        PRODUCTS_SEED_DATA
    )
    cursor.executemany(
        "INSERT INTO clients (name, address, company_registration_no) VALUES (?, ?, ?)",
        CLIENTS_SEED_DATA
    )
