*** Settings ***
Documentation    RF-004: Unit Tests - Frankel Hash Module
...              Migrated from tests/test_frankel_hash.py
...              Per TEST-TAXON-01-v1: Unit test migration example
Library          Collections
Library          String
Library          OperatingSystem
Library          ../../libs/FrankelHashLibrary.py

*** Variables ***
${TEST_CONTENT}    This is test content.
# Pre-generated 64-char hex strings for hash testing
${HASH_A}    aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
${HASH_B}    bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
${HASH_C}    cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
${HASH_D}    dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd

*** Test Cases ***
# =============================================================================
# FH-001: Core Content Hashing
# =============================================================================

Frankel Hash Module Is Importable
    [Documentation]    Verify frankel_hash module can be imported
    [Tags]    unit    evidence    smoke    FH-001
    ${result}=    Import Frankel Hash
    Should Be True    ${result}    Frankel hash module should be importable

Compute Hash Returns Consistent Results
    [Documentation]    Same content should produce same hash
    [Tags]    unit    evidence    validate    FH-001
    ${hash1}=    Compute Hash    ${TEST_CONTENT}
    ${hash2}=    Compute Hash    ${TEST_CONTENT}
    Should Be Equal    ${hash1}    ${hash2}    Same content should produce same hash

Compute Hash Returns 64 Char SHA256
    [Documentation]    Hash should be 64 character SHA-256
    [Tags]    unit    evidence    validate    FH-001
    ${hash}=    Compute Hash    ${TEST_CONTENT}
    ${length}=    Get Length    ${hash}
    Should Be Equal As Integers    ${length}    64    SHA-256 hash should be 64 chars

Different Content Produces Different Hash
    [Documentation]    Different content must produce different hashes
    [Tags]    unit    evidence    validate    FH-001
    ${hash1}=    Compute Hash    Content A
    ${hash2}=    Compute Hash    Content B
    Should Not Be Equal    ${hash1}    ${hash2}    Different content should have different hashes

# =============================================================================
# FH-002: Hash Tree Structure
# =============================================================================

Build Merkle Tree Creates Valid Structure
    [Documentation]    Merkle tree has expected structure
    [Tags]    unit    evidence    validate    FH-002
    @{hashes}=    Create List    ${HASH_A}    ${HASH_B}    ${HASH_C}    ${HASH_D}
    ${tree}=    Build Merkle Tree    ${hashes}
    Dictionary Should Contain Key    ${tree}    root
    Dictionary Should Contain Key    ${tree}    depth
    Dictionary Should Contain Key    ${tree}    levels

Merkle Tree Root Is Computed
    [Documentation]    Tree root is valid hash
    [Tags]    unit    evidence    validate    FH-002
    @{hashes}=    Create List    ${HASH_A}    ${HASH_B}
    ${tree}=    Build Merkle Tree    ${hashes}
    ${root}=    Get From Dictionary    ${tree}    root
    ${length}=    Get Length    ${root}
    Should Be Equal As Integers    ${length}    64

# =============================================================================
# FH-001: Zoom View
# =============================================================================

Zoom View Level 0 Shows Document
    [Documentation]    Zoom level 0 shows document-level hash
    [Tags]    unit    evidence    validate    FH-001
    ${content}=    Set Variable    # Header\n\nParagraph 1\n\n## Section\n\nParagraph 2
    ${output}=    Zoom View    ${content}    level=0
    Should Contain    ${output}    Zoom Level 0
    Should Contain    ${output}    Document

Zoom View Level 3 Shows Lines
    [Documentation]    Zoom level 3 shows line-level hashes
    [Tags]    unit    evidence    validate    FH-001
    ${content}=    Set Variable    Line 1\nLine 2\nLine 3
    ${output}=    Zoom View    ${content}    level=3
    Should Contain    ${output}    Zoom Level 3
    Should Contain    ${output}    Line

# =============================================================================
# FH-002: ASCII Visualization
# =============================================================================

Render Merkle Tree Produces ASCII
    [Documentation]    ASCII tree rendering works
    [Tags]    unit    evidence    validate    FH-002
    @{hashes}=    Create List    ${HASH_A}    ${HASH_B}
    ${tree}=    Build Merkle Tree    ${hashes}
    ${output}=    Render Merkle Tree    ${tree}
    Should Contain    ${output}    Merkle Tree
    Should Contain    ${output}    ROOT
