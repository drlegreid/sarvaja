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
        # BUG-AGENT-ESCAPE-001: Escape agent_id for TypeQL safety
        aid = agent_id.replace('"', '\\"')
        query = f"""
            match $a isa agent,
                has agent-id "{aid}",
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
        # BUG-AGENT-ESCAPE-001: Escape agent_id for consistency
        agent_id_escaped = agent_id.replace('"', '\\"')
        query = f"""
            insert $a isa agent,
                has agent-id "{agent_id_escaped}",
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
        # BUG-AGENT-ESCAPE-001: Escape agent_id for consistency
        agent_id_escaped = agent_id.replace('"', '\\"')
        query = f"""
            match $a isa agent, has agent-id "{agent_id_escaped}";
            delete $a;
        """
        try:
            self._execute_write(query)
            return True
        except Exception:
            return False

    def update_agent_trust(self, agent_id: str, trust_score: float) -> bool:
        """Update an agent's trust score using atomic attribute update."""
        from typedb.driver import TransactionType

        current = self.get_agent(agent_id)
        if not current:
            return False

        # BUG-AGENT-ESCAPE-001: Escape agent_id for consistency
        agent_id_escaped = agent_id.replace('"', '\\"')
        # BUG-AGENT-TRUST-NONATOMIC: Single transaction — update attribute, not delete+re-insert entity
        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                # Delete old trust-score attribute
                try:
                    tx.query(f'''
                        match $a isa agent, has agent-id "{agent_id_escaped}", has trust-score $old;
                        delete has $old of $a;
                    ''').resolve()
                except Exception:
                    pass  # May not have existing trust-score
                # Insert new trust-score attribute
                tx.query(f'''
                    match $a isa agent, has agent-id "{agent_id_escaped}";
                    insert $a has trust-score {trust_score};
                ''').resolve()
                tx.commit()
            return True
        except Exception:
            return False
