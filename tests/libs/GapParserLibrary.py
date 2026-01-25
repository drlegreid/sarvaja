"""
RF-004: Robot Framework Library for Gap Parser.

Wraps governance/utils/gap_parser.py for Robot Framework tests.
Per TEST-TAXON-01-v1: Unit test migration support.
"""

import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class GapParserLibrary:
    """Robot Framework library for Gap Parser functions."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def create_gap(self, gap_id: str, description: str, priority: str, category: str, is_resolved: bool = False) -> Dict:
        """Create a Gap object and return as dict."""
        from governance.utils.gap_parser import Gap
        gap = Gap(gap_id, description, priority, category, is_resolved=is_resolved)
        return gap.to_dict()

    def get_gap_priority_order(self, priority: str) -> int:
        """Get priority order for a given priority level."""
        from governance.utils.gap_parser import Gap
        gap = Gap("temp", "temp", priority, "temp")
        return gap.priority_order

    def gap_to_todo_format(self, gap_id: str, description: str, priority: str, category: str) -> str:
        """Convert gap to todo format string."""
        from governance.utils.gap_parser import Gap
        gap = Gap(gap_id, description, priority, category)
        return gap.to_todo_format()

    def create_temp_gap_file(self, content: str) -> str:
        """Create a temporary file with gap content and return path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            return f.name

    def parse_gaps_from_file(self, file_path: str) -> List[str]:
        """Parse gaps from file and return list of gap IDs."""
        from governance.utils.gap_parser import GapParser
        parser = GapParser(Path(file_path))
        gaps = parser.get_open_gaps()
        return [g.id for g in gaps]

    def delete_temp_file(self, file_path: str):
        """Delete temporary file."""
        Path(file_path).unlink(missing_ok=True)
