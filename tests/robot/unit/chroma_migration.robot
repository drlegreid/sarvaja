*** Settings ***
Documentation    RF-004: Unit Tests - ChromaDB Migration Tool
...              Migrated from tests/test_chroma_migration.py
...              Per P7.4: ChromaDB migration tool
Library          Collections
Library          ../../libs/ChromaMigrationLibrary.py

*** Test Cases ***
# =============================================================================
# Module Tests
# =============================================================================

Migration Tool Module Exists
    [Documentation]    GIVEN governance dir WHEN checking THEN chroma_migration.py exists
    [Tags]    unit    migration    module    file
    ${result}=    Migration Tool Module Exists
    Should Be True    ${result}[exists]

Chroma Migration Class Works
    [Documentation]    GIVEN ChromaMigration WHEN creating THEN instantiable
    [Tags]    unit    migration    class    create
    ${result}=    Chroma Migration Class Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[created]

Migrator Has Required Methods
    [Documentation]    GIVEN ChromaMigration WHEN checking THEN has methods
    [Tags]    unit    migration    class    methods
    ${result}=    Migrator Has Required Methods
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_scan]
    Should Be True    ${result}[has_migrate_collection]
    Should Be True    ${result}[has_migrate_all]
    Should Be True    ${result}[has_get_status]

# =============================================================================
# Scan Tests
# =============================================================================

Scan Chroma Returns Collections
    [Documentation]    GIVEN scan_chroma WHEN called THEN returns collections
    [Tags]    unit    migration    scan    collections
    ${result}=    Scan Chroma Returns Collections
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_dict]
    Should Be True    ${result}[has_collections]

Scan Includes Document Counts
    [Documentation]    GIVEN scan_chroma WHEN called THEN includes counts
    [Tags]    unit    migration    scan    counts
    ${result}=    Scan Includes Document Counts
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_total_docs]

Scan Handles Missing Chroma
    [Documentation]    GIVEN missing ChromaDB WHEN scan THEN handles gracefully
    [Tags]    unit    migration    scan    error
    ${result}=    Scan Handles Missing Chroma
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_dict]

# =============================================================================
# Collection Migration Tests
# =============================================================================

Migrate Collection Dry Run
    [Documentation]    GIVEN dry_run WHEN migrate_collection THEN no write
    [Tags]    unit    migration    collection    dryrun
    ${result}=    Migrate Collection Dry Run
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_dict]
    Should Be True    ${result}[has_dry_run]
    Should Be True    ${result}[dry_run_true]

Migrate Collection Tracks Progress
    [Documentation]    GIVEN migrate_collection WHEN running THEN tracks progress
    [Tags]    unit    migration    collection    progress
    ${result}=    Migrate Collection Tracks Progress
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_progress]

Migrate Collection Handles Errors
    [Documentation]    GIVEN nonexistent collection WHEN migrate THEN handles error
    [Tags]    unit    migration    collection    error
    ${result}=    Migrate Collection Handles Errors
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_dict]

# =============================================================================
# Data Transformation Tests
# =============================================================================

Transform Document Works
    [Documentation]    GIVEN transform_document WHEN called THEN transforms
    [Tags]    unit    migration    transform    document
    ${result}=    Transform Document Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_dict]
    Should Be True    ${result}[has_output]

Transform Preserves Metadata
    [Documentation]    GIVEN document WHEN transform THEN preserves metadata
    [Tags]    unit    migration    transform    metadata
    ${result}=    Transform Preserves Metadata
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[preserves_data]

Detect Document Type Works
    [Documentation]    GIVEN detect_type WHEN called THEN detects correctly
    [Tags]    unit    migration    transform    type
    ${result}=    Detect Document Type Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[rule_correct]
    Should Be True    ${result}[decision_correct]
    Should Be True    ${result}[session_correct]
    Should Be True    ${result}[default_correct]

# =============================================================================
# Full Migration Tests
# =============================================================================

Migrate All Dry Run
    [Documentation]    GIVEN dry_run WHEN migrate_all THEN scans and plans
    [Tags]    unit    migration    full    dryrun
    ${result}=    Migrate All Dry Run
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_dict]
    Should Be True    ${result}[has_dry_run]
    Should Be True    ${result}[dry_run_true]

Migrate All Returns Statistics
    [Documentation]    GIVEN migrate_all WHEN running THEN returns statistics
    [Tags]    unit    migration    full    stats
    ${result}=    Migrate All Returns Statistics
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_stats]

# =============================================================================
# Status Tests
# =============================================================================

Get Migration Status Works
    [Documentation]    GIVEN get_migration_status WHEN called THEN returns status
    [Tags]    unit    migration    status    get
    ${result}=    Get Migration Status Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_dict]
    Should Be True    ${result}[has_status]

Status Tracks Collections
    [Documentation]    GIVEN migration status WHEN checking THEN tracks collections
    [Tags]    unit    migration    status    collections
    ${result}=    Status Tracks Collections
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_dict]

# =============================================================================
# Integration Tests
# =============================================================================

Migration Uses Data Router
    [Documentation]    GIVEN ChromaMigration WHEN checking THEN uses DataRouter
    [Tags]    unit    migration    integration    router
    ${result}=    Migration Uses Data Router
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_router]

Factory Function Creates Migrator
    [Documentation]    GIVEN create_chroma_migration WHEN called THEN creates
    [Tags]    unit    migration    factory    create
    ${result}=    Factory Function Creates Migrator
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[created]

Factory Accepts Options
    [Documentation]    GIVEN create_chroma_migration WHEN options THEN configures
    [Tags]    unit    migration    factory    options
    ${result}=    Factory Accepts Options
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[batch_size_correct]
