"""
Rule Fallback Parser
====================
Parse rules from markdown files when TypeDB is unavailable.

Per GAP-MCP-004: Rule fallback to markdown files not implemented.
Per RULE-021: Fallback to markdown when services unavailable.

File Structure:
    docs/rules/RULES-GOVERNANCE.md   -> RULE-001, RULE-003, RULE-006, RULE-011, RULE-013
    docs/rules/RULES-TECHNICAL.md    -> RULE-002, RULE-007, RULE-008, RULE-009, RULE-010
    docs/rules/RULES-OPERATIONAL.md  -> RULE-004, RULE-005, RULE-012, RULE-014+
"""

import re
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class MarkdownRule:
    """Rule parsed from markdown file."""
    id: str
    name: str
    category: str
    priority: str
    status: str
    directive: str
    source_file: str


# Regex patterns for parsing markdown rules
RULE_HEADER_PATTERN = re.compile(r'^##\s+RULE-(\d+):\s+(.+)$', re.MULTILINE)
METADATA_PATTERN = re.compile(
    r'\*\*Category:\*\*\s*`?([^|`]+)`?\s*\|\s*'
    r'\*\*Priority:\*\*\s*(\w+)\s*\|\s*'
    r'\*\*Status:\*\*\s*(\w+)'
)
DIRECTIVE_PATTERN = re.compile(r'###\s+Directive\s*\n+(.+?)(?=\n###|\n---|\Z)', re.DOTALL)


def get_rules_directory() -> Path:
    """Get path to docs/rules/ directory."""
    # Try relative to governance package
    current = Path(__file__).parent.parent.parent
    rules_dir = current / "docs" / "rules"
    if rules_dir.exists():
        return rules_dir

    # Fallback: try from CWD
    cwd_rules = Path.cwd() / "docs" / "rules"
    if cwd_rules.exists():
        return cwd_rules

    return rules_dir  # Return expected path even if not found


def parse_markdown_rules(content: str, source_file: str) -> list[MarkdownRule]:
    """
    Parse rules from markdown content.

    Args:
        content: Markdown file content
        source_file: Source file name for tracking

    Returns:
        List of parsed MarkdownRule objects
    """
    rules = []

    # Find all rule headers
    headers = list(RULE_HEADER_PATTERN.finditer(content))

    for i, match in enumerate(headers):
        rule_id = f"RULE-{match.group(1).zfill(3)}"
        rule_name = match.group(2).strip()

        # Get content from this header to next header (or end)
        start = match.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(content)
        rule_content = content[start:end]

        # Parse metadata line
        metadata_match = METADATA_PATTERN.search(rule_content)
        if metadata_match:
            category = metadata_match.group(1).strip()
            priority = metadata_match.group(2).strip().upper()
            status = metadata_match.group(3).strip().upper()
        else:
            category = "unknown"
            priority = "MEDIUM"
            status = "ACTIVE"

        # Parse directive section
        directive_match = DIRECTIVE_PATTERN.search(rule_content)
        if directive_match:
            directive = directive_match.group(1).strip()
            # Clean up: remove markdown formatting, truncate if too long
            directive = re.sub(r'\n{3,}', '\n\n', directive)
            if len(directive) > 500:
                directive = directive[:500] + "..."
        else:
            directive = f"See {source_file} for full directive."

        rules.append(MarkdownRule(
            id=rule_id,
            name=rule_name,
            category=category,
            priority=priority,
            status=status,
            directive=directive,
            source_file=source_file
        ))

    return rules


def get_all_markdown_rules() -> list[MarkdownRule]:
    """
    Load all rules from markdown files in docs/rules/.

    Returns:
        List of all parsed rules
    """
    rules_dir = get_rules_directory()
    all_rules = []

    if not rules_dir.exists():
        return []

    for md_file in rules_dir.glob("RULES-*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            rules = parse_markdown_rules(content, md_file.name)
            all_rules.extend(rules)
        except Exception:
            continue  # Skip files that can't be parsed

    # Sort by rule ID
    all_rules.sort(key=lambda r: r.id)
    return all_rules


def get_markdown_rule_by_id(rule_id: str) -> Optional[MarkdownRule]:
    """
    Get a specific rule by ID from markdown files.

    Args:
        rule_id: Rule ID (e.g., "RULE-001")

    Returns:
        MarkdownRule if found, None otherwise
    """
    all_rules = get_all_markdown_rules()
    for rule in all_rules:
        if rule.id == rule_id:
            return rule
    return None


def filter_markdown_rules(
    rules: list[MarkdownRule],
    category: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None
) -> list[MarkdownRule]:
    """
    Filter rules by criteria.

    Pure function: same inputs -> same outputs.
    """
    result = rules

    if category:
        result = [r for r in result if r.category.lower() == category.lower()]
    if status:
        result = [r for r in result if r.status.upper() == status.upper()]
    if priority:
        result = [r for r in result if r.priority.upper() == priority.upper()]

    return result


def markdown_rule_to_dict(rule: MarkdownRule) -> dict:
    """Convert MarkdownRule to dictionary format matching TypeDB Rule."""
    return {
        "id": rule.id,
        "name": rule.name,
        "category": rule.category,
        "priority": rule.priority,
        "status": rule.status,
        "directive": rule.directive,
        "source": "markdown",  # Indicate this came from fallback
        "source_file": rule.source_file
    }
