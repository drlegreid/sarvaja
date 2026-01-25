*** Settings ***
Documentation    RF-004: Unit Tests - Health Modes and AMNESIA Detection
...              Migrated from tests/test_health_modes.py
...              Per GAP-AMNESIA-OUTPUT-001 and GAP-HEALTH-AGGRESSIVE-001
Library          Collections
Library          ../../libs/HealthModesLibrary.py

*** Test Cases ***
# =============================================================================
# AMNESIA Output in Summary Tests - GAP-AMNESIA-OUTPUT-001
# =============================================================================

Format Summary Without Amnesia
    [Documentation]    GIVEN no amnesia WHEN format_summary THEN no warning
    [Tags]    unit    health    amnesia    summary
    ${result}=    Format Summary Without Amnesia
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[health_ok]
    Should Be True    ${result}[no_amnesia]

Format Summary With Amnesia Detected
    [Documentation]    GIVEN amnesia detected WHEN format_summary THEN warning
    [Tags]    unit    health    amnesia    summary
    ${result}=    Format Summary With Amnesia Detected
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[health_ok]
    Should Be True    ${result}[amnesia_shown]

Format Summary Amnesia Not Detected
    [Documentation]    GIVEN low confidence WHEN format_summary THEN no warning
    [Tags]    unit    health    amnesia    summary
    ${result}=    Format Summary Amnesia Not Detected
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[health_ok]
    Should Be True    ${result}[no_amnesia]

# =============================================================================
# Health Mode Configuration Tests - GAP-HEALTH-AGGRESSIVE-001
# =============================================================================

Health Mode Quiet Threshold
    [Documentation]    GIVEN quiet mode WHEN check THEN 0.70 threshold
    [Tags]    unit    health    mode    threshold
    ${result}=    Health Mode Quiet Threshold
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[mode_correct]
    Should Be True    ${result}[threshold_correct]

Health Mode Normal Threshold
    [Documentation]    GIVEN normal mode WHEN check THEN 0.50 threshold
    [Tags]    unit    health    mode    threshold
    ${result}=    Health Mode Normal Threshold
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[mode_correct]
    Should Be True    ${result}[threshold_correct]

Health Mode Aggressive Threshold
    [Documentation]    GIVEN aggressive mode WHEN check THEN 0.25 threshold
    [Tags]    unit    health    mode    threshold
    ${result}=    Health Mode Aggressive Threshold
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[mode_correct]
    Should Be True    ${result}[threshold_correct]

Health Mode Default When Unset
    [Documentation]    GIVEN no ENV WHEN check THEN normal mode
    [Tags]    unit    health    mode    default
    ${result}=    Health Mode Default When Unset
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[mode_correct]
    Should Be True    ${result}[threshold_correct]

Health Mode Case Insensitive
    [Documentation]    GIVEN uppercase mode WHEN check THEN works
    [Tags]    unit    health    mode    case
    ${result}=    Health Mode Case Insensitive
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[mode_correct]
    Should Be True    ${result}[threshold_correct]

# =============================================================================
# Aggressive Mode Detailed Output Tests
# =============================================================================

Use Detailed In Aggressive Mode
    [Documentation]    GIVEN aggressive mode WHEN decide THEN use detailed
    [Tags]    unit    health    aggressive    detailed
    ${result}=    Use Detailed In Aggressive Mode
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[use_detailed]

Use Summary In Normal Mode
    [Documentation]    GIVEN normal mode WHEN decide THEN use summary
    [Tags]    unit    health    normal    summary
    ${result}=    Use Summary In Normal Mode
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[use_summary]

# =============================================================================
# AMNESIA Threshold Behavior Tests
# =============================================================================

Aggressive Detects Low Confidence
    [Documentation]    GIVEN 30% confidence WHEN aggressive THEN detected
    [Tags]    unit    health    threshold    aggressive
    ${result}=    Aggressive Detects Low Confidence
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[detected]

Normal Ignores Low Confidence
    [Documentation]    GIVEN 30% confidence WHEN normal THEN not detected
    [Tags]    unit    health    threshold    normal
    ${result}=    Normal Ignores Low Confidence
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[not_detected]

Quiet Ignores Medium Confidence
    [Documentation]    GIVEN 60% confidence WHEN quiet THEN not detected
    [Tags]    unit    health    threshold    quiet
    ${result}=    Quiet Ignores Medium Confidence
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[not_detected]
