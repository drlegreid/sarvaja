"""
Trame UI for Sarvaja Agent Platform
====================================
Functional Python-based UI using Trame framework.

Per DECISION: Use Trame for Python-native web UI
Per RULE-019: UI/UX Design Standards

Dependencies:
    pip install trame trame-vuetify trame-client
"""

import json
import threading

from trame.app import get_server
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import vuetify3 as v3, html


# =============================================================================
# TRAME APPLICATION
# =============================================================================

class SarvajaTrameUI:
    """
    Trame-based UI for Sarvaja agent platform.

    Features:
    - Task submission form
    - Real-time event streaming (AG-UI)
    - Task history list
    - Agent selection
    """

    def __init__(self, agents: dict, api_base: str = "http://localhost:7777"):
        """
        Initialize Trame UI.

        Args:
            agents: Dict of available agents by name
            api_base: Base URL for API calls
        """
        self.agents = agents
        self.api_base = api_base
        self.server = get_server(client_type="vue3")
        self.state = self.server.state
        self.ctrl = self.server.controller

        # Initialize state
        self.state.agent_options = [
            {"title": name, "value": name}
            for name in agents.keys()
        ]
        self.state.selected_agent = list(agents.keys())[0] if agents else ""
        self.state.prompt = ""
        self.state.events = []
        self.state.tasks = []
        self.state.current_task_id = None
        self.state.status = "Ready"
        self.state.is_loading = False

        # Build UI
        self._build_ui()

    def _build_ui(self):
        """Build Trame UI layout."""
        with VAppLayout(self.server, full_height=True) as layout:
            # App bar
            with v3.VAppBar(color="primary", density="compact"):
                v3.VAppBarTitle("Sarvaja Task Console")
                v3.VSpacer()
                v3.VChip(
                    "{{ status }}",
                    color="success" if "Ready" else "warning",
                    size="small",
                )

            # Main content
            with v3.VMain():
                with v3.VContainer(fluid=True, classes="fill-height"):
                    with v3.VRow(classes="fill-height"):
                        # Left column: Task input
                        with v3.VCol(cols=6):
                            self._build_task_form()
                            self._build_task_list()

                        # Right column: Event stream
                        with v3.VCol(cols=6):
                            self._build_event_stream()

    def _build_task_form(self):
        """Build task submission form."""
        with v3.VCard(title="New Task", classes="mb-4"):
            with v3.VCardText():
                # Agent selector
                v3.VSelect(
                    label="Agent",
                    v_model=("selected_agent",),
                    items=("agent_options",),
                    density="compact",
                )

                # Prompt textarea
                v3.VTextarea(
                    label="Task Prompt",
                    v_model=("prompt",),
                    rows=4,
                    placeholder="Describe your task...",
                )

            with v3.VCardActions():
                v3.VSpacer()
                v3.VBtn(
                    "Submit Task",
                    color="primary",
                    loading=("is_loading",),
                    disabled=("is_loading",),
                    click=self.submit_task,
                )

    def _build_task_list(self):
        """Build task history list."""
        with v3.VCard(title="Recent Tasks"):
            with v3.VCardText():
                with v3.VList(density="compact"):
                    with v3.VListItem(
                        v_for="task in tasks",
                        key="task.task_id",
                        click=lambda task: self.select_task(task["task_id"]),
                        active=("task.task_id === current_task_id",),
                    ):
                        with v3.VListItemTitle():
                            html.Span("{{ task.task_id }}", classes="font-weight-medium")
                        with v3.VListItemSubtitle():
                            html.Span("{{ task.prompt.substring(0, 50) }}...")
                        with html.Template(v_slot_append=True):
                            v3.VChip(
                                "{{ task.status }}",
                                size="x-small",
                                color="success" if "task.status === 'completed'" else (
                                    "error" if "task.status === 'failed'" else "warning"
                                ),
                            )

    def _build_event_stream(self):
        """Build event stream panel."""
        with v3.VCard(title="Event Stream", classes="fill-height"):
            with v3.VCardText(classes="overflow-y-auto", style="max-height: 600px"):
                with v3.VTimeline(density="compact", side="end"):
                    with v3.VTimelineItem(
                        v_for="(event, index) in events",
                        key="index",
                        dot_color="primary" if "event.type === 'RUN_STARTED'" else (
                            "success" if "event.type === 'TEXT_MESSAGE'" else (
                                "error" if "event.type === 'RUN_ERROR'" else "grey"
                            )
                        ),
                        size="small",
                    ):
                        with v3.VCard(density="compact"):
                            with v3.VCardTitle(classes="text-subtitle-2"):
                                html.Span("{{ event.type }}")
                            with v3.VCardText(classes="text-body-2"):
                                html.Pre(
                                    "{{ formatEventData(event) }}",
                                    style="white-space: pre-wrap; font-size: 0.75rem;",
                                )

            with v3.VCardActions():
                v3.VSpacer()
                v3.VBtn(
                    "Clear",
                    variant="text",
                    size="small",
                    click=self.clear_events,
                )

    # =========================================================================
    # CONTROLLER METHODS
    # =========================================================================

    @property
    def submit_task(self):
        """Submit task controller."""
        @self.ctrl.trigger("submit_task")
        def _submit_task():
            if not self.state.prompt:
                return

            self.state.is_loading = True
            self.state.status = "Submitting..."

            try:
                import requests
                response = requests.post(
                    f"{self.api_base}/tasks",
                    json={
                        "prompt": self.state.prompt,
                        "agent": self.state.selected_agent,
                    },
                    timeout=30,
                )

                if response.ok:
                    result = response.json()
                    self.state.current_task_id = result["task_id"]
                    self.state.prompt = ""
                    self.state.status = "Task submitted"
                    self._start_event_stream(result["task_id"])
                    self._refresh_tasks()
                else:
                    self.state.status = f"Error: {response.text}"

            except Exception as e:
                self.state.status = f"Error: {e}"
            finally:
                self.state.is_loading = False

        return _submit_task

    def select_task(self, task_id: str):
        """Select task and start streaming events."""
        self.state.current_task_id = task_id
        self.state.events = []
        self._start_event_stream(task_id)

    @property
    def clear_events(self):
        """Clear events controller."""
        @self.ctrl.trigger("clear_events")
        def _clear():
            self.state.events = []

        return _clear

    def _start_event_stream(self, task_id: str):
        """Start SSE event stream for task."""
        def stream():
            try:
                import requests
                with requests.get(
                    f"{self.api_base}/tasks/{task_id}/events",
                    stream=True,
                    timeout=120,
                ) as response:
                    for line in response.iter_lines():
                        if line:
                            line = line.decode("utf-8")
                            if line.startswith("data: "):
                                event_data = json.loads(line[6:])
                                self.state.events = self.state.events + [event_data]

                                if event_data.get("type") in ("RUN_FINISHED", "RUN_ERROR"):
                                    self.state.status = "Complete"
                                    self._refresh_tasks()
                                    break
            except Exception as e:
                self.state.status = f"Stream error: {e}"

        # Run in background thread
        thread = threading.Thread(target=stream, daemon=True)
        thread.start()

    def _refresh_tasks(self):
        """Refresh task list."""
        try:
            import requests
            response = requests.get(f"{self.api_base}/tasks", timeout=30)
            if response.ok:
                self.state.tasks = response.json()[:10]
        except Exception as e:
            print(f"Failed to refresh tasks: {e}")

    def run(self, port: int = 8080):
        """Run Trame server."""
        self.server.start(port=port, open_browser=True)


# =============================================================================
# STANDALONE LAUNCHER
# =============================================================================

def create_trame_app(agents: dict = None, api_base: str = "http://localhost:7777"):
    """
    Factory function to create Trame app.

    Args:
        agents: Dict of agents (uses defaults if None)
        api_base: API base URL

    Returns:
        SarvajaTrameUI instance
    """
    if agents is None:
        agents = {
            "orchestrator": "Task Orchestrator",
            "researcher": "Research Agent",
            "coder": "Code Agent",
            "rules_curator": "Rules Curator",
            "simple_assistant": "Local Assistant",
        }

    return SarvajaTrameUI(agents=agents, api_base=api_base)


def main():
    """Run Trame UI standalone."""
    import argparse

    parser = argparse.ArgumentParser(description="Sarvaja Trame UI")
    parser.add_argument("--port", type=int, default=8080, help="UI port")
    parser.add_argument("--api", type=str, default="http://localhost:7777", help="API base URL")
    args = parser.parse_args()

    print(f"Starting Sarvaja Trame UI on port {args.port}")
    print(f"API endpoint: {args.api}")

    app = create_trame_app(api_base=args.api)
    app.run(port=args.port)


# Backward compatibility alias (DECISION-008: Sim.ai → Sarvaja rename)
SimAITrameUI = SarvajaTrameUI


if __name__ == "__main__":
    main()
