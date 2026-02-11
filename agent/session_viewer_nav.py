"""
Session Viewer Search & Navigation (Mixin).

Per DOC-SIZE-01-v1: Extracted from session_viewer.py (520 lines).
In-session search, cross-session search, and navigation helpers.
"""

from typing import Any, Dict, List, Optional


class SessionNavigationMixin:
    """Mixin providing search and navigation methods.

    Expects host class to provide:
        self._call_mcp_tool(tool_name, **kwargs) -> Dict
        self.get_session_detail(session_id) -> Dict
        self.get_sessions_timeline(limit) -> List[Dict]
        self.parse_session_id(session_id) -> Dict
    """

    def search_in_session(self, session_id: str, query: str) -> List[Dict[str, Any]]:
        """Search within a single session."""
        detail = self.get_session_detail(session_id)

        if 'error' in detail:
            return []

        content = detail.get('content', '')
        results = []
        query_lower = query.lower()

        for i, line in enumerate(content.split('\n'), 1):
            if query_lower in line.lower():
                lines = content.split('\n')
                start = max(0, i - 2)
                end = min(len(lines), i + 2)
                context = '\n'.join(lines[start:end])

                results.append({
                    'match': line.strip(),
                    'line': i,
                    'context': context,
                })

        return results

    def search_all_sessions(
        self,
        query: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search across all sessions."""
        result = self._call_mcp_tool(
            'governance_evidence_search',
            query=query,
            top_k=limit,
        )

        if 'error' in result:
            return []

        results = []
        for r in result.get('results', []):
            source = r.get('source', '')
            if 'SESSION' in source:
                results.append({
                    'session_id': source,
                    'match': r.get('content', '')[:200],
                    'score': r.get('score', 0),
                })

        return results

    def get_adjacent_sessions(self, session_id: str) -> Dict[str, Optional[str]]:
        """Get previous and next sessions."""
        timeline = self.get_sessions_timeline(limit=100)

        previous_session = None
        next_session = None

        for i, session in enumerate(timeline):
            if session['session_id'] == session_id:
                if i > 0:
                    next_session = timeline[i - 1]['session_id']
                if i < len(timeline) - 1:
                    previous_session = timeline[i + 1]['session_id']
                break

        return {
            'previous': previous_session,
            'next': next_session,
        }

    def get_sessions_by_phase(self) -> Dict[str, List[Dict]]:
        """Group sessions by phase."""
        timeline = self.get_sessions_timeline(limit=100)
        by_phase: Dict[str, List[Dict]] = {}

        for session in timeline:
            metadata = self.parse_session_id(session['session_id'])
            phase = metadata.get('phase', 'Unknown')

            if phase not in by_phase:
                by_phase[phase] = []
            by_phase[phase].append(session)

        return by_phase

    def get_sessions_by_date(self) -> Dict[str, List[Dict]]:
        """Group sessions by date."""
        timeline = self.get_sessions_timeline(limit=100)
        by_date: Dict[str, List[Dict]] = {}

        for session in timeline:
            session_date = session.get('date', 'Unknown')

            if session_date not in by_date:
                by_date[session_date] = []
            by_date[session_date].append(session)

        return by_date
