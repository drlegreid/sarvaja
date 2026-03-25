"""Task Comments Section Component.

Per EPIC-ISSUE-EVIDENCE P19: Resolution comment thread.
Positioned after resolution section in task detail view.
"""

from trame.widgets import vuetify3 as v3, html


def _build_comment_list() -> None:
    """Render existing comments as a list."""
    with html.Div(
        v_if="(task_comments || []).length > 0",
    ):
        with v3.VList(density="compact"):
            with v3.VListItem(
                v_for="(cmt, idx) in task_comments",
                **{":key": "idx"},
                __properties=["data-testid"],
                **{"data-testid": "task-comment-item"},
            ):
                with v3.VListItemTitle():
                    with html.Div(classes="d-flex align-center"):
                        v3.VIcon(
                            "mdi-comment-account",
                            size="small",
                            classes="mr-2",
                        )
                        html.Strong(
                            "{{ cmt.author || 'Unknown' }}",
                            classes="text-body-2",
                        )
                        html.Span(
                            "{{ cmt.created_at ? "
                            "cmt.created_at.substring(0, 19)"
                            ".replace('T', ' ') : '' }}",
                            classes="text-caption text-grey ml-2",
                        )
                        v3.VSpacer()
                        v3.VBtn(
                            icon="mdi-delete-outline",
                            size="x-small",
                            variant="text",
                            color="error",
                            click=(
                                "trigger('delete_task_comment', "
                                "[selected_task.task_id || selected_task.id, "
                                "cmt.comment_id])"
                            ),
                        )
                with v3.VListItemSubtitle():
                    html.Pre(
                        "{{ cmt.body }}",
                        style=(
                            "white-space: pre-wrap; "
                            "font-size: 0.85rem; "
                            "margin: 4px 0 0 0; "
                            "padding: 0;"
                        ),
                    )
                v3.VDivider()


def _build_comment_input() -> None:
    """Render the new comment input form."""
    with html.Div(classes="mt-3"):
        v3.VTextarea(
            v_model=("task_comment_input", ""),
            label="Add a comment...",
            rows=2,
            auto_grow=True,
            variant="outlined",
            density="compact",
            __properties=["data-testid"],
            **{"data-testid": "task-comment-input"},
        )
        with html.Div(classes="d-flex justify-end mt-1"):
            v3.VBtn(
                "Post Comment",
                color="primary",
                variant="tonal",
                size="small",
                prepend_icon="mdi-send",
                disabled=("!task_comment_input || !task_comment_input.trim()",),
                loading=("task_comment_submitting",),
                click=(
                    "trigger('post_task_comment', "
                    "[selected_task.task_id || selected_task.id, "
                    "task_comment_input])"
                ),
                __properties=["data-testid"],
                **{"data-testid": "task-comment-submit"},
            )


def build_task_comments_section() -> None:
    """Build the task comments section.

    Shown below resolution section for any task (not just DONE).
    """
    with html.Div(
        v_if="!edit_task_mode && selected_task",
    ):
        v3.VDivider(classes="my-4")
        with v3.VCard(
            variant="outlined",
            __properties=["data-testid"],
            **{"data-testid": "task-comments-card"},
        ):
            with v3.VCardTitle(classes="d-flex align-center"):
                v3.VIcon(icon="mdi-comment-text-multiple", classes="mr-2")
                html.Span("Comments")
                v3.VChip(
                    v_text="(task_comments || []).length",
                    size="x-small",
                    color="grey",
                    variant="tonal",
                    classes="ml-2",
                )
                v3.VSpacer()
                v3.VBtn(
                    "Refresh",
                    variant="text",
                    size="small",
                    prepend_icon="mdi-refresh",
                    click=(
                        "selected_task && trigger('load_task_comments', "
                        "[selected_task.task_id || selected_task.id])"
                    ),
                    loading=("task_comments_loading",),
                )

            with v3.VCardText():
                # Loading state
                with v3.VProgressLinear(
                    v_if="task_comments_loading",
                    indeterminate=True,
                    color="primary",
                ):
                    pass

                # Comment list
                _build_comment_list()

                # Empty state
                html.Div(
                    "No comments yet",
                    v_if=(
                        "!task_comments_loading && "
                        "(task_comments || []).length === 0"
                    ),
                    classes="text-grey text-center py-2",
                )

                # New comment input
                _build_comment_input()
