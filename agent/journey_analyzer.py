"""
Journey Pattern Analyzer (P9.7)

Detects recurring questions and knowledge gaps in governance queries.

Per RULE-012: DSP Semantic Code Structure
Per FP + Digital Twin Paradigm
Per DOC-SIZE-01-v1: Pattern detection in journey_patterns.py.

Features:
- Question Journal: Log all governor questions with timestamps
- Recurrence Detection: Flag questions asked 2+ times within N days
- Anomaly Alerts: "You've asked this 3 times - creating a dashboard widget"
- Knowledge Gap Report: Which questions keep recurring?
"""

import hashlib
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .journey_patterns import JourneyPatternsMixin  # noqa: F401 — re-export hub

# Re-export for backward compatibility
from .journey_patterns import JourneyPatternsMixin as _Mixin  # noqa: F401


class JourneyAnalyzer(JourneyPatternsMixin):
    """
    Analyzes question patterns to detect recurring queries and knowledge gaps.

    Inherits pattern detection, UI suggestions, and knowledge gap methods
    from JourneyPatternsMixin.

    Attributes:
        questions: List of logged questions
        recurrence_threshold: Number of times a question must recur to trigger alert
        time_window_days: Default time window for recurrence detection
    """

    def __init__(
        self,
        recurrence_threshold: int = 3,
        time_window_days: int = 7
    ):
        self.questions: List[Dict[str, Any]] = []
        self.recurrence_threshold = recurrence_threshold
        self.time_window_days = time_window_days
        self._question_counter = 0

    def _generate_question_id(self) -> str:
        """Generate unique question ID."""
        self._question_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return f"Q-{timestamp}-{self._question_counter:04d}"

    def _normalize_question(self, question: str) -> str:
        """Normalize question for comparison."""
        normalized = question.lower().strip()
        normalized = re.sub(r'[?!.]+$', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized

    def _compute_semantic_hash(self, question: str) -> str:
        """Compute a semantic hash for question similarity."""
        normalized = self._normalize_question(question)
        stop_words = {'how', 'what', 'is', 'are', 'the', 'a', 'an', 'do', 'does',
                      'i', 'we', 'you', 'for', 'to', 'in', 'on', 'of', 'and', 'or'}
        words = [w for w in normalized.split() if w not in stop_words and len(w) > 2]
        words.sort()
        key_string = ' '.join(words)
        return hashlib.md5(key_string.encode()).hexdigest()[:12]

    def _count_recurrences(self, question: str, days: Optional[int] = None) -> int:
        """Count how many times a similar question was asked."""
        normalized = self._normalize_question(question)
        semantic_hash = self._compute_semantic_hash(question)
        count = 0

        cutoff = None
        if days:
            cutoff = datetime.now() - timedelta(days=days)

        for q in self.questions:
            if cutoff:
                q_time = datetime.fromisoformat(q['timestamp'])
                if q_time < cutoff:
                    continue
            if (self._normalize_question(q['question']) == normalized or
                    q.get('semantic_hash') == semantic_hash):
                count += 1

        return count

    def log_question(
        self,
        question: str,
        source: str,
        category: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        answered: bool = True
    ) -> Dict[str, Any]:
        """Log a question with metadata."""
        question_id = self._generate_question_id()
        timestamp = datetime.now().isoformat()
        semantic_hash = self._compute_semantic_hash(question)

        recurrence_count = self._count_recurrences(question, self.time_window_days)

        record = {
            'question_id': question_id,
            'question': question,
            'source': source,
            'category': category,
            'context': context or {},
            'timestamp': timestamp,
            'semantic_hash': semantic_hash,
            'answered': answered,
            'recurrence_count': recurrence_count + 1,
        }

        if recurrence_count + 1 >= self.recurrence_threshold:
            record['alert'] = {
                'type': 'recurring_question',
                'message': f"Question asked {recurrence_count + 1} times",
                'suggestion': self._generate_suggestion(question, recurrence_count + 1),
                'action': 'consider_dashboard_widget'
            }

        self.questions.append(record)
        return record

    def _generate_suggestion(self, question: str, count: int) -> str:
        """Generate actionable suggestion for recurring question."""
        normalized = self._normalize_question(question)

        if 'agent' in normalized or 'trust' in normalized:
            return "Consider adding this to the Trust Dashboard quick links"
        elif 'rule' in normalized or 'governance' in normalized:
            return "Consider adding a governance FAQ widget"
        elif 'session' in normalized or 'evidence' in normalized:
            return "Consider adding session search shortcuts"
        elif 'monitor' in normalized or 'alert' in normalized:
            return "Consider adding monitoring summary widget"
        else:
            return f"This question was asked {count} times - consider creating a dedicated view"

    def get_question_history(
        self,
        limit: int = 50,
        source: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get question history with optional filters."""
        filtered = self.questions.copy()

        if source:
            filtered = [q for q in filtered if q['source'] == source]

        if category:
            filtered = [q for q in filtered if q.get('category') == category]

        filtered.sort(key=lambda x: x['timestamp'], reverse=True)
        return filtered[:limit]

    def clear_history(self) -> None:
        """Clear all question history."""
        self.questions.clear()
        self._question_counter = 0


def create_journey_analyzer(
    recurrence_threshold: int = 3,
    time_window_days: int = 7
) -> JourneyAnalyzer:
    """Factory function to create JourneyAnalyzer instance."""
    return JourneyAnalyzer(
        recurrence_threshold=recurrence_threshold,
        time_window_days=time_window_days
    )
