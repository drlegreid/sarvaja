"""
Infrastructure Data Loader Controllers.

Per DOC-SIZE-01-v1: Extracted from data_loaders.py (770→<300 lines).
Per RULE-012: Single Responsibility - only infra data loading triggers.

Provides:
- load_infra_status: Service health, MCP status, system stats
- start_service / start_all_services / restart_stack
- load_container_logs: Podman socket log fetching
- cleanup_zombies: MCP process cleanup
"""

import os
import json
import socket
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Any


def register_infra_loader_controllers(
    state: Any,
    ctrl: Any,
    api_base_url: str
) -> dict:
    """
    Register infrastructure data loading controllers with Trame.

    Returns:
        Dict with 'load_infra_status' loader function.
    """

    def load_infra_status():
        """Load infrastructure health status. Per GAP-INFRA-004."""
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
                return True
            try:
                result = subprocess.run(
                    ["podman", "info"],
                    capture_output=True, timeout=2
                )
                return result.returncode == 0
            except Exception:
                return False

        service_config = {
            "typedb": ("typedb", 1729, 1729),
            "chromadb": ("chromadb", 8000, 8001),
            "litellm": ("litellm", 4000, 4000),
            "ollama": ("ollama", 11434, 11434),
        }

        podman_ok = check_podman()
        services = {"podman": {"status": "OK" if podman_ok else "DOWN", "ok": podman_ok}}

        for name, (container_host, container_port, host_port) in service_config.items():
            if in_container:
                ok = check_port(container_host, container_port)
            else:
                ok = check_port("localhost", host_port)

            required = name in ("typedb", "chromadb")
            status = "OK" if ok else ("DOWN" if required else "OFF")
            services[name] = {"status": status, "ok": ok, "port": host_port}
        state.infra_services = services

        # Load stats from healthcheck state
        state_file = Path(__file__).parent.parent.parent.parent / ".claude/hooks/.healthcheck_state.json"
        stats = {
            "memory_pct": 0,
            "python_procs": 0,
            "frankel_hash": "--------",
            "last_check": "Never",
            "mcp_servers": {}
        }
        try:
            if state_file.exists():
                with open(state_file) as f:
                    hc_state = json.load(f)
                stats["frankel_hash"] = hc_state.get("master_hash", "--------")
                stats["last_check"] = hc_state.get("last_check", "Never")[:19]
                stats["component_hashes"] = hc_state.get("component_hashes", {})
                stats["component_statuses"] = hc_state.get("components", {})
                components = hc_state.get("components", {})
                mcp_names = ["claude-mem", "gov-core", "gov-agents", "gov-sessions", "gov-tasks"]
                for name in mcp_names:
                    if name in components:
                        stats["mcp_servers"][name] = components[name]
                    else:
                        stats["mcp_servers"][name] = "ON-DEMAND"
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

        # Check DSP conditions per SESSION-DSP-NOTIFY-01-v1
        stats["dsp_suggested"] = False
        stats["dsp_alerts"] = []
        try:
            evidence_dir = Path(__file__).parent.parent.parent.parent / "evidence"
            if evidence_dir.exists():
                evidence_count = len(list(evidence_dir.glob("SESSION-*.md")))
                if evidence_count > 20:
                    stats["dsp_alerts"].append(f"Evidence accumulation: {evidence_count} session files")
                dsp_files = sorted(evidence_dir.glob("*DSP*.md"), reverse=True)
                if dsp_files:
                    latest = dsp_files[0].name
                    date_parts = latest.split("-")[1:4]
                    if len(date_parts) == 3:
                        dsp_date = datetime(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))
                        days_since = (datetime.now() - dsp_date).days
                        if days_since > 7:
                            stats["dsp_alerts"].append(f"No DSP cycle in {days_since} days")
                else:
                    stats["dsp_alerts"].append("No DSP cycle found")
            stats["dsp_suggested"] = len(stats["dsp_alerts"]) >= 2
        except Exception:
            pass

        # Load MCP server details from .mcp.json
        try:
            from agent.governance_ui.controllers.infra import get_mcp_server_details
            stats["mcp_details"] = get_mcp_server_details()
        except Exception:
            stats["mcp_details"] = {}

        # Derive overall health status
        required_down = any(
            s.get("status") == "DOWN"
            for name, s in services.items()
            if name in ("podman", "typedb", "chromadb")
        )
        optional_down = any(
            s.get("status") == "OFF"
            for name, s in services.items()
            if name in ("litellm", "ollama")
        )
        if required_down:
            stats["status"] = "down"
        elif optional_down:
            stats["status"] = "degraded"
        else:
            stats["status"] = "healthy"

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
        try:
            subprocess.Popen(
                ["podman", "compose", "--profile", "cpu", "restart"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            state.infra_last_action = "Restarting stack... (refresh in 60s)"
        except Exception as e:
            state.infra_last_action = f"Failed to restart stack: {e}"

    @ctrl.trigger("load_container_logs")
    def load_container_logs(container: str = "dashboard", lines: int = 50, level: str = ""):
        """Load container logs via API endpoint (uses podman socket)."""
        import httpx
        api_url = os.environ.get("GOVERNANCE_API_URL", "http://localhost:8082")
        try:
            resp = httpx.get(
                f"{api_url}/api/infra/logs",
                params={"container": container, "tail": lines, "level": level or ""},
                timeout=10,
            )
            data = resp.json()
            state.infra_log_lines = data.get("lines", ["No logs returned"])
        except Exception as e:
            state.infra_log_lines = [f"Failed to fetch logs: {e}"]
        state.infra_log_container = container

    @ctrl.trigger("cleanup_zombies")
    def cleanup_zombies():
        """Cleanup zombie MCP processes. Per GAP-INFRA-004."""
        try:
            subprocess.run(
                ["pkill", "-9", "-f", "governance.mcp_server"],
                capture_output=True, timeout=5
            )
            state.infra_last_action = "Cleaned up zombie MCP processes"
        except Exception as e:
            state.infra_last_action = f"Cleanup failed: {e}"

    return {'load_infra_status': load_infra_status}
