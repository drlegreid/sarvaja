"""
TypeDB Schema and Data Loader
Loads governance schema and initial data into TypeDB.

Created: 2024-12-24 (DECISION-003)
Updated: 2026-01-17 - Migrated to TypeDB 3.x API (GAP-TYPEDB-UPGRADE-001)
"""
import os
from pathlib import Path

try:
    from typedb.driver import TypeDB, Credentials, DriverOptions, TransactionType
except ImportError:
    print("TypeDB driver not installed. Run: pip install typedb-driver>=3.7.0")
    exit(1)

# Configuration
TYPEDB_HOST = os.getenv("TYPEDB_HOST", "localhost")
TYPEDB_PORT = int(os.getenv("TYPEDB_PORT", "1729"))
DATABASE_NAME = "sim-ai-governance"
USE_MODULAR_SCHEMA = os.getenv("USE_MODULAR_SCHEMA", "false").lower() == "true"

# Paths
SCRIPT_DIR = Path(__file__).parent
SCHEMA_FILE = SCRIPT_DIR / "schema.tql"  # Legacy monolithic schema
SCHEMA_DIR = SCRIPT_DIR / "schema"       # Modular schema directory
DATA_FILE = SCRIPT_DIR / "data.tql"


def connect():
    """Connect to TypeDB 3.x server."""
    address = f"{TYPEDB_HOST}:{TYPEDB_PORT}"
    print(f"Connecting to TypeDB 3.x at {address}...")

    # TypeDB 3.x requires Credentials and DriverOptions
    # Default credentials for TypeDB CE: admin/password
    username = os.getenv("TYPEDB_USERNAME", "admin")
    password = os.getenv("TYPEDB_PASSWORD", "password")
    credentials = Credentials(username, password)
    options = DriverOptions(is_tls_enabled=False)

    return TypeDB.driver(address, credentials, options)


def create_database(driver):
    """Create database if it doesn't exist."""
    databases = driver.databases.all()
    db_names = [db.name for db in databases]

    if DATABASE_NAME in db_names:
        print(f"Database '{DATABASE_NAME}' already exists. Deleting...")
        driver.databases.get(DATABASE_NAME).delete()

    print(f"Creating database '{DATABASE_NAME}'...")
    driver.databases.create(DATABASE_NAME)


def load_schema_modular(driver):
    """
    Load schema from modular files in schema/ directory.
    Files are loaded in sorted order to ensure dependency ordering.
    """
    if not SCHEMA_DIR.exists():
        raise FileNotFoundError(f"Schema directory not found: {SCHEMA_DIR}")

    schema_files = sorted(SCHEMA_DIR.glob("*.tql"))
    if not schema_files:
        raise FileNotFoundError(f"No .tql files found in {SCHEMA_DIR}")

    print(f"Loading modular schema from {SCHEMA_DIR}/")
    print(f"  Found {len(schema_files)} module files")

    # Concatenate all schema files
    combined_schema = "define\n\n"
    for schema_file in schema_files:
        print(f"  Loading: {schema_file.name}")
        with open(schema_file, "r") as f:
            content = f.read()
            content = content.replace("define\n", "").replace("define", "")
            combined_schema += f"# === {schema_file.name} ===\n"
            combined_schema += content + "\n"

    # TypeDB 3.x: driver.transaction(database, type) - no sessions
    # Must call .resolve() on query Promise before commit
    with driver.transaction(DATABASE_NAME, TransactionType.SCHEMA) as tx:
        tx.query(combined_schema).resolve()
        tx.commit()

    print(f"Schema loaded successfully ({len(schema_files)} modules).")


def load_schema(driver):
    """Load schema from schema.tql or modular files."""
    if USE_MODULAR_SCHEMA:
        return load_schema_modular(driver)

    print(f"Loading schema from {SCHEMA_FILE}...")

    with open(SCHEMA_FILE, "r") as f:
        schema = f.read()

    # TypeDB 3.x: driver.transaction(database, type) - unified query API
    # Must call .resolve() on query Promise before commit
    with driver.transaction(DATABASE_NAME, TransactionType.SCHEMA) as tx:
        tx.query(schema).resolve()
        tx.commit()

    print("Schema loaded successfully.")


def load_data(driver):
    """Load data from data.tql."""
    print(f"Loading data from {DATA_FILE}...")

    with open(DATA_FILE, "r") as f:
        data = f.read()

    # TypeDB 3.x: driver.transaction() with unified tx.query()
    # Must call .resolve() on query Promise before commit
    with driver.transaction(DATABASE_NAME, TransactionType.WRITE) as tx:
        tx.query(data).resolve()
        tx.commit()

    print("Data loaded successfully.")


def verify_load(driver):
    """Verify data was loaded correctly."""
    print("Verifying data load...")

    with driver.transaction(DATABASE_NAME, TransactionType.READ) as tx:
        # Count rules - 3.x: match without get, iterate results
        # TypeDB 3.x uses 'fetch' for JSON output, but for counting just iterate match
        rules = list(tx.query("match $r isa rule-entity;").resolve() or [])
        print(f"  Rules loaded: {len(rules)}")

        decisions = list(tx.query("match $d isa decision;").resolve() or [])
        print(f"  Decisions loaded: {len(decisions)}")

        agents = list(tx.query("match $a isa agent;").resolve() or [])
        print(f"  Agents loaded: {len(agents)}")

        deps = list(tx.query("match $rel isa rule-dependency;").resolve() or [])
        print(f"  Rule dependencies: {len(deps)}")

        affects = list(tx.query("match $rel isa decision-affects;").resolve() or [])
        print(f"  Decision affects: {len(affects)}")

        sessions = list(tx.query("match $s isa work-session;").resolve() or [])
        print(f"  Work sessions loaded: {len(sessions)}")

        evidence = list(tx.query("match $e isa evidence-file;").resolve() or [])
        print(f"  Evidence files loaded: {len(evidence)}")

        tasks = list(tx.query("match $t isa task;").resolve() or [])
        print(f"  Tasks loaded: {len(tasks)}")

        impl_rules = list(tx.query("match $rel isa implements-rule;").resolve() or [])
        print(f"  Task->Rule links: {len(impl_rules)}")

        completed_in = list(tx.query("match $rel isa completed-in;").resolve() or [])
        print(f"  Task->Session links: {len(completed_in)}")

        has_evidence = list(tx.query("match $rel isa has-evidence;").resolve() or [])
        print(f"  Session->Evidence links: {len(has_evidence)}")

    return len(rules) >= 25 and len(decisions) == 4 and len(agents) == 3


def test_inference(driver):
    """Test inference rules work."""
    print("Testing inference...")
    # Note: TypeDB 3.x handles inference differently (functions vs rules)
    # Inference rules are disabled - this test verifies basic queries work

    with driver.transaction(DATABASE_NAME, TransactionType.READ) as tx:
        # TypeDB 3.x: match without get, count results
        query = """
            match
                $r1 isa rule-entity, has rule-id "RULE-006";
                (dependent: $r1, dependency: $r2) isa rule-dependency;
        """
        results = list(tx.query(query).resolve() or [])
        print(f"  RULE-006 dependencies: {len(results)} found")

        query = """
            match
                $d isa decision, has decision-id "DECISION-003";
                (affecting-decision: $d, affected-rule: $r) isa decision-affects;
        """
        results = list(tx.query(query).resolve() or [])
        print(f"  DECISION-003 affects rules: {len(results)} found")

    print("Inference tests complete.")


def main():
    """Main loader function."""
    print("=" * 60)
    print("TypeDB Governance Loader (3.x API)")
    print("=" * 60)

    try:
        driver = connect()
        create_database(driver)
        load_schema(driver)
        load_data(driver)

        if verify_load(driver):
            print("\n[OK] All data loaded and verified!")
            test_inference(driver)
        else:
            print("\n[FAIL] Data verification failed!")
            return 1

        driver.close()
        print("\n" + "=" * 60)
        print("TypeDB ready for use!")
        print(f"Database: {DATABASE_NAME}")
        print(f"Address: {TYPEDB_HOST}:{TYPEDB_PORT}")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
