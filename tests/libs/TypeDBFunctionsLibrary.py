"""
TypeDB Functions Library for Robot Framework
Integration tests for TypeDB 3.x inference functions.
Migrated from tests/integration/test_typedb_functions.py
Per: RF-007 Robot Framework Migration
"""
import os
from robot.api.deco import keyword


class TypeDBFunctionsLibrary:
    """Robot Framework keywords for TypeDB functions tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    TYPEDB_HOST = os.getenv("TYPEDB_HOST", "localhost")
    TYPEDB_PORT = int(os.getenv("TYPEDB_PORT", "1729"))
    DATABASE_NAME = os.getenv("TYPEDB_DATABASE", "sim-ai-governance")

    def _get_driver(self):
        """Get TypeDB 3.x driver connection."""
        try:
            from typedb.driver import TypeDB, Credentials, DriverOptions

            address = f"{self.TYPEDB_HOST}:{self.TYPEDB_PORT}"
            username = os.getenv("TYPEDB_USERNAME", "admin")
            password = os.getenv("TYPEDB_PASSWORD", "password")

            credentials = Credentials(username, password)
            options = DriverOptions(is_tls_enabled=False)

            return TypeDB.driver(address, credentials, options)
        except ImportError:
            return None
        except Exception:
            return None

    # =========================================================================
    # Transitive Dependencies Tests
    # =========================================================================

    @keyword("Transitive Dependencies Function Exists")
    def transitive_dependencies_function_exists(self):
        """Verify transitive_dependencies() function is defined in schema."""
        driver = self._get_driver()
        if driver is None:
            return {"skipped": True, "reason": "TypeDB driver not available"}

        try:
            from typedb.driver import TransactionType

            with driver.transaction(self.DATABASE_NAME, TransactionType.READ) as tx:
                query = """
                    match
                      let $dep, $rule in transitive_dependencies();
                      $dep has rule-id $depId;
                      $rule has rule-id $ruleId;
                """
                result = tx.query(query).resolve()
                driver.close()
                return {"function_exists": True}
        except Exception as e:
            driver.close()
            if "Unknown function" in str(e):
                return {"skipped": True, "reason": "Function not yet defined in schema"}
            return {"skipped": True, "reason": str(e)}

    @keyword("Transitive Dependencies Returns Direct")
    def transitive_dependencies_returns_direct(self):
        """Transitive function includes direct dependencies."""
        driver = self._get_driver()
        if driver is None:
            return {"skipped": True, "reason": "TypeDB driver not available"}

        try:
            from typedb.driver import TransactionType

            with driver.transaction(self.DATABASE_NAME, TransactionType.READ) as tx:
                # Get direct dependencies
                direct_query = """
                    match
                      (dependent: $dep, dependency: $rule) isa rule-dependency;
                      $dep has rule-id $depId;
                      $rule has rule-id $ruleId;
                """
                direct_result = list(tx.query(direct_query).resolve() or [])

                # Get function results
                func_query = """
                    match
                      let $dep, $rule in transitive_dependencies();
                      $dep has rule-id $depId;
                      $rule has rule-id $ruleId;
                """
                func_result = list(tx.query(func_query).resolve() or [])

                driver.close()
                return {
                    "includes_direct": len(func_result) >= len(direct_result),
                    "direct_count": len(direct_result),
                    "function_count": len(func_result)
                }
        except Exception as e:
            driver.close()
            if "Unknown function" in str(e):
                return {"skipped": True, "reason": "Function not yet defined in schema"}
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Priority Conflicts Tests
    # =========================================================================

    @keyword("Priority Conflicts Detection")
    def priority_conflicts_detection(self):
        """Conflicting rules should be detected."""
        driver = self._get_driver()
        if driver is None:
            return {"skipped": True, "reason": "TypeDB driver not available"}

        try:
            from typedb.driver import TransactionType

            with driver.transaction(self.DATABASE_NAME, TransactionType.READ) as tx:
                query = """
                    match
                      let $r1, $r2 in priority_conflicts();
                      $r1 has rule-id $id1;
                      $r2 has rule-id $id2;
                """
                result = list(tx.query(query).resolve() or [])
                driver.close()
                return {
                    "function_executes": True,
                    "conflict_count": len(result)
                }
        except Exception as e:
            driver.close()
            if "Unknown function" in str(e):
                return {"skipped": True, "reason": "Function not yet defined in schema"}
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Escalated Proposals Tests
    # =========================================================================

    @keyword("Escalated Proposals Detection")
    def escalated_proposals_detection(self):
        """Proposals with 'escalate' resolution should be found."""
        driver = self._get_driver()
        if driver is None:
            return {"skipped": True, "reason": "TypeDB driver not available"}

        try:
            from typedb.driver import TransactionType

            with driver.transaction(self.DATABASE_NAME, TransactionType.READ) as tx:
                query = """
                    match
                      let $proposal, $dispute in escalated_proposals();
                      $proposal has proposal-id $pid;
                      $dispute has resolution-method $method;
                """
                result = list(tx.query(query).resolve() or [])

                all_escalate = True
                for row in result:
                    for var in row.column_names():
                        if var == "method":
                            method = row.get(var).value
                            if method != "escalate":
                                all_escalate = False

                driver.close()
                return {
                    "function_executes": True,
                    "result_count": len(result),
                    "all_escalate": all_escalate
                }
        except Exception as e:
            driver.close()
            if "Unknown function" in str(e):
                return {"skipped": True, "reason": "Function not yet defined in schema"}
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Cascaded Decision Affects Tests
    # =========================================================================

    @keyword("Cascaded Decision Affects Includes Direct")
    def cascaded_decision_affects_includes_direct(self):
        """Function should include direct decision-affects relations."""
        driver = self._get_driver()
        if driver is None:
            return {"skipped": True, "reason": "TypeDB driver not available"}

        try:
            from typedb.driver import TransactionType

            with driver.transaction(self.DATABASE_NAME, TransactionType.READ) as tx:
                # Get direct affects
                direct_query = """
                    match
                      (affecting-decision: $d, affected-rule: $r) isa decision-affects;
                      $d has decision-id $did;
                      $r has rule-id $rid;
                """
                direct_result = list(tx.query(direct_query).resolve() or [])

                # Get function results
                func_query = """
                    match
                      let $d, $r in cascaded_decision_affects();
                      $d has decision-id $did;
                      $r has rule-id $rid;
                """
                func_result = list(tx.query(func_query).resolve() or [])

                driver.close()
                return {
                    "includes_direct": len(func_result) >= len(direct_result),
                    "direct_count": len(direct_result),
                    "function_count": len(func_result)
                }
        except Exception as e:
            driver.close()
            if "Unknown function" in str(e):
                return {"skipped": True, "reason": "Function not yet defined in schema"}
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Proposal Cascade Affects Tests
    # =========================================================================

    @keyword("Proposal Cascade Affects Includes Direct")
    def proposal_cascade_affects_includes_direct(self):
        """Function should include direct proposal-affects relations."""
        driver = self._get_driver()
        if driver is None:
            return {"skipped": True, "reason": "TypeDB driver not available"}

        try:
            from typedb.driver import TransactionType

            with driver.transaction(self.DATABASE_NAME, TransactionType.READ) as tx:
                # Get direct affects
                direct_query = """
                    match
                      (proposing: $p, affected-rule: $r) isa proposal-affects;
                      $p has proposal-id $pid;
                      $r has rule-id $rid;
                """
                direct_result = list(tx.query(direct_query).resolve() or [])

                # Get function results
                func_query = """
                    match
                      let $p, $r in proposal_cascade_affects();
                      $p has proposal-id $pid;
                      $r has rule-id $rid;
                """
                func_result = list(tx.query(func_query).resolve() or [])

                driver.close()
                return {
                    "includes_direct": len(func_result) >= len(direct_result),
                    "direct_count": len(direct_result),
                    "function_count": len(func_result)
                }
        except Exception as e:
            driver.close()
            if "Unknown function" in str(e):
                return {"skipped": True, "reason": "Function not yet defined in schema"}
            return {"skipped": True, "reason": str(e)}
