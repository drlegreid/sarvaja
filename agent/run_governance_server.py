"""
Combined Governance Server - API + Dashboard
Per RULE-019: UI/UX Design Standards
Per GAP-UI-031/032: Replace mock CRUD with real API

Starts:
- FastAPI REST API on port 8082
- Trame Dashboard on port 8081

Created: 2024-12-25
"""

import argparse
import asyncio
import threading
import uvicorn
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run_api_server(port: int = 8082):
    """Run the FastAPI governance API server."""
    from governance.api import app
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


def run_dashboard(port: int = 8081, server_mode: bool = True):
    """Run the Trame governance dashboard."""
    from agent.governance_dashboard import create_governance_dashboard
    dashboard = create_governance_dashboard(port=port)
    server = dashboard.build_ui()
    if server:
        print(f"Starting Governance Dashboard on port {port}")
        # Force IPv4 only to avoid Windows IPv6 binding issues
        server.start(port=port, host="127.0.0.1", open_browser=not server_mode, timeout=0)


def main():
    """Run combined governance server."""
    parser = argparse.ArgumentParser(description="Sim.ai Governance Server (API + Dashboard)")
    parser.add_argument("--api-port", type=int, default=8082, help="API port (default: 8082)")
    parser.add_argument("--ui-port", type=int, default=8081, help="Dashboard port (default: 8081)")
    parser.add_argument("--api-only", action="store_true", help="Run only the API server")
    parser.add_argument("--ui-only", action="store_true", help="Run only the dashboard")
    parser.add_argument("--browser", action="store_true", help="Open browser on dashboard start")
    args = parser.parse_args()

    if args.api_only:
        print(f"Starting Governance API on port {args.api_port}")
        run_api_server(args.api_port)
    elif args.ui_only:
        print(f"Starting Governance Dashboard on port {args.ui_port}")
        run_dashboard(args.ui_port, server_mode=not args.browser)
    else:
        # Run both - API in thread, dashboard in main
        print(f"Starting Governance API on port {args.api_port}")
        api_thread = threading.Thread(
            target=run_api_server,
            args=(args.api_port,),
            daemon=True
        )
        api_thread.start()

        print(f"Starting Governance Dashboard on port {args.ui_port}")
        print(f"API available at: http://localhost:{args.api_port}/api/docs")
        print(f"Dashboard available at: http://localhost:{args.ui_port}")
        run_dashboard(args.ui_port, server_mode=not args.browser)


if __name__ == "__main__":
    main()
