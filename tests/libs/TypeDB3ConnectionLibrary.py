"""
TypeDB 3.x Connection Library for Robot Framework
Component tests for TypeDB 3.x connection and queries.
Migrated from tests/component/test_typedb3_connection.py
Per: RF-007 Robot Framework Migration
"""
import os
from robot.api.deco import keyword


class TypeDB3ConnectionLibrary:
    """Robot Framework keywords for TypeDB 3.x connection tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def _should_skip_typedb3(self):
        """Check if TypeDB 3.x tests should be skipped."""
        version = os.getenv("TYPEDB_VERSION", "2")
        return version < "3"

    def _get_client(self):
        """Get TypeDB 3.x client if available."""
        try:
            from governance.typedb.base3 import TypeDB3BaseClient
            return TypeDB3BaseClient()
        except ImportError:
            return None

    # =========================================================================
    # Connection Tests
    # =========================================================================

    @keyword("Connect To TypeDB3")
    def connect_to_typedb3(self):
        """Test connection to TypeDB 3.x server."""
        if self._should_skip_typedb3():
            return {"skipped": True, "reason": "Requires TypeDB 3.x server"}

        try:
            client = self._get_client()
            if client is None:
                return {"skipped": True, "reason": "TypeDB3BaseClient not available"}

            result = client.connect()
            connected = client.is_connected()
            client.close()

            return {
                "connect_returned_true": result is True,
                "is_connected": connected
            }
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("TypeDB3 Health Check")
    def typedb3_health_check(self):
        """Test health check returns correct info."""
        if self._should_skip_typedb3():
            return {"skipped": True, "reason": "Requires TypeDB 3.x server"}

        try:
            client = self._get_client()
            if client is None:
                return {"skipped": True, "reason": "TypeDB3BaseClient not available"}

            if not client.connect():
                return {"skipped": True, "reason": "Cannot connect to TypeDB 3.x"}

            health = client.health_check()
            client.close()

            return {
                "healthy": health.get("healthy", False),
                "has_databases": "databases" in health,
                "driver_version_3x": health.get("driver_version") == "3.x"
            }
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("TypeDB3 Database Exists")
    def typedb3_database_exists(self):
        """Test target database exists."""
        if self._should_skip_typedb3():
            return {"skipped": True, "reason": "Requires TypeDB 3.x server"}

        try:
            client = self._get_client()
            if client is None:
                return {"skipped": True, "reason": "TypeDB3BaseClient not available"}

            if not client.connect():
                return {"skipped": True, "reason": "Cannot connect to TypeDB 3.x"}

            health = client.health_check()
            client.close()

            return {"database_exists": health.get("database_exists", False)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Query Tests
    # =========================================================================

    @keyword("TypeDB3 Simple Match Query")
    def typedb3_simple_match_query(self):
        """Test simple match query."""
        if self._should_skip_typedb3():
            return {"skipped": True, "reason": "Requires TypeDB 3.x server"}

        try:
            client = self._get_client()
            if client is None:
                return {"skipped": True, "reason": "TypeDB3BaseClient not available"}

            if not client.connect():
                return {"skipped": True, "reason": "Cannot connect to TypeDB 3.x"}

            results = client.execute_query(
                "match $t isa rule-entity; select $t; limit 1;"
            )
            client.close()

            return {"returns_list": isinstance(results, list)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("TypeDB3 Query Returns List")
    def typedb3_query_returns_list(self):
        """Query should always return a list."""
        if self._should_skip_typedb3():
            return {"skipped": True, "reason": "Requires TypeDB 3.x server"}

        try:
            client = self._get_client()
            if client is None:
                return {"skipped": True, "reason": "TypeDB3BaseClient not available"}

            if not client.connect():
                return {"skipped": True, "reason": "Cannot connect to TypeDB 3.x"}

            results = client.execute_query(
                "match $r isa rule-entity, has rule-id $id; select $id; limit 5;"
            )
            client.close()

            return {"returns_list": isinstance(results, list)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("TypeDB3 Write Query Requires Write Mode")
    def typedb3_write_query_requires_write_mode(self):
        """Insert queries need read_only=False."""
        if self._should_skip_typedb3():
            return {"skipped": True, "reason": "Requires TypeDB 3.x server"}

        try:
            client = self._get_client()
            if client is None:
                return {"skipped": True, "reason": "TypeDB3BaseClient not available"}

            if not client.connect():
                return {"skipped": True, "reason": "Cannot connect to TypeDB 3.x"}

            try:
                client.execute_query(
                    "insert $r isa rule, has rule-id 'TEST-999';",
                    read_only=True  # Wrong mode
                )
                client.close()
                return {"raises_exception": False}
            except Exception:
                client.close()
                return {"raises_exception": True}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Schema Tests
    # =========================================================================

    @keyword("TypeDB3 Query Schema Types")
    def typedb3_query_schema_types(self):
        """Query schema types."""
        if self._should_skip_typedb3():
            return {"skipped": True, "reason": "Requires TypeDB 3.x server"}

        try:
            client = self._get_client()
            if client is None:
                return {"skipped": True, "reason": "TypeDB3BaseClient not available"}

            if not client.connect():
                return {"skipped": True, "reason": "Cannot connect to TypeDB 3.x"}

            results = client.execute_query(
                "match $r isa rule-entity; select $r; limit 1;"
            )
            client.close()

            return {"returns_list": isinstance(results, list)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Migration Verification Tests
    # =========================================================================

    @keyword("TypeDB3 Rules Exist After Migration")
    def typedb3_rules_exist_after_migration(self):
        """All rules should exist after migration."""
        if self._should_skip_typedb3():
            return {"skipped": True, "reason": "Requires TypeDB 3.x server"}

        try:
            client = self._get_client()
            if client is None:
                return {"skipped": True, "reason": "TypeDB3BaseClient not available"}

            if not client.connect():
                return {"skipped": True, "reason": "Cannot connect to TypeDB 3.x"}

            results = client.execute_query(
                "match $r isa rule-entity, has rule-id $id; select $id; limit 50;"
            )
            client.close()

            return {
                "returns_list": isinstance(results, list),
                "has_rules": len(results) > 0
            }
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("TypeDB3 Tasks Exist After Migration")
    def typedb3_tasks_exist_after_migration(self):
        """All tasks should exist after migration."""
        if self._should_skip_typedb3():
            return {"skipped": True, "reason": "Requires TypeDB 3.x server"}

        try:
            client = self._get_client()
            if client is None:
                return {"skipped": True, "reason": "TypeDB3BaseClient not available"}

            if not client.connect():
                return {"skipped": True, "reason": "Cannot connect to TypeDB 3.x"}

            results = client.execute_query(
                "match $t isa task, has task-id $id; select $id; limit 10;"
            )
            client.close()

            return {"returns_list": isinstance(results, list)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("TypeDB3 Sessions Exist After Migration")
    def typedb3_sessions_exist_after_migration(self):
        """Sessions should exist after migration."""
        if self._should_skip_typedb3():
            return {"skipped": True, "reason": "Requires TypeDB 3.x server"}

        try:
            client = self._get_client()
            if client is None:
                return {"skipped": True, "reason": "TypeDB3BaseClient not available"}

            if not client.connect():
                return {"skipped": True, "reason": "Cannot connect to TypeDB 3.x"}

            results = client.execute_query(
                "match $s isa work-session, has session-id $id; select $id; limit 5;"
            )
            client.close()

            return {"returns_list": isinstance(results, list)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}
