#!/usr/bin/env python3
"""
Set applicability values for all rules.
Per RD-RULE-APPLICABILITY: Rule enforcement level classification.

Usage: python3 scripts/set_rule_applicability.py
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

# Rule classifications per RD-RULE-APPLICABILITY
APPLICABILITY_MAP = {
    # MANDATORY - must comply, blocking
    "SESSION-EVID-01-v1": "MANDATORY",
    "GOV-BICAM-01-v1": "MANDATORY",
    "SAFETY-HEALTH-02-v1": "MANDATORY",
    "RECOVER-AMNES-02-v1": "MANDATORY",
    "ARCH-VERSION-01-v1": "MANDATORY",
    "GOV-RULE-01-v1": "MANDATORY",
    "ARCH-INFRA-02-v1": "MANDATORY",
    "CONTAINER-TYPEDB-01-v1": "MANDATORY",
    "CONTAINER-LIFECYCLE-01-v1": "MANDATORY",
    "WORKFLOW-SHELL-01-v1": "MANDATORY",
    "META-TAXON-01-v1": "MANDATORY",
    "TASK-LIFE-01-v1": "MANDATORY",
    "TASK-VALID-01-v1": "MANDATORY",
    "ARCH-EBMSF-01-v1": "MANDATORY",
    "ARCH-MCP-02-v1": "MANDATORY",

    # CONDITIONAL - context-dependent
    "WORKFLOW-AUTO-02-v1": "CONDITIONAL",
    "WORKFLOW-RD-02-v1": "CONDITIONAL",
    "SESSION-DSP-NOTIFY-01-v1": "CONDITIONAL",
    "SESSION-DSM-01-v1": "CONDITIONAL",

    # RECOMMENDED - should comply, warning
    "DOC-SOURCE-01-v1": "RECOMMENDED",
    "CONTEXT-SAVE-01-v1": "RECOMMENDED",
    "GAP-DOC-01-v1": "RECOMMENDED",
    "PKG-LATEST-01-v1": "RECOMMENDED",
    "UI-NAV-01-v1": "RECOMMENDED",
    "RECOVER-MEM-01-v1": "RECOMMENDED",
    "GOV-TRUST-01-v1": "RECOMMENDED",
    "GOV-PROP-01-v1": "RECOMMENDED",
    "UI-TRAME-01-v1": "RECOMMENDED",
    "UI-LOADER-01-v1": "RECOMMENDED",
    "UI-TRACE-01-v1": "RECOMMENDED",
    "TASK-TECH-01-v1": "RECOMMENDED",
    "REPORT-OBJ-01-v1": "RECOMMENDED",
    "UI-DESIGN-02-v1": "RECOMMENDED",
    "DOC-GAP-ARCHIVE-01-v1": "RECOMMENDED",

    # DRAFT rules get RECOMMENDED by default
    "GOV-AUDIT-01-v1": "RECOMMENDED",
    "REPORT-EXEC-01-v1": "RECOMMENDED",
}


def connect():
    """Connect to TypeDB 3.x server."""
    address = f"{TYPEDB_HOST}:{TYPEDB_PORT}"
    print(f"Connecting to TypeDB 3.x at {address}...")

    credentials = Credentials("admin", "password")
    options = DriverOptions(is_tls_enabled=False)

    return TypeDB.driver(address, credentials, options)


def set_applicability(driver, rule_id: str, applicability: str) -> bool:
    """Set applicability for a rule."""
    # Check if rule exists and get current applicability
    with driver.transaction(DATABASE_NAME, TransactionType.READ) as tx:
        query = f'''
            match $r isa rule-entity, has rule-id "{rule_id}";
        '''
        results = list(tx.query(query).resolve() or [])
        if not results:
            print(f"  [SKIP] Rule {rule_id} not found")
            return False

    # Check if applicability already set
    with driver.transaction(DATABASE_NAME, TransactionType.READ) as tx:
        query = f'''
            match $r isa rule-entity,
                has rule-id "{rule_id}",
                has applicability $app;
        '''
        results = list(tx.query(query).resolve() or [])
        if results:
            print(f"  [SKIP] Rule {rule_id} already has applicability")
            return False

    # Insert applicability
    with driver.transaction(DATABASE_NAME, TransactionType.WRITE) as tx:
        query = f'''
            match
                $r isa rule-entity, has rule-id "{rule_id}";
            insert
                $r has applicability "{applicability}";
        '''
        tx.query(query).resolve()
        tx.commit()

    print(f"  [OK] {rule_id} -> {applicability}")
    return True


def main():
    """Main function."""
    print("=" * 60)
    print("RD-RULE-APPLICABILITY: Setting Rule Applicability Values")
    print("=" * 60)

    try:
        driver = connect()

        counts = {"MANDATORY": 0, "CONDITIONAL": 0, "RECOMMENDED": 0}

        for rule_id, applicability in APPLICABILITY_MAP.items():
            if set_applicability(driver, rule_id, applicability):
                counts[applicability] += 1

        driver.close()

        print("\n" + "=" * 60)
        print("Summary:")
        print(f"  MANDATORY: {counts['MANDATORY']}")
        print(f"  CONDITIONAL: {counts['CONDITIONAL']}")
        print(f"  RECOMMENDED: {counts['RECOMMENDED']}")
        print(f"  Total: {sum(counts.values())}")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
