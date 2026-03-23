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

# ── Navigation tabs (17 items — matches NAVIGATION_ITEMS in constants.py) ──
${NAV_CHAT}                     [data-testid='nav-chat']
${NAV_RULES}                    [data-testid='nav-rules']
${NAV_AGENTS}                   [data-testid='nav-agents']
${NAV_TASKS}                    [data-testid='nav-tasks']
${NAV_SESSIONS}                 [data-testid='nav-sessions']
${NAV_EXECUTIVE}                [data-testid='nav-executive']
${NAV_DECISIONS}                [data-testid='nav-decisions']
${NAV_IMPACT}                   [data-testid='nav-impact']
${NAV_TRUST}                    [data-testid='nav-trust']
${NAV_WORKFLOW}                 [data-testid='nav-workflow']
${NAV_AUDIT}                    [data-testid='nav-audit']
${NAV_MONITOR}                  [data-testid='nav-monitor']
${NAV_INFRA}                    [data-testid='nav-infra']
${NAV_METRICS}                  [data-testid='nav-metrics']
${NAV_TESTS}                    [data-testid='nav-tests']
${NAV_PROJECTS}                 [data-testid='nav-projects']
${NAV_WORKSPACES}               [data-testid='nav-workspaces']

# ── Toolbar chips ──
${TOOLBAR_RULES_CHIP}           [data-testid='toolbar-rules-chip']
${TOOLBAR_DECISIONS_CHIP}       [data-testid='toolbar-decisions-chip']
${TOOLBAR_HEALTH_CHIP}          [data-testid='toolbar-health-chip']

# ── Rules view ──
${RULES_TABLE}                  [data-testid='rules-table']
${RULES_SEARCH}                 [data-testid='rules-search']
${RULES_ADD_BTN}                text=Add Rule

# ── Tasks view ──
${TASKS_TABLE}                  [data-testid='tasks-table']
${TASKS_SEARCH}                 [data-testid='tasks-search']
${TASKS_ADD_BTN}                text=Add Task
${TASK_DETAIL}                  [data-testid='task-detail']
${TASK_EDIT_BTN}                [data-testid='task-detail-edit-btn']
# Task quality selectors (Phase B — EPIC-TASK-QUALITY-V1)
${TASKS_HIDE_TEST_TOGGLE}       text=Hide test tasks
${TASKS_TABLE_HEADER}           ${TASKS_TABLE} thead
${TASKS_TABLE_BODY}             ${TASKS_TABLE} tbody
${TASKS_REFRESH_BTN}            [data-testid='refresh-btn']

# ── Sessions view ──
${SESSIONS_TABLE}               [data-testid='sessions-table']
${SESSIONS_SEARCH}              [data-testid='sessions-search']
${SESSIONS_ADD_BTN}             [data-testid='sessions-add-btn']
${SESSION_DETAIL}               [data-testid='session-detail']
${SESSION_BACK_BTN}             [data-testid='session-detail-back-btn']
${SESSION_ID_LABEL}             [data-testid='session-detail-id']

# ── Infrastructure view ──
${INFRA_DASHBOARD}              [data-testid='infra-dashboard']
${INFRA_CARD_TYPEDB}            [data-testid='infra-card-typedb']
${INFRA_CARD_CHROMADB}          [data-testid='infra-card-chromadb']
${INFRA_STAT_MEMORY}            [data-testid='infra-stat-memory']
${INFRA_STAT_HASH}              [data-testid='infra-stat-hash']
${INFRA_REFRESH_BTN}            [data-testid='infra-refresh-btn']
${INFRA_START_ALL}              [data-testid='infra-start-all']
${INFRA_RESTART}                [data-testid='infra-restart']
${INFRA_CLEANUP}                [data-testid='infra-cleanup']

# ── Workspaces view ──
${WORKSPACES_LIST}              [data-testid='workspaces-list']
${WORKSPACE_CREATE_BTN}         [data-testid='workspace-create-btn']
${WORKSPACE_REFRESH_BTN}        [data-testid='workspace-refresh-btn']
${WORKSPACE_DETAIL}             [data-testid='workspace-detail']
${WORKSPACE_DETAIL_BACK_BTN}    [data-testid='workspace-detail-back-btn']

# ── Projects view ──
${PROJECTS_TABLE}               [data-testid='projects-table']
${PROJECTS_LIST}                [data-testid='projects-list']
${PROJECTS_ADD_BTN}             [data-testid='projects-add-btn']

# ── Chat view ──
${CHAT_VIEW}                    [data-testid='chat-view']
${CHAT_INPUT}                   [data-testid='chat-input']
${CHAT_SEND_BTN}                [data-testid='chat-send-btn']

# ── Trust view ──
${TRUST_DASHBOARD}              [data-testid='trust-dashboard']
${TRUST_REFRESH_BTN}            [data-testid='trust-refresh-btn']

# ── Generic table selectors ──
${TABLE_DATA_ROW}               tbody tr:has(td)
${TABLE_FIRST_ROW}              tbody tr:has(td) >> nth=0
${TABLE_FIRST_CELL}             tbody tr:has(td) td >> nth=0
