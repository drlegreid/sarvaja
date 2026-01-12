"""
AMNESIA detection for Claude Code sessions.

Per RULE-024: Detect context loss and suggest memory restoration.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.base import HookConfig, HookResult, DEFAULT_CONFIG


class AmnesiaDetector:
    """
    Detects AMNESIA (context loss) indicators by analyzing state patterns.

    AMNESIA Detection Heuristics:
    - No previous state → First run or state wiped
    - Long gap since last check → Potential session restart
    - Services were down and now up → Likely restart occurred
    - Hash changed unexpectedly → State corruption
    """

    # Confidence thresholds
    DETECTION_THRESHOLD = 0.5  # Minimum confidence to flag AMNESIA
    LONG_GAP_HOURS = 1  # Hours without check to flag gap

    def __init__(self, config: Optional[HookConfig] = None):
        """
        Initialize AMNESIA detector.

        Args:
            config: Hook configuration (uses DEFAULT_CONFIG if None)
        """
        self.config = config or DEFAULT_CONFIG

    def check(
        self,
        prev_state: Dict[str, Any],
        current_services: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> HookResult:
        """
        Check for AMNESIA indicators.

        Args:
            prev_state: Previous healthcheck state
            current_services: Current service status (optional)

        Returns:
            HookResult with detection status and confidence
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

        # Indicator 2: Long gap since last check
        if last_check_str:
            try:
                last_check = datetime.fromisoformat(last_check_str)
                gap_hours = (datetime.now() - last_check).total_seconds() / 3600
                if gap_hours > self.LONG_GAP_HOURS:
                    indicators.append(f"LONG_GAP_{int(gap_hours)}h")
                    confidence += min(0.4, gap_hours * 0.1)  # Max 0.4
            except Exception:
                pass

        # Indicator 3: Services were DOWN, now UP (restart recovery)
        if current_services:
            for svc in self.config.core_services:
                prev_status = prev_components.get(svc, "")
                current_ok = current_services.get(svc, {}).get("ok", False)
                if prev_status in ("DOWN", "DOCKER_DOWN") and current_ok:
                    indicators.append(f"SERVICE_RECOVERED:{svc}")
                    confidence += 0.2

        # Indicator 4: Check entropy state for session restart signs
        entropy_indicators = self._check_entropy_indicators()
        indicators.extend(entropy_indicators["indicators"])
        confidence += entropy_indicators["confidence"]

        # Cap confidence at 1.0
        confidence = min(1.0, confidence)
        detected = confidence >= self.DETECTION_THRESHOLD

        if detected:
            return HookResult.warning(
                f"AMNESIA RISK: {int(confidence * 100)}% confidence",
                resolution_path="/remember sim-ai to restore context",
                detected=True,
                confidence=confidence,
                indicators=indicators
            )

        return HookResult.ok(
            "No AMNESIA indicators detected",
            detected=False,
            confidence=confidence,
            indicators=indicators
        )

    def _check_entropy_indicators(self) -> Dict[str, Any]:
        """
        Check entropy state for AMNESIA indicators.

        Returns:
            Dictionary with indicators list and confidence boost
        """
        indicators = []
        confidence = 0.0

        try:
            entropy_file = self.config.entropy_file
            if not entropy_file.exists():
                indicators.append("NO_ENTROPY_STATE")
                confidence += 0.2
                return {"indicators": indicators, "confidence": confidence}

            import json
            with open(entropy_file) as f:
                state = json.load(f)

            # Check for signs of recent session reset
            tool_count = state.get("tool_count", 0)
            history = state.get("history", [])

            # Very low tool count after previous activity suggests restart
            if tool_count < 5 and len(history) > 1:
                last_event = history[-1] if history else {}
                if last_event.get("event") == "SESSION_RESET":
                    indicators.append("RECENT_SESSION_RESET")
                    confidence += 0.3

        except Exception:
            pass

        return {"indicators": indicators, "confidence": confidence}

    def get_recovery_suggestions(self, indicators: List[str]) -> List[str]:
        """
        Get recovery suggestions based on detected indicators.

        Args:
            indicators: List of detected AMNESIA indicators

        Returns:
            List of recovery action suggestions
        """
        suggestions = []

        if "NO_PREVIOUS_STATE" in indicators:
            suggestions.append("Run /health to initialize state tracking")

        if any("LONG_GAP" in i for i in indicators):
            suggestions.append("Run /remember sim-ai to restore project context")

        if any("SERVICE_RECOVERED" in i for i in indicators):
            suggestions.append("Verify MCP connections are stable")

        if "RECENT_SESSION_RESET" in indicators:
            suggestions.append("Review conversation history for context loss")

        if not suggestions:
            suggestions.append("Context appears stable, continue normally")

        return suggestions
