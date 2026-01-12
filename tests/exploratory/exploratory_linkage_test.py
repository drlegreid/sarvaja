"""
Exploratory Data Linkage Consistency Test
==========================================
Purpose: LLM-driven gap discovery for data linkage relationships.
Tests entity relationships in TypeDB and API responses.

Per RULE-020: LLM-Driven E2E Test Generation
Per RULE-023: Test Before Ship
Per GAP-DATA-002: Cross-entity relationships

Data Linkage Matrix:
- Task → Agent (agent_id field)
- Task → Session (linked_sessions, completed-in relation)
- Task → Rule (linked_rules, implements-rule relation)
- Rule → Document (document-references-rule relation)
- Evidence → Session (has-evidence relation)
- Session → Agent (agent_id field)

Created: 2026-01-12
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import urllib.request
import urllib.error


# Linkage specification - defines expected relationships
LINKAGE_SPEC = {
    "task_agent": {
        "name": "Task → Agent",
        "source": "tasks",
        "target": "agents",
        "field": "agent_id",
        "api_check": "/api/tasks",
        "min_coverage": 0.1,  # At least 10% tasks should have agent_id
        "severity": "high",
    },
    "task_session": {
        "name": "Task → Session",
        "source": "tasks",
        "target": "sessions",
        "field": "linked_sessions",
        "api_check": "/api/tasks",
        "min_coverage": 0.05,  # At least 5% tasks linked to sessions
        "severity": "medium",
    },
    "task_rule": {
        "name": "Task → Rule",
        "source": "tasks",
        "target": "rules",
        "field": "linked_rules",
        "api_check": "/api/tasks",
        "min_coverage": 0.3,  # At least 30% tasks linked to rules
        "severity": "high",
    },
    "session_evidence": {
        "name": "Session → Evidence",
        "source": "sessions",
        "target": "evidence",
        "field": "evidence_files",
        "api_check": "/api/sessions",
        "min_coverage": 0.5,  # At least 50% sessions have evidence
        "severity": "high",
    },
    "session_agent": {
        "name": "Session → Agent",
        "source": "sessions",
        "target": "agents",
        "field": "agent_id",
        "api_check": "/api/sessions",
        "min_coverage": 0.1,  # At least 10% sessions have agent_id
        "severity": "medium",
    },
}


class ExploratoryLinkageTest:
    """LLM-driven data linkage consistency testing."""

    def __init__(self, api_base: str = "http://localhost:8082"):
        self.api_base = api_base
        self.gaps: List[Dict[str, Any]] = []
        self.findings: List[Dict[str, Any]] = []
        self.entity_data: Dict[str, List[Dict]] = {}
        self.results_path = Path(__file__).parent.parent.parent / "results"

    def log_gap(
        self,
        linkage: str,
        expected: str,
        actual: str,
        severity: str = "high",
        details: Optional[Dict] = None
    ):
        """Log a discovered gap."""
        gap = {
            "timestamp": datetime.now().isoformat(),
            "linkage": linkage,
            "expected": expected,
            "actual": actual,
            "severity": severity,
            "details": details or {},
            "gap_id": f"GAP-LINK-{len(self.gaps) + 1:03d}"
        }
        self.gaps.append(gap)
        print(f"[GAP] {gap['gap_id']}: {linkage} - {expected} (was: {actual})")

    def log_finding(self, linkage: str, finding: str, status: str = "ok"):
        """Log a finding (pass or fail)."""
        self.findings.append({
            "timestamp": datetime.now().isoformat(),
            "linkage": linkage,
            "finding": finding,
            "status": status
        })
        symbol = "[OK]" if status == "ok" else "[!!]"
        print(f"{symbol} {linkage}: {finding}")

    def fetch_entities(self) -> Dict[str, List[Dict]]:
        """Fetch all entity data from API."""
        print("\n" + "=" * 60)
        print("PHASE 1: FETCHING ENTITY DATA")
        print("=" * 60)

        endpoints = {
            "tasks": "/api/tasks?limit=200",
            "sessions": "/api/sessions?limit=200",
            "agents": "/api/agents",
            "rules": "/api/rules?limit=200",
        }

        for entity, endpoint in endpoints.items():
            try:
                url = f"{self.api_base}{endpoint}"
                req = urllib.request.Request(url, headers={"Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode('utf-8'))
                        self.entity_data[entity] = data if isinstance(data, list) else []
                        print(f"  [OK] {entity}: {len(self.entity_data[entity])} items")
                    else:
                        self.entity_data[entity] = []
                        self.log_gap(
                            f"{entity}_fetch",
                            "HTTP 200",
                            f"HTTP {resp.status}",
                            "critical"
                        )
            except urllib.error.HTTPError as e:
                self.entity_data[entity] = []
                self.log_gap(
                    f"{entity}_fetch",
                    "HTTP 200",
                    f"HTTP {e.code}",
                    "critical"
                )
            except Exception as e:
                self.entity_data[entity] = []
                self.log_gap(
                    f"{entity}_fetch",
                    "Connected",
                    str(e)[:50],
                    "critical"
                )

        return self.entity_data

    def check_linkage_coverage(self, spec: Dict[str, Any]) -> Tuple[float, Dict]:
        """
        Check coverage for a specific linkage type.

        Returns:
            Tuple of (coverage_ratio, details_dict)
        """
        source_data = self.entity_data.get(spec["source"], [])
        field = spec["field"]

        if not source_data:
            return 0.0, {"total": 0, "linked": 0, "missing": []}

        total = len(source_data)
        linked = 0
        missing_ids = []

        for item in source_data:
            value = item.get(field)
            # Check if field has meaningful value
            if value is not None and value != "" and value != [] and value != {}:
                linked += 1
            else:
                # Track unlinked items for debugging
                item_id = item.get("task_id") or item.get("session_id") or item.get("id", "?")
                if len(missing_ids) < 10:  # Limit to first 10
                    missing_ids.append(item_id)

        coverage = linked / total if total > 0 else 0.0

        return coverage, {
            "total": total,
            "linked": linked,
            "coverage_pct": round(coverage * 100, 1),
            "sample_missing": missing_ids
        }

    def check_all_linkages(self):
        """Check all linkage types against specification."""
        print("\n" + "=" * 60)
        print("PHASE 2: LINKAGE COVERAGE ANALYSIS")
        print("=" * 60)

        for linkage_id, spec in LINKAGE_SPEC.items():
            coverage, details = self.check_linkage_coverage(spec)

            if coverage >= spec["min_coverage"]:
                self.log_finding(
                    spec["name"],
                    f"Coverage {details['coverage_pct']}% >= {spec['min_coverage']*100}% "
                    f"({details['linked']}/{details['total']} linked)"
                )
            else:
                self.log_gap(
                    spec["name"],
                    f">= {spec['min_coverage']*100}% linked",
                    f"{details['coverage_pct']}% linked ({details['linked']}/{details['total']})",
                    spec["severity"],
                    details
                )

    def check_referential_integrity(self):
        """Check that linked IDs actually exist in target entities."""
        print("\n" + "=" * 60)
        print("PHASE 3: REFERENTIAL INTEGRITY CHECK")
        print("=" * 60)

        # Build lookup sets
        agent_ids = {a.get("agent_id") for a in self.entity_data.get("agents", [])}
        session_ids = {s.get("session_id") for s in self.entity_data.get("sessions", [])}
        rule_ids = {r.get("id") or r.get("rule_id") for r in self.entity_data.get("rules", [])}

        # Check Task → Agent integrity
        orphan_count = 0
        for task in self.entity_data.get("tasks", []):
            agent_id = task.get("agent_id")
            if agent_id and agent_id not in agent_ids:
                orphan_count += 1
        if orphan_count > 0:
            self.log_gap(
                "Task → Agent Integrity",
                "All agent_ids reference valid agents",
                f"{orphan_count} tasks reference non-existent agents",
                "high"
            )
        else:
            self.log_finding("Task → Agent Integrity", "All agent references valid")

        # Check Task → Session integrity
        orphan_sessions = 0
        for task in self.entity_data.get("tasks", []):
            linked = task.get("linked_sessions", [])
            if isinstance(linked, list):
                for sid in linked:
                    if sid not in session_ids:
                        orphan_sessions += 1
        if orphan_sessions > 0:
            self.log_gap(
                "Task → Session Integrity",
                "All session links reference valid sessions",
                f"{orphan_sessions} invalid session references",
                "medium"
            )
        else:
            self.log_finding("Task → Session Integrity", "All session references valid")

        # Check Task → Rule integrity
        orphan_rules = 0
        for task in self.entity_data.get("tasks", []):
            linked = task.get("linked_rules", [])
            if isinstance(linked, list):
                for rid in linked:
                    if rid not in rule_ids:
                        orphan_rules += 1
        if orphan_rules > 0:
            self.log_gap(
                "Task → Rule Integrity",
                "All rule links reference valid rules",
                f"{orphan_rules} invalid rule references",
                "medium"
            )
        else:
            self.log_finding("Task → Rule Integrity", "All rule references valid")

    def check_bidirectional_consistency(self):
        """Check bidirectional relationship consistency."""
        print("\n" + "=" * 60)
        print("PHASE 4: BIDIRECTIONAL CONSISTENCY")
        print("=" * 60)

        # If Task links to Session, Session should have Task in completed tasks
        # This is checking TypeDB relation consistency

        tasks = self.entity_data.get("tasks", [])
        sessions = self.entity_data.get("sessions", [])

        # Build session → task mapping from tasks
        session_task_map: Dict[str, List[str]] = {}
        for task in tasks:
            linked_sessions = task.get("linked_sessions") or []
            for sid in linked_sessions:
                if sid not in session_task_map:
                    session_task_map[sid] = []
                session_task_map[sid].append(task.get("task_id"))

        # Check if sessions report matching task counts
        mismatches = 0
        for session in sessions:
            sid = session.get("session_id")
            reported_count = session.get("tasks_completed", 0)
            actual_tasks = len(session_task_map.get(sid, []))

            # Allow some flexibility - session might have tasks not in our snapshot
            if actual_tasks > 0 and reported_count == 0:
                mismatches += 1

        if mismatches > 0:
            self.log_gap(
                "Session ↔ Task Consistency",
                "Session task counts match linked tasks",
                f"{mismatches} sessions have linked tasks but tasks_completed=0",
                "medium"
            )
        else:
            self.log_finding(
                "Session ↔ Task Consistency",
                "Session task counts consistent"
            )

    def generate_robot_keywords(self) -> str:
        """Generate Robot Framework keywords for linkage tests."""
        print("\n" + "=" * 60)
        print("PHASE 5: ROBOT FRAMEWORK INTEGRATION")
        print("=" * 60)

        keyword_content = '''*** Keywords ***
# =============================================================================
# DATA LINKAGE CONSISTENCY TESTS
# Generated from exploratory_linkage_test.py
# =============================================================================

Verify Task Agent Linkage
    [Documentation]    Check tasks have agent_id populated
    [Tags]    linkage    task_agent
    ${tasks}=    Get Tasks Via API
    ${linked}=    Count Items With Field    ${tasks}    agent_id
    ${total}=    Get Length    ${tasks}
    ${ratio}=    Evaluate    ${linked} / ${total} if ${total} > 0 else 0
    Should Be True    ${ratio} >= 0.1    Task-Agent linkage below 10%

Verify Task Session Linkage
    [Documentation]    Check tasks have linked_sessions
    [Tags]    linkage    task_session
    ${tasks}=    Get Tasks Via API
    ${linked}=    Count Items With Non Empty List    ${tasks}    linked_sessions
    ${total}=    Get Length    ${tasks}
    ${ratio}=    Evaluate    ${linked} / ${total} if ${total} > 0 else 0
    Log    Task-Session linkage: ${ratio}

Verify Task Rule Linkage
    [Documentation]    Check tasks have linked_rules
    [Tags]    linkage    task_rule
    ${tasks}=    Get Tasks Via API
    ${linked}=    Count Items With Non Empty List    ${tasks}    linked_rules
    ${total}=    Get Length    ${tasks}
    ${ratio}=    Evaluate    ${linked} / ${total} if ${total} > 0 else 0
    Should Be True    ${ratio} >= 0.3    Task-Rule linkage below 30%

Verify Session Evidence Linkage
    [Documentation]    Check sessions have evidence_files
    [Tags]    linkage    session_evidence
    ${sessions}=    Get Sessions Via API
    ${linked}=    Count Items With Non Empty List    ${sessions}    evidence_files
    ${total}=    Get Length    ${sessions}
    ${ratio}=    Evaluate    ${linked} / ${total} if ${total} > 0 else 0
    Should Be True    ${ratio} >= 0.5    Session-Evidence linkage below 50%

Check Referential Integrity Task Agent
    [Documentation]    Verify task agent_id references exist
    [Tags]    integrity    task_agent
    ${tasks}=    Get Tasks Via API
    ${agents}=    Get Agents Via API
    ${agent_ids}=    Get Field Values    ${agents}    agent_id
    FOR    ${task}    IN    @{tasks}
        ${aid}=    Get From Dictionary    ${task}    agent_id    default=${NONE}
        Continue For Loop If    '${aid}' == 'None'
        Should Contain    ${agent_ids}    ${aid}    Task references non-existent agent
    END

# Helper keywords
Count Items With Field
    [Arguments]    ${items}    ${field}
    ${count}=    Set Variable    0
    FOR    ${item}    IN    @{items}
        ${value}=    Get From Dictionary    ${item}    ${field}    default=${NONE}
        ${count}=    Run Keyword If    '${value}' != 'None' and '${value}' != ''
        ...    Evaluate    ${count} + 1    ELSE    Set Variable    ${count}
    END
    RETURN    ${count}

Count Items With Non Empty List
    [Arguments]    ${items}    ${field}
    ${count}=    Set Variable    0
    FOR    ${item}    IN    @{items}
        ${value}=    Get From Dictionary    ${item}    ${field}    default=${EMPTY}
        ${len}=    Get Length    ${value}
        ${count}=    Run Keyword If    ${len} > 0
        ...    Evaluate    ${count} + 1    ELSE    Set Variable    ${count}
    END
    RETURN    ${count}
'''
        return keyword_content

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive linkage report."""
        print("\n" + "=" * 60)
        print("EXPLORATORY LINKAGE REPORT")
        print("=" * 60)

        critical = [g for g in self.gaps if g["severity"] == "critical"]
        high = [g for g in self.gaps if g["severity"] == "high"]
        medium = [g for g in self.gaps if g["severity"] == "medium"]
        low = [g for g in self.gaps if g["severity"] == "low"]

        print(f"\nTotal Gaps: {len(self.gaps)}")
        print(f"  Critical: {len(critical)}")
        print(f"  High: {len(high)}")
        print(f"  Medium: {len(medium)}")
        print(f"  Low: {len(low)}")

        if self.gaps:
            print("\nGap Details:")
            for g in self.gaps:
                print(f"  [{g['severity'].upper()}] {g['gap_id']}: {g['linkage']}")
                print(f"      Expected: {g['expected']}")
                print(f"      Actual: {g['actual']}")

        report = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "data_linkage_consistency",
            "summary": {
                "total_gaps": len(self.gaps),
                "critical": len(critical),
                "high": len(high),
                "medium": len(medium),
                "low": len(low),
                "findings_ok": sum(1 for f in self.findings if f["status"] == "ok")
            },
            "entity_counts": {k: len(v) for k, v in self.entity_data.items()},
            "gaps": self.gaps,
            "findings": self.findings
        }

        # Save report
        self.results_path.mkdir(exist_ok=True)
        report_file = self.results_path / "linkage_findings.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved: {report_file}")

        return report

    def run_discovery(self) -> Dict[str, Any]:
        """Run the full linkage discovery process."""
        print("=" * 70)
        print("EXPLORATORY DATA LINKAGE CONSISTENCY TEST")
        print("=" * 70)
        print(f"API Base: {self.api_base}")
        print(f"Started: {datetime.now().isoformat()}")
        print(f"Linkage types to check: {list(LINKAGE_SPEC.keys())}")

        # Phase 1: Fetch all entities
        self.fetch_entities()

        # Phase 2: Check linkage coverage
        self.check_all_linkages()

        # Phase 3: Check referential integrity
        self.check_referential_integrity()

        # Phase 4: Check bidirectional consistency
        self.check_bidirectional_consistency()

        # Phase 5: Generate Robot Framework keywords
        robot_keywords = self.generate_robot_keywords()

        # Save Robot keywords
        robot_file = Path(__file__).parent.parent / "e2e" / "resources" / "linkage.resource"
        robot_file.parent.mkdir(parents=True, exist_ok=True)
        with open(robot_file, "w") as f:
            f.write(robot_keywords)
        print(f"Robot keywords saved: {robot_file}")

        # Generate report
        return self.generate_report()


if __name__ == "__main__":
    test = ExploratoryLinkageTest()
    test.run_discovery()
