*** Comments ***
Centralized Selectors for Sarvaja Dashboard
=============================================
Per TEST-E2E-FRAMEWORK-01-v1: Single source of truth for all selectors.
Uses data-testid attributes from Trame/Vuetify UI views.

All selectors use CSS syntax compatible with Browser Library.
Updated: 2026-02-20

*** Variables ***
# ── Dashboard & App ──
${APP_TITLE}                    Sarvaja Governance
${DASHBOARD_URL}                http://localhost:8081

# ── Navigation tabs ──
${NAV_RULES}                    [data-testid='nav-rules']
${NAV_AGENTS}                   [data-testid='nav-agents']
${NAV_TASKS}                    [data-testid='nav-tasks']
${NAV_SESSIONS}                 [data-testid='nav-sessions']
${NAV_TRUST}                    [data-testid='nav-trust']
${NAV_INFRA}                    [data-testid='nav-infra']

# ── Toolbar chips ──
${TOOLBAR_RULES_CHIP}           [data-testid='toolbar-rules-chip']
${TOOLBAR_DECISIONS_CHIP}       [data-testid='toolbar-decisions-chip']
${TOOLBAR_HEALTH_CHIP}          [data-testid='toolbar-health-chip']

# ── Rules view ──
${RULES_TABLE}                  [data-testid='rules-table']
${RULES_SEARCH}                 [data-testid='rules-search']
${RULES_ADD_BTN}                text=Add Rule

# ── Tasks view ──
${TASKS_SEARCH}                 [data-testid='tasks-search']
${TASKS_ADD_BTN}                text=Add Task
${TASK_DETAIL}                  [data-testid='task-detail']
${TASK_EDIT_BTN}                [data-testid='task-detail-edit-btn']

# ── Sessions view ──
${SESSION_DETAIL}               [data-testid='session-detail']
${SESSION_BACK_BTN}             [data-testid='session-detail-back-btn']
${SESSION_ID_LABEL}             [data-testid='session-detail-id']

# ── Infrastructure view ──
${INFRA_CARD_TYPEDB}            [data-testid='infra-card-typedb']
${INFRA_CARD_CHROMADB}          [data-testid='infra-card-chromadb']
${INFRA_STAT_MEMORY}            [data-testid='infra-stat-memory']
${INFRA_STAT_HASH}              [data-testid='infra-stat-hash']
${INFRA_REFRESH_BTN}            [data-testid='infra-refresh-btn']
${INFRA_START_ALL}              [data-testid='infra-start-all']
${INFRA_RESTART}                [data-testid='infra-restart']
${INFRA_CLEANUP}                [data-testid='infra-cleanup']

# ── Generic table selectors ──
${TABLE_DATA_ROW}               tbody tr:has(td)
${TABLE_FIRST_ROW}              tbody tr:has(td) >> nth=0
${TABLE_FIRST_CELL}             tbody tr:has(td) td >> nth=0
