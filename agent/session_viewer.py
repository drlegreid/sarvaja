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

Dependencies:
    pip install trame trame-vuetify trame-client
"""

import re
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, date
from dataclasses import dataclass, asdict

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import MCP tools
from governance.compat import (
    governance_list_sessions,
    governance_get_session,
    governance_evidence_search,
)

# Project paths (PROJECT_ROOT already defined above for imports)
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


class SessionViewer:
    """
    Enhanced Session Evidence Viewer.

    Provides detailed session browsing capabilities:
    - Timeline navigation (chronological order)
    - Section-based content parsing
    - In-session and cross-session search
    - Metadata extraction (phase, topic, date)
    - Navigation helpers (prev/next, by phase, by date)
    """

    # Session ID pattern: SESSION-YYYY-MM-DD-PHASEn-TOPIC
    SESSION_PATTERN = re.compile(
        r"SESSION-(\d{4})-(\d{2})-(\d{2})-?(PHASE\d+)?-?([A-Z0-9-]+)?"
    )

    def __init__(self):
        """Initialize Session Viewer."""
        self._sessions_cache: Dict[str, Dict] = {}

    # =========================================================================
    # MCP INTEGRATION
    # =========================================================================

    def _call_mcp_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Call an MCP tool and parse JSON response.

        Args:
            tool_name: Name of MCP tool
            **kwargs: Tool arguments

        Returns:
            Parsed JSON dict
        """
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

    # =========================================================================
    # TIMELINE VIEW
    # =========================================================================

    def get_sessions_timeline(
        self,
        limit: int = 50,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get sessions ordered by date (newest first).

        Args:
            limit: Maximum sessions to return
            start_date: Filter start date (YYYY-MM-DD)
            end_date: Filter end date (YYYY-MM-DD)

        Returns:
            List of session entries
        """
        result = self._call_mcp_tool('governance_list_sessions', limit=limit)

        if 'error' in result:
            return []

        sessions = result.get('sessions', [])

        # Apply date filtering
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

        # Sort by date descending (newest first)
        sessions.sort(key=lambda s: s.get('date', ''), reverse=True)

        return sessions

    # =========================================================================
    # DETAIL VIEW
    # =========================================================================

    def get_session_detail(self, session_id: str) -> Dict[str, Any]:
        """
        Get full session details with parsed sections.

        Args:
            session_id: Session ID

        Returns:
            Session detail dict with content and sections
        """
        result = self._call_mcp_tool('governance_get_session', session_id=session_id)

        if 'error' in result:
            return {'session_id': session_id, 'error': result['error']}

        content = result.get('content', '')
        sections = self._parse_sections(content)
        metadata = self.parse_session_id(session_id)

        return {
            'session_id': session_id,
            'content': content,
            'sections': sections,
            **metadata
        }

    def _parse_sections(self, content: str) -> List[Dict[str, str]]:
        """
        Parse markdown content into sections.

        Args:
            content: Markdown content

        Returns:
            List of section dicts with title and content
        """
        sections = []
        current_section = {'title': 'Introduction', 'content': '', 'level': 0}

        for line in content.split('\n'):
            # Check for headers
            if line.startswith('# '):
                if current_section['content'].strip():
                    sections.append(current_section)
                current_section = {'title': line[2:].strip(), 'content': '', 'level': 1}
            elif line.startswith('## '):
                if current_section['content'].strip():
                    sections.append(current_section)
                current_section = {'title': line[3:].strip(), 'content': '', 'level': 2}
            elif line.startswith('### '):
                if current_section['content'].strip():
                    sections.append(current_section)
                current_section = {'title': line[4:].strip(), 'content': '', 'level': 3}
            else:
                current_section['content'] += line + '\n'

        # Add final section
        if current_section['content'].strip() or current_section['title'] != 'Introduction':
            sections.append(current_section)

        return sections

    # =========================================================================
    # METADATA EXTRACTION
    # =========================================================================

    def get_session_metadata(self, session_id: str) -> Dict[str, Any]:
        """
        Get session metadata.

        Args:
            session_id: Session ID

        Returns:
            Metadata dict
        """
        metadata = self.parse_session_id(session_id)

        # Try to get file info
        file_path = EVIDENCE_DIR / f"{session_id}.md"
        if file_path.exists():
            stat = file_path.stat()
            metadata['file_size'] = stat.st_size
            metadata['modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()

        return metadata

    def parse_session_id(self, session_id: str) -> Dict[str, str]:
        """
        Parse session ID to extract metadata.

        Args:
            session_id: Session ID (e.g., SESSION-2024-12-25-PHASE8-HEALTHCHECK)

        Returns:
            Dict with date, phase, topic
        """
        match = self.SESSION_PATTERN.match(session_id)
        if not match:
            return {
                'session_id': session_id,
                'date': '',
                'phase': '',
                'topic': ''
            }

        year, month, day, phase, topic = match.groups()

        return {
            'session_id': session_id,
            'date': f"{year}-{month}-{day}",
            'phase': phase or '',
            'topic': topic or ''
        }

    # =========================================================================
    # SEARCH
    # =========================================================================

    def search_in_session(self, session_id: str, query: str) -> List[Dict[str, Any]]:
        """
        Search within a single session.

        Args:
            session_id: Session ID
            query: Search query

        Returns:
            List of search results with line numbers and context
        """
        detail = self.get_session_detail(session_id)

        if 'error' in detail:
            return []

        content = detail.get('content', '')
        results = []
        query_lower = query.lower()

        for i, line in enumerate(content.split('\n'), 1):
            if query_lower in line.lower():
                # Get context (surrounding lines)
                lines = content.split('\n')
                start = max(0, i - 2)
                end = min(len(lines), i + 2)
                context = '\n'.join(lines[start:end])

                results.append({
                    'match': line.strip(),
                    'line': i,
                    'context': context
                })

        return results

    def search_all_sessions(
        self,
        query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search across all sessions.

        Args:
            query: Search query
            limit: Max results

        Returns:
            List of results with session_id
        """
        result = self._call_mcp_tool(
            'governance_evidence_search',
            query=query,
            top_k=limit
        )

        if 'error' in result:
            return []

        # Filter to session results only
        results = []
        for r in result.get('results', []):
            source = r.get('source', '')
            if 'SESSION' in source:
                results.append({
                    'session_id': source,
                    'match': r.get('content', '')[:200],
                    'score': r.get('score', 0)
                })

        return results

    # =========================================================================
    # SUMMARY
    # =========================================================================

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Generate session summary with statistics.

        Args:
            session_id: Session ID

        Returns:
            Summary dict
        """
        detail = self.get_session_detail(session_id)

        if 'error' in detail:
            return {'session_id': session_id, 'error': detail['error']}

        content = detail.get('content', '')
        lines = content.split('\n')
        words = content.split()

        return {
            'session_id': session_id,
            'line_count': len(lines),
            'word_count': len(words),
            'section_count': len(detail.get('sections', [])),
            'date': detail.get('date', ''),
            'phase': detail.get('phase', ''),
            'topic': detail.get('topic', ''),
        }

    # =========================================================================
    # NAVIGATION
    # =========================================================================

    def get_adjacent_sessions(self, session_id: str) -> Dict[str, Optional[str]]:
        """
        Get previous and next sessions.

        Args:
            session_id: Current session ID

        Returns:
            Dict with 'previous' and 'next' session IDs
        """
        timeline = self.get_sessions_timeline(limit=100)

        previous_session = None
        next_session = None

        for i, session in enumerate(timeline):
            if session['session_id'] == session_id:
                if i > 0:
                    next_session = timeline[i - 1]['session_id']  # Newer
                if i < len(timeline) - 1:
                    previous_session = timeline[i + 1]['session_id']  # Older
                break

        return {
            'previous': previous_session,
            'next': next_session
        }

    def get_sessions_by_phase(self) -> Dict[str, List[Dict]]:
        """
        Group sessions by phase.

        Returns:
            Dict of phase -> sessions list
        """
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
        """
        Group sessions by date.

        Returns:
            Dict of date -> sessions list
        """
        timeline = self.get_sessions_timeline(limit=100)
        by_date: Dict[str, List[Dict]] = {}

        for session in timeline:
            session_date = session.get('date', 'Unknown')

            if session_date not in by_date:
                by_date[session_date] = []
            by_date[session_date].append(session)

        return by_date


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_session_viewer() -> SessionViewer:
    """
    Factory function to create Session Viewer.

    Returns:
        SessionViewer instance
    """
    return SessionViewer()


# =============================================================================
# CLI
# =============================================================================

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
