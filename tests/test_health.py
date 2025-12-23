"""
Health check tests for all Sim.ai PoC services.
Tests service availability and basic functionality.
"""
import pytest
import httpx


class TestServiceHealth:
    """Health checks for all services."""

    @pytest.mark.integration
    def test_litellm_health(self, litellm_client):
        """Test LiteLLM proxy is healthy."""
        client = litellm_client["client"]
        base_url = litellm_client["base_url"]
        api_key = litellm_client["api_key"]
        
        response = client.get(f"{base_url}/health", headers={"Authorization": f"Bearer {api_key}"})
        assert response.status_code == 200, f"LiteLLM unhealthy: {response.text}"

    @pytest.mark.integration
    def test_litellm_models(self, litellm_client):
        """Test LiteLLM has models configured."""
        client = litellm_client["client"]
        base_url = litellm_client["base_url"]
        api_key = litellm_client["api_key"]
        
        response = client.get(f"{base_url}/v1/models", headers={"Authorization": f"Bearer {api_key}"})
        assert response.status_code == 200
        data = response.json()
        assert "data" in data, "No models data returned"
        assert len(data["data"]) > 0, "No models configured"

    @pytest.mark.integration
    def test_chromadb_health(self, chromadb_client):
        """Test ChromaDB is healthy."""
        client = chromadb_client["client"]
        base_url = chromadb_client["base_url"]
        
        response = client.get(f"{base_url}/api/v2/heartbeat")
        assert response.status_code == 200, f"ChromaDB unhealthy: {response.text}"

    @pytest.mark.integration
    def test_chromadb_collections(self, chromadb_client):
        """Test ChromaDB collections endpoint."""
        client = chromadb_client["client"]
        base_url = chromadb_client["base_url"]
        
        response = client.get(f"{base_url}/api/v2/tenants/default_tenant/databases/default_database/collections")
        assert response.status_code == 200

    @pytest.mark.integration
    def test_ollama_health(self, http_client):
        """Test Ollama is healthy."""
        try:
            response = http_client.get("http://localhost:11434/api/tags")
            assert response.status_code == 200, f"Ollama unhealthy: {response.text}"
        except httpx.ConnectError:
            pytest.skip("Ollama not running")

    @pytest.mark.integration
    def test_agents_health(self, agents_client):
        """Test Agents API is healthy."""
        client = agents_client["client"]
        base_url = agents_client["base_url"]
        
        try:
            response = client.get(f"{base_url}/health")
            assert response.status_code in [200, 404], f"Agents API error: {response.text}"
        except httpx.ConnectError:
            pytest.skip("Agents API not running")

    @pytest.mark.integration
    def test_opik_health(self, opik_client):
        """Test Opik UI is healthy."""
        client = opik_client["client"]
        base_url = opik_client["base_url"]
        
        try:
            response = client.get(base_url)
            assert response.status_code == 200, f"Opik unhealthy: {response.text}"
        except httpx.ConnectError:
            pytest.skip("Opik not running - start with: cd opik && ./opik.sh")
