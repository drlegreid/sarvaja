*** Settings ***
Documentation    RF-004: Chat Extended Tests (API, Integration, Message, State)
...              Migrated from test_chat.py
...              Per RF-007 Robot Framework Migration
Library          ../../libs/ChatAPILibrary.py
Library          ../../libs/ChatIntegrationLibrary.py
Library          ../../libs/ChatMessageLibrary.py
Library          ../../libs/ChatStateLibrary.py
Library          Collections
Resource         ../resources/common.resource
Force Tags             unit    chat    extended    low    mcp    session    validate    ARCH-MCP-02-v1

*** Test Cases ***
# =============================================================================
# Chat API Tests
# =============================================================================

Chat Message Request Model
    [Documentation]    Test: Chat Message Request Model
    ${result}=    Chat Message Request Model
    Skip If Import Failed    ${result}

Chat Message Request Defaults
    [Documentation]    Test: Chat Message Request Defaults
    ${result}=    Chat Message Request Defaults
    Skip If Import Failed    ${result}

Chat Message Response Model
    [Documentation]    Test: Chat Message Response Model
    ${result}=    Chat Message Response Model
    Skip If Import Failed    ${result}

Help Command Processing
    [Documentation]    Test: Help Command Processing
    ${result}=    Help Command Processing
    Skip If Import Failed    ${result}

Status Command Processing
    [Documentation]    Test: Status Command Processing
    ${result}=    Status Command Processing
    Skip If Import Failed    ${result}

Tasks Command Processing
    [Documentation]    Test: Tasks Command Processing
    ${result}=    Tasks Command Processing
    Skip If Import Failed    ${result}

Rules Command Processing
    [Documentation]    Test: Rules Command Processing
    ${result}=    Rules Command Processing
    Skip If Import Failed    ${result}

Agents Command Processing
    [Documentation]    Test: Agents Command Processing
    ${result}=    Agents Command Processing
    Skip If Import Failed    ${result}

Search Command No Query
    [Documentation]    Test: Search Command No Query
    ${result}=    Search Command No Query
    Skip If Import Failed    ${result}

Delegate Command No Task
    [Documentation]    Test: Delegate Command No Task
    ${result}=    Delegate Command No Task
    Skip If Import Failed    ${result}

Natural Language Fallback
    [Documentation]    Test: Natural Language Fallback
    ${result}=    Natural Language Fallback
    Skip If Import Failed    ${result}

# =============================================================================
# Chat Integration Tests
# =============================================================================

Generate Session Id
    [Documentation]    Test: Generate Session Id
    ${result}=    Generate Session Id
    Skip If Import Failed    ${result}

Generate Unique Session Ids
    [Documentation]    Test: Generate Unique Session Ids
    ${result}=    Generate Unique Session Ids
    Skip If Import Failed    ${result}

Send Message Creates Session
    [Documentation]    Test: Send Message Creates Session
    ${result}=    Send Message Creates Session
    Skip If Import Failed    ${result}

Send Message With Agent
    [Documentation]    Test: Send Message With Agent
    ${result}=    Send Message With Agent
    Skip If Import Failed    ${result}

List Chat Sessions
    [Documentation]    Test: List Chat Sessions
    ${result}=    List Chat Sessions
    Skip If Import Failed    ${result}

Get Nonexistent Session
    [Documentation]    Test: Get Nonexistent Session
    ${result}=    Get Nonexistent Session
    Skip If Import Failed    ${result}

# =============================================================================
# Chat Message Tests
# =============================================================================

Format Chat Message User
    [Documentation]    Test: Format Chat Message User
    ${result}=    Format Chat Message User
    Skip If Import Failed    ${result}

Format Chat Message Agent
    [Documentation]    Test: Format Chat Message Agent
    ${result}=    Format Chat Message Agent
    Skip If Import Failed    ${result}

Create User Message
    [Documentation]    Test: Create User Message
    ${result}=    Create User Message
    Skip If Import Failed    ${result}

Create Agent Message
    [Documentation]    Test: Create Agent Message
    ${result}=    Create Agent Message
    Skip If Import Failed    ${result}

Create System Message
    [Documentation]    Test: Create System Message
    ${result}=    Create System Message
    Skip If Import Failed    ${result}

# =============================================================================
# Chat State Tests
# =============================================================================

Role Colors Defined
    [Documentation]    Test: Role Colors Defined
    ${result}=    Role Colors Defined
    Skip If Import Failed    ${result}

Status Icons Defined
    [Documentation]    Test: Status Icons Defined
    ${result}=    Status Icons Defined
    Skip If Import Failed    ${result}

With Chat Messages Transform
    [Documentation]    Test: With Chat Messages Transform
    ${result}=    With Chat Messages Transform
    Skip If Import Failed    ${result}

With Chat Message Append
    [Documentation]    Test: With Chat Message Append
    ${result}=    With Chat Message Append
    Skip If Import Failed    ${result}

With Chat Loading Transform
    [Documentation]    Test: With Chat Loading Transform
    ${result}=    With Chat Loading Transform
    Skip If Import Failed    ${result}

With Chat Input Transform
    [Documentation]    Test: With Chat Input Transform
    ${result}=    With Chat Input Transform
    Skip If Import Failed    ${result}

With Chat Agent Transform
    [Documentation]    Test: With Chat Agent Transform
    ${result}=    With Chat Agent Transform
    Skip If Import Failed    ${result}

With Chat Session Transform
    [Documentation]    Test: With Chat Session Transform
    ${result}=    With Chat Session Transform
    Skip If Import Failed    ${result}

With Chat Task Transform
    [Documentation]    Test: With Chat Task Transform
    ${result}=    With Chat Task Transform
    Skip If Import Failed    ${result}

Get Chat Role Color
    [Documentation]    Test: Get Chat Role Color
    ${result}=    Get Chat Role Color
    Skip If Import Failed    ${result}

Get Chat Status Icon
    [Documentation]    Test: Get Chat Status Icon
    ${result}=    Get Chat Status Icon
    Skip If Import Failed    ${result}
