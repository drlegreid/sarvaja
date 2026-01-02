"""
Exploratory Testing Heuristics Framework.

Per GAP-HEUR-001: Implements SFDIPOT, CRUCSS, and HICCUPPS heuristics
for systematic gap discovery at API and UI levels.

Heuristics:
- SFDIPOT: Structure, Function, Data, Interfaces, Platform, Operations, Time
- CRUCSS: Capability, Reliability, Usability, Charisma, Security, Scalability
- HICCUPPS: History, Image, Claims, Competitors, Procedures, Products, Standards

Usage:
    @pytest.mark.heuristic("SFDIPOT.Data")
    def test_task_description_not_null():
        ...

Created: 2026-01-02
Per RULE-023: Test Before Ship
"""

from .sfdipot import (
    SFDIPOT,
    structure,
    function,
    data,
    interfaces,
    platform,
    operations,
    time,
)

from .crucss import (
    CRUCSS,
    capability,
    reliability,
    usability,
    charisma,
    security,
    scalability,
)

from .coverage_report import HeuristicCoverageReport

__all__ = [
    # SFDIPOT
    "SFDIPOT",
    "structure",
    "function",
    "data",
    "interfaces",
    "platform",
    "operations",
    "time",
    # CRUCSS
    "CRUCSS",
    "capability",
    "reliability",
    "usability",
    "charisma",
    "security",
    "scalability",
    # Coverage
    "HeuristicCoverageReport",
]
