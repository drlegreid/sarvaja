"""Tests for rules governance in ChromaDB.
Validates rules CRUD, indexing, and retrieval.
Note: ChromaDB v2 API requires embeddings.
"""
import pytest
import httpx
import json
from datetime import datetime

# Dummy embedding (384 dims)
DUMMY_EMBEDDING = [0.1] * 384


class TestRulesGovernance:
    """Tests for rules management in ChromaDB."""
    
    COLLECTION_NAME = "sim_ai_rules"
    
    @pytest.fixture
    def rules_collection(self, chromadb_client):
        """Ensure rules collection exists."""
        client = chromadb_client["client"]
        base_url = chromadb_client["base_url"]
        
        # Create collection if not exists
        response = client.post(
            f"{base_url}/api/v2/tenants/default_tenant/databases/default_database/collections",
            json={
                "name": self.COLLECTION_NAME,
                "metadata": {"description": "Agent rules and heuristics"}
            }
        )
        # 200 = created, 409 = already exists
        assert response.status_code in [200, 409]
        
        return {"client": client, "base_url": base_url, "collection": self.COLLECTION_NAME}

    @pytest.mark.integration
    @pytest.mark.skip(reason="ChromaDB v2 API requires collection UUID - needs refactoring")
    def test_create_rule(self, rules_collection):
        """Test creating a new rule."""
        client = rules_collection["client"]
        base_url = rules_collection["base_url"]
        collection = rules_collection["collection"]
        
        rule = {
            "ids": ["rule_001"],
            "documents": ["Always validate user input before processing"],
            "embeddings": [DUMMY_EMBEDDING],
            "metadatas": [{
                "category": "security",
                "priority": "high",
                "created_at": datetime.utcnow().isoformat(),
                "status": "active",
                "effectiveness_score": 0.85
            }]
        }
        
        response = client.post(
            f"{base_url}/api/v2/tenants/default_tenant/databases/default_database/collections/{collection}/add",
            json=rule
        )
        assert response.status_code in [200, 201], f"Failed to create rule: {response.text}"

    @pytest.mark.integration
    @pytest.mark.skip(reason="ChromaDB v2 API requires collection UUID - needs refactoring")
    def test_query_rules_by_category(self, rules_collection):
        """Test querying rules by category."""
        client = rules_collection["client"]
        base_url = rules_collection["base_url"]
        collection = rules_collection["collection"]
        
        # Query for security rules
        response = client.post(
            f"{base_url}/api/v2/tenants/default_tenant/databases/default_database/collections/{collection}/query",
            json={
                "query_embeddings": [DUMMY_EMBEDDING],
                "n_results": 5,
                "where": {"category": "security"}
            }
        )
        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.skip(reason="ChromaDB v2 API requires collection UUID - needs refactoring")
    def test_update_rule_effectiveness(self, rules_collection):
        """Test updating rule effectiveness score."""
        client = rules_collection["client"]
        base_url = rules_collection["base_url"]
        collection = rules_collection["collection"]
        
        # Update metadata
        response = client.post(
            f"{base_url}/api/v2/tenants/default_tenant/databases/default_database/collections/{collection}/update",
            json={
                "ids": ["rule_001"],
                "metadatas": [{
                    "effectiveness_score": 0.92,
                    "last_evaluated": datetime.utcnow().isoformat()
                }]
            }
        )
        # May return 200 or 404 if rule doesn't exist
        assert response.status_code in [200, 404]

    @pytest.mark.integration
    def test_list_all_rules(self, rules_collection):
        """Test listing all rules."""
        client = rules_collection["client"]
        base_url = rules_collection["base_url"]
        collection = rules_collection["collection"]
        
        response = client.get(
            f"{base_url}/api/v2/tenants/default_tenant/databases/default_database/collections/{collection}"
        )
        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.skip(reason="ChromaDB v2 API requires collection UUID - needs refactoring")
    def test_delete_rule(self, rules_collection):
        """Test deleting a rule (soft delete via status)."""
        client = rules_collection["client"]
        base_url = rules_collection["base_url"]
        collection = rules_collection["collection"]
        
        # Soft delete by updating status
        response = client.post(
            f"{base_url}/api/v2/tenants/default_tenant/databases/default_database/collections/{collection}/update",
            json={
                "ids": ["rule_001"],
                "metadatas": [{"status": "deprecated"}]
            }
        )
        assert response.status_code in [200, 404]


class TestMemoryManagement:
    """Tests for agent memory storage."""
    
    COLLECTION_NAME = "sim_ai_memories"
    
    @pytest.fixture
    def memories_collection(self, chromadb_client):
        """Ensure memories collection exists."""
        client = chromadb_client["client"]
        base_url = chromadb_client["base_url"]
        
        response = client.post(
            f"{base_url}/api/v2/tenants/default_tenant/databases/default_database/collections",
            json={
                "name": self.COLLECTION_NAME,
                "metadata": {"description": "Agent memories and context"}
            }
        )
        assert response.status_code in [200, 409]
        
        return {"client": client, "base_url": base_url, "collection": self.COLLECTION_NAME}

    @pytest.mark.integration
    @pytest.mark.skip(reason="ChromaDB v2 API requires collection UUID - needs refactoring")
    def test_store_memory(self, memories_collection):
        """Test storing a memory."""
        client = memories_collection["client"]
        base_url = memories_collection["base_url"]
        collection = memories_collection["collection"]
        
        memory = {
            "ids": ["mem_001"],
            "documents": ["User prefers concise responses with code examples"],
            "embeddings": [DUMMY_EMBEDDING],
            "metadatas": [{
                "type": "preference",
                "agent": "orchestrator",
                "session_id": "session_001",
                "timestamp": datetime.utcnow().isoformat()
            }]
        }
        
        response = client.post(
            f"{base_url}/api/v2/tenants/default_tenant/databases/default_database/collections/{collection}/add",
            json=memory
        )
        assert response.status_code in [201, 200]

    @pytest.mark.integration
    @pytest.mark.skip(reason="ChromaDB v2 API requires collection UUID - needs refactoring")
    def test_query_memories_by_session(self, memories_collection):
        """Test querying memories by session."""
        client = memories_collection["client"]
        base_url = memories_collection["base_url"]
        collection = memories_collection["collection"]
        
        response = client.post(
            f"{base_url}/api/v2/tenants/default_tenant/databases/default_database/collections/{collection}/query",
            json={
                "query_embeddings": [DUMMY_EMBEDDING],
                "n_results": 10,
                "where": {"session_id": "session_001"}
            }
        )
        assert response.status_code == 200


class TestSessionLogs:
    """Tests for session logging."""
    
    COLLECTION_NAME = "sim_ai_sessions"
    
    @pytest.fixture
    def sessions_collection(self, chromadb_client):
        """Ensure sessions collection exists."""
        client = chromadb_client["client"]
        base_url = chromadb_client["base_url"]
        
        response = client.post(
            f"{base_url}/api/v2/tenants/default_tenant/databases/default_database/collections",
            json={
                "name": self.COLLECTION_NAME,
                "metadata": {"description": "Session logs and task traces"}
            }
        )
        assert response.status_code in [200, 409]
        
        return {"client": client, "base_url": base_url, "collection": self.COLLECTION_NAME}

    @pytest.mark.integration
    @pytest.mark.skip(reason="ChromaDB v2 API requires collection UUID - needs refactoring")
    def test_log_task(self, sessions_collection):
        """Test logging a task execution."""
        client = sessions_collection["client"]
        base_url = sessions_collection["base_url"]
        collection = sessions_collection["collection"]
        
        task_log = {
            "ids": ["task_001"],
            "documents": ["Executed code review task for user request"],
            "embeddings": [DUMMY_EMBEDDING],
            "metadatas": [{
                "task_type": "code_review",
                "agent": "coder",
                "status": "completed",
                "duration_ms": 1250,
                "tokens_used": 456,
                "model": "claude-opus",
                "timestamp": datetime.utcnow().isoformat()
            }]
        }
        
        response = client.post(
            f"{base_url}/api/v2/tenants/default_tenant/databases/default_database/collections/{collection}/add",
            json=task_log
        )
        assert response.status_code in [201, 200]

    @pytest.mark.integration
    @pytest.mark.skip(reason="ChromaDB v2 API requires collection UUID - needs refactoring")
    def test_query_tasks_by_agent(self, sessions_collection):
        """Test querying tasks by agent."""
        client = sessions_collection["client"]
        base_url = sessions_collection["base_url"]
        collection = sessions_collection["collection"]
        
        response = client.post(
            f"{base_url}/api/v2/tenants/default_tenant/databases/default_database/collections/{collection}/query",
            json={
                "query_embeddings": [DUMMY_EMBEDDING],
                "n_results": 10,
                "where": {"agent": "coder"}
            }
        )
        assert response.status_code == 200
