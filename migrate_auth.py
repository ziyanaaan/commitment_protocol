"""
Database migration script for authentication system.

This script safely adds authentication columns to the existing users table
and creates the audit_logs table, without affecting existing data.

Run this ONCE after deploying the new code:
    python migrate_auth.py

The script is idempotent - running it multiple times is safe.
"""

import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from ulid import ULID

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL is not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def column_exists(inspector, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def table_exists(inspector, table_name: str) -> bool:
    """Check if a table exists."""
    return table_name in inspector.get_table_names()


def run_migration():
    """Run the authentication migration."""
    inspector = inspect(engine)
    
    with engine.begin() as conn:
        print("=" * 60)
        print("COMMITMENT PROTOCOL - AUTH MIGRATION")
        print("=" * 60)
        
        # ============================================================
        # STEP 1: Add authentication columns to users table
        # ============================================================
        print("\n[1/4] Adding authentication columns to users table...")
        
        if not table_exists(inspector, "users"):
            print("  ERROR: users table does not exist!")
            sys.exit(1)
        
        # Add public_id column
        if not column_exists(inspector, "users", "public_id"):
            print("  - Adding public_id column...")
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN public_id VARCHAR(40) UNIQUE
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_public_id ON users(public_id)"))
            print("    ✓ public_id column added")
        else:
            print("  - public_id column already exists, skipping")
        
        # Add password_hash column
        if not column_exists(inspector, "users", "password_hash"):
            print("  - Adding password_hash column...")
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN password_hash VARCHAR(255)
            """))
            print("    ✓ password_hash column added")
        else:
            print("  - password_hash column already exists, skipping")
        
        # Add is_active column
        if not column_exists(inspector, "users", "is_active"):
            print("  - Adding is_active column...")
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true
            """))
            print("    ✓ is_active column added")
        else:
            print("  - is_active column already exists, skipping")
        
        # Add is_verified column
        if not column_exists(inspector, "users", "is_verified"):
            print("  - Adding is_verified column...")
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN is_verified BOOLEAN NOT NULL DEFAULT false
            """))
            print("    ✓ is_verified column added")
        else:
            print("  - is_verified column already exists, skipping")
        
        # Add failed_login_attempts column
        if not column_exists(inspector, "users", "failed_login_attempts"):
            print("  - Adding failed_login_attempts column...")
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0
            """))
            print("    ✓ failed_login_attempts column added")
        else:
            print("  - failed_login_attempts column already exists, skipping")
        
        # Add locked_until column
        if not column_exists(inspector, "users", "locked_until"):
            print("  - Adding locked_until column...")
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN locked_until TIMESTAMP WITH TIME ZONE
            """))
            print("    ✓ locked_until column added")
        else:
            print("  - locked_until column already exists, skipping")
        
        # Add updated_at column
        if not column_exists(inspector, "users", "updated_at"):
            print("  - Adding updated_at column...")
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE
            """))
            print("    ✓ updated_at column added")
        else:
            print("  - updated_at column already exists, skipping")
        
        # ============================================================
        # STEP 2: Create audit_logs table
        # ============================================================
        print("\n[2/4] Creating audit_logs table...")
        
        if not table_exists(inspector, "audit_logs"):
            conn.execute(text("""
                CREATE TABLE audit_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    event_type VARCHAR(50) NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent VARCHAR(500),
                    details JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_audit_logs_event_type ON audit_logs(event_type)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs(created_at)"))
            print("  ✓ audit_logs table created with indexes")
        else:
            print("  - audit_logs table already exists, skipping")
        
        # ============================================================
        # STEP 3: Generate public_ids for existing users
        # ============================================================
        print("\n[3/4] Generating public_ids for existing users...")
        
        result = conn.execute(text("""
            SELECT id, email, role FROM users WHERE public_id IS NULL
        """))
        users_without_public_id = result.fetchall()
        
        if users_without_public_id:
            prefix_map = {
                "client": "cli",
                "freelancer": "fre",
                "admin": "adm",
            }
            
            for user_id, email, role in users_without_public_id:
                prefix = prefix_map.get(role, "usr")
                public_id = f"{prefix}_{ULID()}"
                
                conn.execute(text("""
                    UPDATE users SET public_id = :public_id WHERE id = :user_id
                """), {"public_id": public_id, "user_id": user_id})
                
                print(f"  - User {email}: {public_id}")
            
            print(f"  ✓ Generated public_ids for {len(users_without_public_id)} users")
        else:
            print("  - All users already have public_ids")
        
        # ============================================================
        # STEP 4: Validate migration
        # ============================================================
        print("\n[4/4] Validating migration...")
        
        # Recheck columns
        inspector = inspect(engine)
        
        required_columns = [
            "public_id", "password_hash", "is_active", "is_verified",
            "failed_login_attempts", "locked_until", "updated_at"
        ]
        
        missing_columns = []
        for col in required_columns:
            if not column_exists(inspector, "users", col):
                missing_columns.append(col)
        
        if missing_columns:
            print(f"  ERROR: Missing columns: {missing_columns}")
            sys.exit(1)
        
        # Check audit_logs table
        if not table_exists(inspector, "audit_logs"):
            print("  ERROR: audit_logs table not created")
            sys.exit(1)
        
        # Check for users without public_id
        result = conn.execute(text("SELECT COUNT(*) FROM users WHERE public_id IS NULL"))
        null_count = result.scalar()
        
        if null_count > 0:
            print(f"  WARNING: {null_count} users still without public_id")
        else:
            print("  ✓ All users have public_ids")
        
        print("\n" + "=" * 60)
        print("MIGRATION COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
        # Summary
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        
        result = conn.execute(text("SELECT COUNT(*) FROM audit_logs"))
        audit_count = result.scalar()
        
        print(f"\nDatabase summary:")
        print(f"  - Users: {user_count}")
        print(f"  - Audit logs: {audit_count}")
        print(f"\nYou can now start the server with: uvicorn app.main:app --reload")


if __name__ == "__main__":
    run_migration()
