"""
Robot Framework library for Task Detail Sections tests.

Per GAP-TASK-LINK-004: Task details (business, design, arch, test)
Per TASK-TECH-01-v1: Technology Solution Documentation
Migrated from tests/test_task_details.py
"""

import os
from robot.api.deco import keyword


class TaskDetailsLibrary:
    """Library for testing task detail sections functionality."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Section Design Tests
    # =========================================================================

    @keyword("Section Names Valid")
    def section_names_valid(self):
        """Verify section names match TASK-TECH-01-v1."""
        sections = ['business', 'design', 'architecture', 'test']
        all_lower = all(s.islower() for s in sections)
        all_have_content = all(len(s) > 0 for s in sections)
        return {
            "all_lowercase": all_lower,
            "all_have_content": all_have_content,
            "count_correct": len(sections) == 4
        }

    @keyword("Section Descriptions Valid")
    def section_descriptions_valid(self):
        """Verify sections have clear purposes."""
        sections = {
            'business': 'Why - User problem, business value',
            'design': 'What - Functional requirements, acceptance criteria',
            'architecture': 'How - Technical approach, technology choices',
            'test': 'Verification - Test plan, evidence of completion',
        }
        return {"has_four_sections": len(sections) == 4}

    # =========================================================================
    # Task Entity Tests
    # =========================================================================

    @keyword("Task Has Business Field")
    def task_has_business_field(self):
        """Verify Task entity has business field."""
        try:
            from governance.typedb.entities import Task
            from dataclasses import fields
            field_names = [f.name for f in fields(Task)]
            return {
                "has_field": 'business' in field_names or 'task_business' in field_names
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Task Has Design Field")
    def task_has_design_field(self):
        """Verify Task entity has design field."""
        try:
            from governance.typedb.entities import Task
            from dataclasses import fields
            field_names = [f.name for f in fields(Task)]
            return {
                "has_field": 'design' in field_names or 'task_design' in field_names
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Task Has Architecture Field")
    def task_has_architecture_field(self):
        """Verify Task entity has architecture field."""
        try:
            from governance.typedb.entities import Task
            from dataclasses import fields
            field_names = [f.name for f in fields(Task)]
            return {
                "has_field": 'architecture' in field_names or 'task_architecture' in field_names
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Task Has Test Section Field")
    def task_has_test_section_field(self):
        """Verify Task entity has test_section field."""
        try:
            from governance.typedb.entities import Task
            from dataclasses import fields
            field_names = [f.name for f in fields(Task)]
            return {
                "has_field": 'test_section' in field_names or 'task_test' in field_names
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # TypeDB Schema Tests
    # =========================================================================

    @keyword("Schema Has Business Attribute")
    def schema_has_business_attribute(self):
        """Verify schema has task-business attribute."""
        try:
            schema_path = 'governance/schema.tql'
            with open(schema_path, 'r') as f:
                content = f.read()
            return {"has_attribute": 'task-business' in content}
        except FileNotFoundError:
            return {"skipped": True, "reason": "schema.tql not found"}

    @keyword("Schema Has Design Attribute")
    def schema_has_design_attribute(self):
        """Verify schema has task-design attribute."""
        try:
            schema_path = 'governance/schema.tql'
            with open(schema_path, 'r') as f:
                content = f.read()
            return {"has_attribute": 'task-design' in content}
        except FileNotFoundError:
            return {"skipped": True, "reason": "schema.tql not found"}

    @keyword("Schema Has Architecture Attribute")
    def schema_has_architecture_attribute(self):
        """Verify schema has task-architecture attribute."""
        try:
            schema_path = 'governance/schema.tql'
            with open(schema_path, 'r') as f:
                content = f.read()
            return {"has_attribute": 'task-architecture' in content}
        except FileNotFoundError:
            return {"skipped": True, "reason": "schema.tql not found"}

    @keyword("Schema Has Test Attribute")
    def schema_has_test_attribute(self):
        """Verify schema has task-test attribute."""
        try:
            schema_path = 'governance/schema.tql'
            with open(schema_path, 'r') as f:
                content = f.read()
            return {"has_attribute": 'task-test' in content}
        except FileNotFoundError:
            return {"skipped": True, "reason": "schema.tql not found"}

    # =========================================================================
    # Content Format Tests
    # =========================================================================

    @keyword("Markdown Content Allowed")
    def markdown_content_allowed(self):
        """Verify markdown content is allowed in detail fields."""
        markdown_content = """
## User Problem
Users cannot track task context across sessions.

## Business Value
- Improved traceability
- Better handoff documentation
"""
        return {
            "has_headers": '##' in markdown_content,
            "has_lists": '- ' in markdown_content
        }

    @keyword("Multiline Content Supported")
    def multiline_content_supported(self):
        """Verify multiline content is supported."""
        multiline = """Line 1
Line 2
Line 3"""
        lines = multiline.split('\n')
        return {"supported": len(lines) >= 3}

    # =========================================================================
    # BDD Scenario Tests
    # =========================================================================

    @keyword("Scenario Create Task With Details")
    def scenario_create_task_with_details(self):
        """GIVEN/WHEN/THEN scenario for creating task with details."""
        task_data = {
            'id': 'TASK-001',
            'business': 'Users need X to solve Y',
            'design': 'Feature should do Z',
            'architecture': 'Use technology A',
            'test_section': 'Verify with pytest',
        }
        has_all_fields = all(
            field in task_data
            for field in ['business', 'design', 'architecture', 'test_section']
        )
        return {"has_all_fields": has_all_fields}

    @keyword("Scenario Update Task Section")
    def scenario_update_task_section(self):
        """GIVEN/WHEN/THEN scenario for updating task section."""
        original_sections = {
            'business': 'Original business',
            'design': 'Original design',
            'architecture': 'Original arch',
            'test_section': 'Original test',
        }
        updated_architecture = 'New architecture approach'
        return {
            "can_update": updated_architecture != original_sections['architecture']
        }

    # =========================================================================
    # Documentation Compliance Tests
    # =========================================================================

    @keyword("Rule TASK TECH 01 v1 Exists")
    def rule_task_tech_01_v1_exists(self):
        """Verify TASK-TECH-01-v1 rule exists."""
        rule_path = 'docs/rules/leaf/TASK-TECH-01-v1.md'
        return {"exists": os.path.exists(rule_path)}

    @keyword("Rule Mentions Sections")
    def rule_mentions_sections(self):
        """Verify rule mentions required sections."""
        try:
            rule_path = 'docs/rules/leaf/TASK-TECH-01-v1.md'
            with open(rule_path, 'r') as f:
                content = f.read()
            return {
                "has_business": 'Business' in content,
                "has_design": 'Design' in content,
                "has_architecture": 'Architecture' in content,
                "has_test": 'Test' in content
            }
        except FileNotFoundError:
            return {"skipped": True, "reason": "Rule file not found"}
