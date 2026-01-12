#!/usr/bin/env python3
"""
Exploratory API Test - LLM Heuristics Approach
===============================================
Non-deterministic exploration using domain heuristics.

Per RULE-004: Exploratory Test Automation with domain-specific heuristics
Per RULE-020: LLM-Driven E2E Test Generation (exploration phase)

API Domain Heuristics (from RULE-004):
- CONTRACT: Does response match expected schema?
- IDEMPOTENCY: Does repeating calls produce same result?
- PAYLOAD: How does API handle edge case inputs?
- BOUNDARY: What happens at limits (0, max, negative)?

Exploration Approach:
1. Random endpoint selection
2. Random parameter combinations
3. Boundary value probing
4. Undocumented behavior discovery
5. Error condition exploration

Output: Findings → Robot Framework test candidates

Created: 2026-01-12
"""

import json
import random
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import hashlib
import time

API_BASE = "http://localhost:8082"

# Heuristic categories per RULE-004
HEURISTICS = {
    "CONTRACT": "Response schema matches expectation",
    "IDEMPOTENCY": "Repeated calls produce same result",
    "PAYLOAD": "Edge case inputs handled gracefully",
    "BOUNDARY": "Limit values handled correctly",
}

# Endpoints to explore (discovered dynamically or seeded)
KNOWN_ENDPOINTS = [
    "/api/tasks",
    "/api/sessions",
    "/api/rules",
    "/api/agents",
]

# Boundary values to probe
BOUNDARY_VALUES = {
    "limit": [0, 1, -1, 100, 200, 201, 1000, "abc", None],
    "offset": [0, 1, -1, 100, 1000, "xyz", None],
    "status": ["TODO", "DONE", "IN_PROGRESS", "", "INVALID_STATUS", None],
    "phase": ["P10", "P11", "P12", "RD", "", "FAKE_PHASE", None],
}


class ExploratoryAPITest:
    """
    LLM-driven exploratory API test using domain heuristics.

    This is NOT a consistency checker - it's an explorer that:
    - Randomly probes endpoints
    - Discovers unexpected behaviors
    - Finds what's NOT covered by existing tests
    - Generates candidates for deterministic tests
    """

    def __init__(self, api_base: str = API_BASE, seed: int = None):
        self.api_base = api_base
        self.seed = seed or int(time.time())
        random.seed(self.seed)
        self.findings: List[Dict] = []
        self.test_candidates: List[Dict] = []
        self.results_path = Path(__file__).parent.parent.parent / "results"
        self.session_id = f"EXP-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    def api_request(self, endpoint: str, timeout: int = 5) -> Tuple[Any, int, float]:
        """Make API request, return (data, status, response_time_ms)."""
        start = time.time()
        try:
            url = f"{self.api_base}{endpoint}"
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                elapsed = (time.time() - start) * 1000
                return data, resp.status, elapsed
        except urllib.error.HTTPError as e:
            elapsed = (time.time() - start) * 1000
            return None, e.code, elapsed
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return None, 0, elapsed

    def log_finding(self, heuristic: str, endpoint: str, observation: str,
                    severity: str = "info", data: Dict = None):
        """Log an exploratory finding."""
        finding = {
            "id": f"FIND-{len(self.findings) + 1:03d}",
            "timestamp": datetime.now().isoformat(),
            "session": self.session_id,
            "heuristic": heuristic,
            "endpoint": endpoint,
            "observation": observation,
            "severity": severity,
            "data": data or {}
        }
        self.findings.append(finding)
        icon = {"info": "ℹ️", "warning": "⚠️", "gap": "🔍", "error": "❌"}.get(severity, "•")
        print(f"  {icon} [{heuristic}] {observation}")

    def add_test_candidate(self, name: str, endpoint: str, assertion: str, finding_id: str):
        """Add a candidate for Robot Framework test generation."""
        self.test_candidates.append({
            "name": name,
            "endpoint": endpoint,
            "assertion": assertion,
            "source_finding": finding_id,
            "generated": datetime.now().isoformat()
        })

    # =========================================================================
    # HEURISTIC: CONTRACT - Response Schema Validation
    # =========================================================================
    def explore_contract(self):
        """Explore API contracts - do responses have expected structure?"""
        print("\n" + "=" * 60)
        print("🔍 HEURISTIC: CONTRACT")
        print("=" * 60)

        for endpoint in KNOWN_ENDPOINTS:
            data, status, elapsed = self.api_request(f"{endpoint}?limit=5")

            if status != 200:
                self.log_finding("CONTRACT", endpoint,
                    f"Endpoint returned {status} instead of 200", "warning")
                continue

            if not isinstance(data, list):
                self.log_finding("CONTRACT", endpoint,
                    f"Expected list, got {type(data).__name__}", "gap")
                self.add_test_candidate(
                    f"Verify {endpoint} returns list",
                    endpoint,
                    "Response should be a list",
                    self.findings[-1]["id"]
                )
                continue

            if data:
                # Explore field presence randomness
                sample = random.choice(data)
                fields = list(sample.keys())
                self.log_finding("CONTRACT", endpoint,
                    f"Sample has {len(fields)} fields: {fields[:5]}...", "info")

                # Check for null fields (potential gaps)
                null_fields = [k for k, v in sample.items() if v is None]
                if null_fields:
                    self.log_finding("CONTRACT", endpoint,
                        f"Nullable fields found: {null_fields}", "info",
                        {"null_fields": null_fields})

    # =========================================================================
    # HEURISTIC: BOUNDARY - Limit Value Exploration
    # =========================================================================
    def explore_boundary(self):
        """Explore boundary conditions with random probes."""
        print("\n" + "=" * 60)
        print("🔍 HEURISTIC: BOUNDARY")
        print("=" * 60)

        endpoint = random.choice(KNOWN_ENDPOINTS)

        # Probe limit parameter
        for limit_val in random.sample(BOUNDARY_VALUES["limit"], 4):
            param = f"limit={limit_val}" if limit_val is not None else ""
            url = f"{endpoint}?{param}" if param else endpoint

            data, status, elapsed = self.api_request(url)

            if limit_val is not None and (isinstance(limit_val, int) and limit_val < 0):
                if status == 200:
                    self.log_finding("BOUNDARY", url,
                        f"Negative limit ({limit_val}) accepted - unexpected", "gap")
                    self.add_test_candidate(
                        f"Verify {endpoint} rejects negative limit",
                        url,
                        "Should return 422 for negative limit",
                        self.findings[-1]["id"]
                    )
                else:
                    self.log_finding("BOUNDARY", url,
                        f"Negative limit correctly rejected ({status})", "info")
            elif limit_val == 0:
                if status == 200 and isinstance(data, list) and len(data) == 0:
                    self.log_finding("BOUNDARY", url,
                        "limit=0 returns empty list (expected)", "info")
                elif status == 200 and isinstance(data, list):
                    self.log_finding("BOUNDARY", url,
                        f"limit=0 returned {len(data)} items - unexpected", "gap")
            elif isinstance(limit_val, str):
                if status == 422:
                    self.log_finding("BOUNDARY", url,
                        f"String limit correctly rejected ({status})", "info")
                else:
                    self.log_finding("BOUNDARY", url,
                        f"String limit '{limit_val}' got {status} - check validation", "warning")

    # =========================================================================
    # HEURISTIC: IDEMPOTENCY - Repeated Call Consistency
    # =========================================================================
    def explore_idempotency(self):
        """Explore idempotency - do repeated calls return consistent results?"""
        print("\n" + "=" * 60)
        print("🔍 HEURISTIC: IDEMPOTENCY")
        print("=" * 60)

        endpoint = random.choice(KNOWN_ENDPOINTS)
        url = f"{endpoint}?limit=10"

        # Make same request multiple times
        results = []
        for i in range(3):
            data, status, elapsed = self.api_request(url)
            if status == 200 and isinstance(data, list):
                # Hash the response for comparison
                response_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()[:8]
                results.append((response_hash, len(data), elapsed))
            time.sleep(0.1)  # Small delay between calls

        if len(results) >= 2:
            hashes = [r[0] for r in results]
            if len(set(hashes)) == 1:
                self.log_finding("IDEMPOTENCY", url,
                    f"Consistent results across {len(results)} calls (hash: {hashes[0]})", "info")
            else:
                self.log_finding("IDEMPOTENCY", url,
                    f"Inconsistent results: {hashes}", "gap",
                    {"hashes": hashes})
                self.add_test_candidate(
                    f"Verify {endpoint} idempotency",
                    url,
                    "Repeated calls should return same data",
                    self.findings[-1]["id"]
                )

            # Check response time variance
            times = [r[2] for r in results]
            avg_time = sum(times) / len(times)
            variance = max(times) - min(times)
            if variance > avg_time * 0.5:
                self.log_finding("IDEMPOTENCY", url,
                    f"High response time variance: {variance:.0f}ms (avg: {avg_time:.0f}ms)", "warning")

    # =========================================================================
    # HEURISTIC: PAYLOAD - Unexpected Input Handling
    # =========================================================================
    def explore_payload(self):
        """Explore how API handles unexpected payloads."""
        print("\n" + "=" * 60)
        print("🔍 HEURISTIC: PAYLOAD")
        print("=" * 60)

        # Test filter parameters with unexpected values
        endpoint = "/api/tasks"

        # Random unexpected filter combinations
        probes = [
            ("status=<script>alert(1)</script>", "XSS in status"),
            ("phase=../../etc/passwd", "Path traversal in phase"),
            ("agent_id=1 OR 1=1", "SQL injection attempt"),
            ("status=TODO&status=DONE", "Duplicate parameter"),
            ("limit=10&limit=20", "Conflicting limits"),
        ]

        for probe_params, description in random.sample(probes, 3):
            url = f"{endpoint}?{probe_params}"
            data, status, elapsed = self.api_request(url)

            if status == 200:
                count = len(data) if isinstance(data, list) else 0
                self.log_finding("PAYLOAD", url,
                    f"{description}: accepted, returned {count} items", "info")
            elif status == 422:
                self.log_finding("PAYLOAD", url,
                    f"{description}: correctly rejected (422)", "info")
            else:
                self.log_finding("PAYLOAD", url,
                    f"{description}: unexpected status {status}", "warning")

    # =========================================================================
    # EXPLORATION ORCHESTRATION
    # =========================================================================
    def run_exploration(self, max_iterations: int = 3) -> Dict:
        """Run exploratory session with random heuristic application."""
        print("=" * 70)
        print(f"🔬 EXPLORATORY API TEST SESSION: {self.session_id}")
        print("=" * 70)
        print(f"API Base: {self.api_base}")
        print(f"Random Seed: {self.seed}")
        print(f"Started: {datetime.now().isoformat()}")
        print(f"Max Iterations: {max_iterations}")

        # Randomly ordered heuristic exploration
        heuristic_methods = [
            self.explore_contract,
            self.explore_boundary,
            self.explore_idempotency,
            self.explore_payload,
        ]

        for iteration in range(max_iterations):
            print(f"\n{'─' * 60}")
            print(f"ITERATION {iteration + 1}/{max_iterations}")
            print(f"{'─' * 60}")

            # Randomly select and run heuristics
            selected = random.sample(heuristic_methods, k=min(2, len(heuristic_methods)))
            for method in selected:
                try:
                    method()
                except Exception as e:
                    self.log_finding("ERROR", "exploration",
                        f"Heuristic {method.__name__} failed: {e}", "error")

        return self.generate_report()

    def generate_report(self) -> Dict:
        """Generate exploration report with test candidates."""
        print("\n" + "=" * 70)
        print("📊 EXPLORATION REPORT")
        print("=" * 70)

        severity_counts = {
            "info": len([f for f in self.findings if f["severity"] == "info"]),
            "warning": len([f for f in self.findings if f["severity"] == "warning"]),
            "gap": len([f for f in self.findings if f["severity"] == "gap"]),
            "error": len([f for f in self.findings if f["severity"] == "error"]),
        }

        report = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "seed": self.seed,
            "type": "exploratory_api",
            "summary": {
                "total_findings": len(self.findings),
                "gaps_discovered": severity_counts["gap"],
                "warnings": severity_counts["warning"],
                "test_candidates": len(self.test_candidates),
            },
            "findings": self.findings,
            "test_candidates": self.test_candidates,
            "heuristics_used": list(HEURISTICS.keys()),
        }

        print(f"\nTotal Findings: {report['summary']['total_findings']}")
        print(f"  Gaps Discovered: {severity_counts['gap']}")
        print(f"  Warnings: {severity_counts['warning']}")
        print(f"  Test Candidates Generated: {len(self.test_candidates)}")

        if self.test_candidates:
            print("\n📝 Test Candidates for Robot Framework:")
            for tc in self.test_candidates:
                print(f"  • {tc['name']}")
                print(f"    Endpoint: {tc['endpoint']}")
                print(f"    Assertion: {tc['assertion']}")

        # Save report
        self.results_path.mkdir(exist_ok=True)
        report_file = self.results_path / "exploratory_findings.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved: {report_file}")

        return report


if __name__ == "__main__":
    test = ExploratoryAPITest()
    test.run_exploration(max_iterations=2)
