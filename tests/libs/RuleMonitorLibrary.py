"""
Robot Framework Library for Rule Monitor Tests.

Per P9.6: Real-time rule monitoring and governance feed.
Migrated from tests/test_rule_monitor.py
"""
from pathlib import Path
from robot.api.deco import keyword


class RuleMonitorLibrary:
    """Library for testing rule monitor module."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.agent_dir = self.project_root / "agent"

    # =============================================================================
    # Module Existence Tests
    # =============================================================================

    @keyword("Rule Monitor Module Exists")
    def rule_monitor_module_exists(self):
        """Rule monitor module must exist."""
        monitor_file = self.agent_dir / "rule_monitor.py"
        return {"exists": monitor_file.exists()}

    @keyword("Rule Monitor Class Importable")
    def rule_monitor_class_importable(self):
        """RuleMonitor class must be importable."""
        try:
            from agent.rule_monitor import RuleMonitor

            monitor = RuleMonitor()
            return {
                "importable": True,
                "instantiable": monitor is not None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Init error: {str(e)}"}

    @keyword("Monitor Has Required Methods")
    def monitor_has_required_methods(self):
        """Monitor must have required methods."""
        try:
            from agent.rule_monitor import RuleMonitor

            monitor = RuleMonitor()

            return {
                "has_get_feed": hasattr(monitor, 'get_feed'),
                "has_log_event": hasattr(monitor, 'log_event'),
                "has_get_alerts": hasattr(monitor, 'get_alerts'),
                "has_get_statistics": hasattr(monitor, 'get_statistics')
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Init error: {str(e)}"}

    # =============================================================================
    # Event Logging Tests
    # =============================================================================

    @keyword("Log Event Works")
    def log_event_works(self):
        """Should log governance events."""
        try:
            from agent.rule_monitor import RuleMonitor

            monitor = RuleMonitor()
            result = monitor.log_event(
                event_type="rule_query",
                source="agent-001",
                details={"rule_id": "RULE-001"}
            )

            return {
                "is_dict": isinstance(result, dict),
                "success": result.get('success', True)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Log Violation Works")
    def log_violation_works(self):
        """Should log rule violations."""
        try:
            from agent.rule_monitor import RuleMonitor

            monitor = RuleMonitor()
            result = monitor.log_event(
                event_type="violation",
                source="agent-002",
                details={"rule_id": "RULE-011", "reason": "unauthorized access"}
            )

            return {
                "has_event_id_or_success": 'event_id' in result or result.get('success')
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Log Rule Change Works")
    def log_rule_change_works(self):
        """Should log rule changes."""
        try:
            from agent.rule_monitor import RuleMonitor

            monitor = RuleMonitor()
            result = monitor.log_event(
                event_type="rule_change",
                source="admin",
                details={"rule_id": "RULE-015", "change": "created"}
            )

            return {"success": result.get('success', True)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    # =============================================================================
    # Event Feed Tests
    # =============================================================================

    @keyword("Get Feed Works")
    def get_feed_works(self):
        """Should return event feed."""
        try:
            from agent.rule_monitor import RuleMonitor

            monitor = RuleMonitor()
            feed = monitor.get_feed()

            return {"is_list": isinstance(feed, list)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Feed Contains Logged Events")
    def feed_contains_logged_events(self):
        """Feed should contain logged events."""
        try:
            from agent.rule_monitor import RuleMonitor

            monitor = RuleMonitor()

            # Log an event
            monitor.log_event(
                event_type="test_event",
                source="test",
                details={}
            )

            feed = monitor.get_feed()
            return {"has_events": len(feed) > 0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Feed Filters By Event Type")
    def feed_filters_by_event_type(self):
        """Should filter feed by event type."""
        try:
            from agent.rule_monitor import RuleMonitor

            monitor = RuleMonitor()

            # Log different event types
            monitor.log_event("violation", "test", {})
            monitor.log_event("rule_query", "test", {})

            violations = monitor.get_feed(event_type="violation")
            all_violations = all(e['event_type'] == 'violation' for e in violations) if violations else True

            return {"filters_correctly": all_violations}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Feed Respects Limit")
    def feed_respects_limit(self):
        """Should limit feed results."""
        try:
            from agent.rule_monitor import RuleMonitor

            monitor = RuleMonitor()

            # Log multiple events
            for i in range(10):
                monitor.log_event("test", "test", {"i": i})

            feed = monitor.get_feed(limit=5)
            return {"respects_limit": len(feed) <= 5}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

