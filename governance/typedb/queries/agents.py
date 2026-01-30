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

    Requires a client with _execute_query, _execute_write, and _driver attributes.
    Uses mixin pattern for TypeDBClient composition.
    """

    def get_all_agents(self) -> List[Agent]:
        """Get all agents from TypeDB."""
        query = """
            match $a isa agent,
                has agent-id $id,
                has agent-name $name,
                has agent-type $type,
                has trust-score $trust;
            select $id, $name, $type, $trust;
        """
        results = self._execute_query(query)
        agents = []
        for r in results:
            agent_id = r.get("id")
            agent = Agent(
                id=agent_id,
                name=r.get("name"),
                agent_type=r.get("type"),
                trust_score=r.get("trust", 0.8)
            )
            agents.append(agent)
        return agents

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get a specific agent by ID."""
        query = f"""
            match $a isa agent,
                has agent-id "{agent_id}",
                has agent-name $name,
                has agent-type $type,
                has trust-score $trust;
            select $name, $type, $trust;
        """
        results = self._execute_query(query)
        if results:
            r = results[0]
            return Agent(
                id=agent_id,
                name=r.get("name"),
                agent_type=r.get("type"),
                trust_score=r.get("trust", 0.8)
            )
        return None

    def insert_agent(self, agent_id: str, name: str, agent_type: str,
                     trust_score: float = 0.8) -> bool:
        """Insert a new agent into TypeDB. Deletes existing duplicates first."""
        # Dedup: remove any existing entries with this agent_id
        existing = self.get_agent(agent_id)
        if existing:
            self.delete_agent(agent_id)

        name_escaped = name.replace('"', '\\"')
        type_escaped = agent_type.replace('"', '\\"')
        query = f"""
            insert $a isa agent,
                has agent-id "{agent_id}",
                has agent-name "{name_escaped}",
                has agent-type "{type_escaped}",
                has trust-score {trust_score};
        """
        try:
            self._execute_write(query)
            return True
        except Exception:
            return False

    def delete_agent(self, agent_id: str) -> bool:
        """Delete all agent entities with the given ID from TypeDB."""
        query = f"""
            match $a isa agent, has agent-id "{agent_id}";
            delete $a;
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
            delete $a;
        """
        name_escaped = current.name.replace('"', '\\"')
        type_escaped = current.agent_type.replace('"', '\\"')
        insert_query = f"""
            insert $a isa agent,
                has agent-id "{agent_id}",
                has agent-name "{name_escaped}",
                has agent-type "{type_escaped}",
                has trust-score {trust_score};
        """
        try:
            self._execute_write(delete_query)
            self._execute_write(insert_query)
            return True
        except Exception:
            return False
