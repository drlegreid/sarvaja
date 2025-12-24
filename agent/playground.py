"""
Sim.ai PoC Agent with:
- Claude models via Anthropic
- Opik tracing for observability
- ChromaDB for vector storage
- AgentOS for serving via FastAPI
"""
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
    """Create ChromaDB-backed knowledge base."""
    host = os.getenv("CHROMADB_HOST")
    port = os.getenv("CHROMADB_PORT", "8000")
    
    if not host:
        print("ChromaDB not configured, skipping knowledge base")
        return None
    
    print(f"ChromaDB available at {host}:{port} (knowledge disabled for initial test)")
    # TODO: Fix Agno ChromaDb wrapper integration
    # For now, skip knowledge to get basic agent running
    return None


def create_agents(config: dict) -> list[Agent]:
    """Create agents from configuration."""
    agents = []
    knowledge = create_chromadb_knowledge()
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
        
        if knowledge and agent_data.get("use_knowledge", False):
            agent_kwargs["knowledge"] = knowledge
        
        agent = Agent(**agent_kwargs)
        
        if agent_data.get("chat", True):
            agents.append(agent)
            print(f"Created agent: {agent_data['name']} (model: {model_name})")
    
    return agents


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
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7777)


if __name__ == "__main__":
    main()
