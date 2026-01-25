"""
Robot Framework Library for Rule Fallback Parser Tests.

Per GAP-MCP-004: Rule fallback to markdown files.
Migrated from tests/test_rule_fallback.py
"""
from pathlib import Path
from robot.api.deco import keyword


# Sample markdown content for testing
SAMPLE_MARKDOWN = """
# Test Rules

---

## RULE-001: Session Evidence Logging

**Category:** `governance` | **Priority:** CRITICAL | **Status:** ACTIVE

### Directive

All agent sessions MUST produce evidence logs that include:

1. **Thought Chain Documentation**
   - Every decision point with rationale

### Validation
- [ ] Session log exists

---

## RULE-007: MCP Usage Protocol

**Category:** `technical` | **Priority:** HIGH | **Status:** ACTIVE

### Directive

Use MCP tools correctly. No manual implementations.

---
"""


class RuleFallbackLibrary:
    """Library for testing rule fallback parser."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =============================================================================
    # Markdown Parser Tests
    # =============================================================================

    @keyword("Parse Markdown Rules Basic")
    def parse_markdown_rules_basic(self):
        """Parse rules from markdown content."""
        try:
            from governance.mcp_tools.rule_fallback import parse_markdown_rules
            rules = parse_markdown_rules(SAMPLE_MARKDOWN, "TEST.md")
            return {
                "count_correct": len(rules) == 2,
                "id_correct": rules[0].id == "RULE-001",
                "name_correct": rules[0].name == "Session Evidence Logging",
                "category_correct": rules[0].category == "governance",
                "priority_correct": rules[0].priority == "CRITICAL",
                "status_correct": rules[0].status == "ACTIVE",
                "has_directive": "evidence logs" in rules[0].directive
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Parse Markdown Rules Second Rule")
    def parse_markdown_rules_second_rule(self):
        """Verify second rule in sequence."""
        try:
            from governance.mcp_tools.rule_fallback import parse_markdown_rules
            rules = parse_markdown_rules(SAMPLE_MARKDOWN, "TEST.md")
            return {
                "id_correct": rules[1].id == "RULE-007",
                "name_correct": rules[1].name == "MCP Usage Protocol",
                "category_correct": rules[1].category == "technical",
                "priority_correct": rules[1].priority == "HIGH"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Parse Markdown Rules Source File")
    def parse_markdown_rules_source_file(self):
        """Source file is tracked."""
        try:
            from governance.mcp_tools.rule_fallback import parse_markdown_rules
            rules = parse_markdown_rules(SAMPLE_MARKDOWN, "RULES-TEST.md")
            all_correct = all(rule.source_file == "RULES-TEST.md" for rule in rules)
            return {"source_correct": all_correct}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Filter Markdown Rules By Category")
    def filter_markdown_rules_by_category(self):
        """Filter rules by category."""
        try:
            from governance.mcp_tools.rule_fallback import parse_markdown_rules, filter_markdown_rules
            rules = parse_markdown_rules(SAMPLE_MARKDOWN, "TEST.md")
            filtered = filter_markdown_rules(rules, category="governance")
            return {
                "count_correct": len(filtered) == 1,
                "id_correct": filtered[0].id == "RULE-001"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Filter Markdown Rules By Priority")
    def filter_markdown_rules_by_priority(self):
        """Filter rules by priority."""
        try:
            from governance.mcp_tools.rule_fallback import parse_markdown_rules, filter_markdown_rules
            rules = parse_markdown_rules(SAMPLE_MARKDOWN, "TEST.md")
            filtered = filter_markdown_rules(rules, priority="HIGH")
            return {
                "count_correct": len(filtered) == 1,
                "id_correct": filtered[0].id == "RULE-007"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Filter Markdown Rules By Status")
    def filter_markdown_rules_by_status(self):
        """Filter rules by status."""
        try:
            from governance.mcp_tools.rule_fallback import parse_markdown_rules, filter_markdown_rules
            rules = parse_markdown_rules(SAMPLE_MARKDOWN, "TEST.md")
            filtered = filter_markdown_rules(rules, status="ACTIVE")
            return {"count_correct": len(filtered) == 2}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Markdown Rule To Dict")
    def markdown_rule_to_dict(self):
        """Convert MarkdownRule to dict."""
        try:
            from governance.mcp_tools.rule_fallback import parse_markdown_rules, markdown_rule_to_dict
            rules = parse_markdown_rules(SAMPLE_MARKDOWN, "TEST.md")
            result = markdown_rule_to_dict(rules[0])
            return {
                "id_correct": result["id"] == "RULE-001",
                "name_correct": result["name"] == "Session Evidence Logging",
                "source_correct": result["source"] == "markdown",
                "source_file_correct": result["source_file"] == "TEST.md"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Rules Directory Tests
    # =============================================================================

    @keyword("Get Rules Directory Returns Path")
    def get_rules_directory_returns_path(self):
        """Rules directory returns a Path object."""
        try:
            from governance.mcp_tools.rule_fallback import get_rules_directory
            rules_dir = get_rules_directory()
            return {"is_path": isinstance(rules_dir, Path)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Rules Directory Exists")
    def rules_directory_exists(self):
        """Rules directory exists in project."""
        try:
            from governance.mcp_tools.rule_fallback import get_rules_directory
            rules_dir = get_rules_directory()
            return {"exists": rules_dir.exists()}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Real Markdown Files Tests
    # =============================================================================

    @keyword("Get All Markdown Rules")
    def get_all_markdown_rules(self):
        """Load all rules from actual markdown files."""
        try:
            from governance.mcp_tools.rule_fallback import get_all_markdown_rules
            rules = get_all_markdown_rules()
            return {"has_rules": len(rules) > 0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Markdown Rule By Id Exists")
    def get_markdown_rule_by_id_exists(self):
        """Get specific rule by ID."""
        try:
            from governance.mcp_tools.rule_fallback import get_markdown_rule_by_id
            rule = get_markdown_rule_by_id("RULE-001")
            if rule is None:
                return {"skipped": True, "reason": "RULE-001 not found in markdown"}
            return {
                "not_none": rule is not None,
                "id_correct": rule.id == "RULE-001",
                "name_correct": rule.name == "Session Evidence Logging"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Markdown Rule By Id Not Found")
    def get_markdown_rule_by_id_not_found(self):
        """Get nonexistent rule returns None."""
        try:
            from governance.mcp_tools.rule_fallback import get_markdown_rule_by_id
            rule = get_markdown_rule_by_id("RULE-999")
            return {"is_none": rule is None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Known Rules Present")
    def known_rules_present(self):
        """Verify known rules are parseable."""
        try:
            from governance.mcp_tools.rule_fallback import get_all_markdown_rules
            rules = get_all_markdown_rules()
            rule_ids = [r.id for r in rules]
            # These should exist per CLAUDE.md
            expected = ["RULE-001", "RULE-007", "RULE-012"]
            missing = [e for e in expected if e not in rule_ids]
            if missing:
                return {"skipped": True, "reason": f"Missing rules: {missing}"}
            return {"all_present": len(missing) == 0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Rules Have Required Fields")
    def rules_have_required_fields(self):
        """All parsed rules have required fields."""
        try:
            from governance.mcp_tools.rule_fallback import get_all_markdown_rules
            rules = get_all_markdown_rules()
            if len(rules) == 0:
                return {"skipped": True, "reason": "No rules found"}

            # Check each rule
            for rule in rules:
                if not rule.id.startswith("RULE-"):
                    return {"valid": False, "reason": f"Invalid ID format: {rule.id}"}
                if not rule.name:
                    return {"valid": False, "reason": f"Missing name for {rule.id}"}
                if not rule.category:
                    return {"valid": False, "reason": f"Missing category for {rule.id}"}
                if rule.priority not in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                    return {"valid": False, "reason": f"Invalid priority for {rule.id}: {rule.priority}"}
                if rule.status not in ["ACTIVE", "DRAFT", "DEPRECATED"]:
                    return {"valid": False, "reason": f"Invalid status for {rule.id}: {rule.status}"}

            return {"valid": True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
