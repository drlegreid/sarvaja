*** Settings ***
Documentation    RF-004: Unit Tests - Destructive Command Checker
...              Migrated from tests/test_destructive_checker.py
...              Per GAP-DESTRUCT-001: Validates destructive command detection
...              Per SAFETY-DESTR-01-v1: Enforcement mechanism validation
Library          Collections
Library          ../../libs/DestructiveCheckerLibrary.py
Force Tags        unit    safety    destructive    low    validate    SAFETY-DESTR-01-v1

*** Test Cases ***
# =============================================================================
# Destructive Command Detection Tests
# =============================================================================

Safe Commands Allowed
    [Documentation]    GIVEN safe commands WHEN checking THEN not flagged
    [Tags]    unit    safety    validate    destructive
    ${result}=    Safe Commands Allowed
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Checker module not found
    Should Be True    ${result}[all_safe]

Rm Rf Detected As Destructive
    [Documentation]    GIVEN rm -rf WHEN checking THEN detected as destructive
    [Tags]    unit    safety    validate    destructive
    ${result}=    Rm Rf Detected
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Checker module not found
    Should Be True    ${result}[is_destructive]

Git Reset Hard Detected As Destructive
    [Documentation]    GIVEN git reset --hard WHEN checking THEN detected
    [Tags]    unit    safety    validate    destructive    git
    ${result}=    Git Reset Hard Detected
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Checker module not found
    Should Be True    ${result}[is_destructive]
    Should Be True    ${result}[mentions_uncommitted]

Git Push Force Detected As Destructive
    [Documentation]    GIVEN git push --force WHEN checking THEN detected
    [Tags]    unit    safety    validate    destructive    git
    ${result}=    Git Push Force Detected
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Checker module not found
    Should Be True    ${result}[is_destructive]

Podman System Prune Detected As Destructive
    [Documentation]    GIVEN podman system prune WHEN checking THEN detected
    [Tags]    unit    safety    validate    destructive    podman
    ${result}=    Podman System Prune Detected
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Checker module not found
    Should Be True    ${result}[is_destructive]

Drop Table Detected As Destructive
    [Documentation]    GIVEN DROP TABLE WHEN checking THEN detected
    [Tags]    unit    safety    validate    destructive    sql
    ${result}=    Drop Table Detected
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Checker module not found
    Should Be True    ${result}[is_destructive]

# =============================================================================
# Blocked Commands Tests
# =============================================================================

Rm Rf Root Blocked
    [Documentation]    GIVEN rm -rf / WHEN checking THEN blocked
    [Tags]    unit    safety    validate    destructive    blocked
    ${result}=    Rm Rf Root Blocked
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Checker module not found
    Should Be True    ${result}[is_blocked]
    Should Be True    ${result}[is_destructive]

Rm Rf Root Wildcard Blocked
    [Documentation]    GIVEN rm -rf /* WHEN checking THEN blocked
    [Tags]    unit    safety    validate    destructive    blocked
    ${result}=    Rm Rf Root Wildcard Blocked
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Checker module not found
    Should Be True    ${result}[is_blocked]

# =============================================================================
# Warning Formatting Tests
# =============================================================================

Blocked Warning Has BLOCKED Text
    [Documentation]    GIVEN blocked command WHEN formatting THEN has BLOCKED
    [Tags]    unit    safety    validate    destructive    warning
    ${result}=    Blocked Warning Format
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Checker module not found
    Should Be True    ${result}[has_blocked]

Destructive Warning Has WARNING And Rule Ref
    [Documentation]    GIVEN destructive command WHEN formatting THEN has WARNING
    [Tags]    unit    safety    validate    destructive    warning
    ${result}=    Destructive Warning Format
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Checker module not found
    Should Be True    ${result}[has_warning]
    Should Be True    ${result}[has_rule_ref]

Safe Command Has No Warning
    [Documentation]    GIVEN safe command WHEN formatting THEN empty warning
    [Tags]    unit    safety    validate    destructive    warning
    ${result}=    Safe Command No Warning
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Checker module not found
    Should Be True    ${result}[empty_warning]

# =============================================================================
# Safe Alternatives Tests
# =============================================================================

Rm Rf Suggests Rm I Alternative
    [Documentation]    GIVEN rm -rf WHEN getting alternative THEN suggests rm -i
    [Tags]    unit    safety    validate    destructive    alternative
    ${result}=    Rm Rf Alternative Suggested
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Checker module not found
    Should Be True    ${result}[has_alternative]
    Should Be True    ${result}[suggests_rm_i]

Git Reset Hard Suggests Stash Alternative
    [Documentation]    GIVEN git reset --hard WHEN getting alternative THEN suggests stash
    [Tags]    unit    safety    validate    destructive    alternative    git
    ${result}=    Git Reset Hard Alternative Suggested
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Checker module not found
    Should Be True    ${result}[has_alternative]
    Should Be True    ${result}[suggests_stash]

Git Push Force Suggests Force With Lease
    [Documentation]    GIVEN git push --force WHEN getting alternative THEN suggests --force-with-lease
    [Tags]    unit    safety    validate    destructive    alternative    git
    ${result}=    Git Push Force Alternative Suggested
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Checker module not found
    Should Be True    ${result}[has_alternative]
    Should Be True    ${result}[suggests_lease]

# =============================================================================
# Pattern Coverage Tests
# =============================================================================

Has Multiple Destructive Patterns
    [Documentation]    GIVEN checker WHEN checking THEN has 10+ patterns
    [Tags]    unit    safety    validate    destructive    patterns
    ${result}=    Has Destructive Patterns
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Checker module not found
    Should Be True    ${result}[has_patterns]

Has Blocked Patterns Defined
    [Documentation]    GIVEN checker WHEN checking THEN has blocked patterns
    [Tags]    unit    safety    validate    destructive    patterns
    ${result}=    Has Blocked Patterns
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Checker module not found
    Should Be True    ${result}[has_patterns]

All Patterns Have Descriptions
    [Documentation]    GIVEN patterns WHEN checking THEN all have descriptions
    [Tags]    unit    safety    validate    destructive    patterns
    ${result}=    All Patterns Have Descriptions
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Checker module not found
    Should Be True    ${result}[all_have_descriptions]

