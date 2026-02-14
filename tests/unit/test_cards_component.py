"""
Tests for card components.

Per RULE-019: UI/UX Standards - consistent card patterns.
Batch 165: New coverage for components/cards.py (0->8 tests).
"""
import inspect

import pytest


class TestCardComponents:
    def test_build_entity_card_callable(self):
        from agent.governance_ui.components.cards import build_entity_card
        assert callable(build_entity_card)

    def test_build_stat_card_callable(self):
        from agent.governance_ui.components.cards import build_stat_card
        assert callable(build_stat_card)

    def test_build_detail_field_callable(self):
        from agent.governance_ui.components.cards import build_detail_field
        assert callable(build_detail_field)


class TestEntityCardSignature:
    def test_accepts_title_only(self):
        from agent.governance_ui.components.cards import build_entity_card
        sig = inspect.signature(build_entity_card)
        params = list(sig.parameters.keys())
        assert "title" in params

    def test_has_optional_subtitle(self):
        from agent.governance_ui.components.cards import build_entity_card
        sig = inspect.signature(build_entity_card)
        assert sig.parameters["subtitle"].default is None

    def test_has_optional_icon(self):
        from agent.governance_ui.components.cards import build_entity_card
        sig = inspect.signature(build_entity_card)
        assert sig.parameters["icon"].default is None

    def test_has_optional_actions(self):
        from agent.governance_ui.components.cards import build_entity_card
        sig = inspect.signature(build_entity_card)
        assert sig.parameters["actions"].default is None


class TestStatCardSignature:
    def test_has_required_params(self):
        from agent.governance_ui.components.cards import build_stat_card
        sig = inspect.signature(build_stat_card)
        params = list(sig.parameters.keys())
        assert "icon" in params
        assert "value" in params
        assert "label" in params
        assert "color" in params
