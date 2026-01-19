"""Rule Query MCP Tools. Per RULE-012, GAP-MCP-004. Created: 2026-01-03."""

import json
from typing import Optional
from dataclasses import asdict

from governance.mcp_tools.common import get_typedb_client, format_mcp_result
from governance.mcp_tools.rule_fallback import (
    get_all_markdown_rules,
    get_markdown_rule_by_id,
    filter_markdown_rules,
    markdown_rule_to_dict,
)


def register_rule_query_tools(mcp) -> None:
    """Register rule query MCP tools."""

    @mcp.tool()
    def rules_query(category: Optional[str] = None, status: Optional[str] = None,
                    priority: Optional[str] = None) -> str:
        """Query rules from TypeDB with optional filters.

        Args:
            category: Filter by rule category
            status: Filter by status (e.g., ACTIVE)
            priority: Filter by priority level

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
                return format_mcp_result([asdict(r) for r in rules])
        except Exception:
            use_fallback = True
        finally:
            client.close()

        if use_fallback:
            md_rules = get_all_markdown_rules()
            if not md_rules:
                return format_mcp_result({
                    "error": "TypeDB unavailable and no markdown rules found",
                    "hint": "Ensure docs/rules/*.md files exist"
                })

            filtered = filter_markdown_rules(md_rules, category, status, priority)
            result = [markdown_rule_to_dict(r) for r in filtered]
            return format_mcp_result({
                "rules": result,
                "source": "markdown_fallback",
                "warning": "TypeDB unavailable - using markdown fallback (read-only)"
            })

    @mcp.tool()
    def rules_query_by_tags(tags: Optional[str] = None, agent_role: Optional[str] = None,
                            priority: Optional[str] = None) -> str:
        """Query rules by tags, agent role, or priority.

        Args:
            tags: Comma-separated tags to filter by
            agent_role: Filter by applicable agent role
            priority: Filter by priority level

        Returns:
            JSON object with matching rules and filter info
        """
        client = get_typedb_client()

        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})
            rules = client.get_active_rules()
            results = []
            requested_tags = {t.strip().lower() for t in tags.split(",")} if tags else set()

            for rule in rules:
                rule_dict = asdict(rule)
                rule_tags_str = getattr(rule, 'tags', '') or ''
                rule_roles_str = getattr(rule, 'applicable_roles', '') or ''
                rule_tags = {t.strip().lower() for t in rule_tags_str.split(",") if t.strip()}
                rule_roles = {r.strip().upper() for r in rule_roles_str.split(",") if r.strip()}
                if requested_tags and not requested_tags.intersection(rule_tags):
                    continue
                if agent_role and agent_role.upper() not in rule_roles and rule_roles:
                    continue
                if priority and rule.priority != priority:
                    continue
                rule_dict['tags'] = list(rule_tags) if rule_tags else []
                rule_dict['applicable_roles'] = list(rule_roles) if rule_roles else []
                results.append(rule_dict)

            return format_mcp_result({
                "rules": results,
                "count": len(results),
                "filter": {
                    "tags": tags,
                    "agent_role": agent_role,
                    "priority": priority
                }
            })

        except Exception as e:
            return format_mcp_result({"error": str(e)})

        finally:
            client.close()

    @mcp.tool()
    def wisdom_get(agent_role: str) -> str:
        """Get compiled wisdom for an agent role.

        Composes relevant rules and workspace context for the specified agent.

        Args:
            agent_role: Agent role identifier (e.g., PLATFORM, QUALITY)

        Returns:
            JSON object with agent wisdom including applicable rules
        """
        from governance.skill_composer import (
            compose_agent_wisdom,
            get_workspace_path
        )

        client = get_typedb_client()

        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})
            rules = client.get_active_rules()
            rules_list = [asdict(r) for r in rules]
            workspace_path = get_workspace_path(agent_role)
            wisdom = compose_agent_wisdom(
                agent_role=agent_role,
                all_rules=rules_list,
                workspace_path=workspace_path
            )

            return format_mcp_result(wisdom.to_dict())

        except Exception as e:
            return format_mcp_result({"error": str(e)})

        finally:
            client.close()

    @mcp.tool()
    def rule_get(rule_id: str) -> str:
        """Get a specific rule by ID.

        Fetches from TypeDB with markdown fallback if unavailable.

        Args:
            rule_id: Rule identifier (e.g., RULE-001, SESSION-EVID-01-v1)

        Returns:
            JSON object with rule details
        """
        client = get_typedb_client()
        use_fallback = False

        try:
            if not client.connect():
                use_fallback = True
            else:
                rule = client.get_rule_by_id(rule_id)
                if rule:
                    return format_mcp_result(asdict(rule))
                else:
                    use_fallback = True
        except Exception:
            use_fallback = True
        finally:
            client.close()

        if use_fallback:
            md_rule = get_markdown_rule_by_id(rule_id)
            if md_rule:
                result = markdown_rule_to_dict(md_rule)
                result["warning"] = "TypeDB unavailable - using markdown fallback (read-only)"
                return format_mcp_result(result)
            else:
                return format_mcp_result({"error": f"Rule {rule_id} not found in TypeDB or markdown"})

    @mcp.tool()
    def rule_get_deps(rule_id: str) -> str:
        """Get dependencies for a rule.

        Returns rules that depend on or are depended upon by the specified rule.

        Args:
            rule_id: Rule identifier

        Returns:
            JSON object with dependency information
        """
        client = get_typedb_client()

        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            deps = client.get_rule_dependencies(rule_id)
            return format_mcp_result(deps)

        finally:
            client.close()

    @mcp.tool()
    def rules_find_conflicts() -> str:
        """Find conflicting rules in the governance system.

        Analyzes rules for potential conflicts based on overlapping scope
        or contradictory directives.

        Returns:
            JSON array of detected rule conflicts
        """
        client = get_typedb_client()

        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            conflicts = client.find_conflicts()
            return format_mcp_result(conflicts)

        finally:
            client.close()
