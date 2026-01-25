"""
RF-004: Robot Framework Library for Frankel Hash Module

This library wraps governance/frankel_hash.py for use in Robot Framework tests.
Per TEST-TAXON-01-v1: Unit test migration support.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class FrankelHashLibrary:
    """Robot Framework library for Frankel Hash functions."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def import_frankel_hash(self) -> bool:
        """Verify frankel_hash module is importable."""
        try:
            from governance.frankel_hash import compute_hash
            return True
        except ImportError:
            return False

    def compute_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content."""
        from governance.frankel_hash import compute_hash
        return compute_hash(content)

    def compute_chunk_hashes(self, content: str, level: int = 1) -> List[Dict]:
        """Compute chunk hashes at specified level."""
        from governance.frankel_hash import compute_chunk_hashes
        return compute_chunk_hashes(content, level)

    def build_merkle_tree(self, hashes: List[str]) -> Dict[str, Any]:
        """Build Merkle tree from list of hashes."""
        from governance.frankel_hash import build_merkle_tree
        return build_merkle_tree(hashes)

    def render_merkle_tree(self, tree: Dict[str, Any], show_full: bool = False) -> str:
        """Render Merkle tree as ASCII art."""
        from governance.frankel_hash import render_merkle_tree
        return render_merkle_tree(tree, show_full)

    def zoom_view(self, content: str, level: int = 0) -> str:
        """Generate zoom view at specified level."""
        from governance.frankel_hash import zoom_view
        return zoom_view(content, level)

    def has_changed(self, old_hash: str, new_hash: str) -> bool:
        """Check if content has changed based on hash comparison."""
        from governance.frankel_hash import has_changed
        return has_changed(old_hash, new_hash)

    def compute_short_hash(self, content: str, length: int = 8) -> str:
        """Compute shortened hash for display."""
        from governance.frankel_hash import compute_short_hash
        return compute_short_hash(content, length)
