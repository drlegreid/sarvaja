"""
Sim.ai PoC Agent with:
- Claude models via Anthropic
- Opik tracing for observability
- ChromaDB for vector storage
- AgentOS for serving via FastAPI
"""
from __future__ import annotations

import os
import sys
from typing import Optional

import yaml
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.os import AgentOS
from agno.db.sqlite import SqliteDb
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


def init_opik():
    """Initialize Opik for tracing.
    
    Uses environment variables (no configure() call needed):
    - OPIK_URL_OVERRIDE: Self-hosted Opik URL (e.g., http://opik-backend:8080/api)
    - OPIK_PROJECT_NAME: Project name for traces
    - OPIK_WORKSPACE: Workspace name
    - OPIK_API_KEY: API key (optional for self-hosted)
    """
    opik_url = os.getenv("OPIK_URL_OVERRIDE")
    project = os.getenv("OPIK_PROJECT_NAME", "sim-ai-poc")
    
    if opik_url:
        try:
            import opik
            # Opik SDK auto-configures from environment variables
            # No need to call configure() - just import and use
            print(f"Opik configured via env: {opik_url} (project: {project})")
            return True
        except Exception as e:
            print(f"Opik import failed: {e}")
    else:
        print("Opik not configured (OPIK_URL_OVERRIDE not set)")
    return False


def create_model(model_name: str) -> Claude:
    """Create a Claude model."""
    print(f"Creating Claude model: {model_name}")
    return Claude(id=model_name)


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


def create_agents(config: dict) -> list[Agent]:
    """Create agents from configuration.

    Supports two knowledge modes:
    - use_knowledge: Basic ChromaDB knowledge
    - use_hybrid_knowledge: Hybrid TypeDB + ChromaDB (P3.4)
    """
    agents = []
    chromadb_knowledge = None
    hybrid_knowledge = None
    init_opik()

    model_name = os.getenv("MODEL_NAME", "claude-sonnet-4-20250514")

    for agent_id, agent_data in config.get("agents", {}).items():
        model = create_model(model_name)

        agent_kwargs = {
            "name": agent_data["name"],
            "description": agent_data.get("description"),
            "instructions": agent_data.get("instructions"),
            "model": model,
            "markdown": agent_data.get("markdown", True),
            "add_history_to_context": True,
            "db": SqliteDb(db_file="/app/data/agents.db"),
        }

        # Determine knowledge type
        if agent_data.get("use_hybrid_knowledge", False):
            # Lazy init hybrid knowledge
            if hybrid_knowledge is None:
                hybrid_knowledge = create_hybrid_knowledge()
            if hybrid_knowledge:
                agent_kwargs["knowledge"] = hybrid_knowledge
        elif agent_data.get("use_knowledge", False):
            # Lazy init ChromaDB knowledge
            if chromadb_knowledge is None:
                chromadb_knowledge = create_chromadb_knowledge()
            if chromadb_knowledge:
                agent_kwargs["knowledge"] = chromadb_knowledge
        
        agent = Agent(**agent_kwargs)

        if agent_data.get("chat", True):
            agents.append(agent)
            print(f"Created agent: {agent_data['name']} (model: {model_name})")

    return agents


def create_orchestrator(agents: list[Agent], config: dict) -> Optional["OrchestratorEngine"]:
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


def main():
    config_file = sys.argv[1] if len(sys.argv) > 1 else "/agents.yaml"

    print(f"=== Sim.ai PoC Agent Server ===")
    print(f"Loading config: {config_file}")

    with open(config_file, "r") as f:
        expanded = os.path.expandvars(f.read())
        config = yaml.safe_load(expanded)

    agents = create_agents(config)

    print(f"Starting AgentOS with {len(agents)} agents on port 7777")

    agent_os = AgentOS(agents=agents)
    app = agent_os.get_app()

    # Integrate orchestrator for task polling (GAP-AGENT-010-014)
    orchestrator = create_orchestrator(agents, config)
    if orchestrator:
        import asyncio

        @app.get("/orchestrator/status")
        async def orchestrator_status():
            """Get orchestrator status and statistics."""
            return orchestrator.stats

        @app.post("/orchestrator/dispatch")
        async def orchestrator_dispatch():
            """Manually dispatch next task from queue."""
            result = await orchestrator.dispatch_next()
            return {
                "success": result.success,
                "task_id": result.task_id,
                "agent_id": result.agent_id,
                "message": result.message,
            }

        @app.on_event("startup")
        async def startup_orchestrator():
            """Start orchestration on server startup."""
            asyncio.create_task(start_orchestration(orchestrator))

        print(f"Orchestrator endpoints enabled: /orchestrator/status, /orchestrator/dispatch")

    # Integrate Task UI with AG-UI event streaming (Phase 6.1)
    try:
        from agent.task_ui import integrate_task_ui
        agents_dict = {a.name: a for a in agents}
        integrate_task_ui(app, agents_dict)
        print(f"Task UI enabled: POST /tasks, GET /tasks/{{id}}/events")

        # Serve static UI (Phase 6.3)
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import FileResponse
        # Note: os is already imported at module level - do not re-import

        static_dir = os.path.join(os.path.dirname(__file__), "static")
        if os.path.exists(static_dir):
            app.mount("/static", StaticFiles(directory=static_dir), name="static")

            @app.get("/ui")
            async def ui_redirect():
                return FileResponse(os.path.join(static_dir, "index.html"))

            print(f"Static UI available at: /ui")
    except ImportError as e:
        print(f"Task UI not available: {e}")

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7777)


if __name__ == "__main__":
    main()
