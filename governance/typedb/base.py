"""
TypeDB Base Client - Connection and Query Execution.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-003: Extracted from client.py.
Per GAP-TYPEDB-UPGRADE-001: Migrated to TypeDB 3.x API (2026-01-17)

Created: 2024-12-28
Updated: 2026-01-17 (TypeDB 3.x API migration)
"""

import os
from typing import List, Dict, Any

from .entities import Rule

# Configuration
TYPEDB_HOST = os.getenv("TYPEDB_HOST", "localhost")
TYPEDB_PORT = int(os.getenv("TYPEDB_PORT", "1729"))
DATABASE_NAME = os.getenv("TYPEDB_DATABASE", "sim-ai-governance")


class TypeDBBaseClient:
    """
    Base TypeDB client with connection and query execution.

    Provides core functionality for all TypeDB operations.
    Uses TypeDB 3.x driver API (typedb-driver>=3.7.0).
    """

    def __init__(self, host: str = None, port: int = None, database: str = None):
        self.host = host or TYPEDB_HOST
        self.port = port or TYPEDB_PORT
        self.database = database or DATABASE_NAME
        self._driver = None
        self._connected = False

    def connect(self) -> bool:
        """Connect to TypeDB 3.x server.

        Uses typedb-driver 3.x API with Credentials and DriverOptions.
        """
        try:
            from typedb.driver import TypeDB, Credentials, DriverOptions

            address = f"{self.host}:{self.port}"

            # TypeDB 3.x requires Credentials and DriverOptions
            # Default credentials for TypeDB CE: admin/password
            username = os.getenv("TYPEDB_USERNAME", "admin")
            password = os.getenv("TYPEDB_PASSWORD", "password")
            credentials = Credentials(username, password)
            options = DriverOptions(is_tls_enabled=False)

            self._driver = TypeDB.driver(address, credentials, options)
            self._connected = True
            return True
        except ImportError:
            print("TypeDB driver not installed. Run: pip install typedb-driver>=3.7.0")
            return False
        except Exception as e:
            print(f"Failed to connect to TypeDB 3.x: {e}")
            return False

    def close(self):
        """Close connection."""
        if self._driver:
            self._driver.close()
            self._connected = False

    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected

    def health_check(self) -> Dict[str, Any]:
        """Check TypeDB health status."""
        try:
            if not self._connected:
                return {"healthy": False, "error": "Not connected"}

            databases = self._driver.databases.all()
            db_names = [db.name for db in databases]

            return {
                "healthy": True,
                "host": f"{self.host}:{self.port}",
                "databases": db_names,
                "target_database": self.database,
                "database_exists": self.database in db_names,
                "driver_version": "3.x"
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    # =========================================================================
    # QUERY EXECUTION (TypeDB 3.x API)
    # =========================================================================

    def execute_query(self, query: str, infer: bool = False) -> List[Dict[str, Any]]:
        """Execute a TypeQL query and return results. Public wrapper."""
        return self._execute_query(query, infer)

    def _execute_query(self, query: str, infer: bool = False) -> List[Dict[str, Any]]:
        """Execute a TypeQL query and return results.

        Uses typedb-driver 3.x API:
        - No separate sessions, use driver.transaction() directly
        - tx.query(query_string) unified interface
        """
        if not self._connected:
            raise RuntimeError("Not connected to TypeDB")

        from typedb.driver import TransactionType

        results = []

        # TypeDB 3.x: driver.transaction(database, type) - no sessions
        with self._driver.transaction(self.database, TransactionType.READ) as tx:
            # 3.x: tx.query(query_string).resolve() - must resolve Promise
            iterator = tx.query(query).resolve()

            if iterator is None:
                return results

            for result in iterator:
                row = {}
                # 3.x API: result.column_names() returns variable names
                for var in result.column_names():
                    concept = result.get(var)
                    row[var] = self._concept_to_value(concept)
                results.append(row)

        return results

    def _concept_to_value(self, concept) -> Any:
        """Convert TypeDB concept to Python value.

        In 3.x, Thing is renamed to Instance.
        TypeDB 3.x uses get_value() method for attributes.
        """
        if concept is None:
            return None

        # TypeDB 3.x: Use get_value() method for attributes
        if hasattr(concept, 'get_value'):
            try:
                return concept.get_value()
            except Exception:
                pass

        # Fallback: Check for .value property (older API)
        if hasattr(concept, 'value'):
            return concept.value

        # Check if it's an entity/relation with an IID
        if hasattr(concept, 'get_iid'):
            try:
                return str(concept.get_iid())
            except Exception:
                pass

        if hasattr(concept, 'iid'):
            return str(concept.iid)

        # Fallback
        return str(concept)

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

    def _execute_write(self, query: str) -> bool:
        """Execute a TypeQL write query (insert/update/delete).

        Uses typedb-driver 3.x API:
        - tx.query(query_string) for all query types
        """
        if not self._connected:
            raise RuntimeError("Not connected to TypeDB")

        from typedb.driver import TransactionType

        with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
            tx.query(query).resolve()
            tx.commit()

        return True
