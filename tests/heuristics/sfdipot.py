"""
SFDIPOT Heuristic Test Decorators and Fixtures.

SFDIPOT = Structure, Function, Data, Interfaces, Platform, Operations, Time

Per GAP-HEUR-001: Systematic exploratory testing heuristics framework.

Usage:
    from tests.heuristics import structure, data

    @structure("TypeDB schema validates correctly")
    def test_schema_entities_exist():
        ...

    @data("Task descriptions are never null")
    def test_task_description_integrity():
        ...

Created: 2026-01-02
"""

import functools
from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Optional


class SFDIPOTAspect(Enum):
    """SFDIPOT heuristic aspects."""
    STRUCTURE = "Structure"     # Component hierarchy, schema, architecture
    FUNCTION = "Function"       # Endpoint behavior, user workflows
    DATA = "Data"               # Field validation, data integrity
    INTERFACES = "Interfaces"   # API contracts, navigation flows
    PLATFORM = "Platform"       # Container health, browser compat
    OPERATIONS = "Operations"   # Error handling, user experience
    TIME = "Time"               # Response latency, render performance


@dataclass
class SFDIPOTTest:
    """Metadata for SFDIPOT-tagged test."""
    aspect: SFDIPOTAspect
    description: str
    api_level: bool = False
    ui_level: bool = False
    entity: Optional[str] = None


# Registry of all SFDIPOT tests for coverage reporting
SFDIPOT_REGISTRY: List[SFDIPOTTest] = []


class SFDIPOT:
    """SFDIPOT heuristic decorator class."""

    def __init__(self, aspect: SFDIPOTAspect, description: str,
                 api: bool = False, ui: bool = False, entity: str = None):
        self.aspect = aspect
        self.description = description
        self.api_level = api
        self.ui_level = ui
        self.entity = entity

    def __call__(self, func: Callable) -> Callable:
        import pytest
        # Register test for coverage reporting
        test_meta = SFDIPOTTest(
            aspect=self.aspect,
            description=self.description,
            api_level=self.api_level,
            ui_level=self.ui_level,
            entity=self.entity,
        )
        SFDIPOT_REGISTRY.append(test_meta)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Add proper pytest marker for filtering
        marker = pytest.mark.heuristic(f"SFDIPOT.{self.aspect.name}")
        wrapper = marker(wrapper)
        wrapper._sfdipot = test_meta
        return wrapper


# Convenience decorators for each aspect
def structure(description: str, api: bool = False, ui: bool = False,
              entity: str = None) -> Callable:
    """Mark test as testing Structure aspect (schema, hierarchy, architecture)."""
    return SFDIPOT(SFDIPOTAspect.STRUCTURE, description, api, ui, entity)


def function(description: str, api: bool = False, ui: bool = False,
             entity: str = None) -> Callable:
    """Mark test as testing Function aspect (behavior, workflows)."""
    return SFDIPOT(SFDIPOTAspect.FUNCTION, description, api, ui, entity)


def data(description: str, api: bool = False, ui: bool = False,
         entity: str = None) -> Callable:
    """Mark test as testing Data aspect (validation, integrity)."""
    return SFDIPOT(SFDIPOTAspect.DATA, description, api, ui, entity)


def interfaces(description: str, api: bool = False, ui: bool = False,
               entity: str = None) -> Callable:
    """Mark test as testing Interfaces aspect (contracts, navigation)."""
    return SFDIPOT(SFDIPOTAspect.INTERFACES, description, api, ui, entity)


def platform(description: str, api: bool = False, ui: bool = False,
             entity: str = None) -> Callable:
    """Mark test as testing Platform aspect (container, browser)."""
    return SFDIPOT(SFDIPOTAspect.PLATFORM, description, api, ui, entity)


def operations(description: str, api: bool = False, ui: bool = False,
               entity: str = None) -> Callable:
    """Mark test as testing Operations aspect (error handling, UX)."""
    return SFDIPOT(SFDIPOTAspect.OPERATIONS, description, api, ui, entity)


def time(description: str, api: bool = False, ui: bool = False,
         entity: str = None) -> Callable:
    """Mark test as testing Time aspect (latency, performance)."""
    return SFDIPOT(SFDIPOTAspect.TIME, description, api, ui, entity)


def get_sfdipot_tests() -> List[SFDIPOTTest]:
    """Get all registered SFDIPOT tests."""
    return SFDIPOT_REGISTRY.copy()


def get_coverage_by_aspect() -> dict:
    """Get test count by SFDIPOT aspect."""
    coverage = {aspect: 0 for aspect in SFDIPOTAspect}
    for test in SFDIPOT_REGISTRY:
        coverage[test.aspect] += 1
    return {k.name: v for k, v in coverage.items()}
