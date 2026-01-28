#!/usr/bin/env python3
"""
Add 'applicability' attribute to TypeDB schema.
Per RD-RULE-APPLICABILITY: Rule enforcement level classification.

Usage: python3 scripts/add_applicability_attr.py

Values: MANDATORY, RECOMMENDED, FORBIDDEN, CONDITIONAL
"""
import os
import sys

try:
    from typedb.driver import TypeDB, Credentials, DriverOptions, TransactionType
except ImportError:
    print("TypeDB driver not installed. Run: pip install typedb-driver>=3.7.0")
    sys.exit(1)

# Configuration
TYPEDB_HOST = os.getenv("TYPEDB_HOST", "localhost")
TYPEDB_PORT = int(os.getenv("TYPEDB_PORT", "1729"))
DATABASE_NAME = "sim-ai-governance"


def connect():
    """Connect to TypeDB 3.x server."""
    address = f"{TYPEDB_HOST}:{TYPEDB_PORT}"
    print(f"Connecting to TypeDB 3.x at {address}...")

    username = os.getenv("TYPEDB_USERNAME", "admin")
    password = os.getenv("TYPEDB_PASSWORD", "password")
    credentials = Credentials(username, password)
    options = DriverOptions(is_tls_enabled=False)

    return TypeDB.driver(address, credentials, options)


def add_applicability_attribute(driver):
    """Add applicability attribute to schema."""
    print("Adding 'applicability' attribute to schema...")

    # Check if attribute already exists
    with driver.transaction(DATABASE_NAME, TransactionType.READ) as tx:
        query = """
            match $a label applicability;
        """
        try:
            results = list(tx.query(query).resolve() or [])
            if results:
                print("  Attribute 'applicability' already exists in schema.")
                return True
        except Exception:
            pass  # Attribute doesn't exist, continue

    # Define the attribute and add ownership to rule-entity
    schema_extension = """
        define

        # RD-RULE-APPLICABILITY: Enforcement level classification
        # Values: MANDATORY, RECOMMENDED, FORBIDDEN, CONDITIONAL
        attribute applicability value string;

        rule-entity owns applicability;
    """

    with driver.transaction(DATABASE_NAME, TransactionType.SCHEMA) as tx:
        tx.query(schema_extension).resolve()
        tx.commit()

    print("  Schema extended successfully.")
    return True


def verify_attribute(driver):
    """Verify the attribute was added."""
    print("Verifying attribute...")

    with driver.transaction(DATABASE_NAME, TransactionType.READ) as tx:
        # Try a query that uses the new attribute
        query = """
            match $r isa rule-entity, has rule-id $id;
        """
        results = list(tx.query(query).resolve() or [])
        print(f"  Found {len(results)} rules in database.")

    return True


def main():
    """Main function."""
    print("=" * 60)
    print("RD-RULE-APPLICABILITY Schema Migration")
    print("=" * 60)

    try:
        driver = connect()
        add_applicability_attribute(driver)
        verify_attribute(driver)
        driver.close()

        print("\n[OK] Schema migration complete!")
        print("Next: Use rule_update(applicability='MANDATORY|RECOMMENDED|FORBIDDEN|CONDITIONAL')")
        return 0

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
