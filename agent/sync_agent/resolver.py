"""
Sync Conflict Resolver.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: agent/sync_agent.py

Created: 2026-01-04
"""

from .models import Change


class ConflictResolver:
    """Resolves sync conflicts."""

    STRATEGIES = {
        "skills": "merge_latest",
        "sessions": "local_wins",
        "rules": "remote_wins",
        "memories": "merge_dedupe"
    }

    def resolve(self, local: Change, remote: Change) -> Change:
        """Resolve conflict between local and remote."""
        strategy = self.STRATEGIES.get(local.collection, "local_wins")

        if strategy == "merge_latest":
            return local if local.timestamp > remote.timestamp else remote
        elif strategy == "remote_wins":
            return remote
        else:  # local_wins, merge_dedupe
            return local


__all__ = ['ConflictResolver']
