"""
Session Routing Mixin
Created: 2024-12-25 (P7.3)
Modularized: 2026-01-02 (RULE-032)

Handles routing sessions to TypeDB with embedding.
"""
import re
from typing import Dict, Any
from dataclasses import asdict

from governance.router.models import RouteResult


class SessionRoutingMixin:
    """Mixin for session routing operations."""

    # Session ID pattern for parsing
    SESSION_ID_PATTERN = re.compile(
        r'SESSION-(\d{4})-(\d{2})-(\d{2})-?(PHASE\d+)?-?([A-Z0-9-]+)?'
    )

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
        match = self.SESSION_ID_PATTERN.match(session_id)

        if not match:
            return {'date': '', 'phase': '', 'topic': ''}

        year, month, day, phase, topic = match.groups()
        return {
            'date': f"{year}-{month}-{day}",
            'phase': phase or '',
            'topic': topic or ''
        }
