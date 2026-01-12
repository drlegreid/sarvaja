"""
Batch Routing Mixin
Created: 2024-12-25 (P7.3)
Modularized: 2026-01-02 (RULE-032)

Handles batch routing and auto-detection.
"""
import re
from typing import Dict, Any, List


class BatchRoutingMixin:
    """Mixin for batch and auto routing operations."""

    # ID patterns for auto-detection
    RULE_PATTERN = re.compile(r'^RULE-\d{3}$')
    DECISION_PATTERN = re.compile(r'^DECISION-\d{3}$')
    SESSION_PATTERN = re.compile(r'^SESSION-\d{4}-\d{2}-\d{2}')

    def route_auto(
        self,
        identifier: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Auto-detect type and route accordingly.

        Args:
            identifier: ID string (RULE-*, DECISION-*, SESSION-*)
            data: Data dict

        Returns:
            RouteResult with detected type
        """
        if self.RULE_PATTERN.match(identifier):
            result = self.route_rule(rule_id=identifier, **data)
            result['type'] = 'rule'
            return result

        elif self.DECISION_PATTERN.match(identifier):
            result = self.route_decision(decision_id=identifier, **data)
            result['type'] = 'decision'
            return result

        elif self.SESSION_PATTERN.match(identifier):
            result = self.route_session(session_id=identifier, **data)
            result['type'] = 'session'
            return result

        else:
            return {
                'success': False,
                'type': 'unknown',
                'error': f'Could not detect type for: {identifier}'
            }

    def route_batch(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Route multiple items in batch.

        Args:
            items: List of items with 'type' field

        Returns:
            Batch result with counts
        """
        succeeded = 0
        failed = 0
        results = []

        for item in items:
            item_type = item.pop('type', None)

            try:
                if item_type == 'rule':
                    result = self.route_rule(**item)
                elif item_type == 'decision':
                    result = self.route_decision(**item)
                elif item_type == 'session':
                    result = self.route_session(**item)
                else:
                    result = {'success': False, 'error': f'Unknown type: {item_type}'}

                if result.get('success'):
                    succeeded += 1
                else:
                    failed += 1

                results.append(result)

            except Exception as e:
                failed += 1
                results.append({'success': False, 'error': str(e)})

        return {
            'total': len(items),
            'succeeded': succeeded,
            'failed': failed,
            'results': results
        }
