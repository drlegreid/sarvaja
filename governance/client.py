"""
TypeDB Client Wrapper for Sim.ai Governance
Provides high-level API for rule inference and knowledge queries.
Created: 2024-12-24 (DECISION-003)
"""
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Configuration
TYPEDB_HOST = os.getenv("TYPEDB_HOST", "localhost")
TYPEDB_PORT = int(os.getenv("TYPEDB_PORT", "1729"))
DATABASE_NAME = os.getenv("TYPEDB_DATABASE", "sim-ai-governance")


@dataclass
class Rule:
    """Governance rule entity."""
    id: str
    name: str
    category: str
    priority: str
    status: str
    directive: str
    created_date: Optional[datetime] = None


@dataclass
class Decision:
    """Strategic decision entity."""
    id: str
    name: str
    context: str
    rationale: str
    status: str
    decision_date: Optional[datetime] = None


@dataclass
class InferenceResult:
    """Result from inference query."""
    query: str
    results: List[Dict[str, Any]]
    count: int
    inference_used: bool


class TypeDBClient:
    """
    High-level TypeDB client for governance queries.

    Usage:
        client = TypeDBClient()
        client.connect()

        # Get all active rules
        rules = client.get_active_rules()

        # Find rule dependencies
        deps = client.get_rule_dependencies("RULE-006")

        # Find conflicting rules
        conflicts = client.find_conflicts()

        client.close()
    """

    def __init__(self, host: str = None, port: int = None, database: str = None):
        self.host = host or TYPEDB_HOST
        self.port = port or TYPEDB_PORT
        self.database = database or DATABASE_NAME
        self._client = None
        self._connected = False

    def connect(self) -> bool:
        """Connect to TypeDB server.

        Note: Uses typedb-driver 2.29.x API for TypeDB Core 2.29.1
        See RULE-009 for version compatibility protocol.
        """
        try:
            from typedb.driver import TypeDB
            address = f"{self.host}:{self.port}"
            self._client = TypeDB.core_driver(address)
            self._connected = True
            return True
        except ImportError:
            print("TypeDB driver not installed. Run: pip install typedb-driver==2.29.2")
            return False
        except Exception as e:
            print(f"Failed to connect to TypeDB: {e}")
            return False

    def close(self):
        """Close connection."""
        if self._client:
            self._client.close()
            self._connected = False

    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected

    def health_check(self) -> Dict[str, Any]:
        """Check TypeDB health status."""
        try:
            if not self._connected:
                return {"healthy": False, "error": "Not connected"}

            databases = self._client.databases.all()
            db_names = [db.name for db in databases]

            return {
                "healthy": True,
                "host": f"{self.host}:{self.port}",
                "databases": db_names,
                "target_database": self.database,
                "database_exists": self.database in db_names
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    # =========================================================================
    # RULE QUERIES
    # =========================================================================

    def get_all_rules(self) -> List[Rule]:
        """Get all governance rules."""
        query = """
            match $r isa rule-entity,
                has rule-id $id,
                has rule-name $name,
                has category $cat,
                has priority $pri,
                has status $stat,
                has directive $dir;
            get $id, $name, $cat, $pri, $stat, $dir;
        """
        return self._execute_rule_query(query)

    def get_active_rules(self) -> List[Rule]:
        """Get only active rules."""
        query = """
            match $r isa rule-entity,
                has rule-id $id,
                has rule-name $name,
                has category $cat,
                has priority $pri,
                has status "ACTIVE",
                has directive $dir;
            get $id, $name, $cat, $pri, $dir;
        """
        results = self._execute_query(query)
        return [
            Rule(
                id=r.get("id"),
                name=r.get("name"),
                category=r.get("cat"),
                priority=r.get("pri"),
                status="ACTIVE",
                directive=r.get("dir")
            )
            for r in results
        ]

    def get_rule_by_id(self, rule_id: str) -> Optional[Rule]:
        """Get a specific rule by ID."""
        query = f"""
            match $r isa rule-entity,
                has rule-id "{rule_id}",
                has rule-name $name,
                has category $cat,
                has priority $pri,
                has status $stat,
                has directive $dir;
            get $name, $cat, $pri, $stat, $dir;
        """
        results = self._execute_query(query)
        if results:
            r = results[0]
            return Rule(
                id=rule_id,
                name=r.get("name"),
                category=r.get("cat"),
                priority=r.get("pri"),
                status=r.get("stat"),
                directive=r.get("dir")
            )
        return None

    def get_rules_by_category(self, category: str) -> List[Rule]:
        """Get rules by category."""
        query = f"""
            match $r isa rule-entity,
                has rule-id $id,
                has rule-name $name,
                has category "{category}",
                has priority $pri,
                has status $stat,
                has directive $dir;
            get $id, $name, $pri, $stat, $dir;
        """
        results = self._execute_query(query)
        return [
            Rule(
                id=r.get("id"),
                name=r.get("name"),
                category=category,
                priority=r.get("pri"),
                status=r.get("stat"),
                directive=r.get("dir")
            )
            for r in results
        ]

    # =========================================================================
    # INFERENCE QUERIES
    # =========================================================================

    def get_rule_dependencies(self, rule_id: str) -> List[str]:
        """
        Get all rules that a given rule depends on (including transitive).
        Uses TypeDB inference to find transitive dependencies.
        """
        query = f"""
            match
                $r1 isa rule-entity, has rule-id "{rule_id}";
                (dependent: $r1, dependency: $r2) isa rule-dependency;
                $r2 has rule-id $dep_id;
            get $dep_id;
        """
        results = self._execute_query(query, infer=True)
        return [r.get("dep_id") for r in results]

    def get_rules_depending_on(self, rule_id: str) -> List[str]:
        """Get all rules that depend on a given rule."""
        query = f"""
            match
                $r1 isa rule-entity, has rule-id $id;
                $r2 isa rule-entity, has rule-id "{rule_id}";
                (dependent: $r1, dependency: $r2) isa rule-dependency;
            get $id;
        """
        results = self._execute_query(query, infer=True)
        return [r.get("id") for r in results]

    def find_conflicts(self) -> List[Dict[str, str]]:
        """
        Find conflicting rules using inference.
        Returns pairs of rules that have conflicts.
        """
        query = """
            match
                (conflicting-rule: $r1, conflicting-rule: $r2) isa rule-conflict;
                $r1 has rule-id $id1;
                $r2 has rule-id $id2;
            get $id1, $id2;
        """
        results = self._execute_query(query, infer=True)
        return [{"rule1": r.get("id1"), "rule2": r.get("id2")} for r in results]

    def get_decision_impacts(self, decision_id: str) -> List[str]:
        """
        Get all rules affected by a decision (including cascaded supersedes).
        Uses inference to follow supersede chains.
        """
        query = f"""
            match
                $d isa decision, has decision-id "{decision_id}";
                (affecting-decision: $d, affected-rule: $r) isa decision-affects;
                $r has rule-id $rid;
            get $rid;
        """
        results = self._execute_query(query, infer=True)
        return [r.get("rid") for r in results]

    # =========================================================================
    # DECISION QUERIES
    # =========================================================================

    def get_all_decisions(self) -> List[Decision]:
        """Get all strategic decisions."""
        query = """
            match $d isa decision,
                has decision-id $id,
                has decision-name $name,
                has context $ctx,
                has rationale $rat,
                has decision-status $stat;
            get $id, $name, $ctx, $rat, $stat;
        """
        results = self._execute_query(query)
        return [
            Decision(
                id=r.get("id"),
                name=r.get("name"),
                context=r.get("ctx"),
                rationale=r.get("rat"),
                status=r.get("stat")
            )
            for r in results
        ]

    def get_superseded_decisions(self) -> List[Dict[str, str]]:
        """Get decision supersession chain."""
        query = """
            match
                (superseding: $a, superseded: $b) isa decision-supersedes;
                $a has decision-id $aid;
                $b has decision-id $bid;
            get $aid, $bid;
        """
        results = self._execute_query(query)
        return [{"superseding": r.get("aid"), "superseded": r.get("bid")} for r in results]

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    def _execute_query(self, query: str, infer: bool = False) -> List[Dict[str, Any]]:
        """Execute a TypeQL query and return results.

        Uses typedb-driver 2.29.x API compatible with TypeDB Core 2.29.1
        """
        if not self._connected:
            raise RuntimeError("Not connected to TypeDB")

        from typedb.driver import SessionType, TransactionType, TypeDBOptions

        results = []
        options = TypeDBOptions()
        if infer:
            options.infer = True

        with self._client.session(self.database, SessionType.DATA) as session:
            with session.transaction(TransactionType.READ, options) as tx:
                iterator = tx.query.get(query)
                for result in iterator:
                    row = {}
                    for var in result.map.keys():
                        concept = result.get(var)
                        if concept.is_attribute():
                            row[var] = concept.as_attribute().get_value()
                        elif concept.is_thing():
                            row[var] = concept.as_thing().get_iid()
                    results.append(row)

        return results

    def _execute_rule_query(self, query: str) -> List[Rule]:
        """Execute query and return Rule objects."""
        results = self._execute_query(query)
        return [
            Rule(
                id=r.get("id"),
                name=r.get("name"),
                category=r.get("cat"),
                priority=r.get("pri"),
                status=r.get("stat"),
                directive=r.get("dir")
            )
            for r in results
        ]


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_client() -> TypeDBClient:
    """Get a connected TypeDB client."""
    client = TypeDBClient()
    if client.connect():
        return client
    return None


def quick_health() -> bool:
    """Quick health check for TypeDB."""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((TYPEDB_HOST, TYPEDB_PORT))
        sock.close()
        return result == 0
    except:
        return False


# =============================================================================
# CLI FOR TESTING
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TypeDB Governance Client Test")
    print("=" * 60)

    # Quick health check
    if not quick_health():
        print(f"[FAIL] TypeDB not reachable at {TYPEDB_HOST}:{TYPEDB_PORT}")
        print("   Start with: docker compose --profile cpu up -d")
        exit(1)

    client = TypeDBClient()
    if not client.connect():
        print("[FAIL] Failed to connect")
        exit(1)

    print(f"[OK] Connected to TypeDB at {TYPEDB_HOST}:{TYPEDB_PORT}")

    # Health check
    health = client.health_check()
    print(f"\nHealth: {health}")

    if not health.get("database_exists"):
        print(f"\n[WARN] Database '{DATABASE_NAME}' not found.")
        print("   Run: python governance/loader.py")
        client.close()
        exit(0)

    # Test queries
    print("\n--- Active Rules ---")
    for rule in client.get_active_rules():
        print(f"  [{rule.priority}] {rule.id}: {rule.name}")

    print("\n--- Rule Dependencies (RULE-006) ---")
    deps = client.get_rule_dependencies("RULE-006")
    print(f"  RULE-006 depends on: {deps}")

    print("\n--- Decision Impacts (DECISION-003) ---")
    impacts = client.get_decision_impacts("DECISION-003")
    print(f"  DECISION-003 affects: {impacts}")

    print("\n--- Conflicts (via inference) ---")
    conflicts = client.find_conflicts()
    if conflicts:
        for c in conflicts:
            print(f"  {c['rule1']} <-> {c['rule2']}")
    else:
        print("  No conflicts detected")

    client.close()
    print("\n[OK] All tests passed!")
