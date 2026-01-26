*** Settings ***
Documentation    Rules Archive and Restore Tests
...              Per: RF-007 Robot Framework Migration
...              Migrated from tests/rules/test_archive.py
...              Tests archive, restore, and MCP wrapper functionality.
Library          Collections
Library          ../../libs/RulesArchiveLibrary.py
Resource         ../resources/common.resource
Tags             unit    rules    archive

*** Test Cases ***
# =============================================================================
# Archive Functionality Tests
# =============================================================================

Test Delete Rule Archives By Default
    [Documentation]    delete_rule archives the rule by default
    [Tags]    delete    archive
    ${result}=    Delete Rule Archives By Default
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['archives_called']}
    Should Be True    ${result['delete_returns_true']}

Test Delete Rule Can Skip Archive
    [Documentation]    delete_rule can skip archiving with archive=False
    [Tags]    delete    skip-archive
    ${result}=    Delete Rule Can Skip Archive
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['archive_not_called']}
    Should Be True    ${result['delete_returns_true']}

Test Archive Rule Returns None For Missing
    [Documentation]    archive_rule returns None for non-existent rule
    [Tags]    archive    missing
    ${result}=    Archive Rule Returns None For Missing
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['returns_none']}

Test Archive Rule Creates Record
    [Documentation]    archive_rule creates an archive record
    [Tags]    archive    create
    ${result}=    Archive Rule Creates Record
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['result_not_none']}
    Should Be True    ${result['has_rule_id']}
    Should Be True    ${result['has_archived_at']}
    Should Be True    ${result['file_created']}

Test Get Archived Rules Empty
    [Documentation]    get_archived_rules returns empty list when no archives
    [Tags]    archive    list
    ${result}=    Get Archived Rules Empty
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['returns_empty_list']}

Test Get Archived Rule Returns Most Recent
    [Documentation]    get_archived_rule returns the most recent archive
    [Tags]    archive    recent
    ${result}=    Get Archived Rule Returns Most Recent
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['result_not_none']}
    Should Be True    ${result['returns_most_recent']}

Test Restore Rule Raises If Exists
    [Documentation]    restore_rule raises ValueError if rule already exists
    [Tags]    restore    exists
    ${result}=    Restore Rule Raises If Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['raises_error']}
    Should Be True    ${result['error_mentions_exists']}

Test Restore Rule Returns None If No Archive
    [Documentation]    restore_rule returns None if no archive exists
    [Tags]    restore    missing
    ${result}=    Restore Rule Returns None If No Archive
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['returns_none']}

# =============================================================================
# MCP Archive Tools Tests
# =============================================================================

Test MCP List Archived Rules
    [Documentation]    rules_list_archived returns JSON array
    [Tags]    mcp    list
    ${result}=    MCP List Archived Rules
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_archives']}
    Should Be True    ${result['count_correct']}
    Should Be True    ${result['has_rule_id']}

Test MCP Get Archived Rule Success
    [Documentation]    rule_get_archived returns archive data
    [Tags]    mcp    get
    ${result}=    MCP Get Archived Rule Success
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_rule']}
    Should Be True    ${result['id_matches']}

Test MCP Get Archived Rule Not Found
    [Documentation]    rule_get_archived returns error for missing archive
    [Tags]    mcp    get    error
    ${result}=    MCP Get Archived Rule Not Found
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_error']}

Test MCP Restore Rule Success
    [Documentation]    rule_restore returns restored rule
    [Tags]    mcp    restore
    ${result}=    MCP Restore Rule Success
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['success']}
    Should Be True    ${result['status_draft']}

Test MCP Restore Rule Not Found
    [Documentation]    rule_restore returns error for missing archive
    [Tags]    mcp    restore    error
    ${result}=    MCP Restore Rule Not Found
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_error']}
