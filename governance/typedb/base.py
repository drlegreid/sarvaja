"""
TypeDB Base Client - Connection and Query Execution.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-003: Extracted from client.py.
Per GAP-TYPEDB-UPGRADE-001: Migrated to TypeDB 3.x API (2026-01-17)

Created: 2024-12-28
Updated: 2026-01-17 (TypeDB 3.x API migration)
"""

import logging
import os
import time
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Histogram
    _HAS_PROMETHEUS = True
except ImportError:
    _HAS_PROMETHEUS = False

from .entities import Rule

# ---------------------------------------------------------------------------
# Prometheus instruments — TypeDB query metrics (EPIC-PERF-TELEM-V1 P9)
# No-op when prometheus_client is absent (MCP servers don't need metrics).
# ---------------------------------------------------------------------------

if _HAS_PROMETHEUS:
    TYPEDB_QUERY_DURATION = Histogram(
        "sarvaja_typedb_query_duration_seconds",
        "TypeDB query duration in seconds",
        labelnames=["query_type"],
        buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    )
    TYPEDB_QUERY_COUNT = Counter(
        "sarvaja_typedb_query_total",
        "Total TypeDB queries executed",
        labelnames=["query_type"],
    )
else:
    TYPEDB_QUERY_DURATION = None
    TYPEDB_QUERY_COUNT = None

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
        # EPIC-PERF-TELEM-V1 P1: Query timing instrumentation
        self._query_count = 0
        self._total_query_ms = 0.0

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
            logger.error("TypeDB driver not installed. Run: pip install typedb-driver>=3.7.0")
            return False
        except Exception as e:
            # BUG-472-TBB-001: Sanitize logger message + add exc_info for stack trace preservation
            logger.error(f"Failed to connect to TypeDB 3.x: {type(e).__name__}", exc_info=True)
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
        t0 = time.monotonic()

        # TypeDB 3.x: driver.transaction(database, type) - no sessions
        with self._driver.transaction(self.database, TransactionType.READ) as tx:
            # 3.x: tx.query(query_string).resolve() - must resolve Promise
            iterator = tx.query(query).resolve()

            if iterator is None:
                self._record_query_timing(t0, query)
                return results

            for result in iterator:
                row = {}
                # 3.x API: result.column_names() returns variable names
                for var in result.column_names():
                    concept = result.get(var)
                    row[var] = self._concept_to_value(concept)
                results.append(row)

        self._record_query_timing(t0, query)
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
            except Exception as e:
                # BUG-TYPEDB-SILENT-001: Log instead of silently swallowing
                # BUG-477-TBB-1: Sanitize debug/info logger
                logger.debug(f"get_value() failed for concept: {type(e).__name__}")

        # Fallback: Check for .value property (older API)
        if hasattr(concept, 'value'):
            return concept.value

        # Check if it's an entity/relation with an IID
        if hasattr(concept, 'get_iid'):
            try:
                return str(concept.get_iid())
            except Exception as e:
                # BUG-TYPEDB-SILENT-001: Log instead of silently swallowing
                # BUG-477-TBB-2: Sanitize debug/info logger
                logger.debug(f"get_iid() failed for concept: {type(e).__name__}")

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

        t0 = time.monotonic()

        with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
            tx.query(query).resolve()
            tx.commit()

        self._record_query_timing(t0, query)
        return True

    def _record_query_timing(self, t0: float, query: str) -> None:
        """Record query duration and log slow queries (>500ms).

        Includes request correlation ID (rid) when available, enabling
        end-to-end tracing from HTTP request to TypeDB query.
        (EPIC-PERF-TELEM-V1 Phase 6 + Phase 9 Prometheus)
        """
        from governance.middleware.request_context import get_request_id

        duration_s = time.monotonic() - t0
        duration_ms = duration_s * 1000
        self._query_count += 1
        self._total_query_ms += duration_ms

        # Phase 9: Prometheus metrics — classify read vs write
        if _HAS_PROMETHEUS:
            query_type = "write" if query.strip().lower().startswith(("insert", "delete", "update")) else "read"
            TYPEDB_QUERY_DURATION.labels(query_type=query_type).observe(duration_s)
            TYPEDB_QUERY_COUNT.labels(query_type=query_type).inc()

        if duration_ms > 500:
            snippet = query.strip()[:120]
            rid = get_request_id()
            if rid:
                logger.warning(
                    "Slow TypeDB query: %.0fms rid=%s — %s",
                    duration_ms, rid, snippet,
                )
            else:
                logger.warning(
                    "Slow TypeDB query: %.0fms — %s", duration_ms, snippet
                )
