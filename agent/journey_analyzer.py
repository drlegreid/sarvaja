"""
Journey Pattern Analyzer (P9.7)

Detects recurring questions and knowledge gaps in governance queries.

Per RULE-012: DSP Semantic Code Structure
Per FP + Digital Twin Paradigm

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
from collections import defaultdict


class JourneyAnalyzer:
    """
    Analyzes question patterns to detect recurring queries and knowledge gaps.

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
        """
        Initialize JourneyAnalyzer.

        Args:
            recurrence_threshold: Number of recurrences to trigger alert
            time_window_days: Default time window for pattern detection
        """
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
        """
        Normalize question for comparison.

        Args:
            question: Raw question text

        Returns:
            Normalized question (lowercase, stripped, normalized whitespace)
        """
        # Lowercase and strip
        normalized = question.lower().strip()
        # Remove punctuation at end
        normalized = re.sub(r'[?!.]+$', '', normalized)
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized

    def _compute_semantic_hash(self, question: str) -> str:
        """
        Compute a semantic hash for question similarity.

        Args:
            question: Question text

        Returns:
            Semantic hash (simplified - words sorted and hashed)
        """
        normalized = self._normalize_question(question)
        # Extract key words (remove stop words)
        stop_words = {'how', 'what', 'is', 'are', 'the', 'a', 'an', 'do', 'does',
                      'i', 'we', 'you', 'for', 'to', 'in', 'on', 'of', 'and', 'or'}
        words = [w for w in normalized.split() if w not in stop_words and len(w) > 2]
        words.sort()
        key_string = ' '.join(words)
        return hashlib.md5(key_string.encode()).hexdigest()[:12]

    def _count_recurrences(self, question: str, days: Optional[int] = None) -> int:
        """
        Count how many times a similar question was asked.

        Args:
            question: Question to check
            days: Time window in days (None = all time)

        Returns:
            Number of similar questions
        """
        normalized = self._normalize_question(question)
        semantic_hash = self._compute_semantic_hash(question)
        count = 0

        cutoff = None
        if days:
            cutoff = datetime.now() - timedelta(days=days)

        for q in self.questions:
            # Check time window
            if cutoff:
                q_time = datetime.fromisoformat(q['timestamp'])
                if q_time < cutoff:
                    continue

            # Check exact match or semantic match
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
        """
        Log a question with metadata.

        Args:
            question: Question text
            source: Source of question (user, agent, etc.)
            category: Optional category tag
            context: Optional context dictionary
            answered: Whether the question was answered

        Returns:
            Question record with ID, timestamp, and recurrence info
        """
        question_id = self._generate_question_id()
        timestamp = datetime.now().isoformat()
        semantic_hash = self._compute_semantic_hash(question)

        # Count recurrences before adding this one
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
            'recurrence_count': recurrence_count + 1,  # Including this one
        }

        # Generate alert if threshold exceeded
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
        """
        Generate actionable suggestion for recurring question.

        Args:
            question: The recurring question
            count: Number of times asked

        Returns:
            Suggestion text
        """
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

    def get_recurring_questions(
        self,
        min_count: int = 2,
        days: Optional[int] = None,
        semantic_match: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get questions that recur frequently.

        Args:
            min_count: Minimum occurrences to be considered recurring
            days: Time window in days (None = use default)
            semantic_match: Whether to use semantic matching

        Returns:
            List of recurring questions with counts
        """
        days = days or self.time_window_days
        cutoff = datetime.now() - timedelta(days=days)

        # Group by normalized question or semantic hash
        groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for q in self.questions:
            q_time = datetime.fromisoformat(q['timestamp'])
            if q_time < cutoff:
                continue

            if semantic_match:
                key = q.get('semantic_hash', self._normalize_question(q['question']))
            else:
                key = self._normalize_question(q['question'])

            groups[key].append(q)

        # Filter by min_count and format results
        recurring = []
        for key, questions in groups.items():
            if len(questions) >= min_count:
                # Use first question as representative
                representative = questions[0]
                recurring.append({
                    'question': representative['question'],
                    'count': len(questions),
                    'sources': list(set(q['source'] for q in questions)),
                    'first_asked': min(q['timestamp'] for q in questions),
                    'last_asked': max(q['timestamp'] for q in questions),
                    'semantic_hash': representative.get('semantic_hash'),
                })

        # Sort by count descending
        recurring.sort(key=lambda x: x['count'], reverse=True)
        return recurring

    def detect_patterns(self) -> List[Dict[str, Any]]:
        """
        Detect patterns in question history.

        Returns:
            List of detected patterns with topics and suggestions
        """
        patterns = []

        # Group by semantic hash
        hash_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for q in self.questions:
            hash_groups[q.get('semantic_hash', '')].append(q)

        # Identify significant patterns
        for hash_key, questions in hash_groups.items():
            if len(questions) >= 2:
                # Extract topic from questions
                topic = self._extract_topic(questions)
                pattern = {
                    'topic': topic,
                    'cluster': hash_key,
                    'question_count': len(questions),
                    'questions': [q['question'] for q in questions[:3]],  # Sample
                    'suggestion': self._generate_ui_suggestion(topic, len(questions)),
                    'ui_recommendation': self._get_ui_recommendation(topic),
                }
                patterns.append(pattern)

        # Sort by question count
        patterns.sort(key=lambda x: x['question_count'], reverse=True)
        return patterns

    def _extract_topic(self, questions: List[Dict[str, Any]]) -> str:
        """Extract common topic from questions."""
        # Simple: use category if available, else extract keywords
        categories = [q.get('category') for q in questions if q.get('category')]
        if categories:
            return max(set(categories), key=categories.count)

        # Extract common words
        all_words = []
        stop_words = {'how', 'what', 'is', 'are', 'the', 'a', 'an', 'do', 'does',
                      'i', 'we', 'you', 'for', 'to', 'in', 'on', 'of', 'and', 'or'}
        for q in questions:
            words = self._normalize_question(q['question']).split()
            all_words.extend([w for w in words if w not in stop_words and len(w) > 2])

        if all_words:
            return max(set(all_words), key=all_words.count)
        return "general"

    def _generate_ui_suggestion(self, topic: str, count: int) -> str:
        """Generate UI improvement suggestion."""
        if count >= 5:
            return f"Create dedicated '{topic}' dashboard widget"
        elif count >= 3:
            return f"Add '{topic}' to quick access menu"
        else:
            return f"Consider FAQ entry for '{topic}'"

    def _get_ui_recommendation(self, topic: str) -> Dict[str, Any]:
        """Get specific UI component recommendation."""
        recommendations = {
            'trust': {'component': 'TrustQuickView', 'location': 'sidebar'},
            'agent': {'component': 'AgentStatusWidget', 'location': 'dashboard'},
            'rule': {'component': 'RuleSearchWidget', 'location': 'header'},
            'session': {'component': 'SessionTimeline', 'location': 'main'},
            'monitor': {'component': 'AlertSummary', 'location': 'header'},
        }

        for key, rec in recommendations.items():
            if key in topic.lower():
                return rec

        return {'component': 'InfoWidget', 'location': 'sidebar'}

    def get_knowledge_gaps(self) -> List[Dict[str, Any]]:
        """
        Identify knowledge gaps from unanswered or recurring questions.

        Returns:
            List of knowledge gaps with frequency and topics
        """
        gaps = []

        # Find unanswered questions
        unanswered = [q for q in self.questions if not q.get('answered', True)]

        # Group by semantic hash
        hash_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for q in unanswered:
            hash_groups[q.get('semantic_hash', '')].append(q)

        for hash_key, questions in hash_groups.items():
            if questions:
                gap = {
                    'topic': self._extract_topic(questions),
                    'question_pattern': questions[0]['question'],
                    'count': len(questions),
                    'frequency': len(questions),
                    'sources': list(set(q['source'] for q in questions)),
                    'priority': 'high' if len(questions) >= 3 else 'medium',
                }
                gaps.append(gap)

        # Sort by count (frequency)
        gaps.sort(key=lambda x: x['count'], reverse=True)
        return gaps

    def get_question_history(
        self,
        limit: int = 50,
        source: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get question history with optional filters.

        Args:
            limit: Maximum questions to return
            source: Filter by source
            category: Filter by category

        Returns:
            List of questions (newest first)
        """
        filtered = self.questions.copy()

        if source:
            filtered = [q for q in filtered if q['source'] == source]

        if category:
            filtered = [q for q in filtered if q.get('category') == category]

        # Sort by timestamp descending (newest first)
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
    """
    Factory function to create JourneyAnalyzer instance.

    Args:
        recurrence_threshold: Number of recurrences to trigger alert
        time_window_days: Default time window for pattern detection

    Returns:
        Configured JourneyAnalyzer instance
    """
    return JourneyAnalyzer(
        recurrence_threshold=recurrence_threshold,
        time_window_days=time_window_days
    )
