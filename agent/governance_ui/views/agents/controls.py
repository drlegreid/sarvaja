"""
Agent Control Actions Component.

Per RULE-012: Single Responsibility - only agent control actions UI.
Per RULE-032: File size limit (<300 lines).
Per PLAN-UI-OVERHAUL-001 Task 3.2: Agent Stop/Control.
"""

from trame.widgets import vuetify3 as v3, html


def build_agent_controls_card() -> None:
    """Build agent control actions card with stop, end session, and pause buttons."""
    with v3.VCard(
        variant="outlined",
        classes="mt-4",
        __properties=["data-testid"],
        **{"data-testid": "agent-controls"}
    ):
        with v3.VCardTitle(classes="d-flex align-center", density="compact"):
            v3.VIcon("mdi-cog", size="small", classes="mr-2")
            html.Span("Agent Controls")
        with v3.VCardText():
            with html.Div(classes="d-flex flex-wrap ga-2"):
                # Stop active task
                v3.VBtn(
                    "Stop Task",
                    color="error",
                    variant="outlined",
                    prepend_icon="mdi-stop-circle",
                    disabled=(
                        "!selected_agent.active_tasks || "
                        "selected_agent.active_tasks.length === 0"
                    ),
                    click=(
                        "trigger('stop_agent_task', "
                        "[selected_agent.agent_id || selected_agent.id])"
                    ),
                    __properties=["data-testid"],
                    **{"data-testid": "agent-stop-task-btn"}
                )
                # End active session
                v3.VBtn(
                    "End Session",
                    color="warning",
                    variant="outlined",
                    prepend_icon="mdi-close-circle",
                    disabled=(
                        "!selected_agent.recent_sessions || "
                        "selected_agent.recent_sessions.length === 0"
                    ),
                    click=(
                        "trigger('end_agent_session', "
                        "[selected_agent.agent_id || selected_agent.id])"
                    ),
                    __properties=["data-testid"],
                    **{"data-testid": "agent-end-session-btn"}
                )
                # Pause agent toggle
                v3.VBtn(
                    v_text=(
                        "selected_agent.status === 'PAUSED' ? "
                        "'Resume Agent' : 'Pause Agent'"
                    ),
                    v_bind_color=(
                        "selected_agent.status === 'PAUSED' ? "
                        "'success' : 'info'"
                    ),
                    variant="outlined",
                    v_bind_prepend_icon=(
                        "selected_agent.status === 'PAUSED' ? "
                        "'mdi-play-circle' : 'mdi-pause-circle'"
                    ),
                    click=(
                        "trigger('toggle_agent_pause', "
                        "[selected_agent.agent_id || selected_agent.id])"
                    ),
                    __properties=["data-testid"],
                    **{"data-testid": "agent-pause-btn"}
                )
