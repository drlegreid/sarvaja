*** Settings ***
Documentation    RF-006: E2E Data Integrity Tests
...              Per GAP-UI-AUDIT-2026-01-18: Verify data traceability
...              Per D.3: Uses shared keywords from common_setup.resource
Library          Collections
Library          libs/DataIntegrityE2ELibrary.py
Resource         ../resources/common_setup.resource
Test Tags        e2e    api    integrity    high    tasks    task    validate    TEST-COMP-02-v1

Suite Setup      Platform Setup

*** Test Cases ***
# =============================================================================
# Task-Session Linkage Tests
# =============================================================================

API Returns Tasks
    [Documentation]    Verify API returns tasks
    [Tags]    e2e    integrity    tasks    smoke
    ${tasks}=    Get All Tasks
    ${count}=    Get Length    ${tasks}
    Should Be True    ${count} > 0    API should return at least one task

Closed Tasks Have Session Linkage
    [Documentation]    Per TASK-LIFE-01-v1: Closed tasks SHOULD have session linkage
    [Tags]    e2e    integrity    linkage    baseline    TASK-LIFE-01-v1
    ${result}=    Check Task Session Linkage
    Handle Skippable Result    ${result}
    Log    Task-Session Linkage: ${result}[linkage_rate]% (${result}[with_linkage]/${result}[total_closed])
    # Baseline: 5% achieved 2026-01-19
    Should Be True    ${result}[linkage_rate] >= 5    Linkage below baseline: ${result}[linkage_rate]%

# =============================================================================
# Task-Evidence Linkage Tests
# =============================================================================

Implemented Tasks Have Evidence
    [Documentation]    Per TEST-FIX-01-v1: IMPLEMENTED tasks SHOULD have evidence
    [Tags]    e2e    integrity    evidence    backfill    TEST-FIX-01-v1
    ${result}=    Check Task Evidence Linkage
    Handle Skippable Result    ${result}
    Log    Task-Evidence Linkage: ${result}[evidence_rate]% (${result}[with_evidence]/${result}[total_implemented])
    # Informational - backfill needed if below 70%
    IF    ${result}[evidence_rate] < 70
        Log    WARNING: Evidence backfill needed (${result}[evidence_rate]% < 70%)
    END

# =============================================================================
# Session-Evidence Linkage Tests
# =============================================================================

Sessions Have Evidence Files
    [Documentation]    Sessions SHOULD have evidence files
    [Tags]    e2e    integrity    sessions    evidence
    ${result}=    Check Session Evidence Files
    Handle Skippable Result    ${result}
    Log    Session-Evidence: ${result}[evidence_rate]% (${result}[with_evidence_files]/${result}[total_sessions])
    Log    Files found: ${result}[files_found], missing: ${result}[files_missing]

# =============================================================================
# Task-Commit Linkage Tests
# =============================================================================

Tasks Have Commit Linkage
    [Documentation]    Per GAP-TASK-LINK-002: Tasks MAY have commit linkage
    [Tags]    e2e    integrity    commits    optional    GAP-TASK-LINK-002
    ${result}=    Check Task Commit Linkage
    Handle Skippable Result    ${result}
    Log    Task-Commit Linkage: ${result}[linkage_rate]% (${result}[with_commits]/${result}[total_tasks])

# =============================================================================
# Data Pollution Checks
# =============================================================================

No TEST Prefix Pollution
    [Documentation]    Per WORKFLOW-RD-01-v1: TEST-* entities should be cleaned
    [Tags]    e2e    integrity    pollution    cleanup
    ${result}=    Check Data Pollution
    Log    TEST tasks: ${result}[test_tasks], TEST rules: ${result}[test_rules]
    IF    ${result}[test_tasks] > 0 or ${result}[test_rules] > 0
        Log    WARNING: Data pollution detected - cleanup pending
        Log    TEST tasks: ${result}[sample_test_tasks]
        Log    TEST rules: ${result}[sample_test_rules]
    END

Rules Use Semantic IDs
    [Documentation]    Per META-TAXON-01-v1: All rules MUST use semantic IDs
    [Tags]    e2e    integrity    rules    taxonomy
    ${result}=    Check Data Pollution
    Should Be True    ${result}[legacy_rules] == 0
    ...    Found ${result}[legacy_rules] legacy RULE-XXX IDs: ${result}[sample_legacy_rules]

# =============================================================================
# Summary Report
# =============================================================================

Data Integrity Report
    [Documentation]    Generate comprehensive data integrity report
    [Tags]    e2e    integrity    report    summary
    ${report}=    Generate Integrity Report
    Handle Skippable Result    ${report}
    Log    \n========================================
    Log    DATA INTEGRITY REPORT
    Log    ========================================
    Log    Tasks: ${report}[total_tasks] total, ${report}[closed_tasks] closed
    Log    Sessions: ${report}[total_sessions] total
    Log    ----------------------------------------
    Log    Task→Session: ${report}[task_session_rate]%
    Log    Task→Evidence: ${report}[task_evidence_rate]%
    Log    Task→Commit: ${report}[task_commit_rate]%
    Log    Session→Evidence: ${report}[session_evidence_rate]%
    Log    ========================================
    Should Be True    ${report}[healthy]    Data integrity check failed
