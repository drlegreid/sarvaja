"""
Data Loader Controllers (GAP-FILE-005)
======================================
Controller functions for loading/refreshing data.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-005: Extracted from governance_dashboard.py
Per GAP-UI-048: Trace bar event capture

Created: 2024-12-28
Updated: 2026-01-14 (trace event integration)
"""

import time
import httpx
from typing import Any, Callable

from agent.governance_ui.trace_bar.transforms import (
    add_api_trace,
    add_error_trace,
)
from agent.governance_ui import (
    get_rules,
    get_proposals,
    get_escalated_proposals,
    build_trust_leaderboard,
    get_governance_stats,
    get_monitor_feed,
    get_monitor_alerts,
    get_monitor_stats,
    get_top_monitored_rules,
    get_hourly_monitor_stats,
)


def register_data_loader_controllers(
    state: Any,
    ctrl: Any,
    api_base_url: str
) -> dict:
    """
    Register data loading controllers with Trame.

    Args:
        state: Trame state object
        ctrl: Trame controller object
        api_base_url: Base URL for API calls

    Returns:
        Dict of loader functions for internal use by view change handler
    """

    def load_trust_data():
        """Load agent trust data from REST API."""
        try:
            with httpx.Client(timeout=10.0) as client:
                start = time.time()
                response = client.get(f"{api_base_url}/api/agents")
                duration_ms = int((time.time() - start) * 1000)
                add_api_trace(state, "/api/agents", "GET", response.status_code, duration_ms)
                if response.status_code == 200:
                    state.agents = response.json()
                else:
                    state.agents = []
        except Exception as e:
            add_error_trace(state, f"Load agents failed: {str(e)}", "/api/agents")
            print(f"Error loading agents: {e}")
            state.agents = []

        state.trust_leaderboard = build_trust_leaderboard(state.agents)

        try:
            state.proposals = get_proposals()
        except Exception:
            state.proposals = []

        try:
            state.escalated_proposals = get_escalated_proposals()
        except Exception:
            state.escalated_proposals = []

        state.governance_stats = get_governance_stats(
            state.agents,
            state.proposals
        )

    def load_monitor_data():
        """Load monitoring data from RuleMonitor."""
        state.monitor_feed = get_monitor_feed(limit=50)
        state.monitor_alerts = get_monitor_alerts(acknowledged=False)
        state.monitor_stats = get_monitor_stats()
        state.top_rules = get_top_monitored_rules(limit=10)
        state.hourly_stats = get_hourly_monitor_stats()

    def load_backlog_data():
        """Load available tasks and agent's claimed tasks from REST API."""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_base_url}/api/tasks/available")
                if response.status_code == 200:
                    state.available_tasks = response.json()
                else:
                    state.available_tasks = []

                if state.backlog_agent_id:
                    response = client.get(
                        f"{api_base_url}/api/tasks",
                        params={"agent_id": state.backlog_agent_id}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        # Handle paginated response (EPIC-DR-003)
                        all_tasks = data["items"] if isinstance(data, dict) and "items" in data else data
                        state.claimed_tasks = [
                            t for t in all_tasks
                            if t.get("agent_id") == state.backlog_agent_id
                            and t.get("status") == "IN_PROGRESS"
                        ]
                    else:
                        state.claimed_tasks = []
                else:
                    state.claimed_tasks = []
        except Exception as e:
            print(f"Error loading backlog data: {e}")
            state.available_tasks = []
            state.claimed_tasks = []

    def load_executive_report_data():
        """Load executive report from REST API."""
        try:
            state.executive_loading = True
            with httpx.Client(timeout=15.0) as client:
                params = {"period": state.executive_period or "week"}
                response = client.get(f"{api_base_url}/api/reports/executive", params=params)
                if response.status_code == 200:
                    state.executive_report = response.json()
                else:
                    state.executive_report = {
                        "error": f"Failed to load report: {response.status_code}",
                        "sections": [],
                        "overall_status": "error",
                        "metrics_summary": {},
                    }
        except Exception as e:
            state.executive_report = {
                "error": str(e),
                "sections": [],
                "overall_status": "error",
                "metrics_summary": {},
            }
        finally:
            state.executive_loading = False

    def _traced_get(client: httpx.Client, endpoint: str) -> tuple:
        """Make a traced GET request. Returns (response, duration_ms)."""
        start = time.time()
        try:
            response = client.get(f"{api_base_url}{endpoint}")
            duration_ms = int((time.time() - start) * 1000)
            add_api_trace(state, endpoint, "GET", response.status_code, duration_ms)
            return response, duration_ms
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            add_error_trace(state, f"GET {endpoint} failed: {str(e)}", endpoint)
            raise

    @ctrl.trigger("refresh_data")
    def refresh_data():
        """Refresh all data from REST API."""
        try:
            state.is_loading = True
            with httpx.Client(timeout=10.0) as client:
                try:
                    response, _ = _traced_get(client, "/api/rules")
                    if response.status_code == 200:
                        state.rules = response.json()
                except Exception:
                    pass

                try:
                    response, _ = _traced_get(client, "/api/decisions")
                    if response.status_code == 200:
                        state.decisions = response.json()
                except Exception:
                    pass

                try:
                    response, _ = _traced_get(client, "/api/tasks")
                    if response.status_code == 200:
                        data = response.json()
                        # Handle paginated response (EPIC-DR-003)
                        if isinstance(data, dict) and "items" in data:
                            state.tasks = data["items"]
                            state.tasks_pagination = data.get("pagination", {})
                        else:
                            # Backward compatibility: direct array
                            state.tasks = data
                except Exception:
                    pass

                try:
                    response, _ = _traced_get(client, "/api/sessions")
                    if response.status_code == 200:
                        state.sessions = response.json()
                except Exception:
                    pass

                try:
                    response, _ = _traced_get(client, "/api/agents")
                    if response.status_code == 200:
                        state.agents = response.json()
                except Exception:
                    pass

            state.is_loading = False
            state.status_message = "Data refreshed from API"
        except Exception as e:
            state.is_loading = False
            state.status_message = f"Using cached data (API unavailable: {str(e)})"

    @ctrl.trigger("load_trust_data")
    def trigger_load_trust_data():
        """Trigger for loading trust data."""
        load_trust_data()

    @ctrl.trigger("load_monitor_data")
    def trigger_load_monitor_data():
        """Trigger for loading monitor data."""
        load_monitor_data()

    @ctrl.trigger("refresh_backlog")
    def refresh_backlog():
        """Refresh backlog data."""
        load_backlog_data()

    @ctrl.trigger("load_executive_report")
    def trigger_load_executive_report():
        """Trigger to load executive report."""
        load_executive_report_data()

    def load_infra_status():
        """Load infrastructure health status. Per GAP-INFRA-004."""
        import json
        import os
        import socket
        import subprocess
        from pathlib import Path
        from datetime import datetime

        # Detect if running in container (GAP-UI-EXP-006 fix)
        in_container = os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv")

        def check_port(hostname: str, port: int) -> bool:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((hostname, port))
                sock.close()
                return result == 0
            except Exception:
                return False

        def check_podman() -> bool:
            if in_container:
                # In container, if we're running, podman must be OK
                return True
            try:
                result = subprocess.run(
                    ["podman", "info"],
                    capture_output=True, timeout=2
                )
                return result.returncode == 0
            except Exception:
                return False

        # Service config: (container_host, container_port, host_port)
        # In container: use compose service names + internal ports
        # On host: use localhost + mapped ports
        service_config = {
            "typedb": ("typedb", 1729, 1729),
            "chromadb": ("chromadb", 8000, 8001),  # internal 8000, mapped to 8001
            "litellm": ("litellm", 4000, 4000),
            "ollama": ("ollama", 11434, 11434),
        }

        # Check services using appropriate hostname/port
        podman_ok = check_podman()
        services = {"podman": {"status": "OK" if podman_ok else "DOWN", "ok": podman_ok}}

        for name, (container_host, container_port, host_port) in service_config.items():
            if in_container:
                ok = check_port(container_host, container_port)
            else:
                ok = check_port("localhost", host_port)

            # TypeDB/ChromaDB are required, LiteLLM/Ollama are optional
            required = name in ("typedb", "chromadb")
            status = "OK" if ok else ("DOWN" if required else "OFF")
            services[name] = {"status": status, "ok": ok, "port": host_port}
        state.infra_services = services

        # Load stats from healthcheck state
        state_file = Path(__file__).parent.parent.parent.parent / ".claude/hooks/.healthcheck_state.json"
        stats = {"memory_pct": 0, "python_procs": 0, "frankel_hash": "--------", "last_check": "Never"}
        try:
            if state_file.exists():
                with open(state_file) as f:
                    hc_state = json.load(f)
                stats["frankel_hash"] = hc_state.get("master_hash", "--------")
                stats["last_check"] = hc_state.get("last_check", "Never")[:19]
        except Exception:
            pass

        # Get memory usage
        try:
            with open("/proc/meminfo") as f:
                meminfo = f.read()
            total = int([l for l in meminfo.split("\n") if "MemTotal" in l][0].split()[1])
            avail = int([l for l in meminfo.split("\n") if "MemAvailable" in l][0].split()[1])
            stats["memory_pct"] = round((total - avail) / total * 100, 1)
        except Exception:
            pass

        # Count python processes
        try:
            result = subprocess.run(["pgrep", "-c", "python3"], capture_output=True, text=True, timeout=2)
            stats["python_procs"] = int(result.stdout.strip() or "0")
        except Exception:
            pass

        state.infra_stats = stats
        state.infra_loading = False

    @ctrl.trigger("load_infra_status")
    def trigger_load_infra_status():
        """Trigger for loading infrastructure status."""
        state.infra_loading = True
        load_infra_status()

    @ctrl.trigger("start_service")
    def start_service(service: str):
        """Start a specific service. Per GAP-INFRA-004."""
        import subprocess
        try:
            subprocess.Popen(
                ["podman", "compose", "--profile", "cpu", "up", "-d", service],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            state.infra_last_action = f"Starting {service}... (refresh in 10s)"
        except Exception as e:
            state.infra_last_action = f"Failed to start {service}: {e}"

    @ctrl.trigger("start_all_services")
    def start_all_services():
        """Start all services. Per GAP-INFRA-004."""
        import subprocess
        try:
            subprocess.Popen(
                ["podman", "compose", "--profile", "cpu", "up", "-d"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            state.infra_last_action = "Starting all services... (refresh in 30s)"
        except Exception as e:
            state.infra_last_action = f"Failed to start services: {e}"

    @ctrl.trigger("restart_stack")
    def restart_stack():
        """Restart the entire stack. Per GAP-INFRA-004."""
        import subprocess
        try:
            subprocess.Popen(
                ["podman", "compose", "--profile", "cpu", "restart"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            state.infra_last_action = "Restarting stack... (refresh in 60s)"
        except Exception as e:
            state.infra_last_action = f"Failed to restart stack: {e}"

    @ctrl.trigger("cleanup_zombies")
    def cleanup_zombies():
        """Cleanup zombie MCP processes. Per GAP-INFRA-004."""
        import subprocess
        try:
            subprocess.run(
                ["pkill", "-9", "-f", "governance.mcp_server"],
                capture_output=True, timeout=5
            )
            state.infra_last_action = "Cleaned up zombie MCP processes"
        except Exception as e:
            state.infra_last_action = f"Cleanup failed: {e}"

    def load_workflow_status():
        """Load workflow compliance status. Per RD-WORKFLOW Phase 4."""
        from pathlib import Path
        import sys

        project_root = Path(__file__).parent.parent.parent.parent
        # Import workflow_checker module
        try:
            import importlib.util
            checker_path = project_root / ".claude" / "hooks" / "checkers" / "workflow_checker.py"
            spec = importlib.util.spec_from_file_location("workflow_checker", checker_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            compliance = module.check_workflow_compliance(project_root)

            state.workflow_status = {
                'overall': compliance.get('overall_status', 'UNKNOWN'),
                'passed': compliance.get('checks_passed', 0),
                'failed': compliance.get('checks_failed', 0),
                'warnings': compliance.get('checks_warning', 0),
            }

            # Build checks list for table
            checks = []
            for v in compliance.get('violations', []):
                checks.append({
                    'rule_id': v.get('rule_id', ''),
                    'check_name': v.get('check_name', ''),
                    'status': 'FAIL',
                    'message': v.get('message', '')
                })
            for w in compliance.get('warnings', []):
                checks.append({
                    'rule_id': w.get('rule_id', ''),
                    'check_name': w.get('check_name', ''),
                    'status': 'WARNING',
                    'message': w.get('message', '')
                })
            state.workflow_checks = checks

            state.workflow_violations = compliance.get('violations', [])
            state.workflow_recommendations = compliance.get('recommendations', [])

        except Exception as e:
            print(f"Error loading workflow status: {e}")
            state.workflow_status = {'overall': 'ERROR', 'passed': 0, 'failed': 0, 'warnings': 0}
            state.workflow_checks = []
            state.workflow_violations = []
            state.workflow_recommendations = [str(e)]

        state.workflow_loading = False

    @ctrl.trigger("load_workflow_status")
    def trigger_load_workflow_status():
        """Trigger for loading workflow status."""
        state.workflow_loading = True
        load_workflow_status()

    # =========================================================================
    # AUDIT TRAIL DATA LOADER (RD-DEBUG-AUDIT Phase 4)
    # =========================================================================

    def load_audit_trail():
        """Load audit trail data from API. Per RD-DEBUG-AUDIT Phase 4."""
        import os
        import httpx

        api_url = os.getenv('GOVERNANCE_API_URL', 'http://localhost:8082')

        try:
            # Get audit summary
            summary_response = httpx.get(f"{api_url}/api/audit/summary", timeout=10.0)
            if summary_response.status_code == 200:
                state.audit_summary = summary_response.json()

            # Build query params from filters
            params = {'limit': 50}
            if state.audit_filter_entity_type:
                params['entity_type'] = state.audit_filter_entity_type
            if state.audit_filter_action_type:
                params['action_type'] = state.audit_filter_action_type
            if state.audit_filter_entity_id:
                params['entity_id'] = state.audit_filter_entity_id
            if state.audit_filter_correlation_id:
                params['correlation_id'] = state.audit_filter_correlation_id

            # Get audit entries
            entries_response = httpx.get(f"{api_url}/api/audit", params=params, timeout=10.0)
            if entries_response.status_code == 200:
                entries = entries_response.json()
                # Format applied_rules for display
                for entry in entries:
                    if isinstance(entry.get('applied_rules'), list):
                        entry['applied_rules'] = ', '.join(entry['applied_rules'])
                state.audit_entries = entries

        except Exception as e:
            print(f"Error loading audit trail: {e}")
            state.audit_summary = {'total_entries': 0, 'by_action_type': {}, 'by_entity_type': {}, 'by_actor': {}, 'retention_days': 7, 'error': str(e)}
            state.audit_entries = []

        state.audit_loading = False

    @ctrl.trigger("load_audit_trail")
    def trigger_load_audit_trail():
        """Trigger for loading audit trail."""
        state.audit_loading = True
        load_audit_trail()

    # Return loaders for internal use
    return {
        'load_trust_data': load_trust_data,
        'load_monitor_data': load_monitor_data,
        'load_backlog_data': load_backlog_data,
        'load_executive_report_data': load_executive_report_data,
        'load_infra_status': load_infra_status,
        'load_workflow_status': load_workflow_status,
        'load_audit_trail': load_audit_trail,
    }
