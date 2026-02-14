"""
Session Content Components.

Per RULE-012: Single Responsibility - session content display.
Per RULE-032: File size limit (<300 lines).
Per GAP-DATA-003: File path navigation.
"""

from trame.widgets import vuetify3 as v3, html


def build_session_metadata_chips() -> None:
    """Build session metadata chips including CC fields (SESSION-CC-01-v1)."""
    with v3.VChipGroup(classes="mb-4"):
        v3.VChip(
            v_text="selected_session.start_time || selected_session.date || 'No date'",
            prepend_icon="mdi-calendar",
            color="primary",
            __properties=["data-testid"],
            **{"data-testid": "session-detail-date"}
        )
        v3.VChip(
            v_text="selected_session.status || 'N/A'",
            prepend_icon="mdi-information",
            __properties=["data-testid"],
            **{"data-testid": "session-detail-status"}
        )
        # Source type badge
        v3.VChip(
            v_if="selected_session.source_type",
            v_text="selected_session.source_type",
            prepend_icon="mdi-source-branch",
            color="info",
            size="small",
        )
        # CC Git Branch (SESSION-CC-01-v1)
        v3.VChip(
            v_if="selected_session.cc_git_branch",
            v_text="selected_session.cc_git_branch",
            prepend_icon="mdi-source-branch",
            color="purple",
            size="small",
        )
        # CC Project Slug (SESSION-CC-01-v1)
        v3.VChip(
            v_if="selected_session.cc_project_slug",
            v_text="selected_session.cc_project_slug",
            prepend_icon="mdi-folder",
            color="teal",
            size="small",
        )


def build_session_info_card() -> None:
    """Build session information card."""
    with v3.VCard(
        variant="outlined",
        __properties=["data-testid"],
        **{"data-testid": "session-detail-content"}
    ):
        v3.VCardTitle("Session Information", density="compact")
        with v3.VCardText():
            with v3.VList(density="compact"):
                v3.VListItem(
                    title="Session ID",
                    subtitle=("selected_session.session_id || selected_session.id",),
                    prepend_icon="mdi-identifier",
                )
                v3.VListItem(
                    title="Date",
                    subtitle=("selected_session.start_time || selected_session.date || 'N/A'",),
                    prepend_icon="mdi-calendar",
                )
                # File Path - Clickable to view content (GAP-DATA-003)
                v3.VListItem(
                    v_if="selected_session.file_path || selected_session.path",
                    title="File Path",
                    subtitle=(
                        "selected_session.file_path || selected_session.path",
                    ),
                    prepend_icon="mdi-file-document",
                    click=(
                        "trigger('load_file_content', "
                        "[selected_session.file_path || selected_session.path])"
                    ),
                    __properties=["data-testid"],
                    **{"data-testid": "session-file-path"}
                )
                v3.VListItem(
                    v_if="!selected_session.file_path && !selected_session.path",
                    title="File Path",
                    subtitle="N/A",
                    prepend_icon="mdi-file-document",
                )
                v3.VListItem(
                    title="Agent",
                    subtitle=("selected_session.agent_id || 'No agent assigned'",),
                    prepend_icon="mdi-robot",
                )
                v3.VListItem(
                    title="Description",
                    subtitle=("selected_session.description || 'No description'",),
                    prepend_icon="mdi-text",
                )
                # CC Session UUID (SESSION-CC-01-v1)
                v3.VListItem(
                    v_if="selected_session.cc_session_uuid",
                    title="CC UUID",
                    subtitle=("selected_session.cc_session_uuid",),
                    prepend_icon="mdi-fingerprint",
                )
                # CC Metrics row (SESSION-CC-01-v1)
                v3.VListItem(
                    v_if="selected_session.cc_tool_count",
                    title="Tool Calls",
                    subtitle=(
                        "String(selected_session.cc_tool_count || 0)"
                        " + ' tools, '"
                        " + String(selected_session.cc_thinking_chars || 0)"
                        " + ' thinking chars, '"
                        " + String(selected_session.cc_compaction_count || 0)"
                        " + ' compactions'",
                    ),
                    prepend_icon="mdi-tools",
                )
                # Duration (EPIC-UI-VALUE-001, BUG-SESSION-DURATION-001 fix)
                v3.VListItem(
                    v_if="selected_session.duration",
                    title="Duration",
                    subtitle=(
                        "selected_session.duration",
                    ),
                    prepend_icon="mdi-timer-outline",
                )

    # Linked rules applied (EPIC-UI-VALUE-001)
    with v3.VCard(
        v_if=(
            "selected_session.linked_rules_applied?.length > 0"
        ),
        variant="outlined",
        classes="mt-4",
        __properties=["data-testid"],
        **{"data-testid": "session-linked-rules"},
    ):
        with v3.VCardTitle(classes="d-flex align-center", density="compact"):
            v3.VIcon("mdi-gavel", size="small", classes="mr-2")
            html.Span("Rules Applied")
            v3.VSpacer()
            v3.VChip(
                v_text="selected_session.linked_rules_applied.length",
                size="x-small",
                color="primary",
            )
        with v3.VCardText():
            v3.VChip(
                v_for="rule in selected_session.linked_rules_applied",
                v_text="rule",
                size="small",
                color="primary",
                variant="outlined",
                classes="mr-1 mb-1",
                prepend_icon="mdi-gavel",
            )

    # Linked decisions (EPIC-UI-VALUE-001)
    with v3.VCard(
        v_if=(
            "selected_session.linked_decisions?.length > 0"
        ),
        variant="outlined",
        classes="mt-4",
        __properties=["data-testid"],
        **{"data-testid": "session-linked-decisions"},
    ):
        with v3.VCardTitle(classes="d-flex align-center", density="compact"):
            v3.VIcon("mdi-scale-balance", size="small", classes="mr-2")
            html.Span("Decisions Made")
            v3.VSpacer()
            v3.VChip(
                v_text="selected_session.linked_decisions.length",
                size="x-small",
                color="warning",
            )
        with v3.VCardText():
            v3.VChip(
                v_for="dec in selected_session.linked_decisions",
                v_text="dec",
                size="small",
                color="warning",
                variant="outlined",
                classes="mr-1 mb-1",
                prepend_icon="mdi-scale-balance",
            )
