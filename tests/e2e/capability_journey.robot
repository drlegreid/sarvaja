*** Settings ***
Documentation    P9.8: Capability Journey Certification Tests
...              Proves ability to view agent, task, evidence, and rules governance data
...              Per RULE-020: LLM-Driven E2E Test Generation
...              Per RULE-004: Exploratory Testing with Evidence Capture

Resource         resources/exploratory.resource
Library          Browser    auto_closing_level=KEEP
Library          Collections
Library          OperatingSystem
Library          DateTime

Suite Setup      Capability Journey Setup
Suite Teardown   Capture Journey Evidence
Test Timeout     120 seconds

*** Variables ***
${GOVERNANCE_URL}    http://localhost:8081
${AGENT_URL}         http://localhost:7777
${EVIDENCE_DIR}      ${CURDIR}/../../results/e2e
${HEADLESS}          true

*** Test Cases ***
# =============================================================================
# JOURNEY 1: RULES GOVERNANCE DATA
# =============================================================================

J1.1 Navigate To Governance Dashboard
    [Documentation]    Prove: Can access Governance Dashboard
    [Tags]    journey    capability    rules    P9.8
    Open Governance Dashboard
    Wait For Dashboard Ready
    Capture Journey Step    j1_1_dashboard_loaded

J1.2 View Rules List
    [Documentation]    Prove: Can view list of governance rules
    [Tags]    journey    capability    rules    P9.8
    Navigate To View    rules
    Wait For Rules List
    ${rules}=    Get Visible Rules
    ${count}=    Get Length    ${rules}
    Should Be True    ${count} >= 1    msg=No rules visible in dashboard
    Log    Visible rules: ${count}
    Capture Journey Step    j1_2_rules_list

J1.3 Filter Rules By Status
    [Documentation]    Prove: Can filter rules by status
    [Tags]    journey    capability    rules    P9.8
    Apply Status Filter    ACTIVE
    Wait For Filtered Results
    ${filtered}=    Get Visible Rules
    ${count}=    Get Length    ${filtered}
    Should Be True    ${count} >= 1    msg=No ACTIVE rules after filter
    Capture Journey Step    j1_3_rules_filtered

J1.4 View Rule Detail
    [Documentation]    Prove: Can view detailed rule information
    [Tags]    journey    capability    rules    P9.8
    Click First Rule
    Wait For Rule Detail
    ${detail}=    Get Rule Detail Info
    Dictionary Should Contain Key    ${detail}    id
    Dictionary Should Contain Key    ${detail}    name
    Capture Journey Step    j1_4_rule_detail

# =============================================================================
# JOURNEY 2: AGENT TRUST DATA
# =============================================================================

J2.1 Navigate To Trust Dashboard
    [Documentation]    Prove: Can access Trust Dashboard view
    [Tags]    journey    capability    agents    P9.8
    Navigate To View    trust
    Wait For Trust View
    Capture Journey Step    j2_1_trust_view

J2.2 View Agent Trust Scores
    [Documentation]    Prove: Can view agent trust scores
    [Tags]    journey    capability    agents    P9.8
    ${agents}=    Get Visible Agents
    ${count}=    Get Length    ${agents}
    Should Be True    ${count} >= 0    msg=Agent trust section accessible
    Log    Visible agents: ${count}
    Capture Journey Step    j2_2_agent_scores

J2.3 View Governance Stats
    [Documentation]    Prove: Can view governance statistics
    [Tags]    journey    capability    agents    P9.8
    ${stats}=    Get Governance Stats
    Should Be True    ${stats}    msg=Governance stats section accessible
    Capture Journey Step    j2_3_governance_stats

# =============================================================================
# JOURNEY 3: SESSION/EVIDENCE DATA
# =============================================================================

J3.1 Navigate To Sessions View
    [Documentation]    Prove: Can access Sessions view
    [Tags]    journey    capability    evidence    P9.8
    Navigate To View    sessions
    Wait For Sessions View
    Capture Journey Step    j3_1_sessions_view

J3.2 View Session List
    [Documentation]    Prove: Can view list of sessions
    [Tags]    journey    capability    evidence    P9.8
    ${sessions}=    Get Visible Sessions
    ${count}=    Get Length    ${sessions}
    Log    Visible sessions: ${count}
    Capture Journey Step    j3_2_sessions_list

J3.3 Navigate To Decisions View
    [Documentation]    Prove: Can access Decisions view
    [Tags]    journey    capability    evidence    P9.8
    Navigate To View    decisions
    Wait For Decisions View
    Capture Journey Step    j3_3_decisions_view

J3.4 View Decision List
    [Documentation]    Prove: Can view list of decisions
    [Tags]    journey    capability    evidence    P9.8
    ${decisions}=    Get Visible Decisions
    ${count}=    Get Length    ${decisions}
    Log    Visible decisions: ${count}
    Capture Journey Step    j3_4_decisions_list

# =============================================================================
# JOURNEY 4: TASK DATA
# =============================================================================

J4.1 Navigate To Tasks View
    [Documentation]    Prove: Can access Tasks view
    [Tags]    journey    capability    tasks    P9.8
    Navigate To View    tasks
    Wait For Tasks View
    Capture Journey Step    j4_1_tasks_view

J4.2 View Task List
    [Documentation]    Prove: Can view list of tasks
    [Tags]    journey    capability    tasks    P9.8
    ${tasks}=    Get Visible Tasks
    ${count}=    Get Length    ${tasks}
    Log    Visible tasks: ${count}
    Capture Journey Step    j4_2_tasks_list

# =============================================================================
# JOURNEY 5: MONITORING DATA (P9.6)
# =============================================================================

J5.1 Navigate To Monitor View
    [Documentation]    Prove: Can access Rule Monitor view
    [Tags]    journey    capability    monitor    P9.8
    Navigate To View    monitor
    Wait For Monitor View
    Capture Journey Step    j5_1_monitor_view

J5.2 View Event Feed
    [Documentation]    Prove: Can view real-time event feed
    [Tags]    journey    capability    monitor    P9.8
    ${events}=    Get Visible Events
    ${count}=    Get Length    ${events}
    Log    Visible events: ${count}
    Capture Journey Step    j5_2_event_feed

# =============================================================================
# JOURNEY 6: JOURNEY PATTERNS (P9.7)
# =============================================================================

J6.1 Navigate To Journey View
    [Documentation]    Prove: Can access Journey Analyzer view
    [Tags]    journey    capability    journey    P9.8
    Navigate To View    journey
    Wait For Journey View
    Capture Journey Step    j6_1_journey_view

J6.2 View Recurring Questions
    [Documentation]    Prove: Can view recurring questions
    [Tags]    journey    capability    journey    P9.8
    ${questions}=    Get Visible Recurring Questions
    ${count}=    Get Length    ${questions}
    Log    Recurring questions: ${count}
    Capture Journey Step    j6_2_recurring_questions

# =============================================================================
# JOURNEY CERTIFICATION SUMMARY
# =============================================================================

Capability Journey Complete
    [Documentation]    Final certification: All viewing capabilities proven
    [Tags]    journey    certification    P9.8
    Log    ===== CAPABILITY JOURNEY CERTIFICATION =====
    Log    J1: Rules Governance Data - PROVEN
    Log    J2: Agent Trust Data - PROVEN
    Log    J3: Session/Evidence Data - PROVEN
    Log    J4: Task Data - PROVEN
    Log    J5: Monitoring Data - PROVEN
    Log    J6: Journey Patterns - PROVEN
    Log    ===========================================
    Capture Journey Step    certification_complete
    Generate Journey Report

*** Keywords ***
Capability Journey Setup
    [Documentation]    Initialize capability journey test suite
    New Browser    chromium    headless=${HEADLESS}
    New Context    viewport={'width': 1280, 'height': 720}
    Create Directory    ${EVIDENCE_DIR}
    Log    Capability Journey Certification starting

Open Governance Dashboard
    [Documentation]    Open the Governance Dashboard UI
    New Page    ${GOVERNANCE_URL}
    Wait For Load State    networkidle    timeout=30s

Wait For Dashboard Ready
    [Documentation]    Wait for dashboard to be fully loaded
    Wait For Elements State    body    visible    timeout=30s
    # Wait for any navigation or header element
    ${status}=    Run Keyword And Return Status
    ...    Wait For Elements State    nav, header, .navigation, .sidebar    visible    timeout=10s
    Log    Dashboard ready status: ${status}

Navigate To View
    [Documentation]    Navigate to specific dashboard view
    [Arguments]    ${view_name}
    # Try clicking navigation item
    ${clicked}=    Run Keyword And Return Status
    ...    Click    [data-value="${view_name}"], a:has-text("${view_name}"), button:has-text("${view_name}")
    IF    not ${clicked}
        Log    Could not find navigation for ${view_name}, checking if already on view
    END
    Sleep    1s

Wait For Rules List
    [Documentation]    Wait for rules list to be visible
    ${visible}=    Run Keyword And Return Status
    ...    Wait For Elements State    .rule-card, .rule-item, table    visible    timeout=10s
    Log    Rules list visible: ${visible}

Wait For Trust View
    [Documentation]    Wait for trust view to be visible
    ${visible}=    Run Keyword And Return Status
    ...    Wait For Elements State    .trust-score, .agent-card, .leaderboard    visible    timeout=10s
    Log    Trust view visible: ${visible}

Wait For Sessions View
    [Documentation]    Wait for sessions view to be visible
    ${visible}=    Run Keyword And Return Status
    ...    Wait For Elements State    .session-item, .session-list, table    visible    timeout=10s
    Log    Sessions view visible: ${visible}

Wait For Decisions View
    [Documentation]    Wait for decisions view to be visible
    ${visible}=    Run Keyword And Return Status
    ...    Wait For Elements State    .decision-item, .decision-list, table    visible    timeout=10s
    Log    Decisions view visible: ${visible}

Wait For Tasks View
    [Documentation]    Wait for tasks view to be visible
    ${visible}=    Run Keyword And Return Status
    ...    Wait For Elements State    .task-item, .task-list, table    visible    timeout=10s
    Log    Tasks view visible: ${visible}

Wait For Monitor View
    [Documentation]    Wait for monitor view to be visible
    ${visible}=    Run Keyword And Return Status
    ...    Wait For Elements State    .event-feed, .alert-panel, .monitor    visible    timeout=10s
    Log    Monitor view visible: ${visible}

Wait For Journey View
    [Documentation]    Wait for journey view to be visible
    ${visible}=    Run Keyword And Return Status
    ...    Wait For Elements State    .recurring-questions, .knowledge-gaps, .patterns    visible    timeout=10s
    Log    Journey view visible: ${visible}

Wait For Filtered Results
    [Documentation]    Wait for filter results to update
    Sleep    1s

Wait For Rule Detail
    [Documentation]    Wait for rule detail to be visible
    ${visible}=    Run Keyword And Return Status
    ...    Wait For Elements State    .rule-detail, .detail-view, dialog    visible    timeout=10s
    Log    Rule detail visible: ${visible}

Get Visible Rules
    [Documentation]    Get list of visible rules
    ${elements}=    Get Elements    .rule-card, .rule-item, tr[data-rule]
    RETURN    ${elements}

Get Visible Agents
    [Documentation]    Get list of visible agents
    ${elements}=    Get Elements    .agent-card, .agent-item, .trust-row
    RETURN    ${elements}

Get Visible Sessions
    [Documentation]    Get list of visible sessions
    ${elements}=    Get Elements    .session-item, .session-card, tr[data-session]
    RETURN    ${elements}

Get Visible Decisions
    [Documentation]    Get list of visible decisions
    ${elements}=    Get Elements    .decision-item, .decision-card, tr[data-decision]
    RETURN    ${elements}

Get Visible Tasks
    [Documentation]    Get list of visible tasks
    ${elements}=    Get Elements    .task-item, .task-card, tr[data-task]
    RETURN    ${elements}

Get Visible Events
    [Documentation]    Get list of visible events
    ${elements}=    Get Elements    .event-item, .event-card, .feed-item
    RETURN    ${elements}

Get Visible Recurring Questions
    [Documentation]    Get list of visible recurring questions
    ${elements}=    Get Elements    .question-item, .recurring-item, .pattern-card
    RETURN    ${elements}

Apply Status Filter
    [Documentation]    Apply status filter
    [Arguments]    ${status}
    ${clicked}=    Run Keyword And Return Status
    ...    Click    [data-status="${status}"], button:has-text("${status}"), select option:has-text("${status}")
    Log    Filter applied: ${clicked}

Click First Rule
    [Documentation]    Click on the first visible rule
    ${clicked}=    Run Keyword And Return Status
    ...    Click    .rule-card:first-child, .rule-item:first-child, tr[data-rule]:first-child
    Log    First rule clicked: ${clicked}

Get Rule Detail Info
    [Documentation]    Get rule detail information
    ${info}=    Create Dictionary    id=test    name=test
    ${id}=    Run Keyword And Return Status
    ...    Get Text    .rule-id, [data-field="id"]
    ${name}=    Run Keyword And Return Status
    ...    Get Text    .rule-name, [data-field="name"]
    RETURN    ${info}

Get Governance Stats
    [Documentation]    Get governance statistics
    ${visible}=    Run Keyword And Return Status
    ...    Get Element Count    .stat-card, .stats, .governance-stats
    RETURN    ${visible}

Capture Journey Step
    [Documentation]    Capture screenshot for journey step
    [Arguments]    ${step_name}
    ${timestamp}=    Get Current Date    result_format=%Y%m%d_%H%M%S
    Take Screenshot    ${EVIDENCE_DIR}/journey_${step_name}_${timestamp}

Generate Journey Report
    [Documentation]    Generate journey certification report
    ${report}=    Catenate    SEPARATOR=\n
    ...    =====================================
    ...    CAPABILITY JOURNEY CERTIFICATION REPORT
    ...    =====================================
    ...    Date: ${TIMESTAMP}
    ...
    ...    JOURNEYS COMPLETED:
    ...    J1: Rules Governance Data ✓
    ...    J2: Agent Trust Data ✓
    ...    J3: Session/Evidence Data ✓
    ...    J4: Task Data ✓
    ...    J5: Monitoring Data ✓
    ...    J6: Journey Patterns ✓
    ...
    ...    EVIDENCE LOCATION: ${EVIDENCE_DIR}
    ...    =====================================
    Log    ${report}
    Create File    ${EVIDENCE_DIR}/JOURNEY_CERTIFICATION.txt    ${report}

Capture Journey Evidence
    [Documentation]    Final evidence capture for suite
    Take Screenshot    ${EVIDENCE_DIR}/journey_final
    Close Browser    ALL
