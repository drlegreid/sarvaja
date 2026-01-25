*** Settings ***
Documentation    RF-004: Unit Tests - ChromaDB Read-Only Wrapper
...              Migrated from tests/test_chroma_readonly.py
...              Per P7.5: ChromaDB sunset - read-only wrapper
Library          Collections
Library          ../../libs/ChromaReadonlyLibrary.py

*** Test Cases ***
# =============================================================================
# Module Tests
# =============================================================================

Readonly Wrapper Module Exists
    [Documentation]    GIVEN governance dir WHEN checking THEN chroma_readonly.py exists
    [Tags]    unit    chroma    readonly    module
    ${result}=    Readonly Wrapper Module Exists
    Should Be True    ${result}[exists]

Chroma Readonly Class Works
    [Documentation]    GIVEN ChromaReadOnly WHEN creating THEN instantiable
    [Tags]    unit    chroma    readonly    class
    ${result}=    Chroma Readonly Class Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[created]

Wrapper Has Required Methods
    [Documentation]    GIVEN ChromaReadOnly WHEN checking THEN has methods
    [Tags]    unit    chroma    readonly    methods
    ${result}=    Wrapper Has Required Methods
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_query]
    Should Be True    ${result}[has_get]
    Should Be True    ${result}[has_list_collections]
    Should Be True    ${result}[has_add]
    Should Be True    ${result}[has_update]
    Should Be True    ${result}[has_delete]

# =============================================================================
# Read Operation Tests
# =============================================================================

Query Returns Results
    [Documentation]    GIVEN query WHEN called THEN returns dict
    [Tags]    unit    chroma    readonly    query
    ${result}=    Query Returns Results
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_dict]

Get By ID Works
    [Documentation]    GIVEN get WHEN called with IDs THEN returns dict
    [Tags]    unit    chroma    readonly    get
    ${result}=    Get By ID Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_dict]

List Collections Works
    [Documentation]    GIVEN list_collections WHEN called THEN returns list
    [Tags]    unit    chroma    readonly    list
    ${result}=    List Collections Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_list]

# =============================================================================
# Write Deprecation Tests
# =============================================================================

Add Is Deprecated
    [Documentation]    GIVEN add WHEN called THEN deprecated response
    [Tags]    unit    chroma    readonly    deprecation
    ${result}=    Add Is Deprecated
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_dict]
    Should Be True    ${result}[is_deprecated]

Update Is Deprecated
    [Documentation]    GIVEN update WHEN called THEN deprecated response
    [Tags]    unit    chroma    readonly    deprecation
    ${result}=    Update Is Deprecated
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_dict]
    Should Be True    ${result}[is_deprecated]

Delete Is Deprecated
    [Documentation]    GIVEN delete WHEN called THEN deprecated response
    [Tags]    unit    chroma    readonly    deprecation
    ${result}=    Delete Is Deprecated
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_dict]
    Should Be True    ${result}[is_deprecated]

# =============================================================================
# TypeDB Redirect Tests
# =============================================================================

Add Redirects To TypeDB
    [Documentation]    GIVEN add with rule ID WHEN called THEN redirects
    [Tags]    unit    chroma    readonly    redirect
    ${result}=    Add Redirects To TypeDB
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_redirect]

Wrapper Uses Data Router
    [Documentation]    GIVEN ChromaReadOnly WHEN checking THEN has router
    [Tags]    unit    chroma    readonly    router
    ${result}=    Wrapper Uses Data Router
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_router]

# =============================================================================
# Deprecation Warning Tests
# =============================================================================

Add Logs Deprecation Warning
    [Documentation]    GIVEN add WHEN called THEN logs deprecation
    [Tags]    unit    chroma    readonly    warning
    ${result}=    Add Logs Deprecation Warning
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_deprecation]

Get Deprecation Status Works
    [Documentation]    GIVEN get_deprecation_status WHEN called THEN returns status
    [Tags]    unit    chroma    readonly    status
    ${result}=    Get Deprecation Status Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_dict]
    Should Be True    ${result}[has_writes_deprecated]
    Should Be True    ${result}[writes_deprecated_true]

# =============================================================================
# Backwards Compatibility Tests
# =============================================================================

Has Collection Interface
    [Documentation]    GIVEN ChromaReadOnly WHEN checking THEN has get_collection
    [Tags]    unit    chroma    readonly    compatibility
    ${result}=    Has Collection Interface
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_get_collection]

Get Collection Returns Wrapper
    [Documentation]    GIVEN get_collection WHEN called THEN returns wrapper
    [Tags]    unit    chroma    readonly    collection
    ${result}=    Get Collection Returns Wrapper
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[not_none]
    Should Be True    ${result}[has_query]

# =============================================================================
# Integration Tests
# =============================================================================

Factory Function Creates Wrapper
    [Documentation]    GIVEN create_readonly_client WHEN called THEN creates
    [Tags]    unit    chroma    readonly    factory
    ${result}=    Factory Function Creates Wrapper
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[created]

Factory Accepts Readonly Options
    [Documentation]    GIVEN create_readonly_client WHEN options THEN configures
    [Tags]    unit    chroma    readonly    options
    ${result}=    Factory Accepts Readonly Options
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[log_deprecations_true]
