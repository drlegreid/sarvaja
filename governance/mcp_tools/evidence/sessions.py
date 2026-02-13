"""
Session Evidence MCP Tools
==========================
Session listing and retrieval operations.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-008: Extracted from evidence.py

Tools:
- governance_list_sessions: List all session evidence files
- governance_get_session: Get full session evidence content

Created: 2024-12-28
"""

import glob
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

from governance.mcp_tools.common import format_mcp_result
from .common import EVIDENCE_DIR


def register_session_tools(mcp) -> None:
    """Register session-related MCP tools."""

    @mcp.tool()
    def governance_list_sessions(
        limit: int = 20,
        session_type: Optional[str] = None
    ) -> str:
        """
        List all session evidence files.

        Args:
            limit: Maximum number of sessions to return (default 20)
            session_type: Filter by session type (e.g., "PHASE", "DSP", "STRATEGIC")

        Returns:
            JSON array of sessions with ID, date, topic, and summary
        """
        sessions = []

        # Search evidence directory for session files
        pattern = EVIDENCE_DIR / "SESSION-*.md"
        for filepath in sorted(glob.glob(str(pattern)), reverse=True)[:limit]:
            try:
                path = Path(filepath)
                filename = path.name

                # Parse filename: SESSION-YYYY-MM-DD-TOPIC.md
                parts = filename.replace(".md", "").split("-")
                if len(parts) >= 4:
                    date_str = f"{parts[1]}-{parts[2]}-{parts[3]}"
                    topic = "-".join(parts[4:]) if len(parts) > 4 else "general"
                else:
                    date_str = "unknown"
                    topic = filename

                # Apply type filter
                if session_type and session_type.upper() not in topic.upper():
                    continue

                # Read first few lines for summary
                content = path.read_text(encoding="utf-8")
                lines = content.split("\n")
                summary = ""
                for line in lines[:10]:
                    if line.startswith("## Summary") or line.startswith("**Summary"):
                        idx = lines.index(line)
                        if idx + 1 < len(lines):
                            summary = lines[idx + 1].strip()
                        break

                sessions.append({
                    "session_id": filename.replace(".md", ""),
                    "date": date_str,
                    "topic": topic,
                    "summary": summary[:200] if summary else "No summary available",
                    "path": str(filepath)
                })

            except Exception as e:
                logger.debug(f"Failed to parse session file {filepath}: {e}")
                continue

        return format_mcp_result({
            "sessions": sessions,
            "count": len(sessions),
            "total_available": len(list(glob.glob(str(EVIDENCE_DIR / "SESSION-*.md"))))
        })

    @mcp.tool()
    def governance_get_session(session_id: str) -> str:
        """
        Get full session evidence content.

        Args:
            session_id: Session ID (e.g., "SESSION-2024-12-25-PHASE8")

        Returns:
            JSON object with session metadata and full markdown content
        """
        # Handle both with and without .md extension
        if not session_id.endswith(".md"):
            session_id = session_id + ".md"

        filepath = EVIDENCE_DIR / session_id

        if not filepath.exists():
            # Try without SESSION- prefix
            if not session_id.startswith("SESSION-"):
                filepath = EVIDENCE_DIR / f"SESSION-{session_id}"
            if not filepath.exists():
                return format_mcp_result({"error": f"Session not found: {session_id}"})

        try:
            content = filepath.read_text(encoding="utf-8")

            # Parse metadata from content
            lines = content.split("\n")
            metadata = {}
            for line in lines[:20]:
                if line.startswith("**Date:**"):
                    metadata["date"] = line.replace("**Date:**", "").strip()
                elif line.startswith("**Session ID:**"):
                    metadata["session_id"] = line.replace("**Session ID:**", "").strip()
                elif line.startswith("**Status:**"):
                    metadata["status"] = line.replace("**Status:**", "").strip()

            return format_mcp_result({
                "session_id": session_id.replace(".md", ""),
                "path": str(filepath),
                "metadata": metadata,
                "content": content,
                "lines": len(lines)
            })

        except Exception as e:
            return format_mcp_result({"error": f"Failed to read session: {str(e)}"})
