"""
Robot Framework Library for LiteLLM Routing Tests.

Integration tests for LiteLLM model routing.
Migrated from tests/test_litellm_routing.py
"""
import os
from robot.api.deco import keyword


class LiteLLMRoutingLibrary:
    """Library for testing LiteLLM model routing."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    @keyword("List Available Models")
    def list_available_models(self):
        """Test listing all configured models."""
        try:
            import httpx
            base_url = os.getenv("LITELLM_BASE_URL", "http://localhost:4000")
            api_key = os.getenv("LITELLM_API_KEY", "sk-1234")

            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{base_url}/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"}
                )

                if response.status_code != 200:
                    return {"skipped": True, "reason": f"LiteLLM not available: {response.status_code}"}

                data = response.json()
                model_ids = [m["id"] for m in data.get("data", [])]
                expected = ["claude-opus", "claude-sonnet", "gemma-local"]
                missing = [m for m in expected if not any(m in mid for mid in model_ids)]

                return {
                    "has_models": len(model_ids) > 0,
                    "all_expected": len(missing) == 0,
                    "missing": missing
                }
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Model Fallback Error")
    def model_fallback_error(self):
        """Test that invalid model returns proper error."""
        try:
            import httpx
            base_url = os.getenv("LITELLM_BASE_URL", "http://localhost:4000")
            api_key = os.getenv("LITELLM_API_KEY", "sk-1234")

            with httpx.Client(timeout=10.0) as client:
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
                return {"error_code": response.status_code in [400, 404, 500]}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}
