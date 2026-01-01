"""
Exploratory UI Test - LLM-Driven Gap Discovery
===============================================
Purpose: LLM explores UI via Playwright MCP to discover gaps against
entity management requirements. Findings feed into Robot Framework tests.

Architecture:
- Exploratory (this): LLM + Playwright MCP → discover what works/doesn't
- Deterministic: Robot Framework → verify spec functionality (TDD)

Entity Management Requirements (spec):
- Rules: CRUD + dependencies + status workflow
- Agents: Read + trust updates + metrics
- Tasks: CRUD + status workflow + assignment
- Sessions: Read + timeline + evidence
- Decisions: Read + rationale + impacts

Created: 2024-12-26
Per RULE-020: LLM-Driven E2E Test Generation
Per RULE-023: Test Before Ship (TDD)
"""

import asyncio
import json
from datetime import datetime
import httpx


# Entity management specification
ENTITY_SPEC = {
    'rules': {
        'expected_operations': ['list', 'create', 'read_detail', 'update', 'delete'],
        'expected_fields': ['id', 'name', 'category', 'status', 'priority', 'directive'],
        'api_endpoint': '/api/rules',
    },
    'agents': {
        'expected_operations': ['list', 'read_detail', 'update_trust'],
        'expected_fields': ['agent_id', 'name', 'agent_type', 'trust_score', 'status'],
        'api_endpoint': '/api/agents',
    },
    'tasks': {
        'expected_operations': ['list', 'create', 'read_detail', 'update', 'delete'],
        'expected_fields': ['task_id', 'description', 'phase', 'status', 'agent_id'],
        'api_endpoint': '/api/tasks',
    },
    'sessions': {
        'expected_operations': ['list', 'read_detail'],
        'expected_fields': ['session_id', 'start_time', 'status', 'agent_id'],
        'api_endpoint': '/api/sessions',
    },
    'decisions': {
        'expected_operations': ['list', 'read_detail'],
        'expected_fields': ['decision_id', 'title', 'status', 'date'],
        'api_endpoint': '/api/decisions',
    },
}


class ExploratoryGapDiscovery:
    """LLM-driven gap discovery for entity management UI."""

    def __init__(self):
        self.api_base = "http://localhost:8082"
        self.gaps = []
        self.findings = []

    def log_gap(self, entity: str, operation: str, expected: str, actual: str, severity: str = "high"):
        """Log a discovered gap."""
        gap = {
            "timestamp": datetime.now().isoformat(),
            "entity": entity,
            "operation": operation,
            "expected": expected,
            "actual": actual,
            "severity": severity,
            "gap_id": f"GAP-UI-{len(self.gaps) + 100:03d}"
        }
        self.gaps.append(gap)
        print(f"[GAP] {gap['gap_id']}: {entity}.{operation} - {expected} (was: {actual})")

    def log_finding(self, entity: str, finding: str, status: str = "ok"):
        """Log a finding (pass or fail)."""
        self.findings.append({
            "timestamp": datetime.now().isoformat(),
            "entity": entity,
            "finding": finding,
            "status": status
        })
        symbol = "[OK]" if status == "ok" else "[!!]"
        print(f"{symbol} {entity}: {finding}")

    async def check_api_availability(self):
        """Check API endpoints return expected data structure."""
        print("\n" + "=" * 60)
        print("PHASE 1: API DATA STRUCTURE CHECK")
        print("=" * 60)

        with httpx.Client(timeout=10) as client:
            for entity, spec in ENTITY_SPEC.items():
                try:
                    r = client.get(f"{self.api_base}{spec['api_endpoint']}")
                    if r.status_code == 200:
                        data = r.json()
                        if isinstance(data, list) and len(data) > 0:
                            # Check field structure
                            item = data[0]
                            missing_fields = []
                            for field in spec['expected_fields']:
                                if field not in item:
                                    missing_fields.append(field)

                            if missing_fields:
                                self.log_gap(entity, "api_structure",
                                           f"Fields: {spec['expected_fields']}",
                                           f"Missing: {missing_fields}", "high")
                            else:
                                self.log_finding(entity, f"API returns {len(data)} items with correct structure")
                        elif isinstance(data, list):
                            self.log_gap(entity, "api_data", "Has data", "Empty list", "medium")
                        else:
                            self.log_gap(entity, "api_response", "List", f"Got {type(data).__name__}", "critical")
                    else:
                        self.log_gap(entity, "api_status", "200 OK", f"HTTP {r.status_code}", "critical")
                except Exception as e:
                    self.log_gap(entity, "api_connection", "Connected", str(e), "critical")

    async def analyze_ui_coverage(self):
        """
        Analyze UI coverage against entity management spec.
        This would use Playwright MCP in a full implementation.
        For now, we document what SHOULD be checked.
        """
        print("\n" + "=" * 60)
        print("PHASE 2: UI COVERAGE ANALYSIS")
        print("=" * 60)
        print("(Use Playwright MCP: mcp__playwright__browser_snapshot)")
        print()

        # Document expected checks per entity
        for entity, spec in ENTITY_SPEC.items():
            print(f"\n--- {entity.upper()} ---")
            for op in spec['expected_operations']:
                print(f"  [ ] {op}: Check UI supports this operation")

            # Known gaps from previous runs
            known_gaps = self._get_known_gaps(entity)
            if known_gaps:
                print(f"  Known gaps: {known_gaps}")

    def _get_known_gaps(self, entity: str) -> list:
        """Return known gaps for entity (from previous discoveries)."""
        known = {
            'rules': [
                "UPDATE: No Edit button",
                "DELETE: No Delete button",
                "READ_DETAIL: Click doesn't show detail panel"
            ],
            'agents': [
                "Navigation: nav-agents data-testid not found"
            ],
            'tasks': [
                "CREATE: No Add button",
                "UPDATE: No Edit button",
                "DELETE: No Delete button",
                "READ_DETAIL: Click doesn't show detail"
            ],
            'sessions': [
                "READ_DETAIL: Click doesn't show detail"
            ],
            'decisions': [
                "READ_DETAIL: Click doesn't show detail"
            ],
        }
        return known.get(entity, [])

    def generate_robot_test_skeleton(self):
        """Generate Robot Framework test skeleton based on discoveries."""
        print("\n" + "=" * 60)
        print("PHASE 3: ROBOT FRAMEWORK TEST SKELETON")
        print("=" * 60)

        robot_content = """*** Settings ***
Documentation    Entity Management E2E Tests (Generated from Exploratory)
Library          Browser
Resource         ../resources/common.resource

*** Test Cases ***
"""
        for entity, spec in ENTITY_SPEC.items():
            for op in spec['expected_operations']:
                test_name = f"Verify {entity.title()} {op.replace('_', ' ').title()}"
                robot_content += f"""
{test_name}
    [Documentation]    Verify {entity} supports {op} operation
    [Tags]    {entity}    {op}    generated
    # TODO: Implement based on exploratory findings
    Skip    Not implemented - waiting for UI fix
"""
        # Save skeleton
        skeleton_path = "c:/Users/natik/Documents/Vibe/sim-ai/sim-ai/tests/e2e/entity_crud.robot"
        with open(skeleton_path, "w") as f:
            f.write(robot_content)
        print(f"Generated: {skeleton_path}")

    def generate_gap_report(self):
        """Generate structured gap report for tracking."""
        print("\n" + "=" * 60)
        print("EXPLORATORY GAP DISCOVERY REPORT")
        print("=" * 60)

        # Add known gaps from manual discovery
        self._add_known_gaps_from_v2()

        print(f"\nTotal Gaps: {len(self.gaps)}")
        critical = [g for g in self.gaps if g['severity'] == 'critical']
        high = [g for g in self.gaps if g['severity'] == 'high']
        medium = [g for g in self.gaps if g['severity'] == 'medium']

        if critical:
            print(f"\n[CRITICAL] ({len(critical)}):")
            for g in critical:
                print(f"  {g['gap_id']}: {g['entity']}.{g['operation']} - {g['expected']}")

        if high:
            print(f"\n[HIGH] ({len(high)}):")
            for g in high:
                print(f"  {g['gap_id']}: {g['entity']}.{g['operation']} - {g['expected']}")

        if medium:
            print(f"\n[MEDIUM] ({len(medium)}):")
            for g in medium:
                print(f"  {g['gap_id']}: {g['entity']}.{g['operation']} - {g['expected']}")

        # Save report
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_gaps": len(self.gaps),
                "critical": len(critical),
                "high": len(high),
                "medium": len(medium)
            },
            "gaps": self.gaps,
            "findings": self.findings
        }

        report_path = "c:/Users/natik/Documents/Vibe/sim-ai/sim-ai/results/exploratory_findings.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved: {report_path}")

        return report

    def _add_known_gaps_from_v2(self):
        """Add gaps discovered from v2.0 exploratory run."""
        known_gaps = [
            ("agents", "navigation", "nav-agents data-testid present", "Navigation item missing", "critical"),
            ("rules", "read_detail", "Click shows detail panel", "No detail visible", "high"),
            ("rules", "update", "Edit button present", "No Edit button found", "high"),
            ("rules", "delete", "Delete button present", "No Delete button found", "high"),
            ("tasks", "create", "Add button present", "No Add button found", "critical"),
            ("tasks", "read_detail", "Click shows detail panel", "No detail visible", "high"),
            ("tasks", "update", "Edit button present", "No Edit button found", "high"),
            ("tasks", "delete", "Delete button present", "No Delete button found", "high"),
            ("sessions", "read_detail", "Click shows detail panel", "No detail visible", "high"),
            ("decisions", "read_detail", "Click shows detail panel", "No detail visible", "high"),
            ("trust", "read_detail", "Click shows agent detail", "No detail visible", "medium"),
            ("impact", "read_detail", "Click shows impact detail", "No detail visible", "medium"),
        ]
        for entity, op, expected, actual, severity in known_gaps:
            # Check if already logged
            exists = any(g['entity'] == entity and g['operation'] == op for g in self.gaps)
            if not exists:
                self.log_gap(entity, op, expected, actual, severity)

    async def run_discovery(self):
        """Run the full gap discovery process."""
        print("=" * 70)
        print("EXPLORATORY UI GAP DISCOVERY")
        print("=" * 70)
        print(f"API Base: {self.api_base}")
        print(f"Started: {datetime.now().isoformat()}")
        print(f"Entities to check: {list(ENTITY_SPEC.keys())}")

        # Phase 1: API checks
        await self.check_api_availability()

        # Phase 2: UI coverage analysis
        await self.analyze_ui_coverage()

        # Phase 3: Generate Robot skeleton
        self.generate_robot_test_skeleton()

        # Generate gap report
        return self.generate_gap_report()


if __name__ == "__main__":
    discovery = ExploratoryGapDiscovery()
    asyncio.run(discovery.run_discovery())
