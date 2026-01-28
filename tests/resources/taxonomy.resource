*** Settings ***
Documentation    RF-003: Test Tagging Taxonomy for Robot Framework
...              Per TEST-TAXON-01-v1: Standardized tags for selective execution
...              Implements dimensions: Scope, Domain, Entity, Action, Concern, CI

*** Variables ***
# =============================================================================
# RF-003: TAG TAXONOMY REFERENCE
# All Robot Framework tests MUST use tags from these dimensions
# =============================================================================

# -----------------------------------------------------------------------------
# DIMENSION 1: EXECUTION SCOPE (REQUIRED - at least ONE)
# What infrastructure does this test need?
# -----------------------------------------------------------------------------
# Tag             | Description                          | Robot Runner
# --------------- | ------------------------------------ | ----------------------
# unit            | No external dependencies             | robot --include unit
# integration     | Needs TypeDB/ChromaDB                | robot --include integration
# e2e             | Full stack required                  | robot --include e2e
# api             | Needs REST server on :8082           | robot --include api
# browser         | Needs Browser library (Playwright)   | robot --include browser
# smoke           | Quick validation suite               | robot --include smoke
# dryrun          | Syntax validation only               | robot --dryrun

@{SCOPE_TAGS}     unit    integration    e2e    api    browser    smoke    dryrun

# -----------------------------------------------------------------------------
# DIMENSION 2: DOMAIN (RECOMMENDED)
# What system area is being tested?
# -----------------------------------------------------------------------------
# Tag             | Coverage
# --------------- | ------------------------------------------
# rules           | Rule CRUD, validation, conflict detection
# agents          | Agent registration, trust scoring
# sessions        | Session lifecycle, decisions
# tasks           | Task creation, completion, linking
# evidence        | Evidence collection, reporting
# monitor         | Dashboard, health monitoring

@{DOMAIN_TAGS}    rules    agents    sessions    tasks    evidence    monitor    gaps    mcp    hooks    ui    chroma    typedb

# -----------------------------------------------------------------------------
# DIMENSION 3: ENTITY (OPTIONAL)
# What specific entity type?
# -----------------------------------------------------------------------------
@{ENTITY_TAGS}    rule    agent    session    task    proposal    trust    decision    gap

# -----------------------------------------------------------------------------
# DIMENSION 4: ACTION (OPTIONAL)
# What CRUD operation or action?
# -----------------------------------------------------------------------------
# Tag             | Description
# --------------- | ------------------------------------------
# create          | POST / INSERT operations
# read            | GET / MATCH operations
# read_detail     | GET single entity with full details
# update          | PUT/PATCH / UPDATE operations
# delete          | DELETE / REMOVE operations
# list            | GET collection / MATCH multiple
# validate        | Validation logic tests
# migrate         | Data migration tests
# sync            | Synchronization tests

@{ACTION_TAGS}    create    read    read_detail    update    delete    list    validate    migrate    sync

# -----------------------------------------------------------------------------
# DIMENSION 5: CONCERN / QUALITY (OPTIONAL - CRUCSS Model)
# What quality attribute is being verified?
# -----------------------------------------------------------------------------
# Tag             | CRUCSS Pillar           | Description
# --------------- | ----------------------- | -------------------------
# capability      | Capability (P9.8)       | Feature completeness
# reliability     | Reliability (P9.5)      | Error handling, recovery
# usability       | Usability (P8.9)        | UX, accessibility
# security        | Security (P9.0)         | Auth, data protection
# scalability     | Scalability (P8.5)      | Load, performance
# supportability  | Supportability (P8.3)   | Logging, diagnostics

@{CONCERN_TAGS}    capability    reliability    usability    security    scalability    supportability    performance    accessibility    a11y

# -----------------------------------------------------------------------------
# DIMENSION 6: CI/CD INTEGRATION (OPTIONAL)
# When should this test run?
# -----------------------------------------------------------------------------
# Tag             | CI Stage               | Description
# --------------- | ---------------------- | -------------------------
# critical        | Every commit           | Must pass for merge
# regression      | Daily                  | Full regression suite
# nightly         | Overnight              | Long-running tests
# manual          | On-demand              | Requires human trigger
# skip            | Never (disabled)       | Temporarily disabled

@{CI_TAGS}    critical    regression    nightly    manual    skip    slow    fast

# -----------------------------------------------------------------------------
# DIMENSION 7: GOVERNANCE LINKING (RECOMMENDED FOR E2E)
# Link tests to rules for evidence collection
# -----------------------------------------------------------------------------
# Use rule IDs as tags: TEST-GUARD-01-v1, SESSION-EVID-01-v1, etc.
# Example: [Tags]    e2e    sessions    evidence    SESSION-EVID-01-v1

*** Keywords ***
# =============================================================================
# TAG VALIDATION KEYWORDS
# =============================================================================

Validate Test Has Scope Tag
    [Documentation]    Verify current test has at least one scope tag
    [Arguments]    @{test_tags}
    ${has_scope}=    Set Variable    ${FALSE}
    FOR    ${tag}    IN    @{test_tags}
        ${is_scope}=    Evaluate    "${tag}" in ${SCOPE_TAGS}
        IF    ${is_scope}
            ${has_scope}=    Set Variable    ${TRUE}
            RETURN
        END
    END
    IF    not ${has_scope}
        Log    WARNING: Test missing scope tag (unit/integration/e2e/api/browser/smoke)    WARN
    END

Get Tags For Domain
    [Documentation]    Return recommended tags for a given domain
    [Arguments]    ${domain}
    IF    "${domain}" == "rules"
        RETURN    rules    rule    crud
    ELSE IF    "${domain}" == "agents"
        RETURN    agents    agent    trust
    ELSE IF    "${domain}" == "sessions"
        RETURN    sessions    session    decision
    ELSE IF    "${domain}" == "tasks"
        RETURN    tasks    task    lifecycle
    ELSE IF    "${domain}" == "evidence"
        RETURN    evidence    rf008
    END
    RETURN    ${domain}

# =============================================================================
# USAGE EXAMPLES (Reference Only)
# =============================================================================
#
# *** Test Cases ***
# Rule Creation Should Succeed
#     [Documentation]    Per TEST-TAXON-01-v1: Example of proper tagging
#     [Tags]    api    rules    create    critical    SESSION-EVID-01-v1
#     ...
#
# Agent Trust Score Is Calculated
#     [Tags]    integration    agents    trust    capability    P9.8
#     ...
#
# Dashboard Loads Without Errors
#     [Tags]    e2e    browser    monitor    ui    smoke
#     ...
#
# =============================================================================
