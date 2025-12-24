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
        """Test LiteLLM proxy is healthy.

        Note: LiteLLM proxy returns 400 "No connected db" without DB config.
        This is acceptable for our use case - completions still work.
        """
        client = litellm_client["client"]
        base_url = litellm_client["base_url"]
        api_key = litellm_client["api_key"]

        response = client.get(f"{base_url}/health", headers={"Authorization": f"Bearer {api_key}"})

        # Accept 200 (healthy) or 400 with "No connected db" (proxy without DB)
        if response.status_code == 400:
            data = response.json()
            if data.get("error", {}).get("type") == "no_db_connection":
                # LiteLLM running without DB - acceptable for dev
                return
        assert response.status_code == 200, f"LiteLLM unhealthy: {response.text}"

    @pytest.mark.integration
    def test_litellm_models(self, litellm_client):
        """Test LiteLLM has models configured.

        Note: /v1/models may return 400 without DB. We accept this.
        """
        client = litellm_client["client"]
        base_url = litellm_client["base_url"]
        api_key = litellm_client["api_key"]

        response = client.get(f"{base_url}/v1/models", headers={"Authorization": f"Bearer {api_key}"})

        # Accept 400 "No connected db" as passing for dev setup
        if response.status_code == 400:
            data = response.json()
            if data.get("error", {}).get("type") == "no_db_connection":
                return

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

    @pytest.mark.integration
    def test_typedb_health(self, typedb_config):
        """Test TypeDB is healthy (DECISION-003).

        TypeDB doesn't have HTTP health endpoint, so we check socket connectivity.
        """
        import socket

        host = typedb_config["host"]
        port = typedb_config["port"]

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()

            if result != 0:
                pytest.skip(f"TypeDB not running on {host}:{port}")
        except socket.error as e:
            pytest.skip(f"TypeDB connection failed: {e}")
