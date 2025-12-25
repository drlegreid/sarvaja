"""
Data Router (P7.3)
Created: 2024-12-25

Routes new data to TypeDB with optional embedding generation.
Supports: rules, decisions, sessions.

Per DECISION-003: TypeDB-First Strategy
Per RULE-001: Session Evidence Logging

Usage:
    router = DataRouter()
    router.route_rule(rule_id="RULE-023", name="New Rule", directive="Do the thing")
    router.route_decision(decision_id="DECISION-005", name="New Decision", context="Why")
    router.route_session(session_id="SESSION-2024-12-25-PHASE9", content="Evidence...")
"""

import re
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass, asdict

from governance.embedding_pipeline import EmbeddingPipeline, create_embedding_pipeline
from governance.vector_store import MockEmbeddings

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
EVIDENCE_DIR = PROJECT_ROOT / "evidence"


@dataclass
class RouteResult:
    """Result of a routing operation."""
    success: bool
    destination: str
    item_type: str
    item_id: str
    embedded: bool = False
    error: Optional[str] = None
    metadata: Optional[Dict] = None
    evidence_file: Optional[str] = None


class DataRouter:
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

    # ID patterns for auto-detection
    RULE_PATTERN = re.compile(r'^RULE-\d{3}$')
    DECISION_PATTERN = re.compile(r'^DECISION-\d{3}$')
    SESSION_PATTERN = re.compile(r'^SESSION-\d{4}-\d{2}-\d{2}')

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
        self.embedding_pipeline = None
        if embed:
            self.embedding_pipeline = create_embedding_pipeline(use_mock=True)

    # =========================================================================
    # RULE ROUTING
    # =========================================================================

    def route_rule(
        self,
        rule_id: str,
        name: str,
        directive: str = "",
        category: str = "governance",
        priority: str = "MEDIUM",
        status: str = "ACTIVE"
    ) -> Dict[str, Any]:
        """
        Route a new rule to TypeDB.

        Args:
            rule_id: Rule ID (e.g., "RULE-023")
            name: Rule name/title
            directive: Rule directive (the actual rule text)
            category: Rule category
            priority: Rule priority (CRITICAL, HIGH, MEDIUM, LOW)
            status: Rule status (ACTIVE, DRAFT, DEPRECATED)

        Returns:
            RouteResult as dict
        """
        # Validate
        if not rule_id:
            return asdict(RouteResult(
                success=False,
                destination='none',
                item_type='rule',
                item_id=rule_id,
                error='rule_id is required'
            ))

        # Pre-hook
        data = {
            'rule_id': rule_id,
            'name': name,
            'directive': directive,
            'category': category,
            'priority': priority,
            'status': status
        }
        if self.pre_route_hook:
            data = self.pre_route_hook('rule', data)

        # Generate TypeQL
        typeql = self._generate_rule_typeql(**data)

        # Execute (or dry run)
        embedded = False
        if not self.dry_run:
            success = self._execute_typeql(typeql)
            if success and self.embed and self.embedding_pipeline:
                self.embedding_pipeline.embed_and_store_rule(
                    rule_id,
                    f"{name}: {directive}"
                )
                embedded = True
        else:
            success = True
            embedded = self.embed

        result = asdict(RouteResult(
            success=success,
            destination='typedb',
            item_type='rule',
            item_id=rule_id,
            embedded=embedded
        ))

        # Post-hook
        if self.post_route_hook:
            self.post_route_hook('rule', result)

        return result

    def _generate_rule_typeql(
        self,
        rule_id: str,
        name: str,
        directive: str = "",
        category: str = "governance",
        priority: str = "MEDIUM",
        status: str = "ACTIVE"
    ) -> str:
        """Generate TypeQL insert for rule."""
        return f'''
            insert $r isa rule-entity,
                has id "{self._escape(rule_id)}",
                has name "{self._escape(name)}",
                has directive "{self._escape(directive)}",
                has category "{self._escape(category)}",
                has priority "{self._escape(priority)}",
                has status "{self._escape(status)}",
                has created-date {datetime.now().isoformat()};
        '''

    # =========================================================================
    # DECISION ROUTING
    # =========================================================================

    def route_decision(
        self,
        decision_id: str,
        name: str,
        context: str = "",
        rationale: str = "",
        impacts: str = "",
        status: str = "ACTIVE",
        create_evidence: bool = False
    ) -> Dict[str, Any]:
        """
        Route a new decision to TypeDB.

        Args:
            decision_id: Decision ID (e.g., "DECISION-005")
            name: Decision name
            context: Decision context
            rationale: Decision rationale
            impacts: Expected impacts
            status: Decision status
            create_evidence: Create evidence markdown file

        Returns:
            RouteResult as dict
        """
        # Validate
        if not decision_id:
            return asdict(RouteResult(
                success=False,
                destination='none',
                item_type='decision',
                item_id=decision_id,
                error='decision_id is required'
            ))

        # Pre-hook
        data = {
            'decision_id': decision_id,
            'name': name,
            'context': context,
            'rationale': rationale,
            'impacts': impacts,
            'status': status
        }
        if self.pre_route_hook:
            data = self.pre_route_hook('decision', data)

        # Generate TypeQL
        typeql = self._generate_decision_typeql(**data)

        # Execute
        embedded = False
        evidence_file = None

        if not self.dry_run:
            success = self._execute_typeql(typeql)
            if success and self.embed and self.embedding_pipeline:
                self.embedding_pipeline.embed_decision(
                    decision_id,
                    f"{name}: {context}"
                )
                embedded = True

            if success and create_evidence:
                evidence_file = self._create_decision_evidence(data)
        else:
            success = True
            embedded = self.embed
            if create_evidence:
                evidence_file = f"evidence/{decision_id}.md (dry run)"

        result = asdict(RouteResult(
            success=success,
            destination='typedb',
            item_type='decision',
            item_id=decision_id,
            embedded=embedded,
            evidence_file=evidence_file
        ))

        if self.post_route_hook:
            self.post_route_hook('decision', result)

        return result

    def _generate_decision_typeql(
        self,
        decision_id: str,
        name: str,
        context: str = "",
        rationale: str = "",
        impacts: str = "",
        status: str = "ACTIVE"
    ) -> str:
        """Generate TypeQL insert for decision."""
        return f'''
            insert $d isa decision,
                has decision-id "{self._escape(decision_id)}",
                has decision-name "{self._escape(name)}",
                has decision-context "{self._escape(context)}",
                has decision-rationale "{self._escape(rationale)}",
                has decision-impacts "{self._escape(impacts)}",
                has decision-status "{self._escape(status)}",
                has decision-date {datetime.now().isoformat()};
        '''

    def _create_decision_evidence(self, data: Dict) -> str:
        """Create evidence markdown file for decision."""
        filepath = EVIDENCE_DIR / f"{data['decision_id']}.md"
        content = f"""# {data['decision_id']}: {data['name']}

**Date:** {datetime.now().isoformat()}
**Status:** {data.get('status', 'ACTIVE')}

## Context

{data.get('context', 'No context provided.')}

## Rationale

{data.get('rationale', 'No rationale provided.')}

## Expected Impacts

{data.get('impacts', 'No impacts specified.')}

---
*Generated by governance/data_router.py (P7.3)*
"""
        filepath.write_text(content)
        return str(filepath)

    # =========================================================================
    # SESSION ROUTING
    # =========================================================================

    def route_session(
        self,
        session_id: str,
        content: str = ""
    ) -> Dict[str, Any]:
        """
        Route a new session to TypeDB.

        Args:
            session_id: Session ID (e.g., "SESSION-2024-12-25-PHASE9-FEATURE")
            content: Session markdown content

        Returns:
            RouteResult as dict
        """
        # Validate
        if not session_id:
            return asdict(RouteResult(
                success=False,
                destination='none',
                item_type='session',
                item_id=session_id,
                error='session_id is required'
            ))

        # Extract metadata from session ID
        metadata = self._parse_session_id(session_id)

        # Pre-hook
        data = {
            'session_id': session_id,
            'content': content,
            'metadata': metadata
        }
        if self.pre_route_hook:
            data = self.pre_route_hook('session', data)

        # For sessions, we primarily embed (TypeDB session storage is optional)
        embedded = False
        if self.embed and self.embedding_pipeline:
            if not self.dry_run:
                self.embedding_pipeline.embed_session(session_id, content)
            embedded = True

        result = asdict(RouteResult(
            success=True,
            destination='typedb',
            item_type='session',
            item_id=session_id,
            embedded=embedded,
            metadata=metadata
        ))

        if self.post_route_hook:
            self.post_route_hook('session', result)

        return result

    def _parse_session_id(self, session_id: str) -> Dict[str, str]:
        """Extract metadata from session ID."""
        pattern = re.compile(
            r'SESSION-(\d{4})-(\d{2})-(\d{2})-?(PHASE\d+)?-?([A-Z0-9-]+)?'
        )
        match = pattern.match(session_id)

        if not match:
            return {'date': '', 'phase': '', 'topic': ''}

        year, month, day, phase, topic = match.groups()
        return {
            'date': f"{year}-{month}-{day}",
            'phase': phase or '',
            'topic': topic or ''
        }

    # =========================================================================
    # AUTO ROUTING
    # =========================================================================

    def route_auto(
        self,
        identifier: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Auto-detect type and route accordingly.

        Args:
            identifier: ID string (RULE-*, DECISION-*, SESSION-*)
            data: Data dict

        Returns:
            RouteResult with detected type
        """
        if self.RULE_PATTERN.match(identifier):
            result = self.route_rule(rule_id=identifier, **data)
            result['type'] = 'rule'
            return result

        elif self.DECISION_PATTERN.match(identifier):
            result = self.route_decision(decision_id=identifier, **data)
            result['type'] = 'decision'
            return result

        elif self.SESSION_PATTERN.match(identifier):
            result = self.route_session(session_id=identifier, **data)
            result['type'] = 'session'
            return result

        else:
            return {
                'success': False,
                'type': 'unknown',
                'error': f'Could not detect type for: {identifier}'
            }

    # =========================================================================
    # BATCH ROUTING
    # =========================================================================

    def route_batch(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Route multiple items in batch.

        Args:
            items: List of items with 'type' field

        Returns:
            Batch result with counts
        """
        succeeded = 0
        failed = 0
        results = []

        for item in items:
            item_type = item.pop('type', None)

            try:
                if item_type == 'rule':
                    result = self.route_rule(**item)
                elif item_type == 'decision':
                    result = self.route_decision(**item)
                elif item_type == 'session':
                    result = self.route_session(**item)
                else:
                    result = {'success': False, 'error': f'Unknown type: {item_type}'}

                if result.get('success'):
                    succeeded += 1
                else:
                    failed += 1

                results.append(result)

            except Exception as e:
                failed += 1
                results.append({'success': False, 'error': str(e)})

        return {
            'total': len(items),
            'succeeded': succeeded,
            'failed': failed,
            'results': results
        }

    # =========================================================================
    # HELPERS
    # =========================================================================

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


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

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


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI for data router."""
    import argparse

    parser = argparse.ArgumentParser(description="Data Router")
    parser.add_argument("type", choices=["rule", "decision", "session"])
    parser.add_argument("--id", required=True, help="Item ID")
    parser.add_argument("--name", help="Item name")
    parser.add_argument("--content", help="Content/directive")
    parser.add_argument("--dry-run", "-n", action="store_true")
    args = parser.parse_args()

    router = create_data_router(dry_run=args.dry_run)

    if args.type == "rule":
        result = router.route_rule(
            rule_id=args.id,
            name=args.name or "Unnamed Rule",
            directive=args.content or ""
        )
    elif args.type == "decision":
        result = router.route_decision(
            decision_id=args.id,
            name=args.name or "Unnamed Decision",
            context=args.content or ""
        )
    else:
        result = router.route_session(
            session_id=args.id,
            content=args.content or ""
        )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
