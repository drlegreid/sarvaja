"""
Projects List View Component.

Per GOV-PROJECT-01-v1: Project hierarchy navigation.
Per RULE-012: Single Responsibility - only project list UI.
Per RULE-032: File size limit (<300 lines).
"""

from trame.widgets import vuetify3 as v3, html


def _build_project_metrics():
    """Project summary metrics cards."""
    with v3.VRow(dense=True, classes="mb-2"):
        with v3.VCol(cols=6, sm=3):
            with v3.VCard(variant="tonal", classes="text-center pa-2"):
                html.Div("{{ projects.length || 0 }}", classes="text-h6")
                html.Div("Projects", classes="text-caption")
        with v3.VCol(cols=6, sm=3):
            with v3.VCard(variant="tonal", classes="text-center pa-2"):
                html.Div(
                    "{{ projects.reduce((a, p) => a + (p.plan_count || 0), 0) }}",
                    classes="text-h6",
                )
                html.Div("Plans", classes="text-caption")
        with v3.VCol(cols=6, sm=3):
            with v3.VCard(variant="tonal", classes="text-center pa-2"):
                html.Div(
                    "{{ projects.reduce((a, p) => a + (p.session_count || 0), 0) }}",
                    classes="text-h6",
                )
                html.Div("Sessions", classes="text-caption")


def _build_project_table():
    """Main projects data table."""
    v3.VDataTable(
        v_if="!selected_project",
        items=("projects",),
        headers=("projects_headers", [
            {"title": "Project ID", "key": "project_id", "width": "180px", "sortable": True},
            {"title": "Name", "key": "name", "sortable": True},
            {"title": "Path", "key": "path", "width": "250px", "sortable": True},
            {"title": "Plans", "key": "plan_count", "width": "80px", "sortable": True},
            {"title": "Sessions", "key": "session_count", "width": "100px", "sortable": True},
        ]),
        item_value="project_id",
        density="compact",
        items_per_page=-1,
        hover=True,
        click_row=(
            "($event, row) => { trigger('select_project', "
            "[row.item.project_id || row.item.id]) }"
        ),
        __events=[("click_row", "click:row")],
        loading=("is_loading",),
        __properties=["data-testid"],
        **{"data-testid": "projects-table"},
    )


def _build_project_detail():
    """Project detail view with hierarchy drill-down."""
    with v3.VCard(v_if="selected_project", variant="outlined", classes="mb-2"):
        with v3.VCardTitle(classes="d-flex align-center"):
            v3.VBtn(
                icon="mdi-arrow-left", variant="text",
                click="selected_project = null; project_sessions = []",
            )
            html.Span("{{ selected_project.name || selected_project.project_id }}")
            v3.VSpacer()
            v3.VChip(
                "{{ selected_project.project_id }}",
                size="small", variant="outlined",
            )

        with v3.VCardText():
            # Project info
            with v3.VRow(dense=True, classes="mb-2"):
                with v3.VCol(cols=12, sm=6):
                    html.Div(classes="text-caption text-grey", children=["Path"])
                    html.Div("{{ selected_project.path || 'N/A' }}")
                with v3.VCol(cols=6, sm=3):
                    html.Div(classes="text-caption text-grey", children=["Plans"])
                    html.Div("{{ selected_project.plan_count || 0 }}")
                with v3.VCol(cols=6, sm=3):
                    html.Div(classes="text-caption text-grey", children=["Sessions"])
                    html.Div("{{ selected_project.session_count || 0 }}")

            v3.VDivider(classes="my-2")

            # Linked sessions table
            html.Div("Linked Sessions", classes="text-subtitle-2 mb-1")
            v3.VDataTable(
                items=("project_sessions",),
                headers=([
                    {"title": "Session ID", "key": "session_id", "sortable": True},
                    {"title": "Status", "key": "status", "width": "100px"},
                    {"title": "Agent", "key": "agent_id", "width": "130px"},
                    {"title": "Start", "key": "start_time", "width": "130px"},
                ],),
                density="compact",
                items_per_page=10,
                hover=True,
                no_data_text="No sessions linked to this project",
                click_row=(
                    "($event, row) => { active_view = 'sessions'; "
                    "trigger('select_session', [row.item.session_id]) }"
                ),
                __events=[("click_row", "click:row")],
            )


def build_projects_list_view() -> None:
    """Build the Projects list view with hierarchy navigation."""
    with v3.VCard(
        v_if="active_view === 'projects'",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "projects-list"},
    ):
        with v3.VCardTitle(classes="d-flex align-center"):
            html.Span("Projects")
            v3.VSpacer()
            v3.VBtn(
                "New Project", color="primary", prepend_icon="mdi-plus",
                click="trigger('create_project')",
                __properties=["data-testid"],
                **{"data-testid": "projects-add-btn"},
            )

        with v3.VCardText(classes="pb-0"):
            _build_project_metrics()

        v3.VDivider()
        v3.VProgressLinear(
            v_if="is_loading", indeterminate=True, color="primary",
        )

        with v3.VCardText(classes="pt-1", style="overflow-y: auto"):
            _build_project_table()
            _build_project_detail()
