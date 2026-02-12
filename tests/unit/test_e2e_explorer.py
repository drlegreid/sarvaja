"""
Unit tests for E2E Explorer - Exploratory Testing Framework.

Per DOC-SIZE-01-v1: Tests for agent/e2e_explorer.py module.
Tests: ActionType, ExplorationStep, ExplorationSession,
       RobotGenerator, ExplorationRunner.
"""

import pytest

from agent.e2e_explorer import (
    ActionType,
    ExplorationStep,
    ExplorationSession,
    RobotGenerator,
    ExplorationRunner,
)


# ── ActionType ────────────────────────────────────────────────


class TestActionType:
    def test_values(self):
        assert ActionType.NAVIGATE == "navigate"
        assert ActionType.CLICK == "click"
        assert ActionType.ASSERT_VISIBLE == "assert_visible"

    def test_is_string_enum(self):
        assert isinstance(ActionType.NAVIGATE, str)


# ── ExplorationStep ──────────────────────────────────────────


class TestExplorationStep:
    def test_defaults(self):
        step = ExplorationStep(action=ActionType.CLICK, target="#btn")
        assert step.success is True
        assert step.error is None
        assert step.value is None

    def test_to_robot_navigate(self):
        step = ExplorationStep(action=ActionType.NAVIGATE, target="http://localhost:7777")
        assert "Go To" in step.to_robot_keyword()
        assert "http://localhost:7777" in step.to_robot_keyword()

    def test_to_robot_click(self):
        step = ExplorationStep(action=ActionType.CLICK, target="#btn", description="Click button")
        keyword = step.to_robot_keyword()
        assert "Click" in keyword
        assert "#btn" in keyword

    def test_to_robot_type(self):
        step = ExplorationStep(action=ActionType.TYPE, target="input#name", value="test")
        assert "Fill Text" in step.to_robot_keyword()

    def test_to_robot_select(self):
        step = ExplorationStep(action=ActionType.SELECT, target="select#role", value="admin")
        assert "Select Options By" in step.to_robot_keyword()

    def test_to_robot_wait(self):
        step = ExplorationStep(action=ActionType.WAIT, target=".loading")
        assert "Wait For Elements State" in step.to_robot_keyword()

    def test_to_robot_assert_visible(self):
        step = ExplorationStep(action=ActionType.ASSERT_VISIBLE, target=".modal")
        assert "visible" in step.to_robot_keyword()

    def test_to_robot_assert_text(self):
        step = ExplorationStep(action=ActionType.ASSERT_TEXT, target="h1", value="Welcome")
        keyword = step.to_robot_keyword()
        assert "Get Text" in keyword
        assert "Welcome" in keyword

    def test_to_robot_assert_count(self):
        step = ExplorationStep(action=ActionType.ASSERT_COUNT, target="li.item", value="3")
        assert "Get Element Count" in step.to_robot_keyword()

    def test_to_robot_screenshot(self):
        step = ExplorationStep(action=ActionType.SCREENSHOT, target="screenshot.png")
        assert "Take Screenshot" in step.to_robot_keyword()

    def test_to_robot_snapshot(self):
        step = ExplorationStep(action=ActionType.SNAPSHOT, target="", description="page state")
        assert "Snapshot" in step.to_robot_keyword()


# ── ExplorationSession ───────────────────────────────────────


class TestExplorationSession:
    def test_create(self):
        session = ExplorationSession(name="Test", url="http://localhost:7777")
        assert session.name == "Test"
        assert len(session.steps) == 0
        assert session.completed_at is None

    def test_add_step(self):
        session = ExplorationSession(name="Test", url="/")
        step = ExplorationStep(action=ActionType.CLICK, target="#btn")
        session.add_step(step)
        assert len(session.steps) == 1

    def test_complete(self):
        session = ExplorationSession(name="Test", url="/")
        session.complete()
        assert session.completed_at is not None

    def test_to_robot_test(self):
        session = ExplorationSession(name="Smoke Test", url="/")
        session.add_step(ExplorationStep(action=ActionType.NAVIGATE, target="/ui"))
        session.add_step(ExplorationStep(action=ActionType.CLICK, target="#btn"))
        session.add_step(ExplorationStep(
            action=ActionType.CLICK, target="#fail", success=False, error="Not found",
        ))
        robot = session.to_robot_test()
        assert "Smoke Test" in robot
        assert "Go To" in robot
        assert "Click" in robot
        # Failed step should be excluded
        assert "#fail" not in robot

    def test_findings(self):
        session = ExplorationSession(name="Test", url="/")
        session.findings.append("Bug found")
        assert len(session.findings) == 1


# ── RobotGenerator ────────────────────────────────────────────


class TestRobotGenerator:
    def test_init(self):
        gen = RobotGenerator(base_url="http://localhost:8081")
        assert gen.base_url == "http://localhost:8081"
        assert len(gen.sessions) == 0

    def test_add_session(self):
        gen = RobotGenerator()
        session = ExplorationSession(name="Test", url="/")
        gen.add_session(session)
        assert len(gen.sessions) == 1

    def test_generate(self, tmp_path):
        gen = RobotGenerator(base_url="http://localhost:7777")
        session = ExplorationSession(name="Generated Test", url="/ui")
        session.add_step(ExplorationStep(action=ActionType.NAVIGATE, target="/ui"))
        gen.add_session(session)
        output = tmp_path / "test.robot"
        content = gen.generate(str(output))
        assert "Generated Test" in content
        assert "http://localhost:7777" in content
        assert output.exists()


# ── ExplorationRunner ─────────────────────────────────────────


class TestExplorationRunner:
    def test_init(self):
        runner = ExplorationRunner()
        assert runner.current_session is None

    def test_start_session(self):
        runner = ExplorationRunner()
        session = runner.start_session("Test")
        assert session.name == "Test"
        assert runner.current_session is session

    def test_start_session_custom_url(self):
        runner = ExplorationRunner(base_url="http://localhost:8081")
        session = runner.start_session("Test", url="/custom")
        assert session.url == "/custom"

    def test_record_step(self):
        runner = ExplorationRunner()
        runner.start_session("Test")
        step = runner.record_step(ActionType.CLICK, "#btn", description="Click")
        assert step.action == ActionType.CLICK
        assert len(runner.current_session.steps) == 1

    def test_record_step_no_session_raises(self):
        runner = ExplorationRunner()
        with pytest.raises(ValueError, match="No active session"):
            runner.record_step(ActionType.CLICK, "#btn")

    def test_end_session(self):
        runner = ExplorationRunner()
        runner.start_session("Test")
        runner.record_step(ActionType.NAVIGATE, "/")
        session = runner.end_session()
        assert session.completed_at is not None
        assert runner.current_session is None
        assert len(runner.generator.sessions) == 1

    def test_end_session_no_session_raises(self):
        runner = ExplorationRunner()
        with pytest.raises(ValueError, match="No active session"):
            runner.end_session()

    def test_generate_tests(self, tmp_path):
        runner = ExplorationRunner()
        runner.start_session("Gen Test")
        runner.record_step(ActionType.NAVIGATE, "/ui")
        runner.end_session()
        output = tmp_path / "generated.robot"
        content = runner.generate_tests(str(output))
        assert "Gen Test" in content

    def test_get_exploration_prompt_known(self):
        runner = ExplorationRunner()
        from agent.e2e_heuristics import EXPLORATION_HEURISTICS
        if EXPLORATION_HEURISTICS:
            key = list(EXPLORATION_HEURISTICS.keys())[0]
            prompt = runner.get_exploration_prompt(key)
            assert len(prompt) > 0

    def test_get_exploration_prompt_unknown(self):
        runner = ExplorationRunner()
        prompt = runner.get_exploration_prompt("nonexistent_heuristic")
        assert len(prompt) > 0  # returns system prompt as fallback
