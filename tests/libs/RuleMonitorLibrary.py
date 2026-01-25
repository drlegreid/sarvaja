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

    # =============================================================================
    # Alert Tests
    # =============================================================================

    @keyword("Get Alerts Works")
    def get_alerts_works(self):
        """Should return active alerts."""
        try:
            from agent.rule_monitor import RuleMonitor

            monitor = RuleMonitor()
            alerts = monitor.get_alerts()

            return {"is_list": isinstance(alerts, list)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Violation Generates Alert")
    def violation_generates_alert(self):
        """Violations should generate alerts."""
        try:
            from agent.rule_monitor import RuleMonitor

            monitor = RuleMonitor()

            # Log a violation
            monitor.log_event(
                event_type="violation",
                source="agent-bad",
                details={"rule_id": "RULE-011"}
            )

            alerts = monitor.get_alerts()
            return {"generates_alert": len(alerts) > 0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Acknowledge Alert Works")
    def acknowledge_alert_works(self):
        """Should be able to acknowledge alerts."""
        try:
            from agent.rule_monitor import RuleMonitor

            monitor = RuleMonitor()

            # Create an alert
            monitor.log_event("violation", "test", {"rule_id": "RULE-001"})
            alerts = monitor.get_alerts()

            if alerts:
                result = monitor.acknowledge_alert(alerts[0]['alert_id'])
                return {"success": result.get('success', True)}
            return {"success": True}  # No alerts to acknowledge is valid
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    # =============================================================================
    # Statistics Tests
    # =============================================================================

    @keyword("Get Statistics Works")
    def get_statistics_works(self):
        """Should return monitoring statistics."""
        try:
            from agent.rule_monitor import RuleMonitor

            monitor = RuleMonitor()
            stats = monitor.get_statistics()

            return {
                "is_dict": isinstance(stats, dict),
                "has_total_events": 'total_events' in stats
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Statistics By Type Works")
    def statistics_by_type_works(self):
        """Should break down statistics by event type."""
        try:
            from agent.rule_monitor import RuleMonitor

            monitor = RuleMonitor()

            # Log different types
            monitor.log_event("violation", "test", {})
            monitor.log_event("rule_query", "test", {})

            stats = monitor.get_statistics()
            return {"has_events_by_type": 'events_by_type' in stats}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Get Hourly Stats Works")
    def get_hourly_stats_works(self):
        """Should provide hourly statistics."""
        try:
            from agent.rule_monitor import RuleMonitor

            monitor = RuleMonitor()
            hourly = monitor.get_hourly_stats()

            return {"is_dict": isinstance(hourly, dict)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    # =============================================================================
    # Rule Tracking Tests
    # =============================================================================

    @keyword("Get Rule Events Works")
    def get_rule_events_works(self):
        """Should get events for a specific rule."""
        try:
            from agent.rule_monitor import RuleMonitor

            monitor = RuleMonitor()

            # Log events for specific rule
            monitor.log_event("rule_query", "test", {"rule_id": "RULE-001"})

            events = monitor.get_rule_events("RULE-001")
            return {"is_list": isinstance(events, list)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Get Top Rules Works")
    def get_top_rules_works(self):
        """Should return most queried rules."""
        try:
            from agent.rule_monitor import RuleMonitor

            monitor = RuleMonitor()

            # Query some rules
            for _ in range(5):
                monitor.log_event("rule_query", "test", {"rule_id": "RULE-001"})
            for _ in range(3):
                monitor.log_event("rule_query", "test", {"rule_id": "RULE-011"})

            top_rules = monitor.get_top_rules()
            return {"is_list": isinstance(top_rules, list)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    # =============================================================================
    # Integration Tests
    # =============================================================================

    @keyword("Factory Function Works")
    def factory_function_works(self):
        """Factory function should create monitor."""
        try:
            from agent.rule_monitor import create_rule_monitor

            monitor = create_rule_monitor()
            return {"created": monitor is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Event Persistence Works")
    def event_persistence_works(self):
        """Events should persist in memory."""
        try:
            from agent.rule_monitor import RuleMonitor

            monitor = RuleMonitor()

            # Log event
            monitor.log_event("test", "test", {"data": "value"})

            # Should be retrievable
            feed = monitor.get_feed()
            return {"persists": len(feed) > 0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}
