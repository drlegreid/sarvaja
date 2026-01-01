"""
TypeDB Base Client - Connection and Query Execution.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-003: Extracted from client.py.

Created: 2024-12-28
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
    # QUERY EXECUTION
    # =========================================================================

    def execute_query(self, query: str, infer: bool = False) -> List[Dict[str, Any]]:
        """Execute a TypeQL query and return results. Public wrapper."""
        return self._execute_query(query, infer)

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

    def _execute_write(self, query: str) -> bool:
        """Execute a TypeQL write query (insert/update/delete).

        Uses typedb-driver 2.29.x API compatible with TypeDB Core 2.29.1
        Detects query type and uses appropriate TypeDB query method.
        """
        if not self._connected:
            raise RuntimeError("Not connected to TypeDB")

        from typedb.driver import SessionType, TransactionType

        # Detect query type from content
        query_lower = query.strip().lower()
        is_delete = query_lower.startswith("match") and "delete" in query_lower

        with self._client.session(self.database, SessionType.DATA) as session:
            with session.transaction(TransactionType.WRITE) as tx:
                if is_delete:
                    tx.query.delete(query)
                else:
                    tx.query.insert(query)
                tx.commit()

        return True
