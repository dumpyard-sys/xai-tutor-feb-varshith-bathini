"""
Migration: Create invoicing tables
Version: 002
Description: Creates products, clients, invoices, and invoice_items tables with seed data
"""

import sqlite3
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import DATABASE_PATH

MIGRATION_NAME = "002_create_invoicing_tables"


def upgrade():
    """Apply the migration."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create migrations tracking table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Check if this migration has already been applied
    cursor.execute("SELECT 1 FROM _migrations WHERE name = ?", (MIGRATION_NAME,))
    if cursor.fetchone():
        print(f"Migration {MIGRATION_NAME} already applied. Skipping.")
        conn.close()
        return
    
    # Create products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
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
    
    # Create invoices table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT NOT NULL UNIQUE,
            issue_date DATE NOT NULL,
            due_date DATE NOT NULL,
            client_id INTEGER NOT NULL,
            address TEXT NOT NULL,
            tax_percentage REAL NOT NULL DEFAULT 0,
            tax_amount REAL NOT NULL DEFAULT 0,
            subtotal REAL NOT NULL DEFAULT 0,
            total REAL NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
    """)
    
    # Create invoice_items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            unit_price REAL NOT NULL,
            line_total REAL NOT NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices (id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)
    
    # Seed products data
    products = [
        ("Web Development Service", 1500.00),
        ("Logo Design", 500.00),
        ("Mobile App Development", 3000.00),
        ("SEO Optimization", 750.00),
        ("Content Writing", 200.00),
        ("UI/UX Design", 1200.00),
        ("Server Maintenance", 400.00),
        ("Database Administration", 800.00),
    ]
    cursor.executemany("INSERT INTO products (name, price) VALUES (?, ?)", products)
    
    # Seed clients data
    clients = [
        ("Acme Corporation", "123 Business Ave, Suite 100, New York, NY 10001", "REG-2024-ACME-001"),
        ("TechStart Inc.", "456 Innovation Blvd, San Francisco, CA 94102", "REG-2024-TECH-002"),
        ("Global Solutions Ltd.", "789 Enterprise Way, Chicago, IL 60601", "REG-2024-GLOB-003"),
        ("Creative Media Group", "321 Design Street, Los Angeles, CA 90001", "REG-2024-CREA-004"),
        ("DataFlow Systems", "555 Analytics Road, Seattle, WA 98101", "REG-2024-DATA-005"),
    ]
    cursor.executemany(
        "INSERT INTO clients (name, address, company_registration_no) VALUES (?, ?, ?)",
        clients
    )
    
    # Record this migration
    cursor.execute("INSERT INTO _migrations (name) VALUES (?)", (MIGRATION_NAME,))
    
    conn.commit()
    conn.close()
    print(f"Migration {MIGRATION_NAME} applied successfully.")


def downgrade():
    """Revert the migration."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Drop tables in reverse order (respecting foreign keys)
    cursor.execute("DROP TABLE IF EXISTS invoice_items")
    cursor.execute("DROP TABLE IF EXISTS invoices")
    cursor.execute("DROP TABLE IF EXISTS clients")
    cursor.execute("DROP TABLE IF EXISTS products")
    
    # Remove migration record
    cursor.execute("DELETE FROM _migrations WHERE name = ?", (MIGRATION_NAME,))
    
    conn.commit()
    conn.close()
    print(f"Migration {MIGRATION_NAME} reverted successfully.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run database migration")
    parser.add_argument(
        "action",
        choices=["upgrade", "downgrade"],
        help="Migration action to perform"
    )
    
    args = parser.parse_args()
    
    if args.action == "upgrade":
        upgrade()
    elif args.action == "downgrade":
        downgrade()
