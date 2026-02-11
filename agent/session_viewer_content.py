"""
Session Viewer Content & Metadata (Mixin).

Per DOC-SIZE-01-v1: Extracted from session_viewer.py (520 lines).
Detail view, section parsing, metadata extraction, and summary.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

EVIDENCE_DIR = Path(__file__).parent.parent / "evidence"


class SessionContentMixin:
    """Mixin providing content and metadata methods.

    Expects host class to provide:
        self._call_mcp_tool(tool_name, **kwargs) -> Dict
        self.SESSION_PATTERN: re.Pattern
    """

    def get_session_detail(self, session_id: str) -> Dict[str, Any]:
        """Get full session details with parsed sections."""
        result = self._call_mcp_tool('governance_get_session', session_id=session_id)

        if 'error' in result:
            return {'session_id': session_id, 'error': result['error']}

        content = result.get('content', '')
        sections = _parse_sections(content)
        metadata = self.parse_session_id(session_id)

        return {
            'session_id': session_id,
            'content': content,
            'sections': sections,
            **metadata,
        }

    def get_session_metadata(self, session_id: str) -> Dict[str, Any]:
        """Get session metadata including file info."""
        metadata = self.parse_session_id(session_id)

        file_path = EVIDENCE_DIR / f"{session_id}.md"
        if file_path.exists():
            stat = file_path.stat()
            metadata['file_size'] = stat.st_size
            metadata['modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()

        return metadata

    def parse_session_id(self, session_id: str) -> Dict[str, str]:
        """Parse session ID to extract date, phase, topic."""
        match = self.SESSION_PATTERN.match(session_id)
        if not match:
            return {
                'session_id': session_id,
                'date': '',
                'phase': '',
                'topic': '',
            }

        year, month, day, phase, topic = match.groups()
        return {
            'session_id': session_id,
            'date': f"{year}-{month}-{day}",
            'phase': phase or '',
            'topic': topic or '',
        }

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Generate session summary with statistics."""
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


def _parse_sections(content: str) -> List[Dict[str, str]]:
    """Parse markdown content into sections."""
    sections: List[Dict[str, str]] = []
    current_section: Dict[str, Any] = {'title': 'Introduction', 'content': '', 'level': 0}

    for line in content.split('\n'):
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

    if current_section['content'].strip() or current_section['title'] != 'Introduction':
        sections.append(current_section)

    return sections
