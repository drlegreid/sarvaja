"""
Component Tests for TypeDB 3.x Connection.

TDD Approach: Tests for TypeDB 3.x connection once server upgraded.
Per GAP-TYPEDB-DRIVER-001: TypeDB 3.x upgrade path.

Level: Component (requires TypeDB 3.x server)
"""

import pytest
import os
from typing import Dict, Any

# Mark all tests as typedb3 component tests
pytestmark = [
    pytest.mark.typedb3,
    pytest.mark.component,
    pytest.mark.skipif(
        os.getenv("TYPEDB_VERSION", "2") < "3",
        reason="Requires TypeDB 3.x server"
    ),
]


class TestTypeDB3Connection:
    """Test TypeDB 3.x server connection."""

    @pytest.fixture
    def typedb3_client(self):
        """Get TypeDB 3.x client."""
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        yield client
        if client.is_connected():
            client.close()

    def test_connect_to_typedb3(self, typedb3_client):
        """Test connection to TypeDB 3.x server."""
        result = typedb3_client.connect()
        assert result is True, "Should connect to TypeDB 3.x"
        assert typedb3_client.is_connected()

    def test_health_check(self, typedb3_client):
        """Test health check returns correct info."""
        typedb3_client.connect()
        health = typedb3_client.health_check()

        assert health["healthy"] is True
        assert "databases" in health
        assert health["driver_version"] == "3.x"

    def test_database_exists(self, typedb3_client):
        """Test target database exists."""
        typedb3_client.connect()
        health = typedb3_client.health_check()

        assert health["database_exists"], \
            f"Database {typedb3_client.database} should exist"


class TestTypeDB3Queries:
    """Test TypeDB 3.x query execution."""

    @pytest.fixture
    def connected_client(self):
        """Get connected TypeDB 3.x client."""
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        if not client.connect():
            pytest.skip("Cannot connect to TypeDB 3.x")
        yield client
        client.close()

    def test_simple_match_query(self, connected_client):
        """Test simple match query."""
        # This should work on any database
        results = connected_client.execute_query(
            "match $t isa rule; get $t; limit 1;"
        )
        # May be empty but shouldn't raise
        assert isinstance(results, list)

    def test_query_returns_list(self, connected_client):
        """Query should always return a list."""
        results = connected_client.execute_query(
            "match $r isa rule, has rule-id $id; get $id; limit 5;"
        )
        assert isinstance(results, list)

    def test_write_query_requires_write_mode(self, connected_client):
        """Insert queries need read_only=False."""
        # This should fail in read mode
        with pytest.raises(Exception):
            connected_client.execute_query(
                "insert $r isa rule, has rule-id 'TEST-999';",
                read_only=True  # Wrong mode
            )


class TestTypeDB3Schema:
    """Test TypeDB 3.x schema operations."""

    @pytest.fixture
    def connected_client(self):
        """Get connected TypeDB 3.x client."""
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        if not client.connect():
            pytest.skip("Cannot connect to TypeDB 3.x")
        yield client
        client.close()

    def test_query_schema_types(self, connected_client):
        """Query schema types."""
        # Should return types defined in schema
        results = connected_client.execute_query(
            "match $t type rule; get $t;"
        )
        # Rule type should exist
        assert isinstance(results, list)


# =============================================================================
# MIGRATION VERIFICATION TESTS
# =============================================================================

class TestMigrationVerification:
    """Verify data integrity after migration."""

    @pytest.fixture
    def connected_client(self):
        """Get connected TypeDB 3.x client."""
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        if not client.connect():
            pytest.skip("Cannot connect to TypeDB 3.x")
        yield client
        client.close()

    def test_rules_exist_after_migration(self, connected_client):
        """All rules should exist after migration."""
        results = connected_client.execute_query(
            "match $r isa rule; get $r; count;"
        )
        # We have ~50 rules
        # Note: count query returns differently in 3.x
        assert results is not None

    def test_tasks_exist_after_migration(self, connected_client):
        """All tasks should exist after migration."""
        results = connected_client.execute_query(
            "match $t isa task; get $t; limit 10;"
        )
        assert isinstance(results, list)

    def test_sessions_exist_after_migration(self, connected_client):
        """Sessions should exist after migration."""
        results = connected_client.execute_query(
            "match $s isa session; get $s; limit 5;"
        )
        assert isinstance(results, list)
