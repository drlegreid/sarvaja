*** Settings ***
Documentation    RF-004: Unit Tests - File Watcher Module
...              Migrated from tests/unit/test_file_watcher.py
...              Per GAP-SYNC-AUTO-001: Auto-sync file watching
Library          Collections
Library          ../../libs/FileWatcherLibrary.py
Force Tags        unit    files    watcher    low    monitor    SESSION-HOOK-01-v1

*** Test Cases ***
# =============================================================================
# File Event Categorization Tests
# =============================================================================

Categorize Rules Path
    [Documentation]    GIVEN rules path WHEN categorizing THEN returns RULES
    [Tags]    unit    evidence    validate    file-watcher
    ${category}=    Categorize Rules Path    /docs/rules/RULE-001.md
    Should Be Equal    ${category}    rules
    ${category2}=    Categorize Rules Path    /docs/rules/leaf/TEST-TDD-01-v1.md
    Should Be Equal    ${category2}    rules

Categorize Tasks Path
    [Documentation]    GIVEN tasks path WHEN categorizing THEN returns TASKS
    [Tags]    unit    evidence    validate    file-watcher
    ${category}=    Categorize Tasks Path    /TODO.md
    Should Be Equal    ${category}    tasks
    ${category2}=    Categorize Tasks Path    /docs/backlog/phases/PHASE-10.md
    Should Be Equal    ${category2}    tasks

Categorize Evidence Path
    [Documentation]    GIVEN evidence path WHEN categorizing THEN returns EVIDENCE
    [Tags]    unit    evidence    validate    file-watcher
    ${category}=    Categorize Evidence Path    /evidence/SESSION-2026-01-21.md
    Should Be Equal    ${category}    evidence

Categorize Gaps Path
    [Documentation]    GIVEN gaps path WHEN categorizing THEN returns GAPS
    [Tags]    unit    evidence    validate    file-watcher
    ${category}=    Categorize Gaps Path    /docs/gaps/GAP-INDEX.md
    Should Be Equal    ${category}    gaps
    ${category2}=    Categorize Gaps Path    /docs/gaps/evidence/GAP-001.md
    Should Be Equal    ${category2}    gaps

Categorize Other Path
    [Documentation]    GIVEN unknown path WHEN categorizing THEN returns OTHER
    [Tags]    unit    evidence    validate    file-watcher
    ${category}=    Categorize Other Path    /README.md
    Should Be Equal    ${category}    other
    ${category2}=    Categorize Other Path    /src/main.py
    Should Be Equal    ${category2}    other

# =============================================================================
# FileEvent Tests
# =============================================================================

File Event Creation
    [Documentation]    GIVEN FileEvent WHEN creating THEN fields are set correctly
    [Tags]    unit    evidence    create    file-watcher
    ${event}=    Create File Event
    Should Be Equal    ${event}[path]    /docs/rules/RULE-001.md
    Should Be Equal    ${event}[event_type]    modified
    Should Be True    ${event}[timestamp_positive]

File Event Auto Categorization
    [Documentation]    GIVEN FileEvent WHEN auto-categorizing THEN category is correct
    [Tags]    unit    evidence    validate    file-watcher
    ${category}=    Create Event With Category
    Should Be Equal    ${category}    rules

# =============================================================================
# FileEventQueue Tests
# =============================================================================

Queue Add Event
    [Documentation]    GIVEN queue WHEN adding event THEN size increases
    [Tags]    unit    evidence    create    file-watcher
    ${size}=    Queue Add Event
    Should Be Equal As Integers    ${size}    1

Queue Deduplication
    [Documentation]    GIVEN same path events WHEN adding THEN only one event in queue
    [Tags]    unit    evidence    validate    file-watcher
    ${size}=    Queue Deduplication
    Should Be Equal As Integers    ${size}    1

Queue Debounce Returns Empty
    [Documentation]    GIVEN long debounce WHEN getting batch THEN returns empty
    [Tags]    unit    evidence    validate    file-watcher
    ${count}=    Queue Debounce Returns Empty
    Should Be Equal As Integers    ${count}    0

Queue Batch After Debounce
    [Documentation]    GIVEN short debounce WHEN waiting and getting batch THEN returns events
    [Tags]    unit    evidence    validate    file-watcher
    ${result}=    Queue Batch After Debounce
    Should Be Equal As Integers    ${result}[count]    1
    Should Be Equal    ${result}[path]    /docs/rules/RULE-001.md

Queue Priority Ordering
    [Documentation]    GIVEN events with different categories WHEN getting batch THEN ordered by priority
    [Tags]    unit    evidence    validate    file-watcher
    ${order}=    Queue Priority Ordering
    Should Be Equal    ${order}[0]    rules
    Should Be Equal    ${order}[1]    tasks
    Should Be Equal    ${order}[2]    evidence

Queue Clear
    [Documentation]    GIVEN queue with events WHEN clearing THEN queue is empty
    [Tags]    unit    evidence    delete    file-watcher
    ${result}=    Queue Clear
    Should Be Equal As Integers    ${result}[cleared]    1
    Should Be Equal As Integers    ${result}[size_after]    0

Queue Get Stats
    [Documentation]    GIVEN queue WHEN getting stats THEN returns statistics
    [Tags]    unit    evidence    validate    file-watcher
    ${stats}=    Queue Get Stats
    Should Be True    ${stats}[has_queue_size]
    Should Be True    ${stats}[has_debounce_seconds]
    Should Be Equal As Numbers    ${stats}[debounce_value]    2.0

# =============================================================================
# DocumentChangeHandler Tests
# =============================================================================

Handler Should Process Markdown
    [Documentation]    GIVEN markdown path WHEN checking THEN should process
    [Tags]    unit    evidence    validate    file-watcher
    ${result}=    Handler Should Process Markdown    /docs/rules/RULE-001.md
    Should Be True    ${result}
    ${result2}=    Handler Should Process Markdown    /TODO.md
    Should Be True    ${result2}

Handler Should Ignore Non Markdown
    [Documentation]    GIVEN non-markdown path WHEN checking THEN should ignore
    [Tags]    unit    evidence    validate    file-watcher
    ${result}=    Handler Should Ignore Path    /src/main.py
    Should Be True    ${result}
    ${result2}=    Handler Should Ignore Path    /image.png
    Should Be True    ${result2}

Handler Should Ignore Git Directory
    [Documentation]    GIVEN .git path WHEN checking THEN should ignore
    [Tags]    unit    evidence    validate    file-watcher
    ${result}=    Handler Should Ignore Path    /.git/config
    Should Be True    ${result}
    ${result2}=    Handler Should Ignore Path    /project/.git/HEAD
    Should Be True    ${result2}

Handler Should Ignore Venv
    [Documentation]    GIVEN .venv path WHEN checking THEN should ignore
    [Tags]    unit    evidence    validate    file-watcher
    ${result}=    Handler Should Ignore Path    /.venv/lib/something.md
    Should Be True    ${result}

Handler Should Process YAML
    [Documentation]    GIVEN YAML path WHEN checking THEN should process
    [Tags]    unit    evidence    validate    file-watcher
    ${result}=    Handler Should Process Markdown    /config.yaml
    Should Be True    ${result}
    ${result2}=    Handler Should Process Markdown    /docker-compose.yml
    Should Be True    ${result2}

# =============================================================================
# FileWatcher Tests
# =============================================================================

Watcher Creation
    [Documentation]    GIVEN path WHEN creating watcher THEN base_path set and not running
    [Tags]    unit    evidence    create    file-watcher
    ${result}=    Watcher Creation
    Should Be Equal    ${result}[base_path]    /tmp/test
    Should Not Be True    ${result}[is_running]

Watcher Get Status Not Running
    [Documentation]    GIVEN watcher not running WHEN getting status THEN returns correct info
    [Tags]    unit    evidence    validate    file-watcher
    ${result}=    Watcher Get Status
    Should Not Be True    ${result}[running]
    Should Be True    ${result}[has_queue]
    Should Be True    ${result}[has_stats]

Watcher Register Callback
    [Documentation]    GIVEN watcher WHEN registering callback THEN callback is registered
    [Tags]    unit    evidence    create    file-watcher
    ${result}=    Watcher Register Callback
    Should Be True    ${result}

Watcher Start Without Watchdog
    [Documentation]    GIVEN no watchdog WHEN starting THEN fails gracefully
    [Tags]    unit    evidence    validate    file-watcher
    ${result}=    Watcher Start Without Watchdog
    Should Not Be True    ${result}[result]
    Should Not Be True    ${result}[is_running]

