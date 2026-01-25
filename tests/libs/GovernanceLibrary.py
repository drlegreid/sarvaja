"""
Robot Framework Library for Governance Module Tests.

Tests for rule inference and knowledge reasoning.
Per DECISION-003: TypeDB-First Architecture
Migrated from tests/test_governance.py
"""
import os
from datetime import datetime
from unittest.mock import Mock, patch
from robot.api.deco import keyword


class GovernanceLibrary:
    """Library for testing governance module components."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =============================================================================
    # Dataclass Tests
    # =============================================================================

    @keyword("Rule Creation Works")
    def rule_creation_works(self):
        """Test Rule dataclass creation."""
        try:
            from governance import Rule

            rule = Rule(
                id="RULE-001",
                name="Evidence Logging",
                category="governance",
                priority="CRITICAL",
                status="ACTIVE",
                directive="Log all session evidence"
            )

            return {
                "id_correct": rule.id == "RULE-001",
                "name_correct": rule.name == "Evidence Logging",
                "category_correct": rule.category == "governance",
                "priority_correct": rule.priority == "CRITICAL",
                "status_correct": rule.status == "ACTIVE",
                "created_date_none": rule.created_date is None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Rule With Date Works")
    def rule_with_date_works(self):
        """Test Rule dataclass with datetime."""
        try:
            from governance import Rule

            now = datetime.now()
            rule = Rule(
                id="RULE-002",
                name="Best Practices",
                category="architecture",
                priority="HIGH",
                status="ACTIVE",
                directive="Follow architectural best practices",
                created_date=now
            )

            return {"date_set": rule.created_date == now}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Decision Creation Works")
    def decision_creation_works(self):
        """Test Decision dataclass creation."""
        try:
            from governance import Decision

            decision = Decision(
                id="DECISION-001",
                name="Stack Simplification",
                context="Too many services",
                rationale="Reduce complexity for PoC",
                status="APPROVED"
            )

            return {
                "id_correct": decision.id == "DECISION-001",
                "name_correct": decision.name == "Stack Simplification",
                "status_correct": decision.status == "APPROVED",
                "date_none": decision.decision_date is None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Inference Result Creation Works")
    def inference_result_creation_works(self):
        """Test InferenceResult dataclass creation."""
        try:
            from governance import InferenceResult

            result = InferenceResult(
                query="match $r isa rule-entity;",
                results=[{"id": "RULE-001"}, {"id": "RULE-002"}],
                count=2,
                inference_used=True
            )

            return {
                "query_starts_match": result.query.startswith("match"),
                "results_count_2": len(result.results) == 2,
                "count_correct": result.count == 2,
                "inference_true": result.inference_used is True
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Quick Health Tests
    # =============================================================================

    @keyword("Quick Health Returns Bool")
    def quick_health_returns_bool(self):
        """Test that quick_health returns a boolean."""
        try:
            from governance import quick_health

            result = quick_health()
            return {"is_bool": isinstance(result, bool)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Quick Health Mocked Success")
    def quick_health_mocked_success(self):
        """Test quick_health with mocked successful connection."""
        try:
            from governance import quick_health

            with patch('socket.socket') as mock_socket:
                mock_sock_instance = Mock()
                mock_sock_instance.connect_ex.return_value = 0
                mock_socket.return_value = mock_sock_instance

                result = quick_health()

                return {
                    "returns_true": result is True,
                    "close_called": mock_sock_instance.close.called
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Quick Health Mocked Failure")
    def quick_health_mocked_failure(self):
        """Test quick_health with mocked failed connection."""
        try:
            from governance import quick_health

            with patch('socket.socket') as mock_socket:
                mock_sock_instance = Mock()
                mock_sock_instance.connect_ex.return_value = 1
                mock_socket.return_value = mock_sock_instance

                result = quick_health()

                return {"returns_false": result is False}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Schema Files Tests
    # =============================================================================

    @keyword("Schema File Exists")
    def schema_file_exists(self):
        """Test that schema file path is valid."""
        try:
            from governance import SCHEMA_FILE

            return {
                "ends_with_tql": SCHEMA_FILE.endswith("schema.tql"),
                "exists": os.path.exists(SCHEMA_FILE)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Data File Exists")
    def data_file_exists(self):
        """Test that data file path is valid."""
        try:
            from governance import DATA_FILE

            return {
                "ends_with_tql": DATA_FILE.endswith("data.tql"),
                "exists": os.path.exists(DATA_FILE)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Schema File Has Content")
    def schema_file_has_content(self):
        """Test that schema file has content."""
        try:
            from governance import SCHEMA_FILE

            with open(SCHEMA_FILE, 'r') as f:
                content = f.read()

            return {
                "has_define": "define" in content,
                "has_rule_entity": "rule-entity" in content,
                "has_decision": "decision" in content
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except FileNotFoundError:
            return {"skipped": True, "reason": "Schema file not found"}

    @keyword("Data File Has Content")
    def data_file_has_content(self):
        """Test that data file has content."""
        try:
            from governance import DATA_FILE

            with open(DATA_FILE, 'r') as f:
                content = f.read()

            return {
                "has_insert": "insert" in content,
                "has_rule_001": "RULE-001" in content
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except FileNotFoundError:
            return {"skipped": True, "reason": "Data file not found"}

    # =============================================================================
    # TypeDB Client Unit Tests
    # =============================================================================

    @keyword("Client Initialization Works")
    def client_initialization_works(self):
        """Test client initializes with default values."""
        try:
            from governance import TypeDBClient

            client = TypeDBClient()

            # Accept either localhost (dev) or typedb (container) as valid defaults
            valid_host = client.host in ("localhost", "typedb")

            return {
                "valid_host": valid_host,
                "port_correct": client.port == 1729,
                "database_correct": client.database == "sim-ai-governance",
                "not_connected": client._connected is False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Client Custom Params Works")
    def client_custom_params_works(self):
        """Test client with custom parameters."""
        try:
            from governance import TypeDBClient

            client = TypeDBClient(host="custom-host", port=9999, database="custom-db")

            return {
                "host_correct": client.host == "custom-host",
                "port_correct": client.port == 9999,
                "database_correct": client.database == "custom-db"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Is Connected Default False")
    def is_connected_default_false(self):
        """Test is_connected returns False before connecting."""
        try:
            from governance import TypeDBClient

            client = TypeDBClient()
            return {"not_connected": client.is_connected() is False}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Health Check Not Connected")
    def health_check_not_connected(self):
        """Test health_check returns error when not connected."""
        try:
            from governance import TypeDBClient

            client = TypeDBClient()
            health = client.health_check()

            return {
                "not_healthy": health["healthy"] is False,
                "has_error": "Not connected" in health.get("error", "")
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Execute Query Not Connected Raises")
    def execute_query_not_connected_raises(self):
        """Test _execute_query raises error when not connected."""
        try:
            from governance import TypeDBClient

            client = TypeDBClient()
            raises = False
            error_msg = ""

            try:
                client._execute_query("match $x isa rule-entity;")
            except RuntimeError as e:
                raises = True
                error_msg = str(e)

            return {
                "raises_error": raises,
                "mentions_not_connected": "Not connected" in error_msg
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
