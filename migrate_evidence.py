"""
Database migration script for delivery evidence system.

Creates the delivery_evidence table for storing validated evidence.

Run this ONCE after deploying the new code:
    python migrate_evidence.py

The script is idempotent - running it multiple times is safe.
"""

import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from sqlalchemy import create_engine, text, inspect

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL is not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def table_exists(inspector, table_name: str) -> bool:
    """Check if a table exists."""
    return table_name in inspector.get_table_names()


def run_migration():
    """Run the evidence table migration."""
    inspector = inspect(engine)
    
    with engine.begin() as conn:
        print("=" * 60)
        print("COMMITMENT PROTOCOL - EVIDENCE MIGRATION")
        print("=" * 60)
        
        # ============================================================
        # Check deliveries table exists (dependency)
        # ============================================================
        if not table_exists(inspector, "deliveries"):
            print("ERROR: deliveries table does not exist!")
            print("Run the main migration first.")
            sys.exit(1)
        
        # ============================================================
        # Create delivery_evidence table
        # ============================================================
        print("\n[1/2] Creating delivery_evidence table...")
        
        if not table_exists(inspector, "delivery_evidence"):
            conn.execute(text("""
                CREATE TABLE delivery_evidence (
                    id SERIAL PRIMARY KEY,
                    delivery_id INTEGER NOT NULL REFERENCES deliveries(id),
                    type VARCHAR(20) NOT NULL,
                    url TEXT NOT NULL,
                    metadata JSONB,
                    validated BOOLEAN NOT NULL DEFAULT false,
                    validated_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # Create indexes
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_delivery_evidence_delivery_id "
                "ON delivery_evidence(delivery_id)"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_delivery_evidence_validated "
                "ON delivery_evidence(validated)"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_delivery_evidence_type "
                "ON delivery_evidence(type)"
            ))
            
            print("  ✓ delivery_evidence table created with indexes")
        else:
            print("  - delivery_evidence table already exists, skipping")
        
        # ============================================================
        # Validate migration
        # ============================================================
        print("\n[2/2] Validating migration...")
        
        # Check table exists using direct SQL (inspector may be cached)
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'delivery_evidence'
            )
        """))
        table_created = result.scalar()
        
        if not table_created:
            print("  ERROR: delivery_evidence table not created")
            sys.exit(1)
        
        print("  ✓ delivery_evidence table verified")

        
        print("\n" + "=" * 60)
        print("MIGRATION COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
        # Summary
        result = conn.execute(text("SELECT COUNT(*) FROM deliveries"))
        delivery_count = result.scalar()
        
        result = conn.execute(text("SELECT COUNT(*) FROM delivery_evidence"))
        evidence_count = result.scalar()
        
        print(f"\nDatabase summary:")
        print(f"  - Deliveries: {delivery_count}")
        print(f"  - Evidence records: {evidence_count}")
        print(f"\nYou can now start the server with: uvicorn app.main:app --reload")


if __name__ == "__main__":
    run_migration()
