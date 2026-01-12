"""
Trust Score MCP Tools
=====================
Agent trust score operations (RULE-011).

Per RULE-012: DSP Semantic Code Structure
Per FP + Digital Twin Paradigm: Trust entity module
"""

import json
from dataclasses import asdict

from governance.mcp_tools.common import (
    TrustScore,
    calculate_vote_weight,
    get_typedb_client,
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
                return json.dumps({"error": "Failed to connect to TypeDB"})

            # Query agent data from TypeDB
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

            score = TrustScore(
                agent_id=agent_id,
                agent_name=result.get('name', 'Unknown'),
                trust_score=trust_score,
                compliance_rate=result.get('compliance', 0.0),
                accuracy_rate=result.get('accuracy', 0.0),
                tenure_days=result.get('tenure', 0),
                vote_weight=calculate_vote_weight(trust_score)
            )

            return json.dumps(asdict(score), indent=2, default=str)

        finally:
            client.close()

    @mcp.tool()
    def governance_list_agents() -> str:
        """
        List all registered agents with their trust scores.

        Returns:
            JSON array of agents with trust information
        """
        client = get_typedb_client()

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
                agents.append({
                    "agent_id": r.get('id'),
                    "agent_name": r.get('name'),
                    "agent_type": r.get('type'),
                    "trust_score": r.get('trust'),
                    "vote_weight": calculate_vote_weight(r.get('trust', 0.0))
                })

            return json.dumps(agents, indent=2)

        finally:
            client.close()
