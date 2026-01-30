"""
TypeDB 3.x Base Client - Connection and Query Execution.

Per GAP-TYPEDB-DRIVER-001: TypeDB 3.x upgrade path.
Per RULE-012: DSP Semantic Code Structure.

Created: 2026-01-17
Status: TDD - Tests written, implementation in progress.

Key API Changes from 2.x:
- TypeDB.core_driver() → TypeDB.driver(addr, Credentials, DriverOptions)
- tx.query.match() → tx.query("match ...")
- tx.query.insert() → tx.query("insert ...")
- tx.query.define() → tx.query("define ...")
- Thing → Instance
- Rules → Functions
"""

import logging
import os
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Configuration
TYPEDB_HOST = os.getenv("TYPEDB_HOST", "localhost")
TYPEDB_PORT = int(os.getenv("TYPEDB_PORT", "1729"))
DATABASE_NAME = os.getenv("TYPEDB_DATABASE", "sim-ai-governance")


class TypeDB3BaseClient:
    """
    Base TypeDB 3.x client with connection and query execution.

    Provides core functionality for all TypeDB operations using 3.x API.

    Usage:
        client = TypeDB3BaseClient()
        if client.connect():
            results = client.execute_query("match $r isa rule-entity; select $r;")
            client.close()
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

        except ImportError as e:
            logger.error(f"TypeDB driver not installed: {e}")
            logger.error("Install with: pip install typedb-driver>=3.0.0")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to TypeDB 3.x: {e}")
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
        """Check TypeDB 3.x health status."""
        try:
            if not self._connected:
                return {"healthy": False, "error": "Not connected"}

            # 3.x API: driver.databases.all() still works
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
    # QUERY EXECUTION (3.x Unified API)
    # =========================================================================

    def execute_query(self, query: str, read_only: bool = True) -> List[Dict[str, Any]]:
        """Execute a TypeQL query using 3.x unified API.

        In TypeDB 3.x:
        - All queries use driver.transaction(...).query("...")
        - No more separate match/insert/define methods
        - Transaction type determines read/write access

        Args:
            query: TypeQL query string
            read_only: Use READ transaction if True, else WRITE

        Returns:
            List of result dictionaries
        """
        if not self._connected:
            raise RuntimeError("Not connected to TypeDB")

        try:
            from typedb.driver import TransactionType

            tx_type = TransactionType.READ if read_only else TransactionType.WRITE

            # 3.x API: driver.transaction(database, tx_type)
            with self._driver.transaction(self.database, tx_type) as tx:
                # 3.x API: tx.query(query_string).resolve() - must resolve Promise
                result = tx.query(query).resolve()

                # Process results
                if result is None:
                    return []

                return self._process_results(result)

        except Exception as e:
            raise RuntimeError(f"Query execution failed: {e}")

    def _process_results(self, result) -> List[Dict[str, Any]]:
        """Process TypeDB 3.x query results.

        Result handling differs slightly in 3.x - uses Iterator pattern.
        """
        results = []

        try:
            # 3.x returns an iterator for match queries
            for answer in result:
                row = {}
                # In 3.x, use column_names() to get variable names
                for var_name in answer.column_names():
                    concept = answer.get(var_name)
                    row[var_name] = self._concept_to_value(concept)
                results.append(row)
        except Exception:
            # Some query types don't return iterables
            pass

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

        # Last fallback
        return str(concept)

    # =========================================================================
    # SCHEMA OPERATIONS (3.x)
    # =========================================================================

    def define_schema(self, schema: str) -> bool:
        """Define schema using 3.x unified API.

        In 3.x: tx.query("define ...") instead of tx.query.define()
        """
        if not self._connected:
            raise RuntimeError("Not connected to TypeDB")

        try:
            from typedb.driver import TransactionType

            with self._driver.transaction(self.database, TransactionType.SCHEMA) as tx:
                tx.query(schema).resolve()
                tx.commit()
            return True
        except Exception as e:
            raise RuntimeError(f"Schema definition failed: {e}")

    def insert_data(self, insert_query: str) -> bool:
        """Insert data using 3.x unified API.

        In 3.x: tx.query("insert ...") instead of tx.query.insert()
        """
        if not self._connected:
            raise RuntimeError("Not connected to TypeDB")

        try:
            from typedb.driver import TransactionType

            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                tx.query(insert_query).resolve()
                tx.commit()
            return True
        except Exception as e:
            raise RuntimeError(f"Insert failed: {e}")


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def get_typedb3_client() -> Optional[TypeDB3BaseClient]:
    """Get a connected TypeDB 3.x client, or None if connection fails."""
    client = TypeDB3BaseClient()
    if client.connect():
        return client
    return None
