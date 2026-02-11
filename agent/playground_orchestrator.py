"""
Playground Orchestrator + Knowledge Factories
=============================================
Agent knowledge base creation (ChromaDB, Hybrid) and
orchestrator engine integration for playground.py.

Per DOC-SIZE-01-v1: Extracted from playground.py.
"""

import os
from typing import Optional

from agno.knowledge.knowledge import Knowledge
from agno.vectordb.chroma import ChromaDb

# Import hybrid layer for TypeDB + ChromaDB integration
try:
    from agent.hybrid_vectordb import HybridVectorDb
    HYBRID_AVAILABLE = True
except ImportError:
    HYBRID_AVAILABLE = False

# Import orchestrator for task polling (GAP-AGENT-010-014)
try:
    from agent.orchestrator import OrchestratorEngine, AgentInfo, AgentRole
    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    ORCHESTRATOR_AVAILABLE = False


def create_chromadb_knowledge() -> Optional[Knowledge]:
    """Create ChromaDB-backed knowledge base.

    Uses chromadb.HttpClient to connect to remote ChromaDB server.
    Injects HttpClient directly into Agno's ChromaDb._client property
    since kwargs are passed to ephemeral client, not HttpClient.
    """
    host = os.getenv("CHROMADB_HOST")
    port = os.getenv("CHROMADB_PORT", "8000")
    token = os.getenv("CHROMA_AUTH_TOKEN")

    if not host:
        print("ChromaDB not configured, skipping knowledge base")
        return None

    try:
        import chromadb

        # Create HttpClient for remote ChromaDB server
        headers = {"X-Chroma-Token": token} if token else {}
        http_client = chromadb.HttpClient(
            host=host,
            port=int(port),
            headers=headers
        )

        # Test connection
        http_client.heartbeat()

        # Create Agno ChromaDb wrapper
        # Use sim_ai_knowledge collection (53 docs migrated from claude-mem)
        vector_db = ChromaDb(
            collection="sim_ai_knowledge",
        )

        # Inject HttpClient directly (bypass default ephemeral client)
        vector_db._client = http_client

        knowledge = Knowledge(vector_db=vector_db)
        print(f"ChromaDB knowledge connected: {host}:{port}")
        return knowledge

    except Exception as e:
        print(f"ChromaDB knowledge init failed: {e}")
        return None


def create_hybrid_knowledge() -> Optional[Knowledge]:
    """Create hybrid knowledge base using TypeDB + ChromaDB.

    Routes queries intelligently:
    - Inference queries (dependencies, conflicts) → TypeDB
    - Semantic queries (search, find, about) → ChromaDB

    Per RULE-004: TDD Implementation for P3.4
    """
    if not HYBRID_AVAILABLE:
        print("Hybrid layer not available, falling back to ChromaDB")
        return create_chromadb_knowledge()

    chromadb_host = os.getenv("CHROMADB_HOST")
    chromadb_port = os.getenv("CHROMADB_PORT", "8001")
    typedb_host = os.getenv("TYPEDB_HOST", "localhost")
    typedb_port = os.getenv("TYPEDB_PORT", "1729")

    if not chromadb_host:
        print("ChromaDB not configured, skipping hybrid knowledge")
        return None

    try:
        # Create hybrid vector DB that wraps both backends
        hybrid_db = HybridVectorDb(
            chromadb_host=chromadb_host,
            chromadb_port=int(chromadb_port),
            typedb_host=typedb_host,
            typedb_port=int(typedb_port),
            collection_name="sim_ai_knowledge",
            auto_connect=True
        )

        # Create Agno Knowledge wrapper
        # Note: HybridVectorDb implements search() compatible with Agno VectorDb
        knowledge = Knowledge(vector_db=hybrid_db)
        print(f"Hybrid knowledge connected: TypeDB({typedb_host}:{typedb_port}) + ChromaDB({chromadb_host}:{chromadb_port})")
        return knowledge

    except Exception as e:
        print(f"Hybrid knowledge init failed: {e}, falling back to ChromaDB")
        return create_chromadb_knowledge()


def create_orchestrator(agents: list, config: dict) -> Optional["OrchestratorEngine"]:
    """
    Create orchestrator engine for task polling.

    Per GAP-AGENT-010-014: Integrate OrchestratorEngine with playground.

    Args:
        agents: List of Agno agents
        config: Configuration from agents.yaml

    Returns:
        OrchestratorEngine instance or None if unavailable
    """
    if not ORCHESTRATOR_AVAILABLE:
        print("Orchestrator not available, skipping task polling")
        return None

    try:
        from governance.client import get_client

        # Get TypeDB client
        client = get_client()
        if not client:
            print("TypeDB not available, skipping orchestrator")
            return None

        # Create orchestrator
        poll_interval = float(os.getenv("ORCHESTRATOR_POLL_INTERVAL", "10.0"))
        engine = OrchestratorEngine(client, poll_interval=poll_interval)

        # Register agents from config
        for agent_id, agent_data in config.get("agents", {}).items():
            # Map agent role from config
            role_map = {
                "research": AgentRole.RESEARCH,
                "coding": AgentRole.CODING,
                "curator": AgentRole.CURATOR,
                "sync": AgentRole.SYNC,
                "orchestrator": AgentRole.ORCHESTRATOR,
            }
            role_str = agent_data.get("role", "coding").lower()
            role = role_map.get(role_str, AgentRole.CODING)

            # Default trust score from config or 0.8
            trust_score = float(agent_data.get("trust_score", 0.8))

            agent_info = AgentInfo(
                agent_id=agent_id,
                name=agent_data.get("name", agent_id),
                role=role,
                trust_score=trust_score,
            )
            engine.register_agent(agent_info)
            print(f"Registered agent for orchestration: {agent_id} (trust: {trust_score})")

        return engine

    except Exception as e:
        print(f"Orchestrator init failed: {e}")
        return None


async def start_orchestration(engine: "OrchestratorEngine") -> None:
    """
    Start orchestration loop in background.

    Per GAP-AGENT-011: Agent polling/subscription for new tasks.
    """
    try:
        await engine.start()
        print(f"Orchestrator started (polling every {engine._poller._poll_interval}s)")
    except Exception as e:
        print(f"Orchestrator start failed: {e}")
