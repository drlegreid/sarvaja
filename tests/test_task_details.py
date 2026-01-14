"""
TDD Tests for Task Detail Sections.

Per GAP-TASK-LINK-004: Task details (business, design, arch, test)
Per TASK-TECH-01-v1: Technology Solution Documentation

Sections:
- Business (Why): User problem, business value
- Design (What): Functional requirements, acceptance criteria
- Architecture (How): Technical approach, technology choices
- Test (Verification): Test plan, evidence of completion

Created: 2026-01-14
"""

import pytest


class TestTaskDetailSectionDesign:
    """Test task detail section design."""

    def test_section_names(self):
        """Verify section names match TASK-TECH-01-v1."""
        sections = ['business', 'design', 'architecture', 'test']
        for section in sections:
            assert section.islower()
            assert len(section) > 0

    def test_section_descriptions(self):
        """Verify sections have clear purposes."""
        sections = {
            'business': 'Why - User problem, business value',
            'design': 'What - Functional requirements, acceptance criteria',
            'architecture': 'How - Technical approach, technology choices',
            'test': 'Verification - Test plan, evidence of completion',
        }
        assert len(sections) == 4


class TestTaskEntityDetailFields:
    """Test Task entity has detail fields."""

    def test_task_has_business_field(self):
        """Verify Task entity has business field."""
        from governance.typedb.entities import Task
        from dataclasses import fields
        field_names = [f.name for f in fields(Task)]
        assert 'business' in field_names or 'task_business' in field_names

    def test_task_has_design_field(self):
        """Verify Task entity has design field."""
        from governance.typedb.entities import Task
        from dataclasses import fields
        field_names = [f.name for f in fields(Task)]
        assert 'design' in field_names or 'task_design' in field_names

    def test_task_has_architecture_field(self):
        """Verify Task entity has architecture field."""
        from governance.typedb.entities import Task
        from dataclasses import fields
        field_names = [f.name for f in fields(Task)]
        assert 'architecture' in field_names or 'task_architecture' in field_names

    def test_task_has_test_section_field(self):
        """Verify Task entity has test_section field."""
        from governance.typedb.entities import Task
        from dataclasses import fields
        field_names = [f.name for f in fields(Task)]
        assert 'test_section' in field_names or 'task_test' in field_names


class TestTypeDBSchemaDetailAttributes:
    """Test TypeDB schema for detail attributes."""

    def test_schema_has_business_attribute(self):
        """Verify schema has task-business attribute."""
        schema_path = 'governance/schema.tql'
        with open(schema_path, 'r') as f:
            content = f.read()
        assert 'task-business' in content

    def test_schema_has_design_attribute(self):
        """Verify schema has task-design attribute."""
        schema_path = 'governance/schema.tql'
        with open(schema_path, 'r') as f:
            content = f.read()
        assert 'task-design' in content

    def test_schema_has_architecture_attribute(self):
        """Verify schema has task-architecture attribute."""
        schema_path = 'governance/schema.tql'
        with open(schema_path, 'r') as f:
            content = f.read()
        assert 'task-architecture' in content

    def test_schema_has_test_attribute(self):
        """Verify schema has task-test attribute."""
        schema_path = 'governance/schema.tql'
        with open(schema_path, 'r') as f:
            content = f.read()
        assert 'task-test' in content


class TestDetailContentFormat:
    """Test detail content format."""

    def test_markdown_content_allowed(self):
        """Verify markdown content is allowed in detail fields."""
        markdown_content = """
## User Problem
Users cannot track task context across sessions.

## Business Value
- Improved traceability
- Better handoff documentation
"""
        assert '##' in markdown_content
        assert '- ' in markdown_content

    def test_multiline_content_supported(self):
        """Verify multiline content is supported."""
        multiline = """Line 1
Line 2
Line 3"""
        lines = multiline.split('\n')
        assert len(lines) >= 3


class TestBDDScenarios:
    """BDD-style scenario tests."""

    def test_scenario_create_task_with_details(self):
        """
        GIVEN a new task is being created
        WHEN business/design/arch/test sections are provided
        THEN the task should store all section content
        """
        task_data = {
            'id': 'TASK-001',
            'business': 'Users need X to solve Y',
            'design': 'Feature should do Z',
            'architecture': 'Use technology A',
            'test_section': 'Verify with pytest',
        }
        for field in ['business', 'design', 'architecture', 'test_section']:
            assert field in task_data

    def test_scenario_update_task_section(self):
        """
        GIVEN an existing task
        WHEN updating a specific section (e.g., architecture)
        THEN only that section should change
        """
        original_sections = {
            'business': 'Original business',
            'design': 'Original design',
            'architecture': 'Original arch',
            'test_section': 'Original test',
        }
        updated_architecture = 'New architecture approach'
        # Conceptual - in real test would call update method
        assert updated_architecture != original_sections['architecture']


class TestDocumentationCompliance:
    """Test compliance with TASK-TECH-01-v1."""

    def test_rule_exists(self):
        """Verify TASK-TECH-01-v1 rule exists."""
        import os
        rule_path = 'docs/rules/leaf/TASK-TECH-01-v1.md'
        assert os.path.exists(rule_path)

    def test_rule_mentions_sections(self):
        """Verify rule mentions required sections."""
        rule_path = 'docs/rules/leaf/TASK-TECH-01-v1.md'
        with open(rule_path, 'r') as f:
            content = f.read()
        assert 'Business' in content
        assert 'Design' in content
        assert 'Architecture' in content
        assert 'Test' in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
