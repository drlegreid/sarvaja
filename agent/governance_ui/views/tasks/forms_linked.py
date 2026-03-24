"""
Task Linked Items & Content Preview Components.

Per DOC-SIZE-01-v1: Extracted from forms.py.
Per GAP-UI-037: Task body/content preview and linked items.
"""

from trame.widgets import vuetify3 as v3, html


def build_task_content_preview() -> None:
    """Build task body/content preview (GAP-UI-037)."""
    with v3.VCard(
        v_if="!edit_task_mode && (selected_task.body || selected_task.content)",
        variant="outlined",
        classes="mb-4",
        __properties=["data-testid"],
        **{"data-testid": "task-content-preview"}
    ):
        v3.VCardTitle("Content", density="compact")
        with v3.VCardText():
            html.Pre(
                "{{ selected_task.body || selected_task.content }}",
                style="white-space: pre-wrap; font-family: monospace; "
                      "font-size: 0.875rem; "
                      "padding: 12px; border-radius: 4px; max-height: 300px; "
                      "overflow-y: auto;",
                classes="bg-surface-variant",
                __properties=["data-testid"],
                **{"data-testid": "task-content-text"}
            )


def build_task_linked_items() -> None:
    """Build linked rules/sessions display (GAP-UI-037)."""
    with v3.VCard(
        v_if="!edit_task_mode",
        variant="outlined",
        classes="mb-4",
        __properties=["data-testid"],
        **{"data-testid": "task-linked-items"}
    ):
        v3.VCardTitle("Related Items", density="compact")
        with v3.VCardText():
            # GAP ID
            with html.Div(
                v_if="selected_task.gap_id",
                classes="mb-2"
            ):
                html.Span("Gap: ", classes="font-weight-bold")
                v3.VChip(
                    v_text="selected_task.gap_id",
                    size="small",
                    color="warning",
                    prepend_icon="mdi-alert-circle-outline"
                )
            # Linked Rules
            with html.Div(
                v_if="selected_task.linked_rules?.length > 0",
                classes="mb-2"
            ):
                html.Span("Rules: ", classes="font-weight-bold")
                v3.VChip(
                    v_for="rule in selected_task.linked_rules",
                    v_text="rule",
                    size="small",
                    color="primary",
                    classes="mr-1",
                    prepend_icon="mdi-gavel"
                )
            # Linked Sessions — always visible; clickable for cross-entity navigation (Phase 9d)
            with html.Div(
                classes="mb-2"
            ):
                html.Span("Sessions: ", classes="font-weight-bold")
                v3.VChip(
                    v_for="session in selected_task.linked_sessions",
                    v_if="selected_task.linked_sessions?.length > 0",
                    v_text="session",
                    size="small",
                    color="info",
                    classes="mr-1",
                    prepend_icon="mdi-calendar-clock",
                    click=(
                        "trigger('navigate_to_session', "
                        "[session, 'tasks', selected_task.task_id || selected_task.id, "
                        "'Back to Task ' + (selected_task.task_id || selected_task.id)])"
                    ),
                    style="cursor: pointer",
                    __properties=["data-testid"],
                    **{"data-testid": "task-session-chip"}
                )
                html.Span(
                    "No linked sessions",
                    v_if="!selected_task.linked_sessions?.length",
                    classes="text-medium-emphasis text-caption",
                )
            # Linked Documents with type icons (Phase 9d: Concern 2)
            with html.Div(
                v_if="selected_task.linked_documents?.length > 0",
                classes="mb-2"
            ):
                html.Span("Documents: ", classes="font-weight-bold")
                v3.VChip(
                    v_for="doc in selected_task.linked_documents",
                    v_text="doc.split('/').pop()",
                    size="small",
                    v_bind_color=(
                        "doc.includes('evidence') ? 'teal' : "
                        "doc.includes('backlog/phases') || doc.includes('plans/') ? 'blue' : "
                        "doc.includes('specs/') || doc.includes('.gherkin') ? 'purple' : "
                        "doc.includes('.log') || doc.includes('/logs/') ? 'orange' : "
                        "'secondary'"
                    ),
                    classes="mr-1 mb-1",
                    v_bind_prepend_icon=(
                        "doc.includes('evidence') ? 'mdi-beaker-outline' : "
                        "doc.includes('backlog/phases') || doc.includes('plans/') ? 'mdi-map-outline' : "
                        "doc.includes('specs/') || doc.includes('.gherkin') ? 'mdi-format-list-checks' : "
                        "doc.includes('.log') || doc.includes('/logs/') ? 'mdi-text-box-outline' : "
                        "'mdi-file-document-outline'"
                    ),
                    click="trigger('load_file_content', [doc])",
                    __properties=["data-testid"],
                    **{"data-testid": "task-document-chip"}
                )
            # Link Document button — opens tree browser dialog (SRVJ-FEAT-012)
            v3.VBtn(
                "Link Document",
                prepend_icon="mdi-file-link",
                variant="outlined",
                size="small",
                click="trigger('open_link_document_dialog')",
                v_if="!edit_task_mode",
                classes="mb-2 mr-2",
                __properties=["data-testid"],
                **{"data-testid": "task-attach-doc-btn"}
            )
            # Link Session button — opens picker dialog (SRVJ-FEAT-011)
            v3.VBtn(
                "Link Session",
                prepend_icon="mdi-link-variant",
                variant="outlined",
                size="small",
                click="trigger('open_link_session_dialog')",
                v_if="!edit_task_mode",
                classes="mb-2",
                __properties=["data-testid"],
                **{"data-testid": "task-link-session-btn"}
            )
            # Legacy single document_path (PLAN-UI-OVERHAUL-001 Task 2.4)
            with html.Div(
                v_if="selected_task.document_path && !selected_task.linked_documents?.length",
                classes="mb-2"
            ):
                html.Span("Document: ", classes="font-weight-bold")
                v3.VBtn(
                    v_text="selected_task.document_path",
                    variant="tonal",
                    size="small",
                    color="secondary",
                    prepend_icon="mdi-file-document-outline",
                    click="trigger('load_file_content', [selected_task.document_path])",
                    __properties=["data-testid"],
                    **{"data-testid": "task-document-btn"}
                )
            # Agent pipeline (PLAN-UI-OVERHAUL-001 Task 3.4: Multi-Agent Mapping)
            with html.Div(
                v_if=(
                    "selected_task.involved_agents?.length > 0 || "
                    "selected_task.agent_id"
                ),
                classes="mb-2"
            ):
                html.Span("Agent Pipeline: ", classes="font-weight-bold")
                # Primary assigned agent
                v3.VChip(
                    v_if="selected_task.agent_id",
                    v_text="selected_task.agent_id",
                    size="small",
                    color="info",
                    classes="mr-1",
                    prepend_icon="mdi-robot",
                    __properties=["data-testid"],
                    **{"data-testid": "task-primary-agent"}
                )
                # Additional involved agents
                v3.VChip(
                    v_for="agent in (selected_task.involved_agents || [])",
                    v_if="agent !== selected_task.agent_id",
                    v_text="agent",
                    size="small",
                    color="secondary",
                    variant="outlined",
                    classes="mr-1",
                    prepend_icon="mdi-robot",
                    __properties=["data-testid"],
                    **{"data-testid": "task-involved-agent"}
                )

            # Linked Commits (EPIC-UI-VALUE-001)
            with html.Div(
                v_if="selected_task.linked_commits?.length > 0",
                classes="mb-2"
            ):
                html.Span("Commits: ", classes="font-weight-bold")
                v3.VChip(
                    v_for="commit in selected_task.linked_commits",
                    v_text="commit.substring(0, 7)",
                    size="small",
                    color="deep-purple",
                    variant="outlined",
                    classes="mr-1",
                    prepend_icon="mdi-source-commit",
                    __properties=["data-testid"],
                    **{"data-testid": "task-commit-chip"},
                )

            # Timestamps (EPIC-UI-VALUE-001)
            with html.Div(
                v_if="selected_task.claimed_at || selected_task.completed_at",
                classes="mb-2"
            ):
                with html.Span(
                    v_if="selected_task.claimed_at",
                    classes="mr-3"
                ):
                    html.Span("Claimed: ", classes="font-weight-bold")
                    html.Span("{{ selected_task.claimed_at }}")
                with html.Span(v_if="selected_task.completed_at"):
                    html.Span("Completed: ", classes="font-weight-bold")
                    html.Span("{{ selected_task.completed_at }}")

            # Evidence with verification info (GAP-UI-LINKED-SESSIONS-001)
            with html.Div(
                v_if="selected_task.evidence",
                classes="mt-3"
            ):
                html.Span("Evidence: ", classes="font-weight-bold")
                html.Pre(
                    "{{ selected_task.evidence }}",
                    style="white-space: pre-wrap; font-family: monospace; "
                          "font-size: 0.8rem; "
                          "padding: 8px; border-radius: 4px; margin-top: 4px;",
                    classes="bg-surface-variant",
                    __properties=["data-testid"],
                    **{"data-testid": "task-evidence-text"}
                )
