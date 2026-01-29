"""
Tests for LiteLLM model routing.
Validates routing to Claude, Grok, and Ollama.

Requires LiteLLM proxy running on localhost:4000.
"""
import pytest
import httpx
import os


def _litellm_available():
    """Check if LiteLLM proxy is reachable."""
    try:
        with httpx.Client(timeout=3.0) as client:
            response = client.get("http://localhost:4000/health")
            return response.status_code in [200, 400]
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


@pytest.mark.skipif(not _litellm_available(), reason="LiteLLM proxy not running")
class TestLiteLLMRouting:
    """Tests for LiteLLM model routing."""

    @pytest.mark.integration
    def test_list_available_models(self, litellm_client):
        """Test listing all configured models."""
        client = litellm_client["client"]
        base_url = litellm_client["base_url"]
        api_key = litellm_client["api_key"]

        response = client.get(f"{base_url}/v1/models", headers={"Authorization": f"Bearer {api_key}"})
        assert response.status_code == 200
        
        data = response.json()
        model_ids = [m["id"] for m in data.get("data", [])]
        
        # Check expected models are configured
        expected = ["claude-opus", "claude-sonnet", "gemma-local"]
        for model in expected:
            assert any(model in mid for mid in model_ids), f"Model {model} not found"

    @pytest.mark.integration
    @pytest.mark.slow
    def test_claude_opus_completion(self, litellm_client):
        """Test completion via Claude Opus."""
        client = litellm_client["client"]
        base_url = litellm_client["base_url"]
        api_key = litellm_client["api_key"]
        
        response = client.post(
            f"{base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "claude-opus",
                "messages": [{"role": "user", "content": "Say 'test' and nothing else"}],
                "max_tokens": 10
            },
            timeout=60.0
        )
        
        if response.status_code == 401:
            pytest.skip("API key not configured")
        
        assert response.status_code == 200, f"Claude Opus failed: {response.text}"
        data = response.json()
        assert "choices" in data

    @pytest.mark.integration
    @pytest.mark.slow
    def test_local_ollama_completion(self, litellm_client):
        """Test completion via local Ollama."""
        client = litellm_client["client"]
        base_url = litellm_client["base_url"]
        api_key = litellm_client["api_key"]
        
        response = client.post(
            f"{base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "gemma-local",
                "messages": [{"role": "user", "content": "Say 'hello'"}],
                "max_tokens": 10
            },
            timeout=120.0  # Local models can be slow
        )
        
        if response.status_code in [500, 503]:
            pytest.skip("Ollama model not loaded - run: podman exec platform_ollama_1 ollama pull gemma3:4b")
        
        assert response.status_code == 200, f"Ollama failed: {response.text}"

    @pytest.mark.integration
    def test_grok_completion(self, litellm_client):
        """Test completion via Grok (if configured)."""
        client = litellm_client["client"]
        base_url = litellm_client["base_url"]
        api_key = litellm_client["api_key"]
        
        # Check if XAI key is set
        if not os.getenv("XAI_API_KEY") or os.getenv("XAI_API_KEY") == "xai-your-key-here":
            pytest.skip("XAI_API_KEY not configured")
        
        response = client.post(
            f"{base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "grok",
                "messages": [{"role": "user", "content": "Say 'test'"}],
                "max_tokens": 10
            },
            timeout=60.0
        )
        
        assert response.status_code == 200, f"Grok failed: {response.text}"

    @pytest.mark.integration
    def test_model_fallback(self, litellm_client):
        """Test that invalid model returns proper error."""
        client = litellm_client["client"]
        base_url = litellm_client["base_url"]
        api_key = litellm_client["api_key"]
        
        response = client.post(
            f"{base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "nonexistent-model",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 10
            }
        )
        
        # Should return 400 or 404 for invalid model
        assert response.status_code in [400, 404, 500]
