# E2E-T3-SESSION-TRANSCRIPT: Session Conversation Transcript

Per TEST-E2E-01-v1 Tier 3: Visual CRUD verification for GAP-SESSION-TRANSCRIPT-001.

## Feature: Session Transcript Viewing (E2E-T3-TRANSCRIPT)

### Scenario: Transcript card appears for CC sessions
Given the dashboard is loaded at http://localhost:8081
  And I navigate to the "Sessions" tab
When I click on a session with source_type "CC"
Then the session detail view opens
  And a card with data-testid "session-transcript-card" is visible
  And it displays "Conversation Transcript" in the header
  And it shows an entry count chip (e.g., "23 entries (156 total)")

### Scenario: Transcript shows all entry types
Given I have opened a CC session detail view
When the transcript loads
Then I see entries of these types:
  | Type | Visual | Icon |
  | user_prompt | Blue tonal card | mdi-account |
  | assistant_text | Green tonal card, indented | mdi-robot |
  | tool_use | Orange outlined card, deeply indented, "inbound" chip | mdi-wrench |
  | tool_result | Teal outlined card, deeply indented, "outbound" chip | mdi-arrow-left-bold |
  | thinking | Purple expansion panel (collapsed by default) | mdi-head-lightbulb |
  | compaction | Warning alert banner | mdi-content-cut |

### Scenario: User prompt shows the actual prompt text
Given I have a transcript loaded
When I look at a "user_prompt" entry (blue card)
Then I can see the exact text the user typed
  And the timestamp is shown (HH:MM:SS format)

### Scenario: Tool call shows inbound command with full input
Given I have a transcript loaded
When I look at a "tool_use" entry (orange card)
Then it shows the tool name (e.g., "Bash", "Read", "mcp__gov-tasks__task_create")
  And it shows an "inbound" chip
  And it shows the full JSON input in monospace font
  And MCP tools show a purple "MCP" chip

### Scenario: Tool result shows outbound response
Given I have a transcript loaded
When I look at a "tool_result" entry (teal card)
Then it shows "outbound" chip
  And it shows the tool output in monospace font
  And the content_length character count is displayed
  And error results show a red "error" chip

### Scenario: Expand truncated content
Given I have a transcript with a truncated entry (is_truncated = true)
When I see the "Show Full Content" button on that entry
  And I click "Show Full Content"
Then the entry content expands to show the full text
  And the "Show Full Content" button disappears

### Scenario: Toggle thinking blocks off
Given I have a transcript loaded with thinking entries visible
When I toggle the "Thinking" switch to OFF
Then the transcript reloads
  And no thinking (purple) entries are shown
  And other entry types remain visible

### Scenario: Toggle user prompts off
Given I have a transcript loaded with user_prompt entries
When I toggle the "User Prompts" switch to OFF
Then the transcript reloads
  And no user_prompt (blue) entries are shown
  And tool_result entries still appear (they're separate from user prompts)

### Scenario: Pagination works for large sessions
Given I have a CC session with more than 50 transcript entries
When the transcript loads page 1
Then I see pagination controls at the bottom
  And a "Next" button is enabled
  And a "Previous" button is disabled
When I click "Next"
Then page 2 loads with different entries
  And the "Previous" button is now enabled

### Scenario: Non-CC session shows empty state
Given I navigate to a session that is NOT a CC session (Chat or API type)
When the session detail opens
Then the transcript card shows an info alert:
  "No transcript available. Transcript is only available for Claude Code sessions with JSONL logs."

### Scenario: Session duration shows valid time (not "invalid")
Given I navigate to a session where end_time < start_time (reversed timestamps)
When the session detail loads
Then the duration column shows a valid time (e.g., "1h 57m")
  And it does NOT show "invalid"

## Verification Checklist

- [ ] Transcript card visible on CC session detail
- [ ] All 6 entry types rendered with correct colors and icons
- [ ] User prompts show actual text typed by operator
- [ ] Tool calls show full JSON input (inbound)
- [ ] Tool results show full output (outbound)
- [ ] Truncated entries have "Show Full Content" button
- [ ] Thinking toggle hides/shows thinking blocks
- [ ] User prompt toggle hides/shows user prompts
- [ ] Pagination works (Previous/Next)
- [ ] Non-CC sessions show empty state message
- [ ] Duration no longer shows "invalid"
