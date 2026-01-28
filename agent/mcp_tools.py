"""
MCP → Agno @tool Wrapper - P4.1 Cross-Workspace Integration

Wraps Governance MCP tools as Agno @tool functions for direct agent use.
Pattern per RULE-017 (Cross-Workspace Pattern Reuse).

Usage:
    from agent.mcp_tools import GovernanceTools

    tools = GovernanceTools()
    agent = Agent(tools=[tools], ...)

Created: 2024-12-24 (Phase 4.1)
Per: R&D-BACKLOG.md, CROSS-WORKSPACE-WISDOM.md
"""

import os
import json
from typing import Optional
from dataclasses import dataclass

# Import Agno tools (available in container, may not be locally)
try:
    from agno.tools import tool, Toolkit
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False
    # Create stubs for local testing
    def tool(func):
        """Stub @tool decorator when agno not available."""
        func._is_tool = True
        return func

    class Toolkit:
        """Stub Toolkit class when agno not available."""
        def __init__(self, name: str = ""):
            self.name = name
            self.functions = {}

        def register(self, func):
            """Register a function as a tool."""
            self.functions[func.__name__] = func

# Import TypeDB client for direct access
try:
    from governance.client import TypeDBClient
    TYPEDB_AVAILABLE = True
except ImportError:
    TYPEDB_AVAILABLE = False


@dataclass
class GovernanceConfig:
    """Configuration for Governance MCP tools."""
    typedb_host: str = "localhost"
    typedb_port: int = 1729
    database: str = "sim-ai-governance"


class GovernanceTools(Toolkit):
    """
    Agno Toolkit wrapping Governance MCP tools.

    Provides direct access to TypeDB governance backend from agents.
    All tools follow MCP interface but are exposed as Agno @tool functions.

    Available tools:
        - query_rules: Query rules by category/status/priority
        - get_rule: Get specific rule by ID
        - get_dependencies: Get rule dependencies (uses inference)
        - find_conflicts: Find conflicting rules
        - get_trust_score: Get agent trust score
        - list_agents: List all agents with trust info
        - health_check: Check governance system health
    """

    def __init__(self, config: Optional[GovernanceConfig] = None):
        super().__init__(name="governance")
        self.config = config or GovernanceConfig(
            typedb_host=os.getenv("TYPEDB_HOST", "localhost"),
            typedb_port=int(os.getenv("TYPEDB_PORT", "1729")),
            database=os.getenv("TYPEDB_DATABASE", "sim-ai-governance")
        )

        # Register tools
        self.register(self.query_rules)
        self.register(self.get_rule)
        self.register(self.get_dependencies)
        self.register(self.find_conflicts)
        self.register(self.get_trust_score)
        self.register(self.list_agents)
        self.register(self.health_check)

    def _get_client(self) -> Optional[TypeDBClient]:
        """Get configured TypeDB client."""
        if not TYPEDB_AVAILABLE:
            return None
        return TypeDBClient(
            host=self.config.typedb_host,
            port=self.config.typedb_port,
            database=self.config.database
        )

    @tool
    def query_rules(
        self,
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
            JSON string with matching rules
        """
        client = self._get_client()
        if not client:
            return json.dumps({"error": "TypeDB client not available"})

        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            # Get rules based on status filter
            if status == "ACTIVE":
                rules = client.get_active_rules()
            else:
                rules = client.get_all_rules()

            # Apply additional filters
            if category:
                rules = [r for r in rules if r.category == category]
            if priority:
                rules = [r for r in rules if r.priority == priority]
            if status and status != "ACTIVE":
                rules = [r for r in rules if r.status == status]

            # Convert dataclasses to dicts
            from dataclasses import asdict
            return json.dumps([asdict(r) for r in rules], default=str, indent=2)

        finally:
            client.close()

    @tool
    def get_rule(self, rule_id: str) -> str:
        """
        Get a specific rule by ID.

        Args:
            rule_id: The rule ID (e.g., "RULE-001")

        Returns:
            JSON string with rule details or error
        """
        client = self._get_client()
        if not client:
            return json.dumps({"error": "TypeDB client not available"})

        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            rule = client.get_rule_by_id(rule_id)
            if rule:
                from dataclasses import asdict
                return json.dumps(asdict(rule), default=str, indent=2)
            else:
                return json.dumps({"error": f"Rule {rule_id} not found"})

        finally:
            client.close()

    @tool
    def get_dependencies(self, rule_id: str) -> str:
        """
        Get all dependencies for a rule (uses TypeDB inference for transitive deps).

        Args:
            rule_id: The rule ID to get dependencies for

        Returns:
            JSON string with dependency rule IDs
        """
        client = self._get_client()
        if not client:
            return json.dumps({"error": "TypeDB client not available"})

        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            deps = client.get_rule_dependencies(rule_id)
            return json.dumps(deps, indent=2)

        finally:
            client.close()

    @tool
    def find_conflicts(self) -> str:
        """
        Find conflicting rules using TypeDB inference.

        Returns:
            JSON string with conflict pairs and explanations
        """
        client = self._get_client()
        if not client:
            return json.dumps({"error": "TypeDB client not available"})

        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            conflicts = client.find_conflicts()
            return json.dumps(conflicts, indent=2)

        finally:
            client.close()

    @tool
    def get_trust_score(self, agent_id: str) -> str:
        """
        Get trust score for an agent (RULE-011).

        Trust Formula: (Compliance × 0.4) + (Accuracy × 0.3) + (Consistency × 0.2) + (Tenure × 0.1)

        Args:
            agent_id: The agent ID (e.g., "AGENT-001")

        Returns:
            JSON string with trust score details
        """
        client = self._get_client()
        if not client:
            return json.dumps({"error": "TypeDB client not available"})

        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            query = f'''
                match
                    $a isa agent, has agent-id "{agent_id}";
                    $a has agent-name $name;
                    $a has trust-score $trust;
                    $a has compliance-rate $compliance;
                    $a has accuracy-rate $accuracy;
                    $a has tenure-days $tenure;
                get $name, $trust, $compliance, $accuracy, $tenure;
            '''

            results = client.execute_query(query)

            if not results:
                return json.dumps({"error": f"Agent {agent_id} not found"})

            result = results[0]
            trust_score = result.get('trust', 0.0)

            # Calculate vote weight per RULE-011
            vote_weight = 1.0 if trust_score >= 0.5 else trust_score

            return json.dumps({
                "agent_id": agent_id,
                "agent_name": result.get('name', 'Unknown'),
                "trust_score": trust_score,
                "compliance_rate": result.get('compliance', 0.0),
                "accuracy_rate": result.get('accuracy', 0.0),
                "tenure_days": result.get('tenure', 0),
                "vote_weight": vote_weight
            }, indent=2)

        finally:
            client.close()

    @tool
    def list_agents(self) -> str:
        """
        List all registered agents with their trust scores.

        Returns:
            JSON string with agents and trust information
        """
        client = self._get_client()
        if not client:
            return json.dumps({"error": "TypeDB client not available"})

        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            query = '''
                match
                    $a isa agent;
                    $a has agent-id $id;
                    $a has agent-name $name;
                    $a has agent-type $type;
                    $a has trust-score $trust;
                get $id, $name, $type, $trust;
            '''

            results = client.execute_query(query)

            agents = []
            for r in results:
                trust = r.get('trust', 0.0)
                agents.append({
                    "agent_id": r.get('id'),
                    "agent_name": r.get('name'),
                    "agent_type": r.get('type'),
                    "trust_score": trust,
                    "vote_weight": 1.0 if trust >= 0.5 else trust
                })

            return json.dumps(agents, indent=2)

        finally:
            client.close()

    @tool
    def health_check(self) -> str:
        """
        Check governance system health.

        Returns:
            JSON string with health status and statistics
        """
        from datetime import datetime

        client = self._get_client()
        if not client:
            return json.dumps({
                "status": "unavailable",
                "typedb_available": False,
                "error": "TypeDB client module not available"
            })

        try:
            connected = client.connect()

            if not connected:
                return json.dumps({
                    "status": "unhealthy",
                    "typedb_connected": False,
                    "error": "Cannot connect to TypeDB"
                })

            # Get counts
            rules = client.get_all_rules()

            return json.dumps({
                "status": "healthy",
                "typedb_connected": True,
                "typedb_host": f"{self.config.typedb_host}:{self.config.typedb_port}",
                "database": self.config.database,
                "statistics": {
                    "rules_count": len(rules),
                    "active_rules": len([r for r in rules if r.status == "ACTIVE"])
                },
                "timestamp": datetime.now().isoformat()
            }, indent=2)

        finally:
            client.close()


# Convenience function for quick toolkit creation
def create_governance_tools(
    typedb_host: str = None,
    typedb_port: int = None,
    database: str = None
) -> GovernanceTools:
    """
    Create GovernanceTools toolkit with custom configuration.

    Args:
        typedb_host: TypeDB host (default: from env or localhost)
        typedb_port: TypeDB port (default: from env or 1729)
        database: Database name (default: from env or sim-ai-governance)

    Returns:
        Configured GovernanceTools instance
    """
    config = GovernanceConfig(
        typedb_host=typedb_host or os.getenv("TYPEDB_HOST", "localhost"),
        typedb_port=typedb_port or int(os.getenv("TYPEDB_PORT", "1729")),
        database=database or os.getenv("TYPEDB_DATABASE", "sim-ai-governance")
    )
    return GovernanceTools(config)
