"""
TypeDB Agent Queries.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-003: Extracted from client.py.
Per GAP-ARCH-003: Agent TypeDB operations.

Created: 2024-12-28
"""

from typing import List, Optional

from ..entities import Agent


class AgentQueries:
    """
    Agent query operations for TypeDB.

    Requires a client with _execute_query, _execute_write, and _client attributes.
    Uses mixin pattern for TypeDBClient composition.
    """

    def get_all_agents(self) -> List[Agent]:
        """Get all agents from TypeDB."""
        query = """
            match $a isa agent,
                has agent-id $id,
                has agent-name $name,
                has agent-type $type;
            get $id, $name, $type;
        """
        results = self._execute_query(query)
        agents = []
        for r in results:
            agent_id = r.get("id")
            agent = Agent(
                id=agent_id,
                name=r.get("name"),
                agent_type=r.get("type")
            )
            agents.append(agent)
        return agents

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get a specific agent by ID."""
        query = f"""
            match $a isa agent,
                has agent-id "{agent_id}",
                has agent-name $name,
                has agent-type $type;
            get $name, $type;
        """
        results = self._execute_query(query)
        if results:
            r = results[0]
            return Agent(
                id=agent_id,
                name=r.get("name"),
                agent_type=r.get("type")
            )
        return None

    def insert_agent(self, agent_id: str, name: str, agent_type: str,
                     trust_score: float = 0.8) -> bool:
        """Insert a new agent into TypeDB."""
        query = f"""
            insert $a isa agent,
                has agent-id "{agent_id}",
                has agent-name "{name}",
                has agent-type "{agent_type}",
                has trust-score {trust_score};
        """
        try:
            self._execute_write(query)
            return True
        except Exception:
            return False

    def update_agent_trust(self, agent_id: str, trust_score: float) -> bool:
        """Update an agent's trust score."""
        # Get current agent first
        current = self.get_agent(agent_id)
        if not current:
            return False

        # Delete and re-insert with updated trust score
        delete_query = f"""
            match $a isa agent, has agent-id "{agent_id}";
            delete $a isa agent;
        """
        insert_query = f"""
            insert $a isa agent,
                has agent-id "{agent_id}",
                has agent-name "{current.name}",
                has agent-type "{current.agent_type}",
                has trust-score {trust_score};
        """
        try:
            self._execute_write(delete_query)
            self._execute_write(insert_query)
            return True
        except Exception:
            return False
