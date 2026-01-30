"""
AMNESIA Detection
=================
Detect context loss indicators (RULE-024).

AMNESIA = Autonomous Memory & Network Extraction for Session Intelligence and Awareness
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)
from typing import Dict, List, Optional

# CORE services that indicate potential AMNESIA when recovering
CORE_SERVICES = ["podman", "typedb", "chromadb"]


@dataclass
class AmnesiaResult:
    """Result of AMNESIA detection."""
    detected: bool
    confidence: float  # 0.0 to 1.0
    indicators: List[str] = field(default_factory=list)


def check_amnesia_indicators(
    prev_state: Dict,
    current_services: Optional[Dict] = None
) -> AmnesiaResult:
    """
    Check for AMNESIA indicators by analyzing state patterns.

    AMNESIA Detection Heuristics:
    - Hash changed from previous session → Context may be stale
    - Long time since last check → Potential session restart
    - Services were down and now up → Likely restart occurred

    Args:
        prev_state: Previous healthcheck state (from .healthcheck_state.json)
        current_services: Current service status dict (optional)

    Returns:
        AmnesiaResult with detected flag, confidence, and indicators
    """
    indicators = []
    confidence = 0.0

    prev_hash = prev_state.get("master_hash", "")
    prev_components = prev_state.get("components", {})
    last_check_str = prev_state.get("last_check", "")

    # Indicator 1: No previous state (first run or state wiped)
    if not prev_hash:
        indicators.append("NO_PREVIOUS_STATE")
        confidence += 0.3

    # Indicator 2: Long gap since last check (>1 hour)
    if last_check_str:
        try:
            last_check = datetime.fromisoformat(last_check_str)
            gap_hours = (datetime.now() - last_check).total_seconds() / 3600
            if gap_hours > 1:
                indicators.append(f"LONG_GAP_{int(gap_hours)}h")
                confidence += min(0.4, gap_hours * 0.1)  # Max 0.4
        except Exception as e:
            logger.debug(f"Failed to parse time gap for amnesia detection: {e}")

    # Indicator 3: Services were DOWN, now UP (restart recovery)
    if current_services:
        for svc in CORE_SERVICES:
            prev_status = prev_components.get(svc, "")
            current_ok = current_services.get(svc, {})
            if hasattr(current_ok, 'ok'):
                current_ok = current_ok.ok
            elif isinstance(current_ok, dict):
                current_ok = current_ok.get('ok', False)
            else:
                current_ok = False

            if prev_status in ("DOWN", "PODMAN_DOWN") and current_ok:
                indicators.append(f"SERVICE_RECOVERED:{svc}")
                confidence += 0.2

    return AmnesiaResult(
        detected=confidence >= 0.5,
        confidence=min(1.0, confidence),
        indicators=indicators
    )
