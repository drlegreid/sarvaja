"""
Governance Dashboard UI (P9.2)
Created: 2024-12-25
Updated: 2024-12-25 (DSP refactor - FP + Digital Twin)

Trame-based dashboard for viewing governance artifacts:
- Rules (22 rules from TypeDB)
- Decisions (strategic decisions)
- Sessions (evidence files)
- Tasks (R&D backlog)

Per RULE-019: UI/UX Design Standards
Per DECISION-003: TypeDB-First Strategy
Per RULE-012: DSP Semantic Code Structure

Structure (per DSP):
    governance_ui/data_access.py - Pure MCP data functions
    governance_ui/state.py       - Immutable state, transforms
    governance_ui.py             - Trame view layer (this file)

Dependencies:
    pip install trame trame-vuetify trame-client
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional, Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# =============================================================================
# IMPORTS FROM governance_ui PACKAGE (DSP: Pure functions)
# =============================================================================
from agent.governance_ui import (
    # Data access (pure functions)
    call_mcp_tool,
    get_rules,
    get_rules_by_category,
    get_decisions,
    get_sessions,
    get_tasks,
    search_evidence,
    filter_rules_by_status,
    filter_rules_by_category,
    filter_rules_by_search,
    sort_rules,
    # Impact analysis (P9.4)
    get_rule_dependencies,
    get_rule_dependents,
    get_rule_conflicts,
    build_dependency_graph,
    calculate_rule_impact,
    generate_mermaid_graph,
    # Agent Trust Dashboard (P9.5)
    get_agents,
    get_proposals,
    get_escalated_proposals,
    build_trust_leaderboard,
    get_governance_stats,
    # Real-time Monitoring (P9.6)
    get_rule_monitor,
    get_monitor_feed,
    get_monitor_alerts,
    get_monitor_stats,
    log_monitor_event,
    acknowledge_monitor_alert,
    get_top_monitored_rules,
    get_hourly_monitor_stats,
    # State constants
    STATUS_COLORS,
    PRIORITY_COLORS,
    CATEGORY_ICONS,
    NAVIGATION_ITEMS,
    RULE_CATEGORIES,
    RULE_PRIORITIES,
    RULE_STATUSES,
    RISK_COLORS,
    TRUST_LEVEL_COLORS,
    PROPOSAL_STATUS_COLORS,
    EVENT_TYPE_COLORS,
    EVENT_TYPE_ICONS,
    SEVERITY_COLORS,
    # State factory
    get_initial_state,
    # Pure transforms
    with_loading,
    with_error,
    clear_error,
    with_status,
    with_active_view,
    with_selected_rule,
    with_rule_form,
    with_filters,
    with_sort,
    with_impact_analysis,
    with_graph_view,
    # Trust dashboard (P9.5)
    with_agents,
    with_selected_agent,
    with_proposals,
    # Monitoring transforms (P9.6)
    with_monitor_feed,
    with_monitor_alerts,
    with_monitor_stats,
    with_monitor_filter,
    with_auto_refresh,
    with_top_rules,
    with_hourly_stats,
    # UI helpers
    get_status_color,
    get_priority_color,
    get_category_icon,
    format_rule_card,
    get_risk_color,
    format_impact_summary,
    # Trust UI helpers (P9.5)
    get_trust_level,
    get_trust_level_color,
    format_agent_card,
    format_proposal_card,
    # Monitoring UI helpers (P9.6)
    get_event_type_color,
    get_event_type_icon,
    get_severity_color,
    format_event_item,
    format_alert_item,
)

# Project paths
EVIDENCE_DIR = PROJECT_ROOT / "evidence"
DOCS_DIR = PROJECT_ROOT / "docs"


class GovernanceDashboard:
    """
    Governance Dashboard for sim-ai platform.

    Thin view layer (per DSP FP + Digital Twin paradigm).
    All data access and state management delegated to governance_ui package.

    Provides UI views for:
    - Rules browser (grouped by category)
    - Decisions viewer
    - Sessions timeline
    - Tasks tracker
    - Evidence search
    """

    def __init__(self, port: int = 8081):
        """
        Initialize Governance Dashboard.

        Args:
            port: Port for Trame server (default 8081)
        """
        self.port = port
        self._server = None
        self._state = None

    # =========================================================================
    # TRAME SERVER
    # =========================================================================

    def build_ui(self):
        """
        Build complete Trame UI layout.

        Per UI-FIRST-SPRINT-WORKFLOW.md: All components have data-testid for POM testing.
        Per RULE-004: Page Object Model (POM) pattern.

        GAPs addressed:
        - GAP-UI-001: data-testid attributes
        - GAP-UI-002: CRUD forms
        - GAP-UI-003: Detail drill-down
        - GAP-UI-006: rule_id column
        - GAP-UI-007: Clickable rows
        """
        try:
            from trame.app import get_server
            from trame.ui.vuetify3 import VAppLayout
            from trame.widgets import vuetify3 as v3, html

            self._server = get_server(client_type="vue3", name="governance-dashboard")
            self._state = self._server.state

            # Initialize state (from package pure function)
            for key, value in get_initial_state().items():
                setattr(self._state, key, value)

            # Load initial data (from package pure functions)
            self._state.rules = get_rules()
            self._state.decisions = get_decisions()
            self._state.sessions = get_sessions(limit=10)
            self._state.tasks = get_tasks()

            # Controller for handling UI events
            ctrl = self._server.controller

            @ctrl.set("select_rule")
            def select_rule(rule_id):
                """Handle rule selection for detail view."""
                for rule in self._state.rules:
                    if rule.get('rule_id') == rule_id or rule.get('id') == rule_id:
                        self._state.selected_rule = rule
                        self._state.show_rule_detail = True
                        break

            @ctrl.set("close_rule_detail")
            def close_rule_detail():
                """Close rule detail view."""
                self._state.show_rule_detail = False
                self._state.selected_rule = None

            @ctrl.set("show_rule_form")
            def show_rule_form(mode="create"):
                """Show rule create/edit form."""
                self._state.rule_form_mode = mode
                self._state.show_rule_form = True

            @ctrl.set("close_rule_form")
            def close_rule_form():
                """Close rule form."""
                self._state.show_rule_form = False

            @ctrl.set("submit_rule_form")
            def submit_rule_form():
                """Submit rule form (create/update)."""
                # TODO: Implement actual save via MCP
                self._state.show_rule_form = False
                self._state.status_message = "Rule saved (mock)"

            @ctrl.set("filter_rules_by_status")
            def filter_rules_by_status(status):
                """Filter rules by status."""
                self._state.rules_status_filter = status

            @ctrl.set("filter_rules_by_category")
            def filter_rules_by_category(category):
                """Filter rules by category."""
                self._state.rules_category_filter = category

            @ctrl.set("search_rules")
            def search_rules(query):
                """Search rules by text."""
                self._state.rules_search_query = query

            @ctrl.set("sort_rules")
            def sort_rules(column):
                """Sort rules by column."""
                self._state.rules_sort_column = column
                # Toggle sort direction
                if self._state.rules_sort_asc:
                    self._state.rules_sort_asc = False
                else:
                    self._state.rules_sort_asc = True

            @ctrl.set("analyze_rule_impact")
            def analyze_rule_impact(rule_id):
                """Analyze impact for selected rule (P9.4)."""
                if not rule_id:
                    self._state.impact_selected_rule = None
                    self._state.impact_analysis = None
                    self._state.dependency_graph = None
                    self._state.mermaid_diagram = ''
                    return

                self._state.impact_selected_rule = rule_id
                # Calculate impact using pure functions
                impact = calculate_rule_impact(rule_id, self._state.rules)
                self._state.impact_analysis = impact

                # Build dependency graph for selected rule
                graph = build_dependency_graph(self._state.rules)
                self._state.dependency_graph = graph

                # Generate Mermaid diagram
                mermaid = generate_mermaid_graph(graph)
                self._state.mermaid_diagram = mermaid

            @ctrl.set("toggle_graph_view")
            def toggle_graph_view():
                """Toggle between graph and list view."""
                self._state.show_graph_view = not self._state.show_graph_view

            # =================================================================
            # TRUST DASHBOARD CONTROLLERS (P9.5 - RULE-011)
            # =================================================================

            @ctrl.set("load_trust_data")
            def load_trust_data():
                """Load agent trust data from TypeDB."""
                self._state.agents = get_agents()
                self._state.trust_leaderboard = build_trust_leaderboard(self._state.agents)
                self._state.proposals = get_proposals()
                self._state.escalated_proposals = get_escalated_proposals()
                self._state.governance_stats = get_governance_stats(
                    self._state.agents,
                    self._state.proposals
                )

            @ctrl.set("select_agent")
            def select_agent(agent_id):
                """Select agent for detail view."""
                for agent in self._state.agents:
                    if agent.get('agent_id') == agent_id:
                        self._state.selected_agent = agent
                        self._state.show_agent_detail = True
                        break

            @ctrl.set("close_agent_detail")
            def close_agent_detail():
                """Close agent detail view."""
                self._state.selected_agent = None
                self._state.show_agent_detail = False

            # =================================================================
            # MONITORING CONTROLLERS (P9.6)
            # =================================================================

            @ctrl.set("load_monitor_data")
            def load_monitor_data():
                """Load monitoring data from RuleMonitor."""
                self._state.monitor_feed = get_monitor_feed(limit=50)
                self._state.monitor_alerts = get_monitor_alerts(acknowledged=False)
                self._state.monitor_stats = get_monitor_stats()
                self._state.top_rules = get_top_monitored_rules(limit=10)
                self._state.hourly_stats = get_hourly_monitor_stats()

            @ctrl.set("filter_monitor_events")
            def filter_monitor_events(event_type):
                """Filter monitoring events by type."""
                self._state.monitor_filter = event_type
                self._state.monitor_feed = get_monitor_feed(limit=50, event_type=event_type)

            @ctrl.set("acknowledge_alert")
            def acknowledge_alert(alert_id):
                """Acknowledge a monitoring alert."""
                result = acknowledge_monitor_alert(alert_id)
                if result.get('success'):
                    # Reload alerts
                    self._state.monitor_alerts = get_monitor_alerts(acknowledged=False)
                    self._state.status_message = f"Alert {alert_id} acknowledged"

            @ctrl.set("toggle_auto_refresh")
            def toggle_auto_refresh():
                """Toggle auto-refresh for monitoring view."""
                self._state.auto_refresh = not self._state.auto_refresh

            # Initialize additional state for forms and filters
            self._state.show_rule_detail = False
            self._state.show_rule_form = False
            self._state.rule_form_mode = "create"
            self._state.rules_status_filter = None
            self._state.rules_category_filter = None
            self._state.rules_search_query = ""
            self._state.rules_sort_column = "rule_id"
            self._state.rules_sort_asc = True

            # GAP-UI-027 fix: Filter options as state for proper VSelect binding
            self._state.status_options = RULE_STATUSES  # ['ACTIVE', 'DRAFT', 'DEPRECATED']
            self._state.category_options = RULE_CATEGORIES  # ['governance', 'technical', 'operational']

            # Form field states
            self._state.form_rule_id = ""
            self._state.form_rule_title = ""
            self._state.form_rule_directive = ""
            self._state.form_rule_category = "governance"
            self._state.form_rule_priority = "HIGH"

            with VAppLayout(self._server, full_height=True) as layout:
                # App bar with data-testid
                with v3.VAppBar(
                    color="deep-purple",
                    density="compact",
                    __properties=["data-testid"],
                    **{"data-testid": "app-bar"}
                ):
                    v3.VAppBarTitle("Sim.ai Governance Dashboard")
                    v3.VSpacer()
                    v3.VChip(
                        "{{ rules.length }} Rules | {{ decisions.length }} Decisions",
                        size="small",
                        color="white",
                        variant="outlined",
                    )

                # Navigation drawer with data-testid
                with v3.VNavigationDrawer(
                    permanent=True,
                    rail=True,
                    __properties=["data-testid"],
                    **{"data-testid": "nav-drawer"}
                ):
                    with v3.VList(nav=True, density="compact"):
                        for item in NAVIGATION_ITEMS:
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
                        # =================================================================
                        # RULES LIST VIEW - GAP-UI-001, GAP-UI-006, GAP-UI-007
                        # =================================================================
                        with v3.VCard(
                            v_if="active_view === 'rules' && !show_rule_detail && !show_rule_form",
                            classes="fill-height",
                            __properties=["data-testid"],
                            **{"data-testid": "rules-list"}
                        ):
                            with v3.VCardTitle(classes="d-flex align-center"):
                                html.Span("Governance Rules")
                                v3.VSpacer()
                                # Add Rule button - GAP-UI-002, GAP-UI-024 fixed
                                v3.VBtn(
                                    "Add Rule",
                                    color="primary",
                                    prepend_icon="mdi-plus",
                                    click="rule_form_mode = 'create'; show_rule_form = true",
                                    __properties=["data-testid"],
                                    **{"data-testid": "rules-add-btn"}
                                )

                            # Filters toolbar - GAP-UI-011
                            with v3.VToolbar(density="compact", flat=True):
                                v3.VTextField(
                                    v_model="rules_search_query",
                                    label="Search rules...",
                                    prepend_icon="mdi-magnify",
                                    variant="outlined",
                                    density="compact",
                                    hide_details=True,
                                    style="max-width: 300px",
                                    __properties=["data-testid"],
                                    **{"data-testid": "rules-search"}
                                )
                                v3.VSpacer()
                                # GAP-UI-027 fix: Use state-bound items for proper rendering
                                v3.VSelect(
                                    v_model="rules_status_filter",
                                    items=("status_options",),
                                    label="Status",
                                    variant="outlined",
                                    density="compact",
                                    hide_details=True,
                                    clearable=True,
                                    style="max-width: 150px",
                                    __properties=["data-testid"],
                                    **{"data-testid": "rules-filter-status"}
                                )
                                v3.VSelect(
                                    v_model="rules_category_filter",
                                    items=("category_options",),
                                    label="Category",
                                    variant="outlined",
                                    density="compact",
                                    hide_details=True,
                                    clearable=True,
                                    style="max-width: 150px; margin-left: 8px",
                                    __properties=["data-testid"],
                                    **{"data-testid": "rules-filter-category"}
                                )

                            with v3.VCardText():
                                # Rules table - using VList with slot content
                                html.Div("{{ rules.length }} rules loaded", classes="mb-2 text-grey")

                                # GAP-UI-025: Rules list with clickable items for detail view
                                # GAP-UI-026: Filtered by search query using v-show
                                with v3.VList(density="compact", __properties=["data-testid"], **{"data-testid": "rules-table"}):
                                    with v3.VListItem(
                                        v_for="rule in rules",
                                        v_show="!rules_search_query || (rule.id && rule.id.toLowerCase().includes(rules_search_query.toLowerCase())) || (rule.name && rule.name.toLowerCase().includes(rules_search_query.toLowerCase()))",
                                        click="selected_rule = rule; show_rule_detail = true",
                                        **{":key": "rule.id"},
                                        __properties=["data-testid"],
                                        **{"data-testid": "rule-item"}
                                    ):
                                        with html.Template(v_slot_prepend=True):
                                            v3.VIcon("mdi-gavel", color="primary")
                                        with v3.VListItemTitle():
                                            html.Span("{{ rule.id }}: {{ rule.name }}")
                                        with v3.VListItemSubtitle():
                                            html.Span("{{ rule.category }} | {{ rule.status }} | {{ rule.priority }}")

                        # =================================================================
                        # RULE DETAIL VIEW - GAP-UI-003
                        # =================================================================
                        with v3.VCard(
                            v_if="active_view === 'rules' && show_rule_detail && selected_rule",
                            classes="fill-height",
                            __properties=["data-testid"],
                            **{"data-testid": "rule-detail"}
                        ):
                            with v3.VCardTitle(classes="d-flex align-center"):
                                v3.VBtn(
                                    icon="mdi-arrow-left",
                                    variant="text",
                                    click="show_rule_detail = false; selected_rule = null",
                                    __properties=["data-testid"],
                                    **{"data-testid": "rule-detail-back-btn"}
                                )
                                html.Span(
                                    "{{ selected_rule.rule_id || selected_rule.id }}",
                                    __properties=["data-testid"],
                                    **{"data-testid": "rule-detail-id"}
                                )
                                v3.VSpacer()
                                v3.VBtn(
                                    "Edit",
                                    color="primary",
                                    prepend_icon="mdi-pencil",
                                    click="rule_form_mode = 'edit'; show_rule_form = true",
                                    __properties=["data-testid"],
                                    **{"data-testid": "rule-detail-edit-btn"}
                                )
                                v3.VBtn(
                                    "Delete",
                                    color="error",
                                    prepend_icon="mdi-delete",
                                    variant="outlined",
                                    classes="ml-2",
                                    __properties=["data-testid"],
                                    **{"data-testid": "rule-detail-delete-btn"}
                                )

                            with v3.VCardText():
                                # Header section
                                html.H2(
                                    "{{ selected_rule.title || selected_rule.name }}",
                                    __properties=["data-testid"],
                                    **{"data-testid": "rule-detail-title"}
                                )

                                # Metadata chips
                                with v3.VChipGroup():
                                    v3.VChip(
                                        v_text="selected_rule.status",
                                        color=("selected_rule.status === 'ACTIVE' ? 'success' : 'grey'",),
                                        __properties=["data-testid"],
                                        **{"data-testid": "rule-detail-status"}
                                    )
                                    v3.VChip(
                                        v_text="selected_rule.category",
                                        __properties=["data-testid"],
                                        **{"data-testid": "rule-detail-category"}
                                    )
                                    v3.VChip(
                                        v_text="selected_rule.priority",
                                        color=("selected_rule.priority === 'CRITICAL' ? 'error' : 'grey'",),
                                        __properties=["data-testid"],
                                        **{"data-testid": "rule-detail-priority"}
                                    )

                                # Directive content
                                v3.VDivider(classes="my-4")
                                html.H3("Directive")
                                html.P(
                                    "{{ selected_rule.directive || 'No directive available' }}",
                                    __properties=["data-testid"],
                                    **{"data-testid": "rule-detail-directive"}
                                )

                                # Related entities section
                                v3.VDivider(classes="my-4")
                                html.H3("Related Entities")
                                with v3.VRow():
                                    with v3.VCol(cols=4):
                                        with v3.VCard(
                                            variant="outlined",
                                            __properties=["data-testid"],
                                            **{"data-testid": "rule-detail-related-rules"}
                                        ):
                                            v3.VCardTitle("Related Rules", density="compact")
                                            with v3.VCardText():
                                                html.Span("No related rules")
                                    with v3.VCol(cols=4):
                                        with v3.VCard(
                                            variant="outlined",
                                            __properties=["data-testid"],
                                            **{"data-testid": "rule-detail-related-decisions"}
                                        ):
                                            v3.VCardTitle("Related Decisions", density="compact")
                                            with v3.VCardText():
                                                html.Span("No related decisions")
                                    with v3.VCol(cols=4):
                                        with v3.VCard(
                                            variant="outlined",
                                            __properties=["data-testid"],
                                            **{"data-testid": "rule-detail-related-sessions"}
                                        ):
                                            v3.VCardTitle("Related Sessions", density="compact")
                                            with v3.VCardText():
                                                html.Span("No related sessions")

                        # =================================================================
                        # RULE FORM (CREATE/EDIT) - GAP-UI-002
                        # =================================================================
                        with v3.VCard(
                            v_if="active_view === 'rules' && show_rule_form",
                            classes="fill-height",
                            __properties=["data-testid"],
                            **{"data-testid": "rule-form"}
                        ):
                            with v3.VCardTitle(classes="d-flex align-center"):
                                html.Span("{{ rule_form_mode === 'create' ? 'Create New Rule' : 'Edit Rule' }}")

                            with v3.VCardText():
                                with v3.VForm():
                                    v3.VTextField(
                                        v_model="form_rule_id",
                                        label="Rule ID",
                                        placeholder="RULE-XXX",
                                        variant="outlined",
                                        density="compact",
                                        required=True,
                                        __properties=["data-testid"],
                                        **{"data-testid": "rule-form-id"}
                                    )
                                    v3.VTextField(
                                        v_model="form_rule_title",
                                        label="Title",
                                        variant="outlined",
                                        density="compact",
                                        required=True,
                                        classes="mt-3",
                                        __properties=["data-testid"],
                                        **{"data-testid": "rule-form-title"}
                                    )
                                    v3.VTextarea(
                                        v_model="form_rule_directive",
                                        label="Directive",
                                        variant="outlined",
                                        density="compact",
                                        rows=5,
                                        classes="mt-3",
                                        __properties=["data-testid"],
                                        **{"data-testid": "rule-form-directive"}
                                    )
                                    with v3.VRow(classes="mt-3"):
                                        with v3.VCol(cols=6):
                                            v3.VSelect(
                                                v_model="form_rule_category",
                                                items=RULE_CATEGORIES,
                                                label="Category",
                                                variant="outlined",
                                                density="compact",
                                                __properties=["data-testid"],
                                                **{"data-testid": "rule-form-category"}
                                            )
                                        with v3.VCol(cols=6):
                                            v3.VSelect(
                                                v_model="form_rule_priority",
                                                items=RULE_PRIORITIES,
                                                label="Priority",
                                                variant="outlined",
                                                density="compact",
                                                __properties=["data-testid"],
                                                **{"data-testid": "rule-form-priority"}
                                            )

                            with v3.VCardActions():
                                v3.VSpacer()
                                v3.VBtn(
                                    "Cancel",
                                    variant="text",
                                    click="show_rule_form = false",
                                    __properties=["data-testid"],
                                    **{"data-testid": "rule-form-cancel"}
                                )
                                v3.VBtn(
                                    "Save",
                                    color="primary",
                                    click="show_rule_form = false; status_message = 'Rule saved (mock)'",
                                    __properties=["data-testid"],
                                    **{"data-testid": "rule-form-submit"}
                                )

                        # =================================================================
                        # IMPACT ANALYZER VIEW (P9.4)
                        # =================================================================
                        with v3.VCard(
                            v_if="active_view === 'impact'",
                            classes="fill-height",
                            __properties=["data-testid"],
                            **{"data-testid": "impact-analyzer"}
                        ):
                            with v3.VCardTitle(classes="d-flex align-center"):
                                html.Span("Rule Impact Analyzer")
                                v3.VSpacer()
                                # Graph/List toggle
                                with v3.VBtnToggle(
                                    v_model="show_graph_view",
                                    density="compact",
                                    color="primary",
                                    mandatory=True,
                                    __properties=["data-testid"],
                                    **{"data-testid": "impact-view-toggle"}
                                ):
                                    v3.VBtn(
                                        icon="mdi-graph",
                                        value=True,
                                        __properties=["data-testid"],
                                        **{"data-testid": "impact-graph-btn"}
                                    )
                                    v3.VBtn(
                                        icon="mdi-format-list-bulleted",
                                        value=False,
                                        __properties=["data-testid"],
                                        **{"data-testid": "impact-list-btn"}
                                    )

                            with v3.VCardText():
                                # Rule selector
                                with v3.VRow():
                                    with v3.VCol(cols=4):
                                        v3.VSelect(
                                            v_model="impact_selected_rule",
                                            items=("rules.map(r => r.rule_id || r.id)",),
                                            label="Select Rule to Analyze",
                                            variant="outlined",
                                            density="compact",
                                            clearable=True,
                                            change="analyze_rule_impact($event)",
                                            __properties=["data-testid"],
                                            **{"data-testid": "impact-rule-select"}
                                        )

                                # Analysis results
                                with v3.VRow(v_if="impact_analysis"):
                                    # Risk summary card
                                    with v3.VCol(cols=4):
                                        with v3.VCard(
                                            variant="outlined",
                                            __properties=["data-testid"],
                                            **{"data-testid": "impact-risk-card"}
                                        ):
                                            with v3.VCardTitle(classes="d-flex align-center"):
                                                html.Span("Risk Assessment")
                                                v3.VSpacer()
                                                v3.VChip(
                                                    v_text="impact_analysis.risk_level",
                                                    color=("impact_analysis.risk_level === 'CRITICAL' ? 'error' : impact_analysis.risk_level === 'HIGH' ? 'warning' : impact_analysis.risk_level === 'MEDIUM' ? 'info' : 'success'",),
                                                    size="large",
                                                    __properties=["data-testid"],
                                                    **{"data-testid": "impact-risk-chip"}
                                                )
                                            with v3.VCardText():
                                                with v3.VList(density="compact"):
                                                    v3.VListItem(
                                                        title="Total Rules Affected",
                                                        subtitle=("impact_analysis.total_affected + ' rules'",),
                                                        prepend_icon="mdi-alert-circle-outline",
                                                        __properties=["data-testid"],
                                                        **{"data-testid": "impact-total-affected"}
                                                    )
                                                    v3.VListItem(
                                                        title="Direct Dependents",
                                                        subtitle=("(impact_analysis.direct_dependents || []).length + ' rules'",),
                                                        prepend_icon="mdi-arrow-right-bold",
                                                        __properties=["data-testid"],
                                                        **{"data-testid": "impact-direct-deps"}
                                                    )
                                                    v3.VListItem(
                                                        title="Dependencies",
                                                        subtitle=("(impact_analysis.dependencies || []).length + ' rules'",),
                                                        prepend_icon="mdi-arrow-left-bold",
                                                        __properties=["data-testid"],
                                                        **{"data-testid": "impact-dependencies"}
                                                    )

                                    # Recommendation card
                                    with v3.VCol(cols=8):
                                        with v3.VCard(
                                            variant="outlined",
                                            __properties=["data-testid"],
                                            **{"data-testid": "impact-recommendation-card"}
                                        ):
                                            v3.VCardTitle("Recommendation")
                                            with v3.VCardText():
                                                v3.VAlert(
                                                    v_text="impact_analysis.recommendation",
                                                    type=("impact_analysis.risk_level === 'CRITICAL' ? 'error' : impact_analysis.risk_level === 'HIGH' ? 'warning' : 'info'",),
                                                    variant="tonal",
                                                    __properties=["data-testid"],
                                                    **{"data-testid": "impact-recommendation"}
                                                )

                                                # Critical rules affected
                                                with v3.VCard(
                                                    v_if="impact_analysis.critical_rules_affected && impact_analysis.critical_rules_affected.length > 0",
                                                    variant="outlined",
                                                    color="error",
                                                    classes="mt-4",
                                                    __properties=["data-testid"],
                                                    **{"data-testid": "impact-critical-rules"}
                                                ):
                                                    v3.VCardTitle("Critical Rules Affected", density="compact")
                                                    with v3.VCardText():
                                                        with v3.VChipGroup():
                                                            v3.VChip(
                                                                v_for="ruleId in impact_analysis.critical_rules_affected",
                                                                key=("ruleId",),
                                                                v_text="ruleId",
                                                                color="error",
                                                                size="small",
                                                            )

                                # Graph view
                                with v3.VRow(v_if="show_graph_view && dependency_graph"):
                                    with v3.VCol(cols=12):
                                        with v3.VCard(
                                            variant="outlined",
                                            __properties=["data-testid"],
                                            **{"data-testid": "impact-graph-card"}
                                        ):
                                            v3.VCardTitle("Dependency Graph")
                                            with v3.VCardText():
                                                # Mermaid diagram display
                                                html.Pre(
                                                    "{{ mermaid_diagram }}",
                                                    style="background: #f5f5f5; padding: 16px; border-radius: 4px; overflow-x: auto;",
                                                    __properties=["data-testid"],
                                                    **{"data-testid": "impact-mermaid"}
                                                )
                                                # Graph stats
                                                with v3.VRow(classes="mt-2"):
                                                    with v3.VCol(cols=3):
                                                        v3.VChip(
                                                            v_text="'Nodes: ' + (dependency_graph.stats?.total_nodes || 0)",
                                                            size="small",
                                                            color="primary",
                                                        )
                                                    with v3.VCol(cols=3):
                                                        v3.VChip(
                                                            v_text="'Dependencies: ' + (dependency_graph.stats?.dependency_edges || 0)",
                                                            size="small",
                                                            color="info",
                                                        )
                                                    with v3.VCol(cols=3):
                                                        v3.VChip(
                                                            v_text="'Conflicts: ' + (dependency_graph.stats?.conflict_edges || 0)",
                                                            size="small",
                                                            color="warning",
                                                        )

                                # List view
                                with v3.VRow(v_if="!show_graph_view && impact_analysis"):
                                    with v3.VCol(cols=6):
                                        with v3.VCard(
                                            variant="outlined",
                                            __properties=["data-testid"],
                                            **{"data-testid": "impact-dependents-list"}
                                        ):
                                            v3.VCardTitle("Rules That Depend on This Rule")
                                            with v3.VCardText():
                                                with v3.VList(density="compact"):
                                                    v3.VListItem(
                                                        v_for="ruleId in impact_analysis.direct_dependents",
                                                        key=("ruleId",),
                                                        v_text="ruleId",
                                                        prepend_icon="mdi-arrow-right",
                                                    )
                                                    v3.VListItem(
                                                        v_if="!impact_analysis.direct_dependents || impact_analysis.direct_dependents.length === 0",
                                                        title="No dependents",
                                                        prepend_icon="mdi-check-circle",
                                                        disabled=True,
                                                    )

                                    with v3.VCol(cols=6):
                                        with v3.VCard(
                                            variant="outlined",
                                            __properties=["data-testid"],
                                            **{"data-testid": "impact-dependencies-list"}
                                        ):
                                            v3.VCardTitle("Rules This Rule Depends On")
                                            with v3.VCardText():
                                                with v3.VList(density="compact"):
                                                    v3.VListItem(
                                                        v_for="ruleId in impact_analysis.dependencies",
                                                        key=("ruleId",),
                                                        v_text="ruleId",
                                                        prepend_icon="mdi-arrow-left",
                                                    )
                                                    v3.VListItem(
                                                        v_if="!impact_analysis.dependencies || impact_analysis.dependencies.length === 0",
                                                        title="No dependencies",
                                                        prepend_icon="mdi-check-circle",
                                                        disabled=True,
                                                    )

                                # Empty state
                                with v3.VRow(v_if="!impact_analysis"):
                                    with v3.VCol(cols=12, classes="text-center py-8"):
                                        v3.VIcon("mdi-graph-outline", size="64", color="grey")
                                        html.P(
                                            "Select a rule above to analyze its impact",
                                            classes="text-grey mt-4",
                                            __properties=["data-testid"],
                                            **{"data-testid": "impact-empty-state"}
                                        )

                        # =================================================================
                        # TRUST DASHBOARD VIEW (P9.5 - RULE-011)
                        # =================================================================
                        with v3.VCard(
                            v_if="active_view === 'trust' && !show_agent_detail",
                            classes="fill-height",
                            __properties=["data-testid"],
                            **{"data-testid": "trust-dashboard"}
                        ):
                            with v3.VCardTitle(classes="d-flex align-center"):
                                html.Span("Agent Trust Dashboard")
                                v3.VSpacer()
                                v3.VBtn(
                                    "Refresh Data",
                                    prepend_icon="mdi-refresh",
                                    variant="outlined",
                                    size="small",
                                    click="load_trust_data()",
                                    __properties=["data-testid"],
                                    **{"data-testid": "trust-refresh-btn"}
                                )

                            with v3.VCardText():
                                # Governance stats cards
                                with v3.VRow():
                                    with v3.VCol(cols=3):
                                        with v3.VCard(
                                            variant="tonal",
                                            color="primary",
                                            __properties=["data-testid"],
                                            **{"data-testid": "trust-stat-agents"}
                                        ):
                                            with v3.VCardText(classes="text-center"):
                                                html.Div(
                                                    "{{ governance_stats.total_agents || 0 }}",
                                                    classes="text-h4 font-weight-bold"
                                                )
                                                html.Div("Total Agents", classes="text-subtitle-2")
                                    with v3.VCol(cols=3):
                                        with v3.VCard(
                                            variant="tonal",
                                            color="success",
                                            __properties=["data-testid"],
                                            **{"data-testid": "trust-stat-avg"}
                                        ):
                                            with v3.VCardText(classes="text-center"):
                                                html.Div(
                                                    "{{ (governance_stats.avg_trust_score * 100 || 0).toFixed(1) }}%",
                                                    classes="text-h4 font-weight-bold"
                                                )
                                                html.Div("Avg Trust Score", classes="text-subtitle-2")
                                    with v3.VCol(cols=3):
                                        with v3.VCard(
                                            variant="tonal",
                                            color="info",
                                            __properties=["data-testid"],
                                            **{"data-testid": "trust-stat-pending"}
                                        ):
                                            with v3.VCardText(classes="text-center"):
                                                html.Div(
                                                    "{{ governance_stats.pending_proposals || 0 }}",
                                                    classes="text-h4 font-weight-bold"
                                                )
                                                html.Div("Pending Proposals", classes="text-subtitle-2")
                                    with v3.VCol(cols=3):
                                        with v3.VCard(
                                            variant="tonal",
                                            color="warning",
                                            __properties=["data-testid"],
                                            **{"data-testid": "trust-stat-escalated"}
                                        ):
                                            with v3.VCardText(classes="text-center"):
                                                html.Div(
                                                    "{{ escalated_proposals.length || 0 }}",
                                                    classes="text-h4 font-weight-bold"
                                                )
                                                html.Div("Escalated", classes="text-subtitle-2")

                                # Trust leaderboard and proposals
                                with v3.VRow(classes="mt-4"):
                                    # Leaderboard
                                    with v3.VCol(cols=6):
                                        with v3.VCard(
                                            variant="outlined",
                                            __properties=["data-testid"],
                                            **{"data-testid": "trust-leaderboard"}
                                        ):
                                            v3.VCardTitle("Trust Leaderboard")
                                            with v3.VCardText():
                                                with v3.VList(density="compact"):
                                                    with v3.VListItem(
                                                        v_for="agent in trust_leaderboard",
                                                        key=("agent.agent_id",),
                                                        click="select_agent(agent.agent_id)",
                                                        __properties=["data-testid"],
                                                        **{"data-testid": "trust-agent-item"}
                                                    ):
                                                        with html.Template(v_slot_prepend=True):
                                                            with v3.VAvatar(
                                                                color=("agent.trust_level === 'HIGH' ? 'success' : agent.trust_level === 'MEDIUM' ? 'warning' : 'error'",),
                                                                size="32"
                                                            ):
                                                                html.Span(
                                                                    "{{ agent.rank }}",
                                                                    classes="text-white font-weight-bold"
                                                                )
                                                        with html.Template(v_slot_default=True):
                                                            v3.VListItemTitle("{{ agent.name || agent.agent_id }}")
                                                            v3.VListItemSubtitle("{{ agent.agent_type }}")
                                                        with html.Template(v_slot_append=True):
                                                            v3.VChip(
                                                                v_text="(agent.trust_score * 100).toFixed(0) + '%'",
                                                                color=("agent.trust_level === 'HIGH' ? 'success' : agent.trust_level === 'MEDIUM' ? 'warning' : 'error'",),
                                                                size="small",
                                                            )
                                                    # Empty state
                                                    v3.VListItem(
                                                        v_if="!trust_leaderboard || trust_leaderboard.length === 0",
                                                        title="No agents registered",
                                                        prepend_icon="mdi-robot-off",
                                                        disabled=True,
                                                    )

                                    # Proposals panel
                                    with v3.VCol(cols=6):
                                        with v3.VCard(
                                            variant="outlined",
                                            __properties=["data-testid"],
                                            **{"data-testid": "trust-proposals"}
                                        ):
                                            v3.VCardTitle("Recent Proposals")
                                            with v3.VCardText():
                                                with v3.VList(density="compact"):
                                                    with v3.VListItem(
                                                        v_for="prop in proposals.slice(0, 5)",
                                                        key=("prop.proposal_id",),
                                                        __properties=["data-testid"],
                                                        **{"data-testid": "trust-proposal-item"}
                                                    ):
                                                        with html.Template(v_slot_prepend=True):
                                                            v3.VIcon(
                                                                icon=("prop.proposal_type === 'create' ? 'mdi-plus-circle' : prop.proposal_type === 'modify' ? 'mdi-pencil-circle' : 'mdi-close-circle'",),
                                                                color=("prop.proposal_status === 'approved' ? 'success' : prop.proposal_status === 'rejected' ? 'error' : 'info'",),
                                                            )
                                                        with html.Template(v_slot_default=True):
                                                            v3.VListItemTitle("{{ prop.proposal_id }}")
                                                            v3.VListItemSubtitle("{{ prop.affected_rule }} - {{ prop.proposal_status }}")
                                                        with html.Template(v_slot_append=True):
                                                            v3.VChip(
                                                                v_text="prop.proposal_status",
                                                                color=("prop.proposal_status === 'approved' ? 'success' : prop.proposal_status === 'rejected' ? 'error' : prop.proposal_status === 'pending' ? 'info' : 'warning'",),
                                                                size="x-small",
                                                            )
                                                    # Empty state
                                                    v3.VListItem(
                                                        v_if="!proposals || proposals.length === 0",
                                                        title="No proposals",
                                                        prepend_icon="mdi-file-document-outline",
                                                        disabled=True,
                                                    )

                                # Escalated proposals alert
                                with v3.VRow(
                                    v_if="escalated_proposals && escalated_proposals.length > 0",
                                    classes="mt-4"
                                ):
                                    with v3.VCol(cols=12):
                                        v3.VAlert(
                                            type="warning",
                                            title="Human Escalation Required",
                                            text=("escalated_proposals.length + ' proposals require human review'",),
                                            variant="tonal",
                                            __properties=["data-testid"],
                                            **{"data-testid": "trust-escalation-alert"}
                                        )
                                        with v3.VCard(
                                            variant="outlined",
                                            color="warning",
                                            classes="mt-2",
                                            __properties=["data-testid"],
                                            **{"data-testid": "trust-escalated-list"}
                                        ):
                                            with v3.VList(density="compact"):
                                                v3.VListItem(
                                                    v_for="esc in escalated_proposals",
                                                    key=("esc.proposal_id",),
                                                    title=("esc.proposal_id",),
                                                    subtitle=("'Trigger: ' + (esc.escalation_trigger || 'Unknown')",),
                                                    prepend_icon="mdi-alert-circle",
                                                )

                        # Agent detail view (P9.5)
                        with v3.VCard(
                            v_if="active_view === 'trust' && show_agent_detail && selected_agent",
                            classes="fill-height",
                            __properties=["data-testid"],
                            **{"data-testid": "trust-agent-detail"}
                        ):
                            with v3.VCardTitle(classes="d-flex align-center"):
                                v3.VBtn(
                                    icon="mdi-arrow-left",
                                    variant="text",
                                    click="show_agent_detail = false; selected_agent = null",
                                    __properties=["data-testid"],
                                    **{"data-testid": "agent-detail-back-btn"}
                                )
                                html.Span("{{ selected_agent.name || selected_agent.agent_id }}")
                                v3.VSpacer()
                                v3.VChip(
                                    v_text="selected_agent.agent_type",
                                    color="primary",
                                    size="small",
                                )

                            with v3.VCardText():
                                # Trust metrics
                                with v3.VRow():
                                    with v3.VCol(cols=3):
                                        with v3.VCard(
                                            variant="tonal",
                                            color=("selected_agent.trust_score >= 0.8 ? 'success' : selected_agent.trust_score >= 0.5 ? 'warning' : 'error'",),
                                            __properties=["data-testid"],
                                            **{"data-testid": "agent-trust-score"}
                                        ):
                                            with v3.VCardText(classes="text-center"):
                                                html.Div(
                                                    "{{ (selected_agent.trust_score * 100).toFixed(1) }}%",
                                                    classes="text-h4 font-weight-bold"
                                                )
                                                html.Div("Trust Score", classes="text-subtitle-2")
                                    with v3.VCol(cols=3):
                                        with v3.VCard(
                                            variant="outlined",
                                            __properties=["data-testid"],
                                            **{"data-testid": "agent-compliance"}
                                        ):
                                            with v3.VCardText(classes="text-center"):
                                                html.Div(
                                                    "{{ (selected_agent.compliance_rate * 100 || 0).toFixed(1) }}%",
                                                    classes="text-h5"
                                                )
                                                html.Div("Compliance (40%)", classes="text-caption")
                                    with v3.VCol(cols=3):
                                        with v3.VCard(
                                            variant="outlined",
                                            __properties=["data-testid"],
                                            **{"data-testid": "agent-accuracy"}
                                        ):
                                            with v3.VCardText(classes="text-center"):
                                                html.Div(
                                                    "{{ (selected_agent.accuracy_rate * 100 || 0).toFixed(1) }}%",
                                                    classes="text-h5"
                                                )
                                                html.Div("Accuracy (30%)", classes="text-caption")
                                    with v3.VCol(cols=3):
                                        with v3.VCard(
                                            variant="outlined",
                                            __properties=["data-testid"],
                                            **{"data-testid": "agent-tenure"}
                                        ):
                                            with v3.VCardText(classes="text-center"):
                                                html.Div(
                                                    "{{ selected_agent.tenure_days || 0 }}",
                                                    classes="text-h5"
                                                )
                                                html.Div("Tenure Days (10%)", classes="text-caption")

                                # Trust formula explanation
                                v3.VDivider(classes="my-4")
                                with v3.VCard(
                                    variant="outlined",
                                    classes="bg-grey-lighten-4",
                                    __properties=["data-testid"],
                                    **{"data-testid": "agent-trust-formula"}
                                ):
                                    v3.VCardTitle("RULE-011 Trust Formula", density="compact")
                                    with v3.VCardText():
                                        html.Code(
                                            "Trust = (Compliance × 0.4) + (Accuracy × 0.3) + (Consistency × 0.2) + (Tenure × 0.1)",
                                            style="font-size: 14px;"
                                        )

                        # =================================================================
                        # MONITORING VIEW (P9.6)
                        # =================================================================
                        with v3.VCard(
                            v_if="active_view === 'monitor'",
                            classes="fill-height",
                            __properties=["data-testid"],
                            **{"data-testid": "monitor-dashboard"}
                        ):
                            with v3.VCardTitle(classes="d-flex align-center"):
                                html.Span("Real-time Rule Monitoring")
                                v3.VSpacer()
                                # Event type filter
                                v3.VSelect(
                                    v_model="monitor_filter",
                                    items=['rule_query', 'rule_change', 'violation', 'compliance_check', 'trust_decrease', 'trust_increase'],
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
                                    click="toggle_auto_refresh()",
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
                                    click="load_monitor_data()",
                                    __properties=["data-testid"],
                                    **{"data-testid": "monitor-refresh-btn"}
                                )

                            with v3.VCardText():
                                # Stats cards row
                                with v3.VRow():
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
                                    with v3.VCol(cols=3):
                                        with v3.VCard(
                                            variant="tonal",
                                            color="warning",
                                            __properties=["data-testid"],
                                            **{"data-testid": "monitor-stat-violations"}
                                        ):
                                            with v3.VCardText(classes="text-center"):
                                                html.Div(
                                                    "{{ monitor_stats.violations || 0 }}",
                                                    classes="text-h4 font-weight-bold"
                                                )
                                                html.Div("Violations", classes="text-subtitle-2")
                                    with v3.VCol(cols=3):
                                        with v3.VCard(
                                            variant="tonal",
                                            color="success",
                                            __properties=["data-testid"],
                                            **{"data-testid": "monitor-stat-compliance"}
                                        ):
                                            with v3.VCardText(classes="text-center"):
                                                html.Div(
                                                    "{{ monitor_stats.compliance_checks || 0 }}",
                                                    classes="text-h4 font-weight-bold"
                                                )
                                                html.Div("Compliance Checks", classes="text-subtitle-2")

                                # Main content: Event feed and Alerts
                                with v3.VRow(classes="mt-4"):
                                    # Event feed
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
                                                                icon=("event.event_type === 'rule_query' ? 'mdi-magnify' : event.event_type === 'rule_change' ? 'mdi-pencil' : event.event_type === 'violation' ? 'mdi-alert-circle' : event.event_type === 'compliance_check' ? 'mdi-check-circle' : event.event_type === 'trust_decrease' ? 'mdi-arrow-down' : 'mdi-arrow-up'",),
                                                                color=("event.event_type === 'violation' ? 'error' : event.event_type === 'rule_change' ? 'warning' : event.event_type === 'trust_decrease' ? 'warning' : event.event_type === 'trust_increase' ? 'success' : event.event_type === 'compliance_check' ? 'success' : 'info'",),
                                                                size="small",
                                                            )
                                                        with html.Template(v_slot_default=True):
                                                            v3.VListItemTitle("{{ event.source }}")
                                                            v3.VListItemSubtitle("{{ event.event_type }} - {{ event.timestamp }}")
                                                        with html.Template(v_slot_append=True):
                                                            v3.VChip(
                                                                v_text="event.severity",
                                                                color=("event.severity === 'CRITICAL' ? 'error' : event.severity === 'WARNING' ? 'warning' : 'info'",),
                                                                size="x-small",
                                                            )
                                                    # Empty state
                                                    v3.VListItem(
                                                        v_if="!monitor_feed || monitor_feed.length === 0",
                                                        title="No events recorded",
                                                        prepend_icon="mdi-information-outline",
                                                        disabled=True,
                                                    )

                                    # Alerts panel
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
                                                            v3.VListItemSubtitle("{{ alert.severity }} - {{ alert.timestamp }}")
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

                                # Top monitored rules
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

                        # =================================================================
                        # DECISIONS VIEW (Fixed: VList instead of VDataTable)
                        # =================================================================
                        with v3.VCard(
                            v_if="active_view === 'decisions'",
                            classes="fill-height",
                            __properties=["data-testid"],
                            **{"data-testid": "decisions-list"}
                        ):
                            v3.VCardTitle("Strategic Decisions")
                            with v3.VCardText():
                                html.Div("{{ decisions.length }} decisions loaded", classes="mb-2 text-grey")
                                with v3.VList(density="compact", __properties=["data-testid"], **{"data-testid": "decisions-table"}):
                                    with v3.VListItem(v_for="decision in decisions", **{":key": "decision.decision_id || decision.id"}):
                                        with html.Template(v_slot_prepend=True):
                                            v3.VIcon("mdi-scale-balance", color="primary")
                                        with v3.VListItemTitle():
                                            html.Span("{{ decision.decision_id || decision.id }}: {{ decision.name || decision.title }}")
                                        with v3.VListItemSubtitle():
                                            html.Span("{{ decision.date }} | {{ decision.status }}")

                        # =================================================================
                        # SESSIONS VIEW
                        # =================================================================
                        with v3.VCard(
                            v_if="active_view === 'sessions'",
                            classes="fill-height",
                            __properties=["data-testid"],
                            **{"data-testid": "sessions-list"}
                        ):
                            v3.VCardTitle("Session Evidence")
                            with v3.VCardText():
                                with v3.VTimeline(density="compact"):
                                    with v3.VTimelineItem(
                                        v_for="session in sessions",
                                        key=("session.session_id",),
                                        dot_color="primary",
                                        size="small",
                                    ):
                                        v3.VCard(
                                            title=("session.session_id",),
                                            subtitle=("session.date || 'No date'",),
                                            density="compact",
                                            __properties=["data-testid"],
                                            **{"data-testid": "session-row"}
                                        )

                        # =================================================================
                        # TASKS VIEW (Fixed: VList instead of VDataTable)
                        # =================================================================
                        with v3.VCard(
                            v_if="active_view === 'tasks'",
                            classes="fill-height",
                            __properties=["data-testid"],
                            **{"data-testid": "tasks-list"}
                        ):
                            v3.VCardTitle("R&D Tasks")
                            with v3.VCardText():
                                html.Div("{{ tasks.length }} tasks loaded", classes="mb-2 text-grey")
                                with v3.VList(density="compact", __properties=["data-testid"], **{"data-testid": "tasks-table"}):
                                    with v3.VListItem(v_for="task in tasks", **{":key": "task.task_id || task.id"}):
                                        with html.Template(v_slot_prepend=True):
                                            v3.VIcon("mdi-checkbox-marked", color="primary")
                                        with v3.VListItemTitle():
                                            html.Span("{{ task.task_id || task.id }}: {{ task.title || task.name }}")
                                        with v3.VListItemSubtitle():
                                            html.Span("{{ task.phase }} | {{ task.status }}")

                        # =================================================================
                        # SEARCH VIEW
                        # =================================================================
                        with v3.VCard(
                            v_if="active_view === 'search'",
                            classes="fill-height",
                            __properties=["data-testid"],
                            **{"data-testid": "search-view"}
                        ):
                            v3.VCardTitle("Evidence Search")
                            with v3.VCardText():
                                v3.VTextField(
                                    v_model="search_query",
                                    label="Search evidence...",
                                    prepend_icon="mdi-magnify",
                                    variant="outlined",
                                    density="compact",
                                    __properties=["data-testid"],
                                    **{"data-testid": "search-input"}
                                )
                                # Results would be populated on search

                # =================================================================
                # LOADING SPINNER - GAP-UI-005
                # =================================================================
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

                # =================================================================
                # ERROR BANNER - GAP-UI-005
                # =================================================================
                v3.VSnackbar(
                    v_model="has_error",
                    color="error",
                    timeout=5000,
                    __properties=["data-testid"],
                    **{"data-testid": "error-banner"}
                )

                # =================================================================
                # CONFIRM DIALOG
                # =================================================================
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

            # Initialize additional state for dialogs
            self._state.has_error = False
            self._state.show_confirm = False
            self._state.confirm_message = ""

            return self._server

        except ImportError:
            print("Trame not installed. Run: pip install trame trame-vuetify trame-client")
            return None

    def run(self, port: int = None):
        """
        Run Trame dashboard server.

        Args:
            port: Override port
        """
        if port:
            self.port = port

        server = self.build_ui()
        if server:
            print(f"Starting Governance Dashboard on port {self.port}")
            server.start(port=self.port, open_browser=True)


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_governance_dashboard(port: int = 8081) -> GovernanceDashboard:
    """
    Factory function to create Governance Dashboard.

    Args:
        port: UI port

    Returns:
        GovernanceDashboard instance
    """
    return GovernanceDashboard(port=port)


# =============================================================================
# CLI
# =============================================================================

def main():
    """Run Governance Dashboard standalone."""
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Sim.ai Governance Dashboard")
    parser.add_argument("--port", type=int, default=8081, help="UI port")
    parser.add_argument("--server", action="store_true", help="Run in server mode (no browser)")
    args = parser.parse_args()

    # In Docker or when --server flag is passed, don't open browser
    server_mode = args.server or os.environ.get("TRAME_DEFAULT_HOST") == "0.0.0.0"

    dashboard = create_governance_dashboard(port=args.port)
    server = dashboard.build_ui()
    if server:
        print(f"Starting Governance Dashboard on port {args.port}")
        # timeout=0 keeps server running indefinitely (no idle exit)
        server.start(port=args.port, open_browser=not server_mode, timeout=0)


if __name__ == "__main__":
    main()
