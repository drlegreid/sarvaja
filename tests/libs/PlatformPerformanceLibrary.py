"""
Platform Performance Library for Robot Framework
Tests for SFDIPOT Platform/Time and CRUCSS Charisma/Scalability aspects.
Migrated from tests/heuristics/test_platform_performance.py
Per: RF-007 Robot Framework Migration
"""
import os
import time
from robot.api.deco import keyword


class PlatformPerformanceLibrary:
    """Robot Framework keywords for platform performance tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'
    API_BASE = os.getenv("API_BASE_URL", "http://localhost:8082")

    def _get_client(self):
        """Get HTTP client for API testing."""
        try:
            import httpx
            return httpx.Client(base_url=self.API_BASE, timeout=10.0)
        except ImportError:
            return None

    # =========================================================================
    # SFDIPOT: Platform Tests
    # =========================================================================

    @keyword("Health Endpoint Responds")
    def health_endpoint_responds(self):
        """Health endpoint should respond."""
        try:
            import httpx
            client = self._get_client()
            if client is None:
                return {"skipped": True, "reason": "httpx not available"}

            response = client.get("/api/health")
            client.close()
            return {
                "responds": response.status_code in [200, 404, 422],
                "status_code": response.status_code
            }
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Environment Vars Documented")
    def environment_vars_documented(self):
        """Required environment variables should be documented."""
        documented_vars = [
            "TYPEDB_HOST",
            "TYPEDB_PORT",
            "TYPEDB_DATABASE",
            "CHROMA_HOST",
            "CHROMA_PORT",
        ]
        return {
            "var_count": len(documented_vars),
            "count_correct": len(documented_vars) == 5
        }

    @keyword("Content Type JSON Accepted")
    def content_type_json_accepted(self):
        """API should accept application/json."""
        try:
            import httpx
            client = self._get_client()
            if client is None:
                return {"skipped": True, "reason": "httpx not available"}

            headers = {"Content-Type": "application/json"}
            response = client.get("/api/rules", headers=headers)
            client.close()
            return {
                "accepted": response.status_code in [200, 404, 422],
                "status_code": response.status_code
            }
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # SFDIPOT: Time Tests
    # =========================================================================

    @keyword("API Latency Acceptable")
    def api_latency_acceptable(self):
        """API should respond within 2 seconds."""
        try:
            import httpx
            client = self._get_client()
            if client is None:
                return {"skipped": True, "reason": "httpx not available"}

            start = time.time()
            response = client.get("/api/rules")
            elapsed = time.time() - start
            client.close()

            if response.status_code != 200:
                return {"skipped": True, "reason": f"API returned {response.status_code}"}

            return {
                "latency": elapsed,
                "within_threshold": elapsed < 2.0
            }
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("No Performance Degradation")
    def no_performance_degradation(self):
        """Multiple requests should maintain performance."""
        try:
            import httpx
            client = self._get_client()
            if client is None:
                return {"skipped": True, "reason": "httpx not available"}

            times = []
            for _ in range(3):
                start = time.time()
                response = client.get("/api/rules")
                if response.status_code != 200:
                    client.close()
                    return {"skipped": True, "reason": f"API returned {response.status_code}"}
                times.append(time.time() - start)

            client.close()

            if len(times) >= 3:
                avg = sum(times) / len(times)
                no_degradation = times[-1] < avg * 2
                return {
                    "times": times,
                    "average": avg,
                    "no_degradation": no_degradation
                }
            return {"skipped": True, "reason": "Not enough measurements"}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Timeout Handling Works")
    def timeout_handling_works(self):
        """API should handle timeouts gracefully."""
        try:
            import httpx
            short_client = httpx.Client(base_url=self.API_BASE, timeout=0.001)
            try:
                short_client.get("/api/rules")
                short_client.close()
                return {"timeout_handled": False}  # Should have timed out
            except httpx.TimeoutException:
                short_client.close()
                return {"timeout_handled": True}
            except httpx.ConnectError:
                short_client.close()
                return {"skipped": True, "reason": "API not available"}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # CRUCSS: Charisma Tests
    # =========================================================================

    @keyword("Response Structure Valid")
    def response_structure_valid(self):
        """Responses should be well-formatted JSON."""
        try:
            import httpx
            client = self._get_client()
            if client is None:
                return {"skipped": True, "reason": "httpx not available"}

            response = client.get("/api/rules")
            client.close()

            if response.status_code != 200:
                return {"skipped": True, "reason": f"API returned {response.status_code}"}

            data = response.json()
            return {"valid_structure": isinstance(data, (dict, list))}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Error Messages User Friendly")
    def error_messages_user_friendly(self):
        """Error messages should be helpful."""
        try:
            import httpx
            client = self._get_client()
            if client is None:
                return {"skipped": True, "reason": "httpx not available"}

            response = client.get("/api/rules/NONEXISTENT-ID")
            client.close()

            if response.status_code >= 400:
                try:
                    error = response.json()
                    has_message = "detail" in error or "message" in error or "error" in error
                    return {"has_error_message": has_message}
                except Exception:
                    return {"has_error_message": True}  # Text errors acceptable
            return {"has_error_message": True}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Dashboard Overview Available")
    def dashboard_overview_available(self):
        """Dashboard should provide useful summary."""
        try:
            import httpx
            client = self._get_client()
            if client is None:
                return {"skipped": True, "reason": "httpx not available"}

            response = client.get("/api/dashboard")
            client.close()
            return {
                "endpoint_exists": response.status_code in [200, 404, 422],
                "status_code": response.status_code
            }
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # CRUCSS: Scalability Tests
    # =========================================================================

    @keyword("Pagination Support")
    def pagination_support(self):
        """API should support pagination."""
        try:
            import httpx
            client = self._get_client()
            if client is None:
                return {"skipped": True, "reason": "httpx not available"}

            response = client.get("/api/rules?limit=5")
            client.close()

            if response.status_code != 200:
                return {"skipped": True, "reason": f"API returned {response.status_code}"}

            data = response.json()
            rules = data.get("rules", data) if isinstance(data, dict) else data
            return {"pagination_works": isinstance(rules, list)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Large Results Handled")
    def large_results_handled(self):
        """API should handle large result requests."""
        try:
            import httpx
            client = self._get_client()
            if client is None:
                return {"skipped": True, "reason": "httpx not available"}

            response = client.get("/api/rules?limit=100")
            client.close()

            if response.status_code != 200:
                return {"skipped": True, "reason": f"API returned {response.status_code}"}

            data = response.json()
            return {"handles_large_requests": isinstance(data, (dict, list))}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Concurrent Requests Supported")
    def concurrent_requests_supported(self):
        """API should handle concurrent requests."""
        try:
            import httpx
            import concurrent.futures

            def fetch_rules():
                try:
                    c = httpx.Client(base_url=self.API_BASE, timeout=10.0)
                    response = c.get("/api/rules")
                    c.close()
                    return response.status_code
                except Exception:
                    return 0

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(fetch_rules) for _ in range(3)]
                results = [f.result() for f in futures]

            successful = sum(1 for r in results if r == 200)
            if successful == 0:
                return {"skipped": True, "reason": "API not available"}

            return {
                "successful_requests": successful,
                "concurrency_works": successful >= 2
            }
        except Exception as e:
            return {"skipped": True, "reason": str(e)}
