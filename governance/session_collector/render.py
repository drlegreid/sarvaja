"""
Session Rendering and Serialization.

Per RULE-032: Modularized from session_collector.py (591 lines).
Contains: Markdown rendering, to_dict, to_json methods.
"""

import json
from datetime import datetime
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    pass


class SessionRenderMixin:
    """
    Mixin class providing render/serialization methods for SessionCollector.

    Requires the following attributes on the parent class:
    - session_id: str
    - topic: str
    - session_type: str
    - start_time: datetime
    - end_time: Optional[datetime]
    - events: List[SessionEvent]
    - decisions: List[Decision]
    - tasks: List[Task]
    - intent: Optional[SessionIntent]
    - outcome: Optional[SessionOutcome]
    - evidence_dir: Path
    """

    def generate_session_log(self, output_dir: Path = None) -> str:
        """
        Generate markdown session log.

        Args:
            output_dir: Output directory (default: evidence/)

        Returns:
            Path to generated log file
        """
        self.end_time = datetime.now()
        output_dir = output_dir or self.evidence_dir

        # Ensure directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        filename = f"{self.session_id}.md"
        filepath = output_dir / filename

        # Build markdown content
        content = self._render_session_markdown()

        # Write file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return str(filepath)

    def _render_session_markdown(self) -> str:
        """Render session as markdown document."""
        duration = (self.end_time or datetime.now()) - self.start_time

        lines = [
            f"# Session Evidence Log: {self.topic}",
            "",
            f"**Session ID:** {self.session_id}",
            f"**Type:** {self.session_type}",
            f"**Started:** {self.start_time.isoformat()}",
            f"**Ended:** {(self.end_time or datetime.now()).isoformat()}",
            f"**Duration:** {duration}",
            "",
            "---",
            "",
        ]

        # Intent section (RD-INTENT)
        if hasattr(self, 'intent') and self.intent:
            lines.extend([
                "## Session Intent",
                "",
                f"**Goal:** {self.intent.goal}",
                f"**Source:** {self.intent.source}",
                f"**Captured:** {self.intent.captured_at}",
            ])
            if self.intent.previous_session_id:
                lines.append(f"**Previous Session:** {self.intent.previous_session_id}")
            # Per SESSION-PROMPT-01-v1: Include initial prompt for context recovery
            if hasattr(self.intent, 'initial_prompt') and self.intent.initial_prompt:
                lines.extend([
                    "",
                    "### Initial Prompt",
                    "",
                    f"> {self.intent.initial_prompt}",
                    "",
                ])
            if self.intent.planned_tasks:
                lines.extend([
                    "",
                    "### Planned Tasks",
                    "",
                ])
                for task_id in self.intent.planned_tasks:
                    lines.append(f"- [ ] {task_id}")
            lines.extend(["", "---", ""])

        # Outcome section (RD-INTENT)
        if hasattr(self, 'outcome') and self.outcome:
            lines.extend([
                "## Session Outcome",
                "",
                f"**Status:** {self.outcome.status}",
                f"**Captured:** {self.outcome.captured_at}",
            ])
            if self.outcome.achieved_tasks:
                lines.extend([
                    "",
                    "### Achieved Tasks",
                    "",
                ])
                for task_id in self.outcome.achieved_tasks:
                    lines.append(f"- [x] {task_id}")
            if self.outcome.deferred_tasks:
                lines.extend([
                    "",
                    "### Deferred Tasks",
                    "",
                ])
                for task_id in self.outcome.deferred_tasks:
                    lines.append(f"- [ ] {task_id}")
            if self.outcome.handoff_items:
                lines.extend([
                    "",
                    "### Handoff Items (for next session)",
                    "",
                ])
                for item in self.outcome.handoff_items:
                    lines.append(f"- {item}")
            if self.outcome.discoveries:
                lines.extend([
                    "",
                    "### Discoveries",
                    "",
                ])
                for item in self.outcome.discoveries:
                    lines.append(f"- {item}")
            lines.extend(["", "---", ""])

        # Decisions section
        if self.decisions:
            lines.extend([
                "## Decisions",
                "",
                "| ID | Name | Status |",
                "|-----|------|--------|",
            ])
            for d in self.decisions:
                lines.append(f"| {d.id} | {d.name} | {d.status} |")
            lines.extend(["", "### Decision Details", ""])
            for d in self.decisions:
                lines.extend([
                    f"#### {d.id}: {d.name}",
                    "",
                    f"**Context:** {d.context}",
                    "",
                    f"**Rationale:** {d.rationale}",
                    "",
                ])

        # Tasks section
        if self.tasks:
            lines.extend([
                "## Tasks",
                "",
                "| ID | Name | Status | Priority |",
                "|----|------|--------|----------|",
            ])
            for t in self.tasks:
                lines.append(f"| {t.id} | {t.name} | {t.status} | {t.priority} |")
            lines.append("")

        # Thoughts section (Per AMNESIA recovery - key reasoning chains)
        thought_events = [e for e in self.events if e.event_type == "thought"]
        if thought_events:
            lines.extend([
                "## Key Thoughts",
                "",
                "*Per RECOVER-AMNES-01-v1: Captured for context recovery*",
                "",
            ])
            for event in thought_events:
                thought_type = event.metadata.get("thought_type", "reasoning")
                confidence = event.metadata.get("confidence")
                lines.append(f"### {thought_type.title()}")
                lines.append("")
                lines.append(f"> {event.content}")
                lines.append("")
                if confidence:
                    lines.append(f"*Confidence: {confidence:.1%}*")
                related_tools = event.metadata.get("related_tools", [])
                if related_tools:
                    lines.append(f"*Related tools: {', '.join(related_tools)}*")
                lines.append("")
            lines.extend(["---", ""])

        # Tool calls section (Per AMNESIA recovery - action trail)
        tool_events = [e for e in self.events if e.event_type == "tool_call"]
        if tool_events:
            lines.extend([
                "## Tool Calls",
                "",
                "*Per RECOVER-AMNES-01-v1: Action trail for context recovery*",
                "",
                "| Tool | Success | Duration |",
                "|------|---------|----------|",
            ])
            for event in tool_events:
                tool_name = event.metadata.get("tool_name", event.content[:30])
                success = "✅" if event.metadata.get("success", True) else "❌"
                duration = event.metadata.get("duration_ms", 0)
                lines.append(f"| {tool_name} | {success} | {duration}ms |")
            lines.extend(["", "---", ""])

        # Events timeline
        lines.extend([
            "## Event Timeline",
            "",
        ])
        for event in self.events:
            icon = {
                "prompt": "💬",
                "response": "🤖",
                "decision": "⚖️",
                "task": "📋",
                "error": "❌",
                "intent": "🎯",
                "outcome": "✅",
                "thought": "💭",
                "tool_call": "🔧"
            }.get(event.event_type, "📌")
            lines.append(f"- {icon} **{event.event_type.upper()}** ({event.timestamp}): {event.content[:100]}...")

        lines.extend([
            "",
            "---",
            "",
            "*Generated per RULE-001: Session Evidence Logging*",
        ])

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        result = {
            "session_id": self.session_id,
            "topic": self.topic,
            "session_type": self.session_type,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "events_count": len(self.events),
            "decisions_count": len(self.decisions),
            "tasks_count": len(self.tasks),
            "decisions": [asdict(d) for d in self.decisions],
            "tasks": [asdict(t) for t in self.tasks],
        }

        # Add intent if captured (RD-INTENT)
        if hasattr(self, 'intent') and self.intent:
            result["intent"] = asdict(self.intent)

        # Add outcome if captured (RD-INTENT)
        if hasattr(self, 'outcome') and self.outcome:
            result["outcome"] = asdict(self.outcome)

        return result

    def to_json(self) -> str:
        """Convert session to JSON string."""
        return json.dumps(self.to_dict(), default=str, indent=2)
