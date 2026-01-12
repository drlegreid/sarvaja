# /entropy - Check Session Entropy

Check current session entropy and context usage.

## Usage
```
/entropy
```

## What This Does
Shows current session metrics:
- Tool call count
- Session duration
- Entropy level (LOW/MEDIUM/HIGH)

## Manual Check
Run directly: `python .claude/hooks/entropy_monitor.py --status`
