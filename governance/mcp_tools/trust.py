"""
Trust Score MCP Tools
=====================
Agent trust score operations (RULE-011).

Per RULE-012: DSP Semantic Code Structure
Per FP + Digital Twin Paradigm: Trust entity module
"""

from dataclasses import asdict

from governance.mcp_tools.common import (
    TrustScore,
    calculate_vote_weight,
    get_typedb_client,
    format_mcp_result,
)


def register_trust_tools(mcp) -> None:
    """Register trust-related MCP tools."""

    @mcp.tool()
    def governance_get_trust_score(agent_id: str) -> str:
        """
        Get trust score for an agent (RULE-011).

        Trust Formula: (Compliance × 0.4) + (Accuracy × 0.3) + (Consistency × 0.2) + (Tenure × 0.1)

        Args:
            agent_id: The agent ID (e.g., "AGENT-001")

        Returns:
            JSON object with trust score details
        """
        client = get_typedb_client()

        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            # Query agent data from TypeDB
            query = f'''
                match
                    $a isa agent, has agent-id "{agent_id}";
                    $a has agent-name $name;
                    $a has trust-score $trust;
                    $a has compliance-rate $compliance;
                    $a has accuracy-rate $accuracy;
                    $a has tenure-days $tenure;
                select $name, $trust, $compliance, $accuracy, $tenure;
            '''

            results = client.execute_query(query)

            if not results:
                return format_mcp_result({"error": f"Agent {agent_id} not found"})

            result = results[0]
            trust_score = result.get('trust', 0.0)

            score = TrustScore(
                agent_id=agent_id,
                agent_name=result.get('name', 'Unknown'),
                trust_score=trust_score,
                compliance_rate=result.get('compliance', 0.0),
                accuracy_rate=result.get('accuracy', 0.0),
                tenure_days=result.get('tenure', 0),
                vote_weight=calculate_vote_weight(trust_score)
            )

            return format_mcp_result(asdict(score))

        finally:
            client.close()

    # =========================================================================
    # PHASE 1: Domain-Based Aliases (RD-MCP-TOOL-NAMING)
    # =========================================================================

    def agent_trust_score(agent_id: str) -> str:
        """Get agent trust score. Alias for governance_get_trust_score."""
        return governance_get_trust_score(agent_id)

    # Note: governance_list_agents is defined in agents.py (removed duplicate here)

    # Register domain-based aliases
    mcp.tool()(agent_trust_score)
