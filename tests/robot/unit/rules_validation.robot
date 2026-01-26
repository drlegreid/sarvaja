*** Settings ***
Documentation    Rules Validation Tests
...              Per: RF-007 Robot Framework Migration
...              Migrated from tests/rules/test_validation.py
...              Tests TypeDBClient input validation on rules.
Library          Collections
Library          ../../libs/RulesValidationLibrary.py
Resource         ../resources/common.resource
Tags             unit    rules    validation

*** Test Cases ***
# =============================================================================
# Category Validation Tests
# =============================================================================

Test Create Rule Validates Category
    [Documentation]    Test that create_rule validates category
    [Tags]    create    category
    ${result}=    Create Rule Validates Category
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['raises_error']}
    Should Be True    ${result['message_correct']}

# =============================================================================
# Priority Validation Tests
# =============================================================================

Test Create Rule Validates Priority
    [Documentation]    Test that create_rule validates priority
    [Tags]    create    priority
    ${result}=    Create Rule Validates Priority
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['raises_error']}
    Should Be True    ${result['message_correct']}

# =============================================================================
# Status Validation Tests
# =============================================================================

Test Create Rule Validates Status
    [Documentation]    Test that create_rule validates status
    [Tags]    create    status
    ${result}=    Create Rule Validates Status
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['raises_error']}
    Should Be True    ${result['message_correct']}

# =============================================================================
# Duplicate Checking Tests
# =============================================================================

Test Create Rule Checks Duplicate
    [Documentation]    Test that create_rule rejects duplicate IDs
    [Tags]    create    duplicate
    ${result}=    Create Rule Checks Duplicate
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['raises_error']}
    Should Be True    ${result['message_correct']}

# =============================================================================
# Update Rule Validation Tests
# =============================================================================

Test Update Rule Raises For Missing
    [Documentation]    Test that update_rule raises for non-existent rule
    [Tags]    update    missing
    ${result}=    Update Rule Raises For Missing
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['raises_error']}
    Should Be True    ${result['message_correct']}

Test Update Rule Returns Unchanged If No Updates
    [Documentation]    Test that update_rule returns existing rule if nothing changes
    [Tags]    update    unchanged
    ${result}=    Update Rule Returns Unchanged If No Updates
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['returns_same_rule']}

# =============================================================================
# Deprecate Rule Tests
# =============================================================================

Test Deprecate Rule Calls Update With Deprecated
    [Documentation]    Test that deprecate_rule calls update_rule with DEPRECATED status
    [Tags]    deprecate    status
    ${result}=    Deprecate Rule Calls Update With Deprecated
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['calls_update']}
    Should Be True    ${result['result_status_deprecated']}

# =============================================================================
# Delete Rule Tests
# =============================================================================

Test Delete Rule Returns False For Missing
    [Documentation]    Test that delete_rule returns False for non-existent rule
    [Tags]    delete    missing
    ${result}=    Delete Rule Returns False For Missing
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['returns_false']}
