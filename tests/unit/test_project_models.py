"""
Unit tests for Project-related Pydantic models.

Per GOV-PROJECT-01-v1: Project hierarchy models.
"""

import pytest
from governance.models import (
    ProjectCreate,
    ProjectResponse,
    PlanCreate,
    PlanResponse,
    EpicCreate,
    EpicResponse,
    PaginatedProjectResponse,
    PaginationMeta,
)


class TestProjectCreate:
    """Tests for ProjectCreate model."""

    def test_minimal_create(self):
        p = ProjectCreate(name="Test")
        assert p.name == "Test"
        assert p.project_id is None
        assert p.path is None

    def test_full_create(self):
        p = ProjectCreate(
            project_id="PROJ-1", name="Full", path="/tmp/project",
        )
        assert p.project_id == "PROJ-1"
        assert p.path == "/tmp/project"


class TestProjectResponse:
    """Tests for ProjectResponse model."""

    def test_defaults(self):
        p = ProjectResponse(project_id="PROJ-1", name="Test")
        assert p.plan_count == 0
        assert p.session_count == 0
        assert p.path is None

    def test_with_counts(self):
        p = ProjectResponse(
            project_id="PROJ-1", name="Test",
            plan_count=3, session_count=10, path="/home",
        )
        assert p.plan_count == 3
        assert p.session_count == 10


class TestPlanCreate:
    """Tests for PlanCreate model."""

    def test_minimal(self):
        p = PlanCreate(name="Plan A", project_id="PROJ-1")
        assert p.name == "Plan A"
        assert p.project_id == "PROJ-1"
        assert p.plan_id is None

    def test_with_description(self):
        p = PlanCreate(
            plan_id="PLAN-1", name="Plan A",
            project_id="PROJ-1", description="A description",
        )
        assert p.description == "A description"


class TestPlanResponse:
    """Tests for PlanResponse model."""

    def test_defaults(self):
        p = PlanResponse(plan_id="PLAN-1", name="Plan A", project_id="PROJ-1")
        assert p.epic_count == 0
        assert p.description is None


class TestEpicCreate:
    """Tests for EpicCreate model."""

    def test_minimal(self):
        e = EpicCreate(name="Epic A", plan_id="PLAN-1")
        assert e.name == "Epic A"
        assert e.plan_id == "PLAN-1"

    def test_with_all_fields(self):
        e = EpicCreate(
            epic_id="EPIC-1", name="Epic A",
            plan_id="PLAN-1", description="Epic desc",
        )
        assert e.epic_id == "EPIC-1"


class TestEpicResponse:
    """Tests for EpicResponse model."""

    def test_defaults(self):
        e = EpicResponse(epic_id="EPIC-1", name="Epic A", plan_id="PLAN-1")
        assert e.task_count == 0
        assert e.description is None


class TestPaginatedProjectResponse:
    """Tests for PaginatedProjectResponse model."""

    def test_empty(self):
        p = PaginatedProjectResponse(
            items=[],
            pagination=PaginationMeta(
                total=0, offset=0, limit=50, has_more=False, returned=0,
            ),
        )
        assert len(p.items) == 0
        assert p.pagination.total == 0

    def test_with_items(self):
        items = [
            ProjectResponse(project_id="PROJ-1", name="A"),
            ProjectResponse(project_id="PROJ-2", name="B"),
        ]
        p = PaginatedProjectResponse(
            items=items,
            pagination=PaginationMeta(
                total=2, offset=0, limit=50, has_more=False, returned=2,
            ),
        )
        assert len(p.items) == 2
        assert p.pagination.returned == 2
