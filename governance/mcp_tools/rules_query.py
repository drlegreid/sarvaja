"""
Rule Query MCP Tools
====================
Query operations for governance rules.

Per RULE-012: DSP Semantic Code Structure
Per RULE-032: File size <300 lines
Per GAP-MCP-004: Fallback to markdown when TypeDB unavailable

Extracted from rules.py per modularization plan.
Created: 2026-01-03
"""

import json
from typing import Optional
from dataclasses import asdict

from governance.mcp_tools.common import get_typedb_client
from governance.mcp_tools.rule_fallback import (
    get_all_markdown_rules,
    get_markdown_rule_by_id,
    filter_markdown_rules,
    markdown_rule_to_dict,
)


def register_rule_query_tools(mcp) -> None:
    """Register rule query MCP tools."""

    @mcp.tool()
    def governance_query_rules(
        category: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> str:
        """
        Query rules from the governance database.

        Args:
            category: Filter by category (governance, architecture, testing, etc.)
            status: Filter by status (ACTIVE, DRAFT, DEPRECATED)
            priority: Filter by priority (CRITICAL, HIGH, MEDIUM, LOW)

        Returns:
            JSON array of matching rules
        """
        client = get_typedb_client()
        use_fallback = False

        try:
            if not client.connect():
                use_fallback = True
            else:
                # Build query based on filters
                if status == "ACTIVE":
                    rules = client.get_active_rules()
                else:
                    rules = client.get_all_rules()

                # Apply additional filters (pure functions)
                if category:
                    rules = [r for r in rules if r.category == category]
                if priority:
                    rules = [r for r in rules if r.priority == priority]
                if status and status != "ACTIVE":
                    rules = [r for r in rules if r.status == status]

                return json.dumps([asdict(r) for r in rules], default=str, indent=2)

        except Exception:
            use_fallback = True

        finally:
            client.close()

        # Fallback to markdown files (GAP-MCP-004)
        if use_fallback:
            md_rules = get_all_markdown_rules()
            if not md_rules:
                return json.dumps({
                    "error": "TypeDB unavailable and no markdown rules found",
                    "hint": "Ensure docs/rules/*.md files exist"
                })

            filtered = filter_markdown_rules(md_rules, category, status, priority)
            result = [markdown_rule_to_dict(r) for r in filtered]
            return json.dumps({
                "rules": result,
                "source": "markdown_fallback",
                "warning": "TypeDB unavailable - using markdown fallback (read-only)"
            }, indent=2)

    @mcp.tool()
    def governance_query_rules_by_tags(
        tags: Optional[str] = None,
        agent_role: Optional[str] = None,
        priority: Optional[str] = None
    ) -> str:
        """
        Query rules by skill tags and agent role (RD-WORKSPACE Phase 3).

        Args:
            tags: Comma-separated skill tags to match (e.g., "research,analysis")
            agent_role: Agent role to filter by (RESEARCH, CODING, CURATOR, SYNC)
            priority: Filter by priority (CRITICAL, HIGH, MEDIUM, LOW)

        Returns:
            JSON array of matching rules with tags and applicable roles
        """
        client = get_typedb_client()

        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            # Get all active rules
            rules = client.get_active_rules()
            results = []

            # Parse requested tags
            requested_tags = set()
            if tags:
                requested_tags = {t.strip().lower() for t in tags.split(",")}

            for rule in rules:
                rule_dict = asdict(rule)

                # Get tags and roles from rule (may be None)
                rule_tags_str = getattr(rule, 'tags', '') or ''
                rule_roles_str = getattr(rule, 'applicable_roles', '') or ''

                rule_tags = {t.strip().lower() for t in rule_tags_str.split(",") if t.strip()}
                rule_roles = {r.strip().upper() for r in rule_roles_str.split(",") if r.strip()}

                # Filter by tags (if any match)
                if requested_tags and not requested_tags.intersection(rule_tags):
                    continue

                # Filter by agent role
                if agent_role and agent_role.upper() not in rule_roles:
                    # If no roles defined, include rule for all agents
                    if rule_roles:
                        continue

                # Filter by priority
                if priority and rule.priority != priority:
                    continue

                # Add parsed tags and roles to result
                rule_dict['tags'] = list(rule_tags) if rule_tags else []
                rule_dict['applicable_roles'] = list(rule_roles) if rule_roles else []
                results.append(rule_dict)

            return json.dumps({
                "rules": results,
                "count": len(results),
                "filter": {
                    "tags": tags,
                    "agent_role": agent_role,
                    "priority": priority
                }
            }, default=str, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)})

        finally:
            client.close()

    @mcp.tool()
    def governance_get_agent_wisdom(agent_role: str) -> str:
        """
        Get wisdom (filtered rules + skills) for an agent role (RD-WORKSPACE Phase 3).

        Composes rules and skills relevant to the specified agent role based on:
        - Role-specific tags (research, coding, governance, sync)
        - Priority filters (CRITICAL, HIGH for most roles)
        - Loaded skills from workspace directory

        Args:
            agent_role: Agent role (RESEARCH, CODING, CURATOR, SYNC)

        Returns:
            JSON with rules_count, skills_count, filtered rules, and skills
        """
        from pathlib import Path
        from governance.skill_composer import (
            compose_agent_wisdom,
            get_workspace_path
        )

        client = get_typedb_client()

        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            # Get all active rules
            rules = client.get_active_rules()
            rules_list = [asdict(r) for r in rules]

            # Get workspace path
            workspace_path = get_workspace_path(agent_role)

            # Compose wisdom
            wisdom = compose_agent_wisdom(
                agent_role=agent_role,
                all_rules=rules_list,
                workspace_path=workspace_path
            )

            return json.dumps(wisdom.to_dict(), default=str, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)})

        finally:
            client.close()

    @mcp.tool()
    def governance_get_rule(rule_id: str) -> str:
        """
        Get a specific rule by ID.

        Args:
            rule_id: The rule ID (e.g., "RULE-001")

        Returns:
            JSON object with rule details or error
        """
        client = get_typedb_client()
        use_fallback = False

        try:
            if not client.connect():
                use_fallback = True
            else:
                rule = client.get_rule_by_id(rule_id)
                if rule:
                    return json.dumps(asdict(rule), default=str, indent=2)
                else:
                    # Rule not in TypeDB, try markdown
                    use_fallback = True

        except Exception:
            use_fallback = True

        finally:
            client.close()

        # Fallback to markdown files (GAP-MCP-004)
        if use_fallback:
            md_rule = get_markdown_rule_by_id(rule_id)
            if md_rule:
                result = markdown_rule_to_dict(md_rule)
                result["warning"] = "TypeDB unavailable - using markdown fallback (read-only)"
                return json.dumps(result, indent=2)
            else:
                return json.dumps({"error": f"Rule {rule_id} not found in TypeDB or markdown"})

    @mcp.tool()
    def governance_get_dependencies(rule_id: str) -> str:
        """
        Get all dependencies for a rule (uses TypeDB inference for transitive deps).

        Args:
            rule_id: The rule ID to get dependencies for

        Returns:
            JSON array of dependency rule IDs
        """
        client = get_typedb_client()

        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            deps = client.get_rule_dependencies(rule_id)
            return json.dumps(deps, indent=2)

        finally:
            client.close()

    @mcp.tool()
    def governance_find_conflicts() -> str:
        """
        Find conflicting rules using TypeDB inference.

        Returns:
            JSON array of conflict pairs with explanations
        """
        client = get_typedb_client()

        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            conflicts = client.find_conflicts()
            return json.dumps(conflicts, indent=2)

        finally:
            client.close()
