*** Settings ***
Documentation    RF-004: Unit Tests - Shell Command Guidelines
...              Migrated from tests/test_shell_guidelines.py
...              Per RULE-023: Test Before Ship
...              Per P11.3: Shell MCP documentation validation
Library          Collections
Library          ../../libs/ShellGuidelinesLibrary.py

*** Test Cases ***
# =============================================================================
# Shell Documentation Tests
# =============================================================================

Claude MD Exists
    [Documentation]    GIVEN project WHEN checking THEN CLAUDE.md exists
    [Tags]    unit    docs    validate    shell
    ${result}=    Claude MD Exists
    Should Be True    ${result}[exists]

Shell Guide Exists
    [Documentation]    GIVEN project WHEN checking THEN SHELL-GUIDE.md exists
    [Tags]    unit    docs    validate    shell
    ${result}=    Shell Guide Exists
    Should Be True    ${result}[exists]

Claude MD Links To Shell Guide
    [Documentation]    GIVEN CLAUDE.md WHEN checking THEN links to SHELL-GUIDE.md
    [Tags]    unit    docs    validate    shell
    ${result}=    Claude MD Links To Shell Guide
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    CLAUDE.md not found
    Should Be True    ${result}[has_link]

Bash Tool Documented
    [Documentation]    GIVEN SHELL-GUIDE.md WHEN checking THEN Bash tool documented
    [Tags]    unit    docs    validate    shell
    ${result}=    Bash Tool Documented
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    SHELL-GUIDE.md not found
    Should Be True    ${result}[documented]

PowerShell MCP Documented
    [Documentation]    GIVEN SHELL-GUIDE.md WHEN checking THEN PowerShell MCP documented
    [Tags]    unit    docs    validate    shell
    ${result}=    PowerShell MCP Documented
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    SHELL-GUIDE.md not found
    Should Be True    ${result}[documented]

Common Pitfalls Documented
    [Documentation]    GIVEN SHELL-GUIDE.md WHEN checking THEN common pitfalls documented
    [Tags]    unit    docs    validate    shell
    ${result}=    Common Pitfalls Documented
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    SHELL-GUIDE.md not found
    Should Be True    ${result}[has_start_sleep]
    Should Be True    ${result}[has_sleep]

# =============================================================================
# Shell Command Equivalents Tests
# =============================================================================

Wait Command Documented
    [Documentation]    GIVEN SHELL-GUIDE.md WHEN checking THEN sleep documented
    [Tags]    unit    docs    validate    shell    equivalents
    ${result}=    Wait Command Documented
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    SHELL-GUIDE.md not found
    Should Be True    ${result}[documented]

HTTP Request Documented
    [Documentation]    GIVEN SHELL-GUIDE.md WHEN checking THEN curl/Invoke-WebRequest documented
    [Tags]    unit    docs    validate    shell    equivalents
    ${result}=    HTTP Request Documented
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    SHELL-GUIDE.md not found
    Should Be True    ${result}[has_curl]
    Should Be True    ${result}[has_invoke_webrequest]

Head Tail Documented
    [Documentation]    GIVEN SHELL-GUIDE.md WHEN checking THEN head/tail documented
    [Tags]    unit    docs    validate    shell    equivalents
    ${result}=    Head Tail Documented
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    SHELL-GUIDE.md not found
    Should Be True    ${result}[has_head]
    Should Be True    ${result}[has_tail]
    Should Be True    ${result}[has_select_object]

Last N Lines Documented
    [Documentation]    GIVEN SHELL-GUIDE.md WHEN checking THEN last N lines documented
    [Tags]    unit    docs    validate    shell    equivalents
    ${result}=    Last N Lines Documented
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    SHELL-GUIDE.md not found
    Should Be True    ${result}[has_tail_n]
    Should Be True    ${result}[has_select_last]

# =============================================================================
# Codebase Shell Usage Tests
# =============================================================================

No PowerShell In Bash Scripts
    [Documentation]    GIVEN bash scripts WHEN checking THEN no PowerShell commands
    [Tags]    unit    docs    validate    shell    codebase
    ${result}=    No PowerShell In Bash Scripts
    Should Be True    ${result}[no_violations]

Docker Compose Uses Bash Syntax
    [Documentation]    GIVEN docker-compose.yml WHEN checking THEN uses bash syntax
    [Tags]    unit    docs    validate    shell    docker
    ${result}=    Docker Compose Uses Bash Syntax
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    docker-compose.yml not found
    Should Be True    ${result}[no_powershell]

