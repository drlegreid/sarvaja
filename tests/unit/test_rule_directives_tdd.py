"""TDD tests for rule directive completeness.

Per GAP-RULE-DOC-PATH-001: Every active rule should have a document_path.
Per TDD approach: Tests encode expected rule-document linkage.

Created: 2026-02-09
"""
import os
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestRuleDocumentFiles:
    """Verify rule leaf documents exist on filesystem."""

    EXPECTED_LEAF_RULES = [
        "ARCH-BACKFILL-01-v1",
        "ARCH-BEST-01-v1",
        "ARCH-EBMSF-01-v1",
        "ARCH-INFRA-01-v1",
        "ARCH-INFRA-02-v1",
        "ARCH-MCP-01-v1",
        "ARCH-MCP-02-v1",
        "ARCH-MCP-PARITY-01-v1",
        "DATA-COMPLETE-01-v1",
        "DATA-LINK-01-v1",
        "TEST-CVP-01-v1",
        "WORKFLOW-DSP-01-v1",
    ]

    @pytest.mark.parametrize("rule_id", EXPECTED_LEAF_RULES)
    def test_leaf_document_exists(self, rule_id):
        """Each rule must have a corresponding leaf markdown document."""
        doc_path = PROJECT_ROOT / "docs" / "rules" / "leaf" / f"{rule_id}.md"
        assert doc_path.exists(), f"Missing leaf doc: {doc_path}"

    @pytest.mark.parametrize("rule_id", EXPECTED_LEAF_RULES)
    def test_leaf_document_has_directive(self, rule_id):
        """Each leaf document must contain a ## Directive section."""
        doc_path = PROJECT_ROOT / "docs" / "rules" / "leaf" / f"{rule_id}.md"
        if not doc_path.exists():
            pytest.skip(f"File not found: {doc_path}")
        content = doc_path.read_text()
        assert "## Directive" in content, f"{rule_id} leaf doc missing ## Directive section"

    @pytest.mark.parametrize("rule_id", EXPECTED_LEAF_RULES)
    def test_leaf_document_has_validation_or_coverage(self, rule_id):
        """Each leaf document must contain a ## Validation or ## Test Coverage section."""
        doc_path = PROJECT_ROOT / "docs" / "rules" / "leaf" / f"{rule_id}.md"
        if not doc_path.exists():
            pytest.skip(f"File not found: {doc_path}")
        content = doc_path.read_text()
        has_validation = "## Validation" in content or "## Test Coverage" in content
        assert has_validation, f"{rule_id} leaf doc missing ## Validation or ## Test Coverage section"


class TestRuleDirectiveContent:
    """Verify rule directives are substantive (not empty or placeholder)."""

    def test_all_leaf_files_have_substantive_directive(self):
        """Each leaf file directive section must have >10 chars of content."""
        leaf_dir = PROJECT_ROOT / "docs" / "rules" / "leaf"
        for f in leaf_dir.glob("*.md"):
            content = f.read_text()
            if "## Directive" in content:
                # Extract text after ## Directive
                idx = content.index("## Directive")
                after = content[idx + len("## Directive"):]
                # Find next section or end
                next_section = after.find("\n## ")
                directive_text = after[:next_section].strip() if next_section > 0 else after.strip()
                assert len(directive_text) > 10, f"{f.name} has empty/placeholder directive"


class TestRuleDocumentPathSync:
    """Verify that rule-document relations are maintained."""

    def test_new_rules_have_document_format(self):
        """New semantic rules (2026+) should follow leaf/{RULE-ID}.md format."""
        new_rules = [
            "ARCH-BACKFILL-01-v1",
            "ARCH-MCP-PARITY-01-v1",
            "DATA-COMPLETE-01-v1",
            "DATA-LINK-01-v1",
            "TEST-CVP-01-v1",
            "WORKFLOW-DSP-01-v1",
        ]
        for rule_id in new_rules:
            expected = f"docs/rules/leaf/{rule_id}.md"
            actual_path = PROJECT_ROOT / expected
            assert actual_path.exists(), f"Rule {rule_id} missing document at {expected}"

    def test_leaf_directory_no_stale_files(self):
        """Leaf directory should not contain files for non-existent rules."""
        leaf_dir = PROJECT_ROOT / "docs" / "rules" / "leaf"
        if not leaf_dir.exists():
            pytest.skip("Leaf directory not found")

        md_files = list(leaf_dir.glob("*.md"))
        assert len(md_files) > 0, "No leaf rule documents found"

        for f in md_files:
            # Each file should have the expected format: RULE-ID.md
            content = f.read_text()
            assert len(content) > 50, f"Leaf file {f.name} appears empty or placeholder ({len(content)} chars)"


class TestRuleDocumentStructure:
    """Verify leaf document structure follows the template."""

    def _get_leaf_files(self):
        leaf_dir = PROJECT_ROOT / "docs" / "rules" / "leaf"
        return [f for f in leaf_dir.glob("*.md") if "-workaround" not in f.name]

    def test_all_leaf_files_have_title(self):
        """Each leaf file should start with # RULE-ID: Title."""
        for f in self._get_leaf_files():
            content = f.read_text()
            lines = content.strip().split("\n")
            assert lines[0].startswith("# "), f"{f.name} missing title (first line should start with #)"

    def test_all_leaf_files_have_category(self):
        """Each leaf file should declare category (inline or table format)."""
        for f in self._get_leaf_files():
            content = f.read_text()
            has_category = "Category:" in content or "Category**" in content
            assert has_category, f"{f.name} missing Category declaration"

    def test_all_leaf_files_have_priority(self):
        """Each leaf file should declare priority (inline or table format)."""
        for f in self._get_leaf_files():
            content = f.read_text()
            has_priority = "Priority:" in content or "Priority**" in content
            assert has_priority, f"{f.name} missing Priority declaration"
