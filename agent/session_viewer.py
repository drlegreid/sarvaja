"""
Session Evidence Viewer (P9.3)
Created: 2024-12-25

Enhanced session browsing with:
- Timeline view (chronological navigation)
- Detail view (full markdown content with sections)
- Search (within session and across all sessions)
- Metadata extraction (phase, topic, date)

Per RULE-001: Session Evidence Logging
Per RULE-019: UI/UX Design Standards
Per DOC-SIZE-01-v1: Content in session_viewer_content.py, nav in session_viewer_nav.py.

Dependencies:
    pip install trame trame-vuetify trame-client
"""

import re
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from governance.compat import (
    governance_list_sessions,
    governance_get_session,
    governance_evidence_search,
)
from .session_viewer_content import SessionContentMixin  # noqa: F401 — re-export
from .session_viewer_nav import SessionNavigationMixin  # noqa: F401 — re-export

EVIDENCE_DIR = PROJECT_ROOT / "evidence"


@dataclass
class SessionEntry:
    """Session timeline entry."""
    session_id: str
    date: str
    phase: str
    topic: str
    file_path: str


@dataclass
class SearchResult:
    """Session search result."""
    session_id: str
    match: str
    line: int
    context: str


class SessionViewer(SessionContentMixin, SessionNavigationMixin):
    """
    Enhanced Session Evidence Viewer.

    Provides detailed session browsing capabilities:
    - Timeline navigation (chronological order)
    - Section-based content parsing
    - In-session and cross-session search
    - Metadata extraction (phase, topic, date)
    - Navigation helpers (prev/next, by phase, by date)
    """

    SESSION_PATTERN = re.compile(
        r"SESSION-(\d{4})-(\d{2})-(\d{2})-?(PHASE\d+)?-?([A-Z0-9-]+)?"
    )

    def __init__(self):
        self._sessions_cache: Dict[str, Dict] = {}

    def _call_mcp_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Call an MCP tool and parse JSON response."""
        tools = {
            'governance_list_sessions': governance_list_sessions,
            'governance_get_session': governance_get_session,
            'governance_evidence_search': governance_evidence_search,
        }

        tool_func = tools.get(tool_name)
        if not tool_func:
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            result = tool_func(**kwargs)
            return json.loads(result)
        except Exception as e:
            return {"error": str(e)}

    def get_sessions_timeline(
        self,
        limit: int = 50,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get sessions ordered by date (newest first)."""
        result = self._call_mcp_tool('governance_list_sessions', limit=limit)

        if 'error' in result:
            return []

        sessions = result.get('sessions', [])

        if start_date or end_date:
            filtered = []
            for session in sessions:
                session_date = session.get('date', '')
                if start_date and session_date < start_date:
                    continue
                if end_date and session_date > end_date:
                    continue
                filtered.append(session)
            sessions = filtered

        sessions.sort(key=lambda s: s.get('date', ''), reverse=True)
        return sessions


def create_session_viewer() -> SessionViewer:
    """Factory function to create Session Viewer."""
    return SessionViewer()


def main():
    """CLI for session viewer."""
    import argparse

    parser = argparse.ArgumentParser(description="Session Evidence Viewer")
    parser.add_argument("command", choices=["timeline", "detail", "search", "summary"])
    parser.add_argument("--session", "-s", help="Session ID")
    parser.add_argument("--query", "-q", help="Search query")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Limit results")
    args = parser.parse_args()

    viewer = SessionViewer()

    if args.command == "timeline":
        timeline = viewer.get_sessions_timeline(limit=args.limit)
        for entry in timeline:
            print(f"{entry['date']} | {entry['session_id']}")
    elif args.command == "detail" and args.session:
        detail = viewer.get_session_detail(args.session)
        print(f"Session: {detail['session_id']}")
        print(f"Phase: {detail.get('phase', 'N/A')}")
        print(f"Topic: {detail.get('topic', 'N/A')}")
        print(f"Sections: {len(detail.get('sections', []))}")
    elif args.command == "search" and args.query:
        if args.session:
            results = viewer.search_in_session(args.session, args.query)
        else:
            results = viewer.search_all_sessions(args.query, limit=args.limit)
        for r in results:
            print(f"Line {r.get('line', 'N/A')}: {r.get('match', '')[:80]}...")
    elif args.command == "summary" and args.session:
        summary = viewer.get_session_summary(args.session)
        print(f"Session: {summary['session_id']}")
        print(f"Lines: {summary.get('line_count', 0)}")
        print(f"Words: {summary.get('word_count', 0)}")
        print(f"Sections: {summary.get('section_count', 0)}")


if __name__ == "__main__":
    main()
