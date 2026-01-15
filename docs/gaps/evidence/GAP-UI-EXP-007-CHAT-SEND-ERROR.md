# GAP-UI-EXP-007: Chat Send Button JavaScript Error

**Status:** OPEN
**Priority:** CRITICAL
**Category:** functionality
**Discovered:** 2026-01-14 via Playwright exploratory testing

## Problem Statement

When clicking the send button in Chat view, a JavaScript TypeError is thrown and the message is never sent. The chat functionality is completely broken.

## Technical Details

### Console Error (Exact)
```
TypeError: n[s[a]] is not a function
    at i (http://localhost:8081/assets/index-5f6ebc8d.js:1:92546)
    at notifyListeners (http://localhost:8081/assets/index-5f6ebc8d.js:1:87644)
    at dirty (http://localhost:8081/assets/index-5f6ebc8d.js:1:88568)
    at set (http://localhost:8081/assets/index-5f6ebc8d.js:1:88251)
    at s (http://localhost:8081/assets/index-5f6ebc8d.js:23:5219)
    at Is/</< (http://localhost:8081/assets/index-5f6ebc8d.js:23:5059)
```

### Affected Files
| File | Line | Issue |
|------|------|-------|
| `agent/governance_ui/views/chat_view.py` | TBD | Send button click handler |
| `agent/governance_ui/handlers/chat_handlers.py` | TBD | `send_message` function |
| `agent/governance_ui/state/initial.py` | TBD | Chat state initialization |

### Reproduction Steps
1. Navigate to http://localhost:8081
2. Click "Chat" in navigation
3. Type any message (or use default "/status")
4. Click send button (arrow icon)
5. **Result**: JavaScript error, message stays in input, no response

### Root Cause Analysis
The error `n[s[a]] is not a function` in minified code suggests:
- A state update callback is not properly defined
- The `send_message` handler may be calling an undefined method
- Possible missing state variable initialization

### Files to Investigate
```python
# agent/governance_ui/views/chat_view.py - Send button definition
v3.VBtn(
    click="send_message",  # This handler may be broken
    ...
)

# agent/governance_ui/handlers/chat_handlers.py - Handler implementation
def send_message(state):
    # Check what this function does and if it updates state correctly
    pass

# agent/governance_ui/state/initial.py - State initialization
initial_state = {
    "chat_messages": [],  # Verify this exists
    "chat_input": "",     # Verify this exists
}
```

### Fix Approach
1. Check if `send_message` handler is properly registered
2. Verify all chat state variables are initialized
3. Check if handler updates state with correct method signature
4. Test with unminified build to get better error message

## Evidence

- **Screenshot**: N/A (error is in console, UI appears frozen)
- **Console Error**: See above
- **Test Input**: "/status" command
- **Expected**: Message appears in chat, response received
- **Actual**: JavaScript error, no message sent

## Related

- Rules: RULE-019 (UI/UX Standards)
- Other GAPs: GAP-UI-EXP-006 (Infrastructure health - similar state issue?)
- Session: SESSION-2026-01-14-EXPLORATORY

---
*Per GAP-DOC-01-v1: Full technical details in evidence file*
