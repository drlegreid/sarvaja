*** Settings ***
Documentation    RF-004: Unit Tests - Document Service
...              Migrated from tests/test_document_service.py
...              Per RD-DOC-SERVICE: Document Service Architecture
Library          Collections
Library          ../../libs/DocumentServiceLibrary.py

*** Test Cases ***
# =============================================================================
# Rule Document Scanning Tests
# =============================================================================

Scan Rule Documents Returns List
    [Documentation]    GIVEN rule docs WHEN scan_rule_documents THEN returns list
    [Tags]    unit    document    scan    list
    ${result}=    Scan Rule Documents Returns List
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_list]
    Should Be True    ${result}[has_documents]

Rule Document Has Required Fields
    [Documentation]    GIVEN RuleDocument WHEN create THEN has all fields
    [Tags]    unit    document    dataclass    fields
    ${result}=    Rule Document Has Required Fields
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[id_correct]
    Should Be True    ${result}[title_correct]
    Should Be True    ${result}[path_correct]
    Should Be True    ${result}[type_correct]
    Should Be True    ${result}[storage_correct]

Scan Converts Semantic To Legacy
    [Documentation]    GIVEN semantic IDs WHEN scan THEN converts to legacy
    [Tags]    unit    document    scan    convert
    ${result}=    Scan Converts Semantic To Legacy
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_legacy_ids]

Scan Finds Legacy IDs
    [Documentation]    GIVEN rule docs WHEN scan THEN finds legacy IDs
    [Tags]    unit    document    scan    legacy
    ${result}=    Scan Finds Legacy IDs
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_legacy_ids]

# =============================================================================
# Rule ID Extraction Tests
# =============================================================================

Extract Legacy Rule ID
    [Documentation]    GIVEN RULE-001 format WHEN extract THEN found
    [Tags]    unit    document    extract    legacy
    ${result}=    Extract Legacy Rule ID
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_001]
    Should Be True    ${result}[has_042]

Extract Semantic Converts To Legacy
    [Documentation]    GIVEN semantic ID WHEN extract THEN converts to legacy
    [Tags]    unit    document    extract    semantic
    ${result}=    Extract Semantic Converts To Legacy
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_rule_001]

Extract Multiple Formats Returns Legacy
    [Documentation]    GIVEN mixed formats WHEN extract THEN all legacy
    [Tags]    unit    document    extract    mixed
    ${result}=    Extract Multiple Formats Returns Legacy
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_001]
    Should Be True    ${result}[has_012]
    Should Be True    ${result}[has_011]

No Duplicate Extractions
    [Documentation]    GIVEN duplicate IDs WHEN extract THEN no duplicates
    [Tags]    unit    document    extract    dedup
    ${result}=    No Duplicate Extractions
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[no_duplicates]

# =============================================================================
# Rule ID Normalization Tests
# =============================================================================

Normalize Keeps Legacy ID
    [Documentation]    GIVEN legacy ID WHEN normalize THEN preserved
    [Tags]    unit    document    normalize    legacy
    ${result}=    Normalize Keeps Legacy ID
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[preserved]

Normalize Converts Semantic To Legacy
    [Documentation]    GIVEN semantic ID WHEN normalize THEN converts to legacy
    [Tags]    unit    document    normalize    semantic
    ${result}=    Normalize Converts Semantic To Legacy
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[converted]

# =============================================================================
# TypeDB Document Linking Tests
# =============================================================================

Link Rules To Documents Returns Stats
    [Documentation]    GIVEN documents WHEN link_rules_to_documents THEN stats
    [Tags]    unit    document    link    stats
    ${result}=    Link Rules To Documents Returns Stats
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_dict]
    Should Be True    ${result}[has_documents_inserted]
    Should Be True    ${result}[has_documents_skipped]
    Should Be True    ${result}[has_relations_created]
    Should Be True    ${result}[has_relations_skipped]
    Should Be True    ${result}[has_errors]

Insert Document Datetime Format
    [Documentation]    GIVEN document WHEN insert THEN TypeDB datetime format
    [Tags]    unit    document    insert    datetime
    ${result}=    Insert Document Datetime Format
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_datetime]
    Should Be True    ${result}[no_microseconds]

Insert Document Escapes Special Chars
    [Documentation]    GIVEN special chars WHEN insert THEN escaped
    [Tags]    unit    document    insert    escape
    ${result}=    Insert Document Escapes Special Chars
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_escape]
    Should Be True    ${result}[has_backslash]

# =============================================================================
# Document Service MCP Integration Tests
# =============================================================================

File Type Map Exists
    [Documentation]    GIVEN module WHEN check THEN FILE_TYPE_MAP exists
    [Tags]    unit    document    mcp    map
    ${result}=    File Type Map Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]
    Should Be True    ${result}[is_dict]

File Type Map Has Python
    [Documentation]    GIVEN FILE_TYPE_MAP WHEN check THEN has Python
    [Tags]    unit    document    mcp    python
    ${result}=    File Type Map Has Python
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_py]
    Should Be True    ${result}[is_python]

File Type Map Has Markdown
    [Documentation]    GIVEN FILE_TYPE_MAP WHEN check THEN has Markdown
    [Tags]    unit    document    mcp    markdown
    ${result}=    File Type Map Has Markdown
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_md]
    Should Be True    ${result}[is_markdown]

File Type Map Has TypeQL
    [Documentation]    GIVEN FILE_TYPE_MAP WHEN check THEN has TypeQL
    [Tags]    unit    document    mcp    typeql
    ${result}=    File Type Map Has TypeQL
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_tql]
    Should Be True    ${result}[is_typeql]

File Type Map Has Haskell
    [Documentation]    GIVEN FILE_TYPE_MAP WHEN check THEN has Haskell
    [Tags]    unit    document    mcp    haskell
    ${result}=    File Type Map Has Haskell
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_hs]
    Should Be True    ${result}[is_haskell]

Register Document Tools Function Exists
    [Documentation]    GIVEN module WHEN check THEN register_document_tools exists
    [Tags]    unit    document    mcp    register
    ${result}=    Register Document Tools Function Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]
    Should Be True    ${result}[callable]
