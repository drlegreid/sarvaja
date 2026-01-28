"""
Trace Minimizer - Intelligent trace compression for LLM context efficiency.

Per RD-TESTING-STRATEGY TEST-003: Debug workflow trace minimization.

This module provides:
- Error classification (AssertionError vs setup failures vs timeouts)
- Stack frame filtering (removes framework internals, keeps user code)
- Summary extraction (error message + relevant context)
- Token estimation for LLM context optimization

Usage:
    minimizer = TraceMinimizer()

    # From pytest report
    minimized = minimizer.minimize_traceback(report.longrepr, test_id="test_example")

    # From trace capture
    minimized_traces = minimizer.minimize_traces(trace_capture.get_traces())

Created: 2026-01-21
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# Error type classification
class ErrorCategory:
    """Error category constants for prioritization."""

    ASSERTION = "assertion"  # AssertionError - most useful for debugging
    ATTRIBUTE = "attribute"  # AttributeError - missing method/property
    TYPE = "type"  # TypeError - wrong argument types
    VALUE = "value"  # ValueError - wrong values
    TIMEOUT = "timeout"  # TimeoutError - performance issues
    SETUP = "setup"  # Setup/teardown failures
    IMPORT = "import"  # ImportError - missing dependencies
    NETWORK = "network"  # Connection errors
    UNKNOWN = "unknown"  # Other errors


# Patterns to identify framework internals (filter these out)
FRAMEWORK_PATTERNS = [
    r"site-packages/pytest",
    r"site-packages/_pytest",
    r"site-packages/pluggy",
    r"site-packages/trame",
    r"site-packages/vuetify",
    r"site-packages/anyio",
    r"site-packages/httpx",
    r"site-packages/starlette",
    r"site-packages/fastapi",
    r"/lib/python\d+\.\d+/",
    r"asyncio/runners\.py",
    r"concurrent/futures",
    r"unittest/mock\.py",
]


@dataclass
class MinimizedFrame:
    """A single minimized stack frame."""

    file: str
    line: int
    function: str
    code: Optional[str] = None
    is_user_code: bool = True

    def format_compact(self) -> str:
        """Format frame compactly."""
        short_file = self.file.split("/")[-1]
        code_snippet = f" → {self.code}" if self.code else ""
        return f"{short_file}:{self.line} {self.function}(){code_snippet}"


@dataclass
class MinimizedTrace:
    """Minimized trace output optimized for LLM context."""

    correlation_id: Optional[str] = None
    test_id: Optional[str] = None
    error_type: str = "unknown"
    error_category: str = ErrorCategory.UNKNOWN
    error_message: str = ""
    bdd_context: Optional[str] = None  # BDD step where error occurred
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    stack_frames: List[MinimizedFrame] = field(default_factory=list)
    related_traces: List[str] = field(default_factory=list)
    original_tokens: int = 0
    minimized_tokens: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "correlation_id": self.correlation_id,
            "test_id": self.test_id,
            "error_type": self.error_type,
            "error_category": self.error_category,
            "error_message": self.error_message,
            "bdd_context": self.bdd_context,
            "source_file": self.source_file,
            "source_line": self.source_line,
            "stack_frames": [
                {"file": f.file, "line": f.line, "function": f.function, "code": f.code}
                for f in self.stack_frames
            ],
            "related_traces": self.related_traces,
            "compression": {
                "original_tokens": self.original_tokens,
                "minimized_tokens": self.minimized_tokens,
                "ratio": (
                    f"{(1 - self.minimized_tokens / self.original_tokens) * 100:.0f}%"
                    if self.original_tokens > 0
                    else "N/A"
                ),
            },
        }

    def format_compact(self) -> str:
        """Format trace compactly for LLM context."""
        lines = []
        lines.append(f"[{self.error_category.upper()}] {self.error_type}: {self.error_message}")

        if self.bdd_context:
            lines.append(f"  BDD: {self.bdd_context}")

        if self.stack_frames:
            lines.append(f"  Location: {self.stack_frames[0].format_compact()}")

        if self.correlation_id:
            lines.append(f"  Trace: {self.correlation_id}")

        return "\n".join(lines)


class TraceMinimizer:
    """
    Minimizes traces for efficient LLM context usage.

    Strategies:
    - Error classification for prioritization
    - Stack frame filtering to remove framework internals
    - Message extraction (first line + assertion details)
    - Token estimation before/after compression
    """

    def __init__(
        self,
        max_frames: int = 3,
        max_message_length: int = 200,
        include_user_code_only: bool = True,
    ):
        """Initialize minimizer.

        Args:
            max_frames: Maximum stack frames to keep
            max_message_length: Maximum error message length
            include_user_code_only: Filter out framework code
        """
        self.max_frames = max_frames
        self.max_message_length = max_message_length
        self.include_user_code_only = include_user_code_only
        self._framework_patterns = [re.compile(p) for p in FRAMEWORK_PATTERNS]

    def classify_error(self, error_str: str) -> Tuple[str, str]:
        """Classify error type and category.

        Args:
            error_str: String representation of error

        Returns:
            Tuple of (error_type, error_category)
        """
        # Extract error type from string
        type_match = re.search(r"(\w+Error|\w+Exception|(\w+)Timeout)", error_str)
        error_type = type_match.group(1) if type_match else "Error"

        # Categorize
        error_lower = error_type.lower()
        if "assertion" in error_lower:
            return error_type, ErrorCategory.ASSERTION
        elif "attribute" in error_lower:
            return error_type, ErrorCategory.ATTRIBUTE
        elif "type" in error_lower:
            return error_type, ErrorCategory.TYPE
        elif "value" in error_lower:
            return error_type, ErrorCategory.VALUE
        elif "timeout" in error_lower:
            return error_type, ErrorCategory.TIMEOUT
        elif "import" in error_lower or "module" in error_lower:
            return error_type, ErrorCategory.IMPORT
        elif "connection" in error_lower or "socket" in error_lower:
            return error_type, ErrorCategory.NETWORK
        elif "fixture" in error_str.lower() or "setup" in error_str.lower():
            return error_type, ErrorCategory.SETUP
        else:
            return error_type, ErrorCategory.UNKNOWN

    def extract_message(self, error_str: str) -> str:
        """Extract the core error message.

        Args:
            error_str: Full error string

        Returns:
            Extracted and truncated message
        """
        # Try to find assertion message
        assertion_match = re.search(
            r"AssertionError:\s*(.+?)(?:\n|$)", error_str, re.DOTALL
        )
        if assertion_match:
            msg = assertion_match.group(1).strip()
            # Truncate and clean
            if len(msg) > self.max_message_length:
                msg = msg[: self.max_message_length] + "..."
            return msg

        # Try to find general error message after colon
        msg_match = re.search(r"Error:\s*(.+?)(?:\n|$)", error_str)
        if msg_match:
            msg = msg_match.group(1).strip()
            if len(msg) > self.max_message_length:
                msg = msg[: self.max_message_length] + "..."
            return msg

        # Fallback: first non-empty line
        for line in error_str.split("\n"):
            line = line.strip()
            if line and not line.startswith("E "):
                if len(line) > self.max_message_length:
                    line = line[: self.max_message_length] + "..."
                return line

        return "Unknown error"

    def is_framework_code(self, file_path: str) -> bool:
        """Check if file path is framework/library code.

        Args:
            file_path: Path to check

        Returns:
            True if framework code, False if user code
        """
        for pattern in self._framework_patterns:
            if pattern.search(file_path):
                return True
        return False

    def parse_traceback(self, traceback_str: str) -> List[MinimizedFrame]:
        """Parse traceback string into frames.

        Args:
            traceback_str: Traceback string

        Returns:
            List of MinimizedFrame objects
        """
        frames = []

        # Pattern to match traceback frames
        frame_pattern = re.compile(
            r'File "([^"]+)", line (\d+), in (\w+)\n\s*(.+?)(?=\n|$)',
            re.MULTILINE,
        )

        for match in frame_pattern.finditer(traceback_str):
            file_path = match.group(1)
            line_num = int(match.group(2))
            function = match.group(3)
            code = match.group(4).strip() if match.group(4) else None

            is_user = not self.is_framework_code(file_path)

            frame = MinimizedFrame(
                file=file_path,
                line=line_num,
                function=function,
                code=code,
                is_user_code=is_user,
            )
            frames.append(frame)

        return frames

    def filter_frames(self, frames: List[MinimizedFrame]) -> List[MinimizedFrame]:
        """Filter frames to keep only relevant ones.

        Args:
            frames: All parsed frames

        Returns:
            Filtered frames (user code only, max count)
        """
        if self.include_user_code_only:
            user_frames = [f for f in frames if f.is_user_code]
        else:
            user_frames = frames

        # Keep first N frames (most relevant to error)
        if len(user_frames) > self.max_frames:
            return user_frames[: self.max_frames]

        return user_frames

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Uses rough approximation: ~4 characters per token for code.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        if not text:
            return 0
        # Code tends to be ~4-5 chars per token
        return len(text) // 4

    def minimize_traceback(
        self,
        traceback_str: str,
        test_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        bdd_context: Optional[str] = None,
    ) -> MinimizedTrace:
        """Minimize a traceback string.

        Args:
            traceback_str: Full traceback string
            test_id: Test identifier
            correlation_id: Trace correlation ID
            bdd_context: BDD step context

        Returns:
            MinimizedTrace object
        """
        if not traceback_str:
            return MinimizedTrace(
                test_id=test_id,
                correlation_id=correlation_id,
                error_message="No traceback",
            )

        original_str = str(traceback_str)
        original_tokens = self.estimate_tokens(original_str)

        # Classify error
        error_type, error_category = self.classify_error(original_str)

        # Extract message
        error_message = self.extract_message(original_str)

        # Parse and filter frames
        all_frames = self.parse_traceback(original_str)
        filtered_frames = self.filter_frames(all_frames)

        # Get source location
        source_file = None
        source_line = None
        if filtered_frames:
            source_file = filtered_frames[0].file
            source_line = filtered_frames[0].line

        # Create minimized trace
        minimized = MinimizedTrace(
            correlation_id=correlation_id,
            test_id=test_id,
            error_type=error_type,
            error_category=error_category,
            error_message=error_message,
            bdd_context=bdd_context,
            source_file=source_file,
            source_line=source_line,
            stack_frames=filtered_frames,
            original_tokens=original_tokens,
        )

        # Calculate minimized tokens
        minimized.minimized_tokens = self.estimate_tokens(minimized.format_compact())

        return minimized

    def minimize_traces(
        self,
        traces: List[Dict[str, Any]],
        filter_successful: bool = True,
    ) -> Dict[str, Any]:
        """Minimize a collection of traces.

        Args:
            traces: List of trace dictionaries
            filter_successful: Remove successful (2xx) traces

        Returns:
            Summary with minimized traces
        """
        if filter_successful:
            # Keep only error traces
            error_traces = [
                t
                for t in traces
                if t.get("error")
                or (t.get("status_code") and t.get("status_code") >= 400)
            ]
        else:
            error_traces = traces

        # Group by correlation ID
        by_correlation: Dict[str, List[Dict[str, Any]]] = {}
        for trace in error_traces:
            corr_id = trace.get("correlation_id", "unknown")
            if corr_id not in by_correlation:
                by_correlation[corr_id] = []
            by_correlation[corr_id].append(trace)

        # Summarize each correlation group
        summaries = []
        for corr_id, group_traces in by_correlation.items():
            summary = {
                "correlation_id": corr_id,
                "trace_count": len(group_traces),
                "errors": [t.get("error") for t in group_traces if t.get("error")],
                "status_codes": [
                    t.get("status_code")
                    for t in group_traces
                    if t.get("status_code") and t.get("status_code") >= 400
                ],
                "endpoints": list(set(t.get("url", "") for t in group_traces if t.get("url"))),
            }
            summaries.append(summary)

        original_tokens = self.estimate_tokens(str(traces))
        minimized_tokens = self.estimate_tokens(str(summaries))

        return {
            "total_traces": len(traces),
            "error_traces": len(error_traces),
            "correlation_groups": len(summaries),
            "summaries": summaries,
            "compression": {
                "original_tokens": original_tokens,
                "minimized_tokens": minimized_tokens,
                "ratio": (
                    f"{(1 - minimized_tokens / original_tokens) * 100:.0f}%"
                    if original_tokens > 0
                    else "N/A"
                ),
            },
        }


# Convenience functions


def minimize_for_llm(
    traceback_str: str,
    test_id: Optional[str] = None,
    max_frames: int = 3,
) -> str:
    """Minimize a traceback for LLM context.

    Args:
        traceback_str: Full traceback
        test_id: Test identifier
        max_frames: Maximum frames to include

    Returns:
        Compact string suitable for LLM context
    """
    minimizer = TraceMinimizer(max_frames=max_frames)
    minimized = minimizer.minimize_traceback(traceback_str, test_id=test_id)
    return minimized.format_compact()


def estimate_compression(original: str, minimized: str) -> Dict[str, Any]:
    """Estimate compression ratio.

    Args:
        original: Original text
        minimized: Minimized text

    Returns:
        Compression statistics
    """
    original_tokens = len(original) // 4
    minimized_tokens = len(minimized) // 4
    ratio = (1 - minimized_tokens / original_tokens) * 100 if original_tokens > 0 else 0

    return {
        "original_tokens": original_tokens,
        "minimized_tokens": minimized_tokens,
        "ratio": f"{ratio:.0f}%",
        "saved_tokens": original_tokens - minimized_tokens,
    }
