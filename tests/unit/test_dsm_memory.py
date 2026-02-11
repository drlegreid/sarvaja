"""
Unit tests for DSM Session Memory Integration.

Per DOC-SIZE-01-v1: Tests for extracted dsm/memory.py module.
Tests: get_session_memory_payload.
"""

import pytest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from governance.dsm.memory import get_session_memory_payload
from governance.dsm.models import DSMCycle, PhaseCheckpoint


class TestGetSessionMemoryPayload:
    """Tests for get_session_memory_payload()."""

    def test_none_cycle_returns_none(self):
        assert get_session_memory_payload(None) is None

    def test_import_error_returns_none(self):
        cycle = DSMCycle(cycle_id="DSM-001", current_phase="measure")
        with patch.dict("sys.modules", {"governance.session_memory": None}):
            result = get_session_memory_payload(cycle)
            assert result is None

    @patch("governance.session_memory.create_dsp_session_context")
    def test_returns_payload(self, mock_create):
        mock_ctx = MagicMock()
        mock_ctx.to_document.return_value = "cycle summary doc"
        mock_ctx.to_metadata.return_value = {"cycle_id": "DSM-001"}
        mock_create.return_value = mock_ctx

        cycle = DSMCycle(
            cycle_id="DSM-001",
            batch_id="B-01",
            current_phase="measure",
            phases_completed=["init"],
            findings=["found X"],
            checkpoints=[],
            metrics={"score": 0.8},
        )

        result = get_session_memory_payload(cycle)
        assert result is not None
        assert result["collection_name"] == "claude_memories"
        assert result["ids"] == ["sim-ai-dsp-DSM-001"]
        assert result["documents"] == ["cycle summary doc"]

    @patch("governance.session_memory.create_dsp_session_context")
    def test_exception_returns_none(self, mock_create):
        mock_create.side_effect = Exception("serialization error")
        cycle = DSMCycle(cycle_id="DSM-002", current_phase="init")
        result = get_session_memory_payload(cycle)
        assert result is None

    @patch("governance.session_memory.create_dsp_session_context")
    def test_passes_cycle_data_correctly(self, mock_create):
        mock_ctx = MagicMock()
        mock_ctx.to_document.return_value = ""
        mock_ctx.to_metadata.return_value = {}
        mock_create.return_value = mock_ctx

        cp = PhaseCheckpoint(
            phase="init",
            timestamp="2026-02-11T10:00:00",
            description="completed init phase",
        )
        cycle = DSMCycle(
            cycle_id="DSM-003",
            batch_id="B-03",
            current_phase="optimize",
            phases_completed=["init", "hypothesize"],
            findings=["f1", "f2"],
            checkpoints=[cp],
            metrics={"m1": 1},
        )

        get_session_memory_payload(cycle)
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["cycle_id"] == "DSM-003"
        assert call_kwargs["batch_id"] == "B-03"
        assert call_kwargs["phases_completed"] == ["init", "hypothesize"]
        assert call_kwargs["findings"] == ["f1", "f2"]
