"""
Sarvaja PoC Agent with:
- Claude models via Anthropic
- Opik tracing for observability
- ChromaDB for vector storage
- AgentOS for serving via FastAPI

Per DOC-SIZE-01-v1: Knowledge + orchestrator in playground_orchestrator.py.
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

# Re-export for backward compatibility
from .playground_orchestrator import (  # noqa: F401
    create_chromadb_knowledge,
    create_hybrid_knowledge,
    create_orchestrator,
    start_orchestration,
    HYBRID_AVAILABLE,
    ORCHESTRATOR_AVAILABLE,
)


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


def main():
    config_file = sys.argv[1] if len(sys.argv) > 1 else "/agents.yaml"

    print("=== Sarvaja PoC Agent Server ===")
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

        print("Orchestrator endpoints enabled: /orchestrator/status, /orchestrator/dispatch")

    # Integrate Task UI with AG-UI event streaming (Phase 6.1)
    try:
        from agent.task_ui import integrate_task_ui
        agents_dict = {a.name: a for a in agents}
        integrate_task_ui(app, agents_dict)
        print("Task UI enabled: POST /tasks, GET /tasks/{id}/events")

        # Serve static UI (Phase 6.3)
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import FileResponse

        static_dir = os.path.join(os.path.dirname(__file__), "static")
        if os.path.exists(static_dir):
            app.mount("/static", StaticFiles(directory=static_dir), name="static")

            @app.get("/ui")
            async def ui_redirect():
                return FileResponse(os.path.join(static_dir, "index.html"))

            print("Static UI available at: /ui")
    except ImportError as e:
        print(f"Task UI not available: {e}")

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7777)


if __name__ == "__main__":
    main()
