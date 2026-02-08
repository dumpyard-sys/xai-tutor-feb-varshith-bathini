"""
Migration: Initialize migrations table
Version: 001
Description: Creates the migrations tracking table (original scaffold migration - kept for compatibility)
"""

import sqlite3
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import DATABASE_PATH

MIGRATION_NAME = "001_create_items_table"


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
    
    # Note: Original scaffold created an 'items' table here, but it's not part of
    # the invoicing system requirements. Keeping migration for compatibility.
    
    # Record this migration
    cursor.execute("INSERT INTO _migrations (name) VALUES (?)", (MIGRATION_NAME,))
    
    conn.commit()
    conn.close()
    print(f"Migration {MIGRATION_NAME} applied successfully.")


def downgrade():
    """Revert the migration."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
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
