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
    
    # Clear any cached imports to pick up new database path
    modules_to_remove = [k for k in sys.modules.keys() if k.startswith('app')]
    for mod in modules_to_remove:
        del sys.modules[mod]
    
    from app.database import get_connection
    from app.schema import create_tables, seed_data
    from app.main import app
    from fastapi.testclient import TestClient
    
    # Create all tables using shared schema
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create migrations table (needed for schema consistency)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Use shared schema
    create_tables(cursor)
    seed_data(cursor)
    
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
    """
    Sample invoice data for testing.
    Uses products/clients from seed data:
    - Product ID 1: Web Development Service @ $1500
    - Product ID 2: Logo Design @ $500
    - Client ID 1: Acme Corporation
    """
    return {
        "client_id": 1,
        "issue_date": "2026-02-08",
        "due_date": "2026-03-08",
        "tax": 350.0,
        "items": [
            {"product_id": 1, "quantity": 2},  # 2 x $1500 = $3000
            {"product_id": 2, "quantity": 1}   # 1 x $500 = $500
        ]
        # Subtotal: $3500, Tax: $350, Total: $3850
    }
