"""
Data Router Main Class
Created: 2024-12-25 (P7.3)
Modularized: 2026-01-02 (RULE-032)

Main DataRouter class combining all routing mixins.

Per DECISION-003: TypeDB-First Strategy
Per RULE-001: Session Evidence Logging
"""
from typing import Optional, Callable

from governance.embedding_pipeline import create_embedding_pipeline
from governance.router.rules import RuleRoutingMixin
from governance.router.decisions import DecisionRoutingMixin
from governance.router.sessions import SessionRoutingMixin
from governance.router.batch import BatchRoutingMixin


class DataRouter(
    RuleRoutingMixin,
    DecisionRoutingMixin,
    SessionRoutingMixin,
    BatchRoutingMixin
):
    """
    Routes new governance data to TypeDB.

    Features:
    - Automatic type detection from ID patterns
    - Optional embedding generation
    - Batch routing support
    - Pre/post routing hooks
    - Dry run mode for testing

    Example:
        router = DataRouter()
        result = router.route_rule(
            rule_id="RULE-023",
            name="New Rule",
            directive="All agents must log evidence"
        )
    """

    def __init__(
        self,
        dry_run: bool = False,
        embed: bool = True,
        typedb_host: str = "localhost",
        typedb_port: int = 1729,
        database: str = "sim-ai-governance",
        pre_route_hook: Optional[Callable] = None,
        post_route_hook: Optional[Callable] = None
    ):
        """
        Initialize Data Router.

        Args:
            dry_run: If True, don't actually write to TypeDB
            embed: If True, generate embeddings for routed data
            typedb_host: TypeDB host
            typedb_port: TypeDB port
            database: TypeDB database name
            pre_route_hook: Called before routing (item_type, data) -> data
            post_route_hook: Called after routing (item_type, result)
        """
        self.dry_run = dry_run
        self.embed = embed
        self.typedb_host = typedb_host
        self.typedb_port = typedb_port
        self.database = database
        self.pre_route_hook = pre_route_hook
        self.post_route_hook = post_route_hook

        # Initialize embedding pipeline if needed
        # Per GAP-EMBED-001: Use env config, not hardcoded mock
        self.embedding_pipeline = None
        if embed:
            self.embedding_pipeline = create_embedding_pipeline()

    def _execute_typeql(self, typeql: str) -> bool:
        """Execute TypeQL against TypeDB."""
        if self.dry_run:
            return True

        try:
            from typedb.driver import TypeDB, SessionType, TransactionType

            address = f"{self.typedb_host}:{self.typedb_port}"
            with TypeDB.core_driver(address) as client:
                with client.session(self.database, SessionType.DATA) as session:
                    with session.transaction(TransactionType.WRITE) as tx:
                        tx.query.insert(typeql)
                        tx.commit()
            return True

        except ImportError:
            print("TypeDB driver not installed")
            return False
        except Exception as e:
            print(f"TypeQL execution failed: {e}")
            return False

    @staticmethod
    def _escape(text: str) -> str:
        """Escape text for TypeQL string literals."""
        if not text:
            return ""
        return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')


def create_data_router(
    dry_run: bool = False,
    embed: bool = True,
    **kwargs
) -> DataRouter:
    """
    Factory function to create Data Router.

    Args:
        dry_run: Don't write to TypeDB
        embed: Generate embeddings
        **kwargs: Additional options

    Returns:
        DataRouter instance
    """
    return DataRouter(dry_run=dry_run, embed=embed, **kwargs)
