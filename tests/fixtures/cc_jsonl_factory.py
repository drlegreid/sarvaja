"""
CC JSONL Fixture Factory — shared test fixture for all CC session tests.

Per TEST-FIXTURE-01-v1: Test fixtures MUST match production data format.
All entries match real Claude Code JSONL structure (25+ fields per entry).

Usage:
    factory = CCJsonlFactory()
    entries = factory.make_full_session(turns=3)
    path = factory.write_session_file(tmp_path, turns=3)

    # Convenience for tests that need a temp file with custom entries:
    from tests.fixtures.cc_jsonl_factory import write_jsonl_temp
    path = write_jsonl_temp([{"type": "user", ...}])
"""

import json
import uuid
import base64
import tempfile
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


class CCJsonlFactory:
    """Generate production-format CC JSONL entries for testing.

    All entries include the full field set that real Claude Code writes:
    uuid, parentUuid, sessionId, timestamp, cwd, gitBranch, version,
    userType, isSidechain, message (with content blocks), etc.
    """

    def __init__(
        self,
        session_id: str | None = None,
        cwd: str = "/home/testuser/Documents/project",
        git_branch: str = "main",
        version: str = "2.1.76",
    ):
        self.session_id = session_id or str(uuid.uuid4())
        self.cwd = cwd
        self.git_branch = git_branch
        self.version = version
        self._ts = datetime(2026, 3, 19, 10, 0, 0, tzinfo=timezone.utc)
        self._last_uuid: str | None = None
        self._tool_use_counter = 0

    # -- internal helpers --------------------------------------------------

    def _next_ts(self, delta_seconds: int = 5) -> str:
        """Advance clock and return ISO-8601 timestamp."""
        self._ts += timedelta(seconds=delta_seconds)
        return self._ts.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    def _new_uuid(self) -> str:
        return str(uuid.uuid4())

    def _common_fields(self, entry_type: str, delta_seconds: int = 5) -> dict:
        """Fields present on every entry (user, assistant, system, progress)."""
        entry_uuid = self._new_uuid()
        fields = {
            "type": entry_type,
            "uuid": entry_uuid,
            "parentUuid": self._last_uuid,
            "isSidechain": False,
            "timestamp": self._next_ts(delta_seconds),
            "userType": "external",
            "cwd": self.cwd,
            "sessionId": self.session_id,
            "version": self.version,
            "gitBranch": self.git_branch,
        }
        self._last_uuid = entry_uuid
        return fields

    def _make_tool_use_id(self) -> str:
        self._tool_use_counter += 1
        raw = f"tool-{self._tool_use_counter}-{uuid.uuid4().hex[:16]}"
        return f"toolu_{base64.b64encode(raw.encode()).decode()[:24]}"

    def _make_signature(self, text: str) -> str:
        h = hashlib.sha256(text.encode()).digest()
        return base64.b64encode(h).decode()[:40]

    # -- public entry builders ---------------------------------------------

    def make_user_prompt(self, text: str, **overrides: Any) -> dict:
        """Create a user prompt entry matching production CC format."""
        entry = self._common_fields("user")
        entry["message"] = {
            "role": "user",
            "content": [{"type": "text", "text": text}],
        }
        entry.update(overrides)
        return entry

    def make_assistant_response(
        self,
        text: str,
        model: str = "claude-opus-4-6",
        **overrides: Any,
    ) -> dict:
        """Create an assistant text response matching production CC format."""
        entry = self._common_fields("assistant")
        entry["requestId"] = f"req_{uuid.uuid4().hex[:24]}"
        entry["message"] = {
            "id": f"msg_{uuid.uuid4().hex[:24]}",
            "type": "message",
            "role": "assistant",
            "model": model,
            "content": [{"type": "text", "text": text}],
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {
                "input_tokens": 1500 + len(text),
                "output_tokens": len(text) + 50,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 1200,
                "service_tier": "standard",
            },
        }
        entry.update(overrides)
        return entry

    def make_tool_use(
        self,
        tool_name: str,
        tool_input: dict,
        text: str | None = None,
        model: str = "claude-opus-4-6",
        **overrides: Any,
    ) -> dict:
        """Create an assistant entry with a tool_use content block."""
        entry = self._common_fields("assistant")
        tool_use_id = self._make_tool_use_id()
        entry["requestId"] = f"req_{uuid.uuid4().hex[:24]}"

        content: list[dict] = []
        if text:
            content.append({"type": "text", "text": text})
        content.append({
            "type": "tool_use",
            "id": tool_use_id,
            "name": tool_name,
            "input": tool_input,
        })

        entry["message"] = {
            "id": f"msg_{uuid.uuid4().hex[:24]}",
            "type": "message",
            "role": "assistant",
            "model": model,
            "content": content,
            "stop_reason": "tool_use",
            "stop_sequence": None,
            "usage": {
                "input_tokens": 2000,
                "output_tokens": 150,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 1800,
                "service_tier": "standard",
            },
        }
        entry.update(overrides)
        return entry

    def make_tool_result(
        self,
        tool_use_id: str,
        content: str,
        is_error: bool = False,
        **overrides: Any,
    ) -> dict:
        """Create a user entry with a tool_result content block."""
        entry = self._common_fields("user")
        entry["message"] = {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": content,
                    "is_error": is_error,
                },
            ],
        }
        entry.update(overrides)
        return entry

    def make_thinking(
        self,
        text: str,
        model: str = "claude-opus-4-6",
        **overrides: Any,
    ) -> dict:
        """Create an assistant entry with a thinking content block."""
        entry = self._common_fields("assistant")
        entry["requestId"] = f"req_{uuid.uuid4().hex[:24]}"
        entry["message"] = {
            "id": f"msg_{uuid.uuid4().hex[:24]}",
            "type": "message",
            "role": "assistant",
            "model": model,
            "content": [
                {
                    "type": "thinking",
                    "thinking": text,
                    "signature": self._make_signature(text),
                },
            ],
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {
                "input_tokens": 1000,
                "output_tokens": len(text) + 20,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 800,
                "service_tier": "standard",
            },
        }
        entry.update(overrides)
        return entry

    def make_compaction(self, tokens_removed: int = 5000, **overrides: Any) -> dict:
        """Create a system compaction entry."""
        entry = {
            "type": "system",
            "timestamp": self._next_ts(),
            "compactMetadata": {
                "version": self.version,
                "timestamp": self._ts.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "tokensRemoved": tokens_removed,
            },
        }
        entry.update(overrides)
        return entry

    # -- session builders --------------------------------------------------

    def make_full_session(self, turns: int = 3) -> list[dict]:
        """Generate a complete multi-turn session.

        Each turn is: user_prompt → (optional thinking) → assistant_response
        Turn 2 includes a tool_use → tool_result cycle.
        """
        entries: list[dict] = []

        for i in range(turns):
            # User prompt
            entries.append(self.make_user_prompt(
                f"Turn {i + 1}: Please help with task {i + 1}"))

            if i == 1:
                # Turn 2: tool use cycle
                tool_entry = self.make_tool_use(
                    "Read", {"file_path": f"/tmp/file_{i}.py"},
                    text=f"Let me read file_{i}.py")
                tool_id = [b for b in tool_entry["message"]["content"]
                           if b["type"] == "tool_use"][0]["id"]
                entries.append(tool_entry)
                entries.append(self.make_tool_result(
                    tool_id, f"# Contents of file_{i}.py\ndef main(): pass"))
                entries.append(self.make_assistant_response(
                    f"I've read the file. Here's my analysis for task {i + 1}."))
            elif i == 0:
                # Turn 1: thinking + response
                entries.append(self.make_thinking(
                    f"Let me think about task {i + 1}..."))
                entries.append(self.make_assistant_response(
                    f"I'll help with task {i + 1}. Let me start."))
            else:
                # Other turns: simple response
                entries.append(self.make_assistant_response(
                    f"Done with task {i + 1}. All changes applied."))

        return entries

    # -- file I/O ----------------------------------------------------------

    @staticmethod
    def write_jsonl(entries: list[dict], path: Path) -> Path:
        """Write entries to a JSONL file."""
        with open(path, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")
        return path

    def write_session_file(
        self,
        directory: Path,
        name: str | None = None,
        turns: int = 3,
    ) -> Path:
        """Create a JSONL session file with a full session."""
        if name is None:
            name = f"{self.session_id}.jsonl"
        if not name.endswith(".jsonl"):
            name += ".jsonl"
        entries = self.make_full_session(turns=turns)
        return self.write_jsonl(entries, directory / name)


# -- module-level convenience -----------------------------------------------

def write_jsonl_temp(entries: list[dict]) -> Path:
    """Write entries to a temp JSONL file, return path.

    Convenience wrapper for tests that don't use pytest tmp_path.
    Caller should unlink the file when done (or use pytest tmp_path instead).
    """
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
    for entry in entries:
        f.write(json.dumps(entry) + "\n")
    f.close()
    return Path(f.name)
