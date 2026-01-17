"""
TypeDB Schema and Data Loader
Loads governance schema and initial data into TypeDB.
Created: 2024-12-24 (DECISION-003)
Updated: 2024-12-24 - Uses typedb-driver 2.29.x API for TypeDB Core 2.29.1 (RULE-009)
Updated: 2024-12-24 - Added RULE-011 multi-agent governance entities
Updated: 2026-01-17 - Added modular schema support (EPIC-DR-012)
"""
import os
from pathlib import Path

try:
    from typedb.driver import TypeDB, SessionType, TransactionType
except ImportError:
    print("TypeDB driver not installed. Run: pip install typedb-driver==2.29.2")
    exit(1)

# Configuration
TYPEDB_HOST = os.getenv("TYPEDB_HOST", "localhost")
TYPEDB_PORT = int(os.getenv("TYPEDB_PORT", "1729"))
DATABASE_NAME = "sim-ai-governance"
USE_MODULAR_SCHEMA = os.getenv("USE_MODULAR_SCHEMA", "false").lower() == "true"

# Paths
SCRIPT_DIR = Path(__file__).parent
SCHEMA_FILE = SCRIPT_DIR / "schema.tql"  # Legacy monolithic schema
SCHEMA_DIR = SCRIPT_DIR / "schema"       # Modular schema directory (EPIC-DR-012)
DATA_FILE = SCRIPT_DIR / "data.tql"


def connect():
    """Connect to TypeDB server using typedb-driver 2.29.x API."""
    address = f"{TYPEDB_HOST}:{TYPEDB_PORT}"
    print(f"Connecting to TypeDB at {address}...")
    return TypeDB.core_driver(address)


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

    Per EPIC-DR-012: Schema split into domain modules for maintainability.
    Files are loaded in sorted order (01_*, 10_*, 20_*, 30_*) to ensure
    proper dependency ordering (attributes before entities, etc.).
    """
    if not SCHEMA_DIR.exists():
        raise FileNotFoundError(f"Schema directory not found: {SCHEMA_DIR}")

    # Get all .tql files sorted by name (numeric prefix ensures order)
    schema_files = sorted(SCHEMA_DIR.glob("*.tql"))
    if not schema_files:
        raise FileNotFoundError(f"No .tql files found in {SCHEMA_DIR}")

    print(f"Loading modular schema from {SCHEMA_DIR}/")
    print(f"  Found {len(schema_files)} module files")

    # Concatenate all schema files (remove duplicate 'define' keywords)
    combined_schema = "define\n\n"
    for schema_file in schema_files:
        print(f"  Loading: {schema_file.name}")
        with open(schema_file, "r") as f:
            content = f.read()
            # Strip 'define' keyword from module files (we add one at the top)
            content = content.replace("define\n", "").replace("define", "")
            combined_schema += f"# === {schema_file.name} ===\n"
            combined_schema += content + "\n"

    with driver.session(DATABASE_NAME, SessionType.SCHEMA) as session:
        with session.transaction(TransactionType.WRITE) as tx:
            tx.query.define(combined_schema)
            tx.commit()

    print(f"Schema loaded successfully ({len(schema_files)} modules).")


def load_schema(driver):
    """
    Load schema from schema.tql or modular files.

    Uses USE_MODULAR_SCHEMA env var to select mode (default: monolithic).
    """
    if USE_MODULAR_SCHEMA:
        return load_schema_modular(driver)

    # Legacy monolithic loading
    print(f"Loading schema from {SCHEMA_FILE}...")

    with open(SCHEMA_FILE, "r") as f:
        schema = f.read()

    with driver.session(DATABASE_NAME, SessionType.SCHEMA) as session:
        with session.transaction(TransactionType.WRITE) as tx:
            tx.query.define(schema)
            tx.commit()

    print("Schema loaded successfully.")


def load_data(driver):
    """Load data from data.tql."""
    print(f"Loading data from {DATA_FILE}...")

    with open(DATA_FILE, "r") as f:
        data = f.read()

    with driver.session(DATABASE_NAME, SessionType.DATA) as session:
        with session.transaction(TransactionType.WRITE) as tx:
            tx.query.insert(data)
            tx.commit()

    print("Data loaded successfully.")


def verify_load(driver):
    """Verify data was loaded correctly."""
    print("Verifying data load...")

    with driver.session(DATABASE_NAME, SessionType.DATA) as session:
        with session.transaction(TransactionType.READ) as tx:
            # Count rules
            rules = list(tx.query.get("match $r isa rule-entity; get $r;"))
            print(f"  Rules loaded: {len(rules)}")

            # Count decisions
            decisions = list(tx.query.get("match $d isa decision; get $d;"))
            print(f"  Decisions loaded: {len(decisions)}")

            # Count agents (RULE-011)
            agents = list(tx.query.get("match $a isa agent; get $a;"))
            print(f"  Agents loaded: {len(agents)}")

            # Count relationships
            deps = list(tx.query.get("match $rel isa rule-dependency; get $rel;"))
            print(f"  Rule dependencies: {len(deps)}")

            affects = list(tx.query.get("match $rel isa decision-affects; get $rel;"))
            print(f"  Decision affects: {len(affects)}")

            # P11.3: Count new entities
            sessions = list(tx.query.get("match $s isa work-session; get $s;"))
            print(f"  Work sessions loaded: {len(sessions)}")

            evidence = list(tx.query.get("match $e isa evidence-file; get $e;"))
            print(f"  Evidence files loaded: {len(evidence)}")

            tasks = list(tx.query.get("match $t isa task; get $t;"))
            print(f"  Tasks loaded: {len(tasks)}")

            # P11.3: Count entity linkage relations
            impl_rules = list(tx.query.get("match $rel isa implements-rule; get $rel;"))
            print(f"  Task->Rule links: {len(impl_rules)}")

            completed_in = list(tx.query.get("match $rel isa completed-in; get $rel;"))
            print(f"  Task->Session links: {len(completed_in)}")

            has_evidence = list(tx.query.get("match $rel isa has-evidence; get $rel;"))
            print(f"  Session->Evidence links: {len(has_evidence)}")

    return len(rules) >= 25 and len(decisions) == 4 and len(agents) == 3


def test_inference(driver):
    """Test inference rules work."""
    from typedb.driver import TypeDBOptions

    print("Testing inference...")
    options = TypeDBOptions()
    options.infer = True

    with driver.session(DATABASE_NAME, SessionType.DATA) as session:
        with session.transaction(TransactionType.READ, options) as tx:
            # Test rule dependency query
            query = """
                match
                    $r1 isa rule-entity, has rule-id "RULE-006";
                    (dependent: $r1, dependency: $r2) isa rule-dependency;
                    $r2 has rule-id $id2;
                get $id2;
            """
            results = list(tx.query.get(query))
            deps = [r.get('id2').as_attribute().get_value() for r in results]
            print(f"  RULE-006 dependencies: {deps}")

            # Test decision affects
            query = """
                match
                    $d isa decision, has decision-id "DECISION-003";
                    (affecting-decision: $d, affected-rule: $r) isa decision-affects;
                    $r has rule-id $rid;
                get $rid;
            """
            results = list(tx.query.get(query))
            affected = [r.get('rid').as_attribute().get_value() for r in results]
            print(f"  DECISION-003 affects rules: {affected}")

    print("Inference tests complete.")


def main():
    """Main loader function."""
    print("=" * 60)
    print("TypeDB Governance Loader (2.29.x API)")
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
