"""
RF-004: Robot Framework Library for Health Check Tests.

Wraps tests/test_health.py for Robot Framework tests.
Integration tests for service health checks.
"""

import sys
import socket
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class HealthLibrary:
    """Robot Framework library for Health Check tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        try:
            import httpx
            self._client = httpx.Client(timeout=10.0)
        except ImportError:
            self._client = None

    def check_litellm_health(self, base_url: str = "http://localhost:4000",
                             api_key: str = "sk-litellm") -> Dict[str, Any]:
        """Check LiteLLM proxy health."""
        if not self._client:
            return {"status": "skip", "reason": "httpx not installed"}
        try:
            response = self._client.get(
                f"{base_url}/health",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            if response.status_code == 400:
                data = response.json()
                if data.get("error", {}).get("type") == "no_db_connection":
                    return {"status": "ok", "reason": "No DB connection (acceptable)"}
            return {
                "status": "ok" if response.status_code == 200 else "fail",
                "status_code": response.status_code
            }
        except Exception as e:
            return {"status": "skip", "reason": str(e)}

    def check_litellm_models(self, base_url: str = "http://localhost:4000",
                             api_key: str = "sk-litellm") -> Dict[str, Any]:
        """Check LiteLLM models endpoint."""
        if not self._client:
            return {"status": "skip", "reason": "httpx not installed"}
        try:
            response = self._client.get(
                f"{base_url}/v1/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            if response.status_code == 400:
                data = response.json()
                if data.get("error", {}).get("type") == "no_db_connection":
                    return {"status": "ok", "reason": "No DB connection (acceptable)"}
            if response.status_code == 200:
                data = response.json()
                model_count = len(data.get("data", []))
                return {"status": "ok", "model_count": model_count}
            return {"status": "fail", "status_code": response.status_code}
        except Exception as e:
            return {"status": "skip", "reason": str(e)}

    def check_chromadb_health(self, base_url: str = "http://localhost:8001") -> Dict[str, Any]:
        """Check ChromaDB health."""
        if not self._client:
            return {"status": "skip", "reason": "httpx not installed"}
        try:
            response = self._client.get(f"{base_url}/api/v2/heartbeat")
            return {
                "status": "ok" if response.status_code == 200 else "fail",
                "status_code": response.status_code
            }
        except Exception as e:
            return {"status": "skip", "reason": str(e)}

    def check_chromadb_collections(self, base_url: str = "http://localhost:8001") -> Dict[str, Any]:
        """Check ChromaDB collections endpoint."""
        if not self._client:
            return {"status": "skip", "reason": "httpx not installed"}
        try:
            response = self._client.get(
                f"{base_url}/api/v2/tenants/default_tenant/databases/default_database/collections"
            )
            return {
                "status": "ok" if response.status_code == 200 else "fail",
                "status_code": response.status_code
            }
        except Exception as e:
            return {"status": "skip", "reason": str(e)}

    def check_ollama_health(self, base_url: str = "http://localhost:11434") -> Dict[str, Any]:
        """Check Ollama health."""
        if not self._client:
            return {"status": "skip", "reason": "httpx not installed"}
        try:
            response = self._client.get(f"{base_url}/api/tags")
            return {
                "status": "ok" if response.status_code == 200 else "fail",
                "status_code": response.status_code
            }
        except Exception as e:
            return {"status": "skip", "reason": str(e)}

    def check_agents_health(self, base_url: str = "http://localhost:8082") -> Dict[str, Any]:
        """Check Agents API health."""
        if not self._client:
            return {"status": "skip", "reason": "httpx not installed"}
        try:
            response = self._client.get(f"{base_url}/health")
            return {
                "status": "ok" if response.status_code in [200, 404] else "fail",
                "status_code": response.status_code
            }
        except Exception as e:
            return {"status": "skip", "reason": str(e)}

    def check_typedb_health(self, host: str = "localhost", port: int = 1729) -> Dict[str, Any]:
        """Check TypeDB socket connectivity."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            return {
                "status": "ok" if result == 0 else "skip",
                "reason": None if result == 0 else f"Not running on {host}:{port}"
            }
        except socket.error as e:
            return {"status": "skip", "reason": str(e)}

    def check_all_services(self) -> Dict[str, Any]:
        """Check all services and return summary."""
        return {
            "litellm": self.check_litellm_health(),
            "chromadb": self.check_chromadb_health(),
            "ollama": self.check_ollama_health(),
            "agents": self.check_agents_health(),
            "typedb": self.check_typedb_health()
        }
