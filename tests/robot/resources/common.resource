*** Settings ***
Documentation    Common resources for Robot Framework tests
...              Per: RF-007 Robot Framework Migration

*** Variables ***
${API_BASE}           http://localhost:8082
${DASHBOARD_URL}      http://localhost:8081
${TYPEDB_HOST}        localhost
${TYPEDB_PORT}        1729
${CHROMADB_HOST}      localhost
${CHROMADB_PORT}      8001
${DEFAULT_TIMEOUT}    10

*** Keywords ***
Skip If API Unavailable
    [Documentation]    Skip test if API is not available
    [Arguments]    ${result}
    ${skipped}=    Evaluate    $result.get('skipped', False)
    ${reason}=     Evaluate    $result.get('reason', 'API not available')
    Skip If    ${skipped}    ${reason}

Skip If Import Failed
    [Documentation]    Skip test if import failed
    [Arguments]    ${result}
    ${skipped}=    Evaluate    $result.get('skipped', False)
    ${reason}=     Evaluate    $result.get('reason', 'Import failed')
    Skip If    ${skipped}    ${reason}

Log Result Details
    [Documentation]    Log result dictionary for debugging
    [Arguments]    ${result}
    ${details}=    Evaluate    str($result)
    Log    Result: ${details}
