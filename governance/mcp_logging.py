"""
MCP Structured Logging Configuration.

Per MCP-LOGGING-01-v1: Enterprise logging for MCP servers.

Log Levels:
    TRACE (5)  - Protocol-level details, JSON-RPC messages
    DEBUG (10) - Tool invocations, timing, internal state
    INFO (20)  - Server start/stop, tool registration
    WARNING (30) - Recoverable issues, deprecations
    ERROR (40) - Failures, exceptions

Configuration:
    MCP_LOG_LEVEL=DEBUG  - Set log level (default: ERROR in prod)
    MCP_LOG_FILE=path    - Log to file (default: logs/mcp.jsonl)
    MCP_LOG_CONSOLE=1    - Also log to console (default: 0)

Usage:
    from governance.mcp_logging import get_logger, log_tool_call

    logger = get_logger("gov-core")
    logger.info("server_started", tools=15)

    with log_tool_call(logger, "health_check", args={}):
        result = do_health_check()
"""

import logging
import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import structlog

# =============================================================================
# CUSTOM LOG LEVELS
# =============================================================================

# Add TRACE level (more verbose than DEBUG)
TRACE = 5
logging.addLevelName(TRACE, "TRACE")


def trace(self, message, *args, **kwargs):
    """Log at TRACE level."""
    if self.isEnabledFor(TRACE):
        self._log(TRACE, message, args, **kwargs)


logging.Logger.trace = trace

# =============================================================================
# CONFIGURATION
# =============================================================================

# Log level from environment (default ERROR for production)
LOG_LEVEL_MAP = {
    "TRACE": TRACE,
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}

MCP_LOG_LEVEL = os.getenv("MCP_LOG_LEVEL", "ERROR").upper()
MCP_LOG_FILE = os.getenv("MCP_LOG_FILE", "logs/mcp.jsonl")
MCP_LOG_CONSOLE = os.getenv("MCP_LOG_CONSOLE", "0") == "1"

# Ensure logs directory exists
LOG_DIR = Path(MCP_LOG_FILE).parent
LOG_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# STRUCTLOG CONFIGURATION
# =============================================================================

_configured = False


def configure_logging():
    """Configure structlog for MCP servers."""
    global _configured
    if _configured:
        return

    level = LOG_LEVEL_MAP.get(MCP_LOG_LEVEL, logging.ERROR)

    # Processors for structured logging
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # JSON output for file logging
    if MCP_LOG_FILE:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(
            file=open(MCP_LOG_FILE, "a") if MCP_LOG_FILE else sys.stderr
        ),
        cache_logger_on_first_use=True,
    )

    _configured = True


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger for an MCP server.

    Args:
        name: Server name (e.g., "gov-core", "gov-agents")

    Returns:
        Configured structlog logger
    """
    configure_logging()
    return structlog.get_logger(server=name)


# =============================================================================
# TOOL CALL LOGGING
# =============================================================================

@contextmanager
def log_tool_call(
    logger: structlog.BoundLogger,
    tool_name: str,
    args: Optional[Dict[str, Any]] = None
):
    """
    Context manager for logging tool calls with timing.

    Usage:
        with log_tool_call(logger, "health_check", {"timeout": 5}):
            result = do_health_check()
    """
    start_time = time.perf_counter()
    call_id = f"{tool_name}-{int(time.time() * 1000)}"

    logger.debug(
        "tool_call_start",
        tool=tool_name,
        call_id=call_id,
        args=args or {}
    )

    try:
        yield call_id
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "tool_call_success",
            tool=tool_name,
            call_id=call_id,
            duration_ms=round(duration_ms, 2)
        )
    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.error(
            "tool_call_error",
            tool=tool_name,
            call_id=call_id,
            duration_ms=round(duration_ms, 2),
            error=type(e).__name__,  # BUG-476-MLC-1: sanitize error info
            error_type=type(e).__name__
        )
        raise


def log_server_start(
    logger: structlog.BoundLogger,
    server_name: str,
    tool_count: int,
    version: str = "1.0.0"
):
    """Log MCP server startup."""
    logger.info(
        "server_started",
        server=server_name,
        tools=tool_count,
        version=version,
        log_level=MCP_LOG_LEVEL,
        pid=os.getpid()
    )


def log_server_stop(logger: structlog.BoundLogger, server_name: str):
    """Log MCP server shutdown."""
    logger.info("server_stopped", server=server_name)


# =============================================================================
# METRICS LOGGING
# =============================================================================

class MCPMetrics:
    """
    Metrics collector for MCP server operations.

    Writes metrics to a separate JSONL file for analysis.
    """

    def __init__(self, server_name: str):
        self.server_name = server_name
        self.metrics_file = Path(os.getenv(
            "MCP_METRICS_FILE",
            "logs/mcp-metrics.jsonl"
        ))
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        self._tool_calls = {}
        self._start_time = time.time()

    def record_tool_call(
        self,
        tool_name: str,
        duration_ms: float,
        success: bool,
        error: Optional[str] = None
    ):
        """Record a tool call metric."""
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "server": self.server_name,
            "metric_type": "tool_call",
            "tool": tool_name,
            "duration_ms": round(duration_ms, 2),
            "success": success,
            "error": error
        }
        self._write_metric(metric)

        # Update in-memory stats
        if tool_name not in self._tool_calls:
            self._tool_calls[tool_name] = {"count": 0, "errors": 0, "total_ms": 0}
        self._tool_calls[tool_name]["count"] += 1
        self._tool_calls[tool_name]["total_ms"] += duration_ms
        if not success:
            self._tool_calls[tool_name]["errors"] += 1

    def record_startup(self, tool_count: int, startup_ms: float):
        """Record server startup metric."""
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "server": self.server_name,
            "metric_type": "startup",
            "tools": tool_count,
            "startup_ms": round(startup_ms, 2)
        }
        self._write_metric(metric)

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        uptime = time.time() - self._start_time
        return {
            "server": self.server_name,
            "uptime_seconds": round(uptime, 2),
            "tool_stats": self._tool_calls
        }

    def _write_metric(self, metric: Dict[str, Any]):
        """Write metric to JSONL file."""
        import json
        try:
            with open(self.metrics_file, "a") as f:
                f.write(json.dumps(metric) + "\n")
        except Exception:
            pass  # Don't fail on metrics write errors


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def set_log_level(level: str):
    """
    Dynamically change log level.

    Args:
        level: One of TRACE, DEBUG, INFO, WARNING, ERROR
    """
    global MCP_LOG_LEVEL, _configured
    MCP_LOG_LEVEL = level.upper()
    _configured = False  # Force reconfiguration
    configure_logging()
