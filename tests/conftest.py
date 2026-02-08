"""
Pytest configuration and fixtures for integration tests.
"""

import os
import sys
import tempfile
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="function")
def client():
    """
    Create a test client with a fresh temporary database for each test.
    """
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    
    # Set database path before importing app modules
    os.environ["DATABASE_PATH"] = db_path
    
    # Import after setting env var - need to reimport to pick up new path
    # Clear any cached imports
    modules_to_remove = [k for k in sys.modules.keys() if k.startswith('app')]
    for mod in modules_to_remove:
        del sys.modules[mod]
    
    from app.database import get_connection
    from app.main import app
    from fastapi.testclient import TestClient
    
    # Create all tables
    conn = get_connection()
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            company_registration_no TEXT NOT NULL
        )
    """)
    
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
    
    # Seed test data
    cursor.executemany(
        "INSERT INTO products (name, price) VALUES (?, ?)",
        [
            ("Web Development", 1500.00),
            ("Logo Design", 500.00),
            ("SEO Service", 750.00),
        ]
    )
    
    cursor.executemany(
        "INSERT INTO clients (name, address, company_registration_no) VALUES (?, ?, ?)",
        [
            ("Acme Corp", "123 Main St, New York, NY 10001", "REG-001"),
            ("TechStart Inc", "456 Tech Blvd, San Francisco, CA 94102", "REG-002"),
        ]
    )
    
    conn.commit()
    conn.close()
    
    # Create test client
    with TestClient(app) as test_client:
        yield test_client
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def sample_invoice_data():
    """Sample invoice data for testing."""
    return {
        "client_id": 1,
        "issue_date": "2026-02-08",
        "due_date": "2026-03-08",
        "tax_percentage": 10.0,
        "items": [
            {"product_id": 1, "quantity": 2},
            {"product_id": 2, "quantity": 1}
        ]
    }
