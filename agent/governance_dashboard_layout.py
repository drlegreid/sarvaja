"""
Dashboard Layout Builder.

Per DOC-SIZE-01-v1: Extracted from governance_dashboard.py (522 lines).
Builds the complete Trame VAppLayout with app bar, nav, views, dialogs.
"""

from shared.constants import APP_TITLE

from agent.governance_ui.views import (
    build_rules_view,
    build_tasks_view,
    build_sessions_view,
    build_agents_view,
    build_decisions_view,
    build_executive_view,
    build_chat_view,
    build_backlog_view,
    build_monitor_view,
    build_trust_view,
    build_search_view,
    build_impact_view,
    build_infra_view,
    build_workflow_view,
    build_audit_view,
    build_tests_view,
    build_metrics_view,
    build_projects_view,
    build_trace_bar,
    build_all_dialogs,
)


def build_dashboard_layout(server, navigation_items):
    """Build the complete dashboard VAppLayout.

    Creates app bar, navigation drawer, main content with all views,
    shared dialogs, loading overlay, error banner, and trace bar.

    Args:
        server: Trame server instance
        navigation_items: List of nav item dicts with title/icon/value
    """
    from trame.ui.vuetify3 import VAppLayout
    from trame.widgets import vuetify3 as v3, html

    with VAppLayout(
        server,
        full_height=True,
        theme=("dark_mode ? 'dark' : 'light'",)
    ):
        # Inject mermaid.js for diagram rendering (RULE-039)
        from agent.governance_ui.components.mermaid import inject_mermaid_script
        inject_mermaid_script()

        # Inject window state isolator (GAP-UI-AUDIT-002: Option C)
        from agent.governance_ui.components.window_state import inject_window_state_isolator
        inject_window_state_isolator()

        # Inject list styles (UI-LIST-01)
        from agent.governance_ui.components.list_styles import inject_list_styles
        inject_list_styles()

        # App bar
        with v3.VAppBar(
            color="deep-purple",
            density="compact",
            __properties=["data-testid"],
            **{"data-testid": "app-bar"}
        ):
            v3.VAppBarTitle(APP_TITLE)
            v3.VSpacer()
            v3.VChip(
                "{{ rules.length }} Rules",
                size="small",
                color="white",
                variant="outlined",
                click="active_view = 'rules'",
                style="cursor: pointer;",
                __properties=["data-testid"],
                **{"data-testid": "toolbar-rules-chip"}
            )
            v3.VChip(
                "{{ decisions.length }} Decisions",
                size="small",
                color="white",
                variant="outlined",
                click="active_view = 'decisions'",
                style="cursor: pointer;",
                classes="ml-1",
                __properties=["data-testid"],
                **{"data-testid": "toolbar-decisions-chip"}
            )
            v3.VChip(
                "{{ '#' + ((infra_stats && infra_stats.frankel_hash) || '').substring(0, 8) }}",
                v_if="infra_stats && infra_stats.frankel_hash",
                size="small",
                variant="outlined",
                prepend_icon=(
                    "infra_stats.status === 'healthy' ? 'mdi-shield-check' : "
                    "infra_stats.status === 'degraded' ? 'mdi-shield-alert' : "
                    "'mdi-shield-off'",
                ),
                click="active_view = 'infra'",
                style="cursor: pointer;",
                classes="ml-1",
                color=(
                    "infra_stats.status === 'healthy' ? '#4caf50' : "
                    "infra_stats.status === 'degraded' ? '#ff9800' : "
                    "'#f44336'",
                ),
                title=(
                    "'Health: ' + (infra_stats.status || 'unknown') + "
                    "' | Last: ' + (infra_stats.last_check || 'Never')",
                ),
                __properties=["data-testid"],
                **{"data-testid": "toolbar-health-chip"}
            )
            v3.VBtn(
                icon="mdi-refresh",
                variant="text",
                click="trigger('refresh_data')",
                title="Refresh data from API",
                __properties=["data-testid"],
                **{"data-testid": "refresh-btn"}
            )
            # Dark mode toggle (GAP-UI-DARK-THEME)
            v3.VSwitch(
                v_model="dark_mode",
                prepend_icon="mdi-theme-light-dark",
                hide_details=True,
                density="compact",
                color="white",
                __properties=["data-testid"],
                **{"data-testid": "dark-mode-toggle"}
            )

        # Navigation drawer
        with v3.VNavigationDrawer(
            permanent=True,
            rail=True,
            __properties=["data-testid"],
            **{"data-testid": "nav-drawer"}
        ):
            with v3.VList(nav=True, density="compact"):
                for item in navigation_items:
                    v3.VListItem(
                        title=item['title'],
                        prepend_icon=item['icon'],
                        value=item['value'],
                        active=(f"active_view === '{item['value']}'",),
                        click=f"active_view = '{item['value']}'",
                        __properties=["data-testid"],
                        **{"data-testid": f"nav-{item['value']}"}
                    )

        # Main content
        with v3.VMain():
            with v3.VContainer(fluid=True, classes="fill-height pa-4"):
                build_rules_view()
                build_tasks_view()
                build_sessions_view()
                build_decisions_view()
                build_agents_view()
                build_executive_view()
                build_chat_view()
                build_backlog_view()
                build_monitor_view()
                build_trust_view()
                build_search_view()
                build_impact_view()
                build_infra_view()
                build_workflow_view()
                build_audit_view()
                build_tests_view()
                build_metrics_view()
                build_projects_view()

            build_all_dialogs()

        # Loading overlay (GAP-UI-005)
        with v3.VOverlay(
            v_model="is_loading",
            persistent=True,
            classes="align-center justify-center",
            __properties=["data-testid"],
            **{"data-testid": "loading-overlay"}
        ):
            v3.VProgressCircular(
                indeterminate=True,
                size=64,
                __properties=["data-testid"],
                **{"data-testid": "loading-spinner"}
            )

        # Error banner (GAP-UI-005)
        v3.VSnackbar(
            v_model="has_error",
            color="error",
            timeout=5000,
            __properties=["data-testid"],
            **{"data-testid": "error-banner"}
        )

        # Confirm dialog
        with v3.VDialog(
            v_model="show_confirm",
            max_width=400,
            __properties=["data-testid"],
            **{"data-testid": "confirm-dialog"}
        ):
            with v3.VCard():
                v3.VCardTitle("Confirm Action")
                v3.VCardText("{{ confirm_message }}")
                with v3.VCardActions():
                    v3.VSpacer()
                    v3.VBtn(
                        "No",
                        variant="text",
                        click="show_confirm = false",
                        __properties=["data-testid"],
                        **{"data-testid": "confirm-no"}
                    )
                    v3.VBtn(
                        "Yes",
                        color="primary",
                        click="confirm_action(); show_confirm = false",
                        __properties=["data-testid"],
                        **{"data-testid": "confirm-yes"}
                    )

        # Trace bar (GAP-UI-048)
        build_trace_bar()
