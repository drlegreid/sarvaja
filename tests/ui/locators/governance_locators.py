"""
Governance Dashboard Locators.
Per RULE-004: Centralized selectors for UI testing.

IMPORTANT: These are the EXPECTED locators based on DSM specification.
GAP-UI-001 documents that data-testid attributes are MISSING.
Once implemented, these selectors will work.

Naming convention: {entity}_{view}_{element}
Example: rules_list_add_btn, rules_detail_title
"""

# =============================================================================
# NAVIGATION
# =============================================================================

NAV = {
    'rules_tab': '[data-testid="nav-rules"]',
    'decisions_tab': '[data-testid="nav-decisions"]',
    'sessions_tab': '[data-testid="nav-sessions"]',
    'tasks_tab': '[data-testid="nav-tasks"]',
    'search_tab': '[data-testid="nav-search"]',
}

# =============================================================================
# RULES ENTITY
# =============================================================================

RULES_LIST = {
    # Container
    'container': '[data-testid="rules-list"]',
    'table': '[data-testid="rules-table"]',
    'row': '[data-testid="rule-row"]',

    # Columns
    'col_id': '[data-testid="rule-col-id"]',
    'col_title': '[data-testid="rule-col-title"]',
    'col_status': '[data-testid="rule-col-status"]',
    'col_category': '[data-testid="rule-col-category"]',
    'col_priority': '[data-testid="rule-col-priority"]',

    # Actions
    'add_btn': '[data-testid="rules-add-btn"]',
    'row_view_btn': '[data-testid="rule-view-btn"]',
    'row_edit_btn': '[data-testid="rule-edit-btn"]',
    'row_delete_btn': '[data-testid="rule-delete-btn"]',

    # Filters
    'filter_status': '[data-testid="rules-filter-status"]',
    'filter_category': '[data-testid="rules-filter-category"]',
    'search_input': '[data-testid="rules-search"]',

    # Sort headers
    'sort_id': '[data-testid="rules-sort-id"]',
    'sort_title': '[data-testid="rules-sort-title"]',
    'sort_updated': '[data-testid="rules-sort-updated"]',
}

RULES_DETAIL = {
    # Container
    'container': '[data-testid="rule-detail"]',

    # Header
    'header_id': '[data-testid="rule-detail-id"]',
    'header_title': '[data-testid="rule-detail-title"]',
    'header_status': '[data-testid="rule-detail-status"]',

    # Content
    'directive': '[data-testid="rule-detail-directive"]',
    'category': '[data-testid="rule-detail-category"]',
    'priority': '[data-testid="rule-detail-priority"]',
    'created_at': '[data-testid="rule-detail-created"]',
    'updated_at': '[data-testid="rule-detail-updated"]',

    # Relations
    'related_rules': '[data-testid="rule-detail-related-rules"]',
    'related_decisions': '[data-testid="rule-detail-related-decisions"]',
    'related_sessions': '[data-testid="rule-detail-related-sessions"]',

    # Actions
    'edit_btn': '[data-testid="rule-detail-edit-btn"]',
    'deprecate_btn': '[data-testid="rule-detail-deprecate-btn"]',
    'history_btn': '[data-testid="rule-detail-history-btn"]',
    'back_btn': '[data-testid="rule-detail-back-btn"]',
}

RULES_FORM = {
    # Container
    'container': '[data-testid="rule-form"]',

    # Fields
    'input_id': '[data-testid="rule-form-id"]',
    'input_title': '[data-testid="rule-form-title"]',
    'input_directive': '[data-testid="rule-form-directive"]',
    'select_category': '[data-testid="rule-form-category"]',
    'select_priority': '[data-testid="rule-form-priority"]',
    'select_status': '[data-testid="rule-form-status"]',

    # Validation messages
    'error_id': '[data-testid="rule-form-error-id"]',
    'error_title': '[data-testid="rule-form-error-title"]',
    'error_directive': '[data-testid="rule-form-error-directive"]',

    # Actions
    'submit_btn': '[data-testid="rule-form-submit"]',
    'cancel_btn': '[data-testid="rule-form-cancel"]',
    'preview_btn': '[data-testid="rule-form-preview"]',
}

# =============================================================================
# DECISIONS ENTITY
# =============================================================================

DECISIONS_LIST = {
    'container': '[data-testid="decisions-list"]',
    'table': '[data-testid="decisions-table"]',
    'row': '[data-testid="decision-row"]',
    'col_id': '[data-testid="decision-col-id"]',
    'col_title': '[data-testid="decision-col-title"]',
    'col_date': '[data-testid="decision-col-date"]',
    'col_status': '[data-testid="decision-col-status"]',
}

DECISIONS_DETAIL = {
    'container': '[data-testid="decision-detail"]',
    'summary': '[data-testid="decision-detail-summary"]',
    'context': '[data-testid="decision-detail-context"]',
    'rationale': '[data-testid="decision-detail-rationale"]',
    'impacts': '[data-testid="decision-detail-impacts"]',
    'related_rules': '[data-testid="decision-detail-related-rules"]',
}

# =============================================================================
# SESSIONS ENTITY
# =============================================================================

SESSIONS_LIST = {
    'container': '[data-testid="sessions-list"]',
    'table': '[data-testid="sessions-table"]',
    'row': '[data-testid="session-row"]',
    'col_id': '[data-testid="session-col-id"]',
    'col_date': '[data-testid="session-col-date"]',
    'col_summary': '[data-testid="session-col-summary"]',
}

SESSIONS_DETAIL = {
    'container': '[data-testid="session-detail"]',
    'timeline': '[data-testid="session-detail-timeline"]',
    'evidence': '[data-testid="session-detail-evidence"]',
    'decisions': '[data-testid="session-detail-decisions"]',
    'tasks': '[data-testid="session-detail-tasks"]',
}

# =============================================================================
# COMMON COMPONENTS
# =============================================================================

COMMON = {
    # Loading states - GAP-UI-005
    'loading_spinner': '[data-testid="loading-spinner"]',
    'loading_overlay': '[data-testid="loading-overlay"]',

    # Error states - GAP-UI-005
    'error_banner': '[data-testid="error-banner"]',
    'error_message': '[data-testid="error-message"]',
    'retry_btn': '[data-testid="retry-btn"]',

    # Empty states
    'empty_state': '[data-testid="empty-state"]',
    'empty_message': '[data-testid="empty-message"]',

    # Pagination
    'pagination': '[data-testid="pagination"]',
    'page_prev': '[data-testid="page-prev"]',
    'page_next': '[data-testid="page-next"]',
    'page_size': '[data-testid="page-size"]',

    # Dialogs
    'confirm_dialog': '[data-testid="confirm-dialog"]',
    'confirm_yes': '[data-testid="confirm-yes"]',
    'confirm_no': '[data-testid="confirm-no"]',
}
