"""
RF-006: E2E Platform Health Library.
Wraps tests/e2e/test_platform_health_e2e.py for Robot Framework.
"""
import os
import sys
import socket
from pathlib import Path
from typing import Dict, Any
from robot.api.deco import keyword

# Add project root to path for governance imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class PlatformHealthE2ELibrary:
    """Robot Framework library for Platform Health E2E tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.typedb_host = os.getenv("TYPEDB_HOST", "localhost")
        self.typedb_port = int(os.getenv("TYPEDB_PORT", "1729"))
        self.chromadb_host = os.getenv("CHROMADB_HOST", "localhost")
        self.chromadb_port = int(os.getenv("CHROMADB_PORT", "8001"))
        self.dashboard_url = os.getenv("DASHBOARD_URL", "http://localhost:8081")
        self.api_url = os.getenv("API_URL", "http://localhost:8082")

    @keyword("TypeDB Health Check")
    def typedb_health_check(self) -> Dict[str, Any]:
        """Check TypeDB connectivity."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.typedb_host, self.typedb_port))
            sock.close()
            return {"healthy": result == 0, "port_open": result == 0}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    @keyword("ChromaDB Health Check")
    def chromadb_health_check(self) -> Dict[str, Any]:
        """Check ChromaDB connectivity."""
        try:
            import chromadb
            client = chromadb.HttpClient(host=self.chromadb_host, port=self.chromadb_port)
            heartbeat = client.heartbeat()
            collections = client.list_collections()
            return {"healthy": True, "heartbeat": heartbeat, "collections_count": len(collections)}
        except ImportError:
            return {"skipped": True, "reason": "chromadb not installed"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    @keyword("Kanren Health Check")
    def kanren_health_check(self) -> Dict[str, Any]:
        """Check Kanren constraint engine."""
        try:
            from governance.kanren import trust_level, requires_supervisor, filter_rag_chunks
            from governance.kanren import AgentContext, TaskContext, valid_task_assignment

            trust = trust_level(0.85)
            supervisor = requires_supervisor(trust)
            test_chunks = [
                {"source": "typedb", "verified": True, "type": "rule"},
                {"source": "external", "verified": False, "type": "unknown"},
            ]
            filtered = filter_rag_chunks(test_chunks)
            agent = AgentContext("TEST-AGENT", "Test", 0.85, "claude-code")
            task = TaskContext("TEST-TASK", "HIGH", True)
            assignment = valid_task_assignment(agent, task)

            return {
                "healthy": True,
                "rag_filter_works": len(filtered) == 1,
                "task_assignment_works": assignment.get("valid", False)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    @keyword("Kanren Benchmark Check")
    def kanren_benchmark_check(self) -> Dict[str, Any]:
        """Check Kanren benchmark performance."""
        try:
            from governance.kanren.benchmark import bench_trust_level
            result = bench_trust_level()
            return {"healthy": result.passed, "avg_ms": result.avg_ms, "target_ms": result.target_ms}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    @keyword("Dashboard Health Check")
    def dashboard_health_check(self) -> Dict[str, Any]:
        """Check Dashboard HTTP endpoint."""
        try:
            import requests
            response = requests.get(self.dashboard_url, timeout=5, allow_redirects=True)
            return {"healthy": response.status_code in [200, 302], "status_code": response.status_code}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    @keyword("API Health Check")
    def api_health_check(self) -> Dict[str, Any]:
        """Check API endpoint."""
        try:
            import requests
            endpoints = ["/api/health", "/health", "/"]
            for endpoint in endpoints:
                try:
                    response = requests.get(f"{self.api_url}{endpoint}", timeout=5)
                    if response.status_code in [200, 302]:
                        return {"healthy": True, "endpoint": endpoint}
                except Exception:
                    continue
            return {"healthy": False, "error": "No endpoints responding"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    @keyword("MCP Core Services Check")
    def mcp_core_services_check(self) -> Dict[str, Any]:
        """Check MCP CORE services can import."""
        try:
            results = {}
            # Try direct import instead of subprocess
            try:
                import governance.mcp_server_core
                results["governance.mcp_server_core"] = True
            except ImportError:
                results["governance.mcp_server_core"] = False

            try:
                import governance.mcp_server_agents
                results["governance.mcp_server_agents"] = True
            except ImportError:
                results["governance.mcp_server_agents"] = False

            try:
                import governance.mcp_server_sessions
                results["governance.mcp_server_sessions"] = True
            except ImportError:
                results["governance.mcp_server_sessions"] = False

            try:
                import governance.mcp_server_tasks
                results["governance.mcp_server_tasks"] = True
            except ImportError:
                results["governance.mcp_server_tasks"] = False

            all_ok = all(results.values())
            return {"healthy": all_ok, "services": results}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
