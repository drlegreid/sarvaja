"""
Monitor View for Governance Dashboard.

Per RULE-012: Single Responsibility - only real-time monitoring UI.
Per RULE-021: MCP Healthcheck Protocol.
Per GAP-FILE-001: Modularization of governance_dashboard.py.

Extracted from governance_dashboard.py lines 1892-2101.
"""

from trame.widgets import vuetify3 as v3, html


def build_monitor_header() -> None:
    """Build monitor header with filters and controls."""
    with v3.VCardTitle(classes="d-flex align-center"):
        html.Span("Real-time Rule Monitoring")
        v3.VSpacer()
        # Event type filter
        v3.VSelect(
            v_model="monitor_filter",
            items=[
                'rule_query', 'rule_change', 'violation',
                'compliance_check', 'trust_decrease', 'trust_increase'
            ],
            label="Event Type",
            variant="outlined",
            density="compact",
            hide_details=True,
            clearable=True,
            style="max-width: 180px; margin-right: 8px",
            change="filter_monitor_events($event)",
            __properties=["data-testid"],
            **{"data-testid": "monitor-filter"}
        )
        # Auto-refresh toggle
        v3.VBtn(
            icon=("auto_refresh ? 'mdi-pause-circle' : 'mdi-play-circle'",),
            variant="outlined",
            size="small",
            click="trigger('toggle_auto_refresh')",
            title=("auto_refresh ? 'Pause auto-refresh' : 'Start auto-refresh'",),
            classes="mr-2",
            __properties=["data-testid"],
            **{"data-testid": "monitor-auto-refresh"}
        )
        v3.VBtn(
            "Refresh",
            prepend_icon="mdi-refresh",
            variant="outlined",
            size="small",
            click="trigger('load_monitor_data')",
            __properties=["data-testid"],
            **{"data-testid": "monitor-refresh-btn"}
        )


def build_monitor_stats() -> None:
    """Build monitor stats cards row."""
    with v3.VRow():
        # Total Events
        with v3.VCol(cols=3):
            with v3.VCard(
                variant="tonal",
                color="info",
                __properties=["data-testid"],
                **{"data-testid": "monitor-stat-total"}
            ):
                with v3.VCardText(classes="text-center"):
                    html.Div(
                        "{{ monitor_stats.total_events || 0 }}",
                        classes="text-h4 font-weight-bold"
                    )
                    html.Div("Total Events", classes="text-subtitle-2")
        # Active Alerts
        with v3.VCol(cols=3):
            with v3.VCard(
                variant="tonal",
                color="error",
                __properties=["data-testid"],
                **{"data-testid": "monitor-stat-alerts"}
            ):
                with v3.VCardText(classes="text-center"):
                    html.Div(
                        "{{ monitor_alerts.length || 0 }}",
                        classes="text-h4 font-weight-bold"
                    )
                    html.Div("Active Alerts", classes="text-subtitle-2")
        # Violations
        with v3.VCol(cols=3):
            with v3.VCard(
                variant="tonal",
                color="warning",
                __properties=["data-testid"],
                **{"data-testid": "monitor-stat-violations"}
            ):
                with v3.VCardText(classes="text-center"):
                    html.Div(
                        "{{ (monitor_stats.events_by_type && monitor_stats.events_by_type.violation) || 0 }}",
                        classes="text-h4 font-weight-bold"
                    )
                    html.Div("Violations", classes="text-subtitle-2")
        # Compliance Checks
        with v3.VCol(cols=3):
            with v3.VCard(
                variant="tonal",
                color="success",
                __properties=["data-testid"],
                **{"data-testid": "monitor-stat-compliance"}
            ):
                with v3.VCardText(classes="text-center"):
                    html.Div(
                        "{{ (monitor_stats.events_by_type && monitor_stats.events_by_type.compliance_check) || 0 }}",
                        classes="text-h4 font-weight-bold"
                    )
                    html.Div("Compliance Checks", classes="text-subtitle-2")


def build_event_feed() -> None:
    """Build event feed panel."""
    with v3.VCol(cols=8):
        with v3.VCard(
            variant="outlined",
            __properties=["data-testid"],
            **{"data-testid": "monitor-feed"}
        ):
            v3.VCardTitle("Event Feed")
            with v3.VCardText(style="max-height: 400px; overflow-y: auto;"):
                with v3.VList(density="compact"):
                    with v3.VListItem(
                        v_for="event in monitor_feed",
                        key=("event.event_id",),
                        __properties=["data-testid"],
                        **{"data-testid": "monitor-event-item"}
                    ):
                        with html.Template(v_slot_prepend=True):
                            v3.VIcon(
                                icon=(
                                    "event.event_type === 'rule_query' ? 'mdi-magnify' : "
                                    "event.event_type === 'rule_change' ? 'mdi-pencil' : "
                                    "event.event_type === 'violation' ? 'mdi-alert-circle' : "
                                    "event.event_type === 'compliance_check' ? 'mdi-check-circle' : "
                                    "event.event_type === 'trust_decrease' ? 'mdi-arrow-down' : "
                                    "'mdi-arrow-up'"
                                ),
                                color=(
                                    "event.event_type === 'violation' ? 'error' : "
                                    "event.event_type === 'rule_change' ? 'warning' : "
                                    "event.event_type === 'trust_decrease' ? 'warning' : "
                                    "event.event_type === 'trust_increase' ? 'success' : "
                                    "event.event_type === 'compliance_check' ? 'success' : 'info'"
                                ),
                                size="small",
                            )
                        with html.Template(v_slot_default=True):
                            v3.VListItemTitle("{{ event.source }}")
                            v3.VListItemSubtitle(
                                "{{ event.event_type }} - {{ event.timestamp }}"
                            )
                        with html.Template(v_slot_append=True):
                            v3.VChip(
                                v_text="event.severity",
                                color=(
                                    "event.severity === 'CRITICAL' ? 'error' : "
                                    "event.severity === 'WARNING' ? 'warning' : 'info'"
                                ),
                                size="x-small",
                            )
                    # Empty state
                    v3.VListItem(
                        v_if="!monitor_feed || monitor_feed.length === 0",
                        title="No events recorded",
                        prepend_icon="mdi-information-outline",
                        disabled=True,
                    )


def build_alerts_panel() -> None:
    """Build alerts panel."""
    with v3.VCol(cols=4):
        with v3.VCard(
            variant="outlined",
            color=("monitor_alerts && monitor_alerts.length > 0 ? 'error' : ''",),
            __properties=["data-testid"],
            **{"data-testid": "monitor-alerts"}
        ):
            v3.VCardTitle("Active Alerts")
            with v3.VCardText(style="max-height: 400px; overflow-y: auto;"):
                with v3.VList(density="compact"):
                    with v3.VListItem(
                        v_for="alert in monitor_alerts",
                        key=("alert.alert_id",),
                        __properties=["data-testid"],
                        **{"data-testid": "monitor-alert-item"}
                    ):
                        with html.Template(v_slot_prepend=True):
                            v3.VIcon(
                                icon="mdi-alert",
                                color=("alert.severity === 'CRITICAL' ? 'error' : 'warning'",),
                            )
                        with html.Template(v_slot_default=True):
                            v3.VListItemTitle("{{ alert.message || alert.alert_id }}")
                            v3.VListItemSubtitle(
                                "{{ alert.severity }} - {{ alert.timestamp }}"
                            )
                        with html.Template(v_slot_append=True):
                            v3.VBtn(
                                icon="mdi-check",
                                size="x-small",
                                variant="text",
                                color="success",
                                click="acknowledge_alert(alert.alert_id)",
                                title="Acknowledge",
                            )
                    # Empty state
                    v3.VListItem(
                        v_if="!monitor_alerts || monitor_alerts.length === 0",
                        title="No active alerts",
                        prepend_icon="mdi-check-circle",
                        disabled=True,
                    )


def build_top_rules_section() -> None:
    """Build top monitored rules section."""
    with v3.VRow(classes="mt-4"):
        with v3.VCol(cols=12):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "monitor-top-rules"}
            ):
                v3.VCardTitle("Most Active Rules")
                with v3.VCardText():
                    with v3.VChipGroup():
                        v3.VChip(
                            v_for="rule in top_rules",
                            key=("rule.rule_id",),
                            v_text="rule.rule_id + ' (' + rule.event_count + ')'",
                            color="primary",
                            variant="outlined",
                            size="small",
                        )
                        # Empty state
                        html.Span(
                            v_if="!top_rules || top_rules.length === 0",
                            classes="text-grey",
                        ).__setattr__("innerHTML", "No rule activity recorded yet")


def build_monitor_view() -> None:
    """
    Build the Real-time Rule Monitoring view.

    This is the main entry point for the monitor view module.
    Per RULE-021: MCP Healthcheck Protocol.
    Per P9.6: Real-time Monitoring implementation.
    """
    with v3.VCard(
        v_if="active_view === 'monitor'",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "monitor-dashboard"}
    ):
        build_monitor_header()

        with v3.VCardText():
            # Stats cards row
            build_monitor_stats()

            # Main content: Event feed and Alerts
            with v3.VRow(classes="mt-4"):
                build_event_feed()
                build_alerts_panel()

            # Top monitored rules
            build_top_rules_section()
