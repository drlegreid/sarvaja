"""DSP Fix #2: Deprecated task_type error message tests.

Verifies that deprecated types produce helpful error messages
pointing users to the canonical replacement.
"""
import pytest
from pydantic import ValidationError

from governance.models.task import TaskCreate, TaskUpdate


class TestDeprecatedTypeErrorMessage:
    """Deprecated types produce helpful 'use X instead' error messages."""

    def test_gap_suggests_bug(self):
        with pytest.raises(ValidationError, match="'gap' is deprecated.*Use 'bug'"):
            TaskCreate(description="Test", phase="P10", task_type="gap")

    def test_story_suggests_feature(self):
        with pytest.raises(ValidationError, match="'story' is deprecated.*Use 'feature'"):
            TaskCreate(description="Test", phase="P10", task_type="story")

    def test_specification_suggests_spec(self):
        with pytest.raises(ValidationError, match="'specification' is deprecated.*Use 'spec'"):
            TaskCreate(description="Test", phase="P10", task_type="specification")

    def test_epic_suggests_feature(self):
        with pytest.raises(ValidationError, match="'epic' is deprecated.*Use 'feature'"):
            TaskCreate(description="Test", phase="P10", task_type="epic")

    def test_unknown_type_no_suggestion(self):
        with pytest.raises(ValidationError, match="Invalid task_type 'banana'"):
            TaskCreate(description="Test", phase="P10", task_type="banana")

    def test_canonical_types_accepted(self):
        for t in ["bug", "feature", "chore", "research", "spec", "test"]:
            tc = TaskCreate(description=f"Test {t}", phase="P10", task_type=t)
            assert tc.task_type == t

    def test_none_accepted(self):
        tc = TaskCreate(description="Test", phase="P10")
        assert tc.task_type is None


class TestDeprecatedTypeErrorMessageUpdate:
    """Same validation on TaskUpdate."""

    def test_gap_suggests_bug_on_update(self):
        with pytest.raises(ValidationError, match="'gap' is deprecated.*Use 'bug'"):
            TaskUpdate(task_type="gap")

    def test_canonical_accepted_on_update(self):
        for t in ["bug", "feature", "chore", "research", "spec", "test"]:
            tu = TaskUpdate(task_type=t)
            assert tu.task_type == t
