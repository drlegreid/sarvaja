"""
Journey Pattern Detection & Knowledge Gaps (Mixin).

Per DOC-SIZE-01-v1: Extracted from journey_analyzer.py (419 lines).
Pattern detection, UI suggestions, and knowledge gap analysis.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class JourneyPatternsMixin:
    """Mixin providing pattern detection and knowledge gap methods.

    Expects host class to provide:
        self.questions: List[Dict[str, Any]]
        self.time_window_days: int
        self._normalize_question(question) -> str
        self._compute_semantic_hash(question) -> str
    """

    def get_recurring_questions(
        self,
        min_count: int = 2,
        days: Optional[int] = None,
        semantic_match: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get questions that recur frequently."""
        days = days or self.time_window_days
        cutoff = datetime.now() - timedelta(days=days)

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

        recurring = []
        for key, questions in groups.items():
            if len(questions) >= min_count:
                representative = questions[0]
                recurring.append({
                    'question': representative['question'],
                    'count': len(questions),
                    'sources': list(set(q['source'] for q in questions)),
                    'first_asked': min(q['timestamp'] for q in questions),
                    'last_asked': max(q['timestamp'] for q in questions),
                    'semantic_hash': representative.get('semantic_hash'),
                })

        recurring.sort(key=lambda x: x['count'], reverse=True)
        return recurring

    def detect_patterns(self) -> List[Dict[str, Any]]:
        """Detect patterns in question history."""
        patterns = []

        hash_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for q in self.questions:
            hash_groups[q.get('semantic_hash', '')].append(q)

        for hash_key, questions in hash_groups.items():
            if len(questions) >= 2:
                topic = self._extract_topic(questions)
                pattern = {
                    'topic': topic,
                    'cluster': hash_key,
                    'question_count': len(questions),
                    'questions': [q['question'] for q in questions[:3]],
                    'suggestion': self._generate_ui_suggestion(topic, len(questions)),
                    'ui_recommendation': self._get_ui_recommendation(topic),
                }
                patterns.append(pattern)

        patterns.sort(key=lambda x: x['question_count'], reverse=True)
        return patterns

    def _extract_topic(self, questions: List[Dict[str, Any]]) -> str:
        """Extract common topic from questions."""
        categories = [q.get('category') for q in questions if q.get('category')]
        if categories:
            return max(set(categories), key=categories.count)

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
        """Identify knowledge gaps from unanswered or recurring questions."""
        gaps = []

        unanswered = [q for q in self.questions if not q.get('answered', True)]

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

        gaps.sort(key=lambda x: x['count'], reverse=True)
        return gaps
