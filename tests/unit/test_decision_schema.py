"""
Tests for decision log pros/cons/options schema.

Per PLAN-UI-OVERHAUL-001 Task 4.2: Decision Log Redesign.
TDD: Tests written before implementation.
"""

import pytest
import inspect


class TestDecisionOptionsSchema:
    """Verify decision model supports options with pros/cons."""

    def test_decision_create_has_options_field(self):
        """DecisionCreate model should accept options list."""
        from governance.models import DecisionCreate
        fields = DecisionCreate.model_fields
        assert 'options' in fields, (
            "DecisionCreate should have 'options' field for decision alternatives"
        )

    def test_decision_response_has_options_field(self):
        """DecisionResponse model should include options list."""
        from governance.models import DecisionResponse
        fields = DecisionResponse.model_fields
        assert 'options' in fields, (
            "DecisionResponse should have 'options' field"
        )

    def test_decision_response_has_selected_option(self):
        """DecisionResponse should have selected_option field."""
        from governance.models import DecisionResponse
        fields = DecisionResponse.model_fields
        assert 'selected_option' in fields, (
            "DecisionResponse should have 'selected_option' field"
        )

    def test_decision_form_has_options_input(self):
        """Decision form UI should have options input area."""
        from agent.governance_ui.views.decisions import form
        source = inspect.getsource(form)
        assert 'options' in source.lower(), (
            "Decision form should have options input"
        )

    def test_decision_detail_shows_options(self):
        """Decision detail view should display options."""
        from agent.governance_ui.views.decisions import content
        source = inspect.getsource(content)
        assert 'option' in source.lower(), (
            "Decision detail/content should show options"
        )
