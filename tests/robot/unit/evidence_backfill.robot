*** Settings ***
Documentation     Evidence Backfill MCP Tools Tests
...               Per A4: Evidence backfill (session→evidence linking)
...               Created: 2026-01-28 | Per BACKFILL-OPS-01-v1, SESSION-EVID-01-v1
Library           ../../libs/EvidenceBackfillLibrary.py
Force Tags        unit    evidence    backfill    medium    SESSION-EVID-01-v1    evidence-file    session    link

*** Test Cases ***
# =========================================================================
# Module Import Tests
# =========================================================================

Evidence Scanner Module Should Import
    [Documentation]    Verify evidence_scanner module imports with patterns
    [Tags]    smoke    import
    ${result}=    Evidence Scanner Module Imports
    Should Be True    ${result}[imported]
    Should Be True    ${result}[pattern_count] >= 4

Evidence Backfill Tools Should Import
    [Documentation]    Verify evidence_backfill MCP tools import
    [Tags]    smoke    import
    ${result}=    Evidence Backfill Tools Import
    Should Be True    ${result}[imported]

# =========================================================================
# Pattern Tests
# =========================================================================

Evidence Patterns Should Cover All Types
    [Documentation]    All evidence file types have glob patterns
    [Tags]    patterns
    ${result}=    Evidence Patterns Cover All Types
    Should Be True    ${result}[covers_expected]
    Should Be True    ${result}[count] >= 4

Extract Task Refs Should Find References
    [Documentation]    Task reference extraction from sample content
    [Tags]    extraction    patterns
    ${result}=    Extract Task Refs From Content
    Should Be True    ${result}[has_phase]
    Should Be True    ${result}[has_rd]
    Should Be True    ${result}[has_fh]

Extract Rule Refs Should Find References
    [Documentation]    Rule reference extraction from sample content
    [Tags]    extraction    patterns
    ${result}=    Extract Rule Refs From Content
    Should Be True    ${result}[has_semantic] or ${result}[has_legacy]
    Should Be True    ${result}[count] >= 2

Extract Gap Refs Should Find References
    [Documentation]    Gap reference extraction from sample content
    [Tags]    extraction    patterns
    ${result}=    Extract Gap Refs From Content
    Should Be True    ${result}[has_gaps]

# =========================================================================
# Scanner Function Tests
# =========================================================================

Scan All Evidence Should Find Files
    [Documentation]    scan_all_evidence_files finds evidence directory files
    [Tags]    scanner    filesystem
    ${result}=    Scan All Evidence Files Returns Results
    Should Be True    ${result}[has_results]
    Should Be True    ${result}[count] > 0

Scan Evidence Session Links Should Return Result
    [Documentation]    scan_evidence_session_links returns structured result
    [Tags]    scanner    filesystem
    ${result}=    Scan Evidence Session Links Returns Result
    Should Be True    ${result}[scanned] > 0

# =========================================================================
# MCP Tool Registration Tests
# =========================================================================

Backfill Should Register Five Tools
    [Documentation]    Mock MCP receives exactly 5 backfill tool registrations
    [Tags]    registration    mock
    ${result}=    Backfill Registers Five Tools
    Skip If    $result.get("skipped", False)    ${result.get("reason", "skipped")}
    Should Be Equal As Numbers    ${result}[count]    5
    Should Be True    ${result}[all_present]

Format Evidence Link Summary Should Return Dict
    [Documentation]    Summary formatter returns expected structure
    [Tags]    formatter
    ${result}=    Format Evidence Link Summary Returns Dict
    Should Be True    ${result}[is_dict]
    Should Be True    ${result}[has_scanned]
    Should Be True    ${result}[has_linked]
    Should Be Equal As Numbers    ${result}[scanned_value]    5
