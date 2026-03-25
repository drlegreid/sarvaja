"""Unit tests for task_comments service — EPIC-ISSUE-EVIDENCE P19.

Tests CRUD operations for resolution comments.
"""

import pytest
from unittest.mock import patch

from governance.services.task_comments import (
    add_comment,
    list_comments,
    delete_comment,
    get_comment,
    _comments_store,
)

_SVC = "governance.services.task_comments"


@pytest.fixture(autouse=True)
def _clean_store():
    """Reset the in-memory store between tests."""
    _comments_store.clear()
    yield
    _comments_store.clear()


# ---------------------------------------------------------------------------
# add_comment
# ---------------------------------------------------------------------------

class TestAddComment:

    def test_creates_comment(self):
        """Successfully creates a comment with generated ID."""
        result = add_comment("TASK-001", body="Fix applied")
        assert result["comment_id"].startswith("CMT-")
        assert result["task_id"] == "TASK-001"
        assert result["body"] == "Fix applied"
        assert result["author"] == "code-agent"
        assert result["created_at"]

    def test_custom_author(self):
        """Accepts custom author."""
        result = add_comment("TASK-001", body="LGTM", author="reviewer")
        assert result["author"] == "reviewer"

    def test_empty_body_raises(self):
        """Empty body raises ValueError."""
        with pytest.raises(ValueError, match="body is required"):
            add_comment("TASK-001", body="")

    def test_whitespace_body_raises(self):
        """Whitespace-only body raises ValueError."""
        with pytest.raises(ValueError, match="body is required"):
            add_comment("TASK-001", body="   ")

    def test_empty_task_id_raises(self):
        """Empty task_id raises ValueError."""
        with pytest.raises(ValueError, match="task_id is required"):
            add_comment("", body="test")

    def test_body_truncated_at_5000(self):
        """Body longer than 5000 chars is truncated."""
        result = add_comment("TASK-001", body="x" * 6000)
        assert len(result["body"]) == 5000

    def test_body_stripped(self):
        """Body is stripped of leading/trailing whitespace."""
        result = add_comment("TASK-001", body="  hello  ")
        assert result["body"] == "hello"


# ---------------------------------------------------------------------------
# list_comments
# ---------------------------------------------------------------------------

class TestListComments:

    def test_empty_list(self):
        """Returns empty list for task with no comments."""
        result = list_comments("TASK-NONE")
        assert result == []

    def test_returns_all_comments(self):
        """Returns all comments in chronological order."""
        add_comment("TASK-001", body="First")
        add_comment("TASK-001", body="Second")
        add_comment("TASK-001", body="Third")
        result = list_comments("TASK-001")
        assert len(result) == 3
        assert result[0]["body"] == "First"
        assert result[2]["body"] == "Third"

    def test_isolated_per_task(self):
        """Comments for one task don't appear in another."""
        add_comment("TASK-A", body="A comment")
        add_comment("TASK-B", body="B comment")
        assert len(list_comments("TASK-A")) == 1
        assert len(list_comments("TASK-B")) == 1


# ---------------------------------------------------------------------------
# delete_comment
# ---------------------------------------------------------------------------

class TestDeleteComment:

    def test_deletes_existing(self):
        """Successfully deletes an existing comment."""
        c = add_comment("TASK-001", body="To delete")
        assert delete_comment("TASK-001", c["comment_id"]) is True
        assert len(list_comments("TASK-001")) == 0

    def test_not_found_returns_false(self):
        """Returns False for non-existent comment."""
        assert delete_comment("TASK-001", "CMT-nonexist") is False

    def test_wrong_task_returns_false(self):
        """Returns False when comment_id exists on different task."""
        c = add_comment("TASK-A", body="A comment")
        assert delete_comment("TASK-B", c["comment_id"]) is False


# ---------------------------------------------------------------------------
# get_comment
# ---------------------------------------------------------------------------

class TestGetComment:

    def test_returns_existing(self):
        """Returns comment dict for existing ID."""
        c = add_comment("TASK-001", body="Find me")
        result = get_comment("TASK-001", c["comment_id"])
        assert result is not None
        assert result["body"] == "Find me"

    def test_returns_none_for_missing(self):
        """Returns None for non-existent comment."""
        assert get_comment("TASK-001", "CMT-missing") is None
