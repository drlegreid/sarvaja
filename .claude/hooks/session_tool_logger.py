#!/usr/bin/env python3
"""
Session Tool Logger Hook - PostToolUse Auto-Logging.

Per GAP-SESSION-THOUGHT-001: Auto-log tool calls to governance sessions.
Per WORKFLOW-AUTO-01-v1: Autonomous operation with silent fail.

This hook is called after every tool use and logs the call to the
active governance session in TypeDB. If no session is active or
TypeDB is unavailable, it silently fails without blocking workflow.

Usage:
    Configured in .claude/settings.local.json:
    {
        "hooks": {
            "PostToolUse": [{
                "hooks": [{
                    "type": "command",
                    "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/session_tool_logger.py\"",
                    "timeout": 1
                }]
            }]
        }
    }
"""

import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from hooks_utils.session_tool_logger import main
    sys.exit(main())
except ImportError as e:
    # Silent fail if module not available
    sys.exit(0)
except Exception:
    # Never block main workflow
    sys.exit(0)
