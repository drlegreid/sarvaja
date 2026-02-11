"""
Unit tests for Document Change Handler.

Per DOC-SIZE-01-v1: Tests for extracted file_watcher/handler.py module.
Tests: DocumentChangeHandler._should_process, categorization.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from governance.file_watcher.handler import DocumentChangeHandler
from governance.file_watcher.queue import FileEventQueue, FileEventType


class TestShouldProcess:
    """Tests for DocumentChangeHandler._should_process()."""

    @pytest.fixture
    def handler(self):
        queue = MagicMock(spec=FileEventQueue)
        return DocumentChangeHandler(queue=queue)

    def test_accepts_markdown(self, handler):
        assert handler._should_process("/project/docs/rules/R-01.md") is True

    def test_accepts_yaml(self, handler):
        assert handler._should_process("/project/config.yaml") is True

    def test_accepts_yml(self, handler):
        assert handler._should_process("/project/config.yml") is True

    def test_accepts_tql(self, handler):
        assert handler._should_process("/project/schema.tql") is True

    def test_rejects_python(self, handler):
        assert handler._should_process("/project/main.py") is False

    def test_rejects_json(self, handler):
        assert handler._should_process("/project/data.json") is False

    def test_rejects_git(self, handler):
        assert handler._should_process("/project/.git/HEAD") is False

    def test_rejects_venv(self, handler):
        assert handler._should_process("/project/.venv/lib/readme.md") is False

    def test_rejects_pycache(self, handler):
        assert handler._should_process("/project/__pycache__/notes.md") is False

    def test_rejects_pytest_cache(self, handler):
        assert handler._should_process("/project/.pytest_cache/readme.md") is False

    def test_rejects_claude(self, handler):
        assert handler._should_process("/project/.claude/settings.md") is False


class TestHandlerConstants:
    """Tests for handler configuration."""

    def test_watched_extensions(self):
        assert ".md" in DocumentChangeHandler.WATCHED_EXTENSIONS
        assert ".yaml" in DocumentChangeHandler.WATCHED_EXTENSIONS
        assert ".yml" in DocumentChangeHandler.WATCHED_EXTENSIONS
        assert ".tql" in DocumentChangeHandler.WATCHED_EXTENSIONS

    def test_ignored_patterns(self):
        assert ".git" in DocumentChangeHandler.IGNORED_PATTERNS
        assert ".venv" in DocumentChangeHandler.IGNORED_PATTERNS
        assert "__pycache__" in DocumentChangeHandler.IGNORED_PATTERNS
