"""
Session Conversation Transcript Component (GAP-SESSION-TRANSCRIPT-001).

Renders the full conversation flow for a Claude Code session:
user prompts, assistant responses, tool calls/results, thinking, compactions.

Per DOC-SIZE-01-v1: <300 lines.
Created: 2026-02-15
"""

from trame.widgets import vuetify3 as v3, html


# Entry type → (icon, color, indent class, label)
_ENTRY_STYLES = {
    "user_prompt": ("mdi-account", "blue", "", "User"),
    "assistant_text": ("mdi-robot", "green", "ml-4", "Assistant"),
    "tool_use": ("mdi-wrench", "orange", "ml-8", "Tool Call"),
    "tool_result": ("mdi-arrow-left-bold", "teal", "ml-8", "Tool Result"),
    "thinking": ("mdi-head-lightbulb", "purple", "ml-4", "Thinking"),
    "compaction": ("mdi-content-cut", "warning", "", "Compaction"),
}


def build_session_transcript_card() -> None:
    """Build the conversation transcript card for session detail."""

    with v3.VCard(
        v_if="selected_session",
        classes="mt-4",
        variant="outlined",
        __properties=["data-testid"],
        **{"data-testid": "session-transcript-card"},
    ):
        # Header with controls
        with v3.VCardTitle(classes="d-flex align-center"):
            v3.VIcon("mdi-message-text-outline", classes="mr-2")
            html.Span("Conversation Transcript")
            v3.VSpacer()

            # Entry count chip
            v3.VChip(
                "{{ session_transcript.length }} entries"
                " ({{ session_transcript_total }} total)",
                size="small",
                color="primary",
                variant="tonal",
                v_if="session_transcript_total > 0",
            )

            # Loading spinner
            v3.VProgressCircular(
                indeterminate=True,
                size=20,
                width=2,
                v_if="session_transcript_loading",
                classes="ml-2",
            )

        # Toggle switches
        with v3.VCardText(classes="py-1"):
            with html.Div(classes="d-flex align-center ga-4"):
                v3.VSwitch(
                    v_model="session_transcript_include_thinking",
                    label="Thinking",
                    color="purple",
                    density="compact",
                    hide_details=True,
                    change="trigger('toggle_transcript_thinking')",
                )
                v3.VSwitch(
                    v_model="session_transcript_include_user",
                    label="User Prompts",
                    color="blue",
                    density="compact",
                    hide_details=True,
                    change="trigger('toggle_transcript_user')",
                )

        v3.VDivider()

        # Empty state
        with v3.VCardText(v_if="!session_transcript_loading && session_transcript.length === 0"):
            with v3.VAlert(type="info", variant="tonal", density="compact"):
                html.Span(
                    "No transcript data available for this session. "
                    "CC sessions show full conversation flow. "
                    "Chat sessions show tool calls and thoughts captured during the session."
                )

        # Transcript entries
        with v3.VCardText(
            v_if="session_transcript.length > 0",
            style="max-height: 600px; overflow-y: auto;",
        ):
            _build_transcript_entries()

        # Pagination
        _build_transcript_pagination()


def _build_transcript_entries() -> None:
    """Render the list of transcript entries with type-specific styling."""
    with html.Div(
        v_for="(entry, idx) in session_transcript",
        key="idx",
        classes="mb-2",
    ):
        # Compaction marker — special alert style
        with v3.VAlert(
            v_if="entry.entry_type === 'compaction'",
            type="warning",
            variant="tonal",
            density="compact",
            icon="mdi-content-cut",
        ):
            html.Span("{{ entry.content }}")

        # Thinking — collapsible expansion panel
        with v3.VExpansionPanels(
            v_if="entry.entry_type === 'thinking'",
            variant="accordion",
        ):
            with v3.VExpansionPanel():
                with v3.VExpansionPanelTitle():
                    v3.VIcon("mdi-head-lightbulb", color="purple", size="small", classes="mr-2")
                    html.Span("Thinking", classes="text-purple font-weight-medium")
                    v3.VSpacer()
                    v3.VChip(
                        "{{ entry.content_length }} chars",
                        size="x-small",
                        color="purple",
                        variant="tonal",
                    )
                with v3.VExpansionPanelText():
                    html.Pre(
                        "{{ entry.content }}",
                        style="white-space: pre-wrap; word-break: break-word; "
                        "font-size: 0.85rem; max-height: 300px; overflow-y: auto;",
                    )
                    _build_expand_button()

        # User prompt
        with v3.VCard(
            v_if="entry.entry_type === 'user_prompt'",
            variant="tonal",
            color="blue",
            density="compact",
            classes="mb-1",
        ):
            with v3.VCardTitle(classes="text-body-2 py-1"):
                v3.VIcon("mdi-account", size="small", classes="mr-1")
                html.Span("User")
                v3.VSpacer()
                v3.VChip(
                    "{{ entry.timestamp?.substring(11, 19) }}",
                    size="x-small",
                    variant="text",
                )
            with v3.VCardText(classes="py-1"):
                html.Pre(
                    "{{ entry.content }}",
                    style="white-space: pre-wrap; word-break: break-word; font-size: 0.85rem;",
                )
                _build_expand_button()

        # Assistant text
        with v3.VCard(
            v_if="entry.entry_type === 'assistant_text'",
            variant="tonal",
            color="green",
            density="compact",
            classes="ml-4 mb-1",
        ):
            with v3.VCardTitle(classes="text-body-2 py-1"):
                v3.VIcon("mdi-robot", size="small", classes="mr-1")
                html.Span("Assistant")
                v3.VSpacer()
                v3.VChip(
                    "{{ entry.model }}",
                    size="x-small",
                    variant="text",
                    v_if="entry.model",
                )
                v3.VChip(
                    "{{ entry.timestamp?.substring(11, 19) }}",
                    size="x-small",
                    variant="text",
                )
            with v3.VCardText(classes="py-1"):
                html.Pre(
                    "{{ entry.content }}",
                    style="white-space: pre-wrap; word-break: break-word; font-size: 0.85rem;",
                )
                _build_expand_button()

        # Tool use (inbound call)
        with v3.VCard(
            v_if="entry.entry_type === 'tool_use'",
            variant="outlined",
            density="compact",
            classes="ml-8 mb-1",
        ):
            with v3.VCardTitle(classes="text-body-2 py-1"):
                v3.VIcon(
                    "{{ entry.is_mcp ? 'mdi-cloud' : 'mdi-wrench' }}",
                    size="small",
                    color="orange",
                    classes="mr-1",
                )
                html.Span("{{ entry.tool_name }}", classes="text-orange font-weight-medium")
                v3.VChip("inbound", size="x-small", color="orange", variant="tonal", classes="ml-2")
                v3.VChip("MCP", size="x-small", color="deep-purple", variant="tonal",
                         v_if="entry.is_mcp", classes="ml-1")
                v3.VSpacer()
                v3.VChip(
                    "{{ entry.timestamp?.substring(11, 19) }}",
                    size="x-small",
                    variant="text",
                )
            with v3.VCardText(classes="py-1"):
                html.Pre(
                    "{{ entry.content }}",
                    style="white-space: pre-wrap; word-break: break-word; "
                    "font-family: monospace; font-size: 0.8rem; "
                    "max-height: 200px; overflow-y: auto;",
                )
                _build_expand_button()

        # Tool result (outbound response)
        with v3.VCard(
            v_if="entry.entry_type === 'tool_result'",
            variant="outlined",
            density="compact",
            classes="ml-8 mb-1",
        ):
            with v3.VCardTitle(classes="text-body-2 py-1"):
                v3.VIcon("mdi-arrow-left-bold", size="small", color="teal", classes="mr-1")
                html.Span(
                    "{{ entry.tool_name || 'Result' }}",
                    classes="text-teal font-weight-medium",
                )
                v3.VChip("outbound", size="x-small", color="teal", variant="tonal", classes="ml-2")
                v3.VChip("error", size="x-small", color="error", variant="tonal",
                         v_if="entry.is_error", classes="ml-1")
                v3.VSpacer()
                v3.VChip(
                    "{{ entry.content_length }} chars",
                    size="x-small",
                    variant="text",
                )
            with v3.VCardText(classes="py-1"):
                html.Pre(
                    "{{ entry.content }}",
                    style="white-space: pre-wrap; word-break: break-word; "
                    "font-family: monospace; font-size: 0.8rem; "
                    "max-height: 200px; overflow-y: auto;",
                )
                _build_expand_button()


def _build_expand_button() -> None:
    """Show Full Content button for truncated entries."""
    v3.VBtn(
        "Show Full Content",
        v_if="entry.is_truncated",
        size="x-small",
        variant="text",
        color="primary",
        prepend_icon="mdi-arrow-expand",
        click="trigger('expand_transcript_entry', [entry.index])",
        classes="mt-1",
    )


def _build_transcript_pagination() -> None:
    """Pagination controls for transcript pages."""
    with v3.VCardActions(
        v_if="session_transcript_total > 50",
        classes="justify-center",
    ):
        v3.VBtn(
            "Previous",
            variant="text",
            prepend_icon="mdi-chevron-left",
            disabled=("session_transcript_page <= 1",),
            click="trigger('load_transcript_page', [session_transcript_page - 1])",
        )
        v3.VChip(
            "Page {{ session_transcript_page }}",
            variant="tonal",
            size="small",
        )
        v3.VBtn(
            "Next",
            variant="text",
            append_icon="mdi-chevron-right",
            disabled=("!session_transcript_has_more",),
            click="trigger('load_transcript_page', [session_transcript_page + 1])",
        )
