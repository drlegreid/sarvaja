"""
CRUCSS Heuristic Test Decorators and Fixtures.

CRUCSS = Capability, Reliability, Usability, Charisma, Security, Scalability

Per GAP-HEUR-001: Systematic exploratory testing heuristics framework.

Usage:
    from tests.heuristics import security, reliability

    @security("API rejects unauthenticated requests")
    def test_api_auth_required():
        ...

    @reliability("Service recovers from TypeDB downtime")
    def test_typedb_failover():
        ...

Created: 2026-01-02
"""

import functools
from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Optional


class CRUCSSAspect(Enum):
    """CRUCSS heuristic aspects."""
    CAPABILITY = "Capability"     # Can it do what users need?
    RELIABILITY = "Reliability"   # Will it work under stress/failure?
    USABILITY = "Usability"       # Is it easy to use correctly?
    CHARISMA = "Charisma"         # Does it attract and engage users?
    SECURITY = "Security"         # Is it protected from threats?
    SCALABILITY = "Scalability"   # Does it handle growth?


@dataclass
class CRUCSSTest:
    """Metadata for CRUCSS-tagged test."""
    aspect: CRUCSSAspect
    description: str
    integration_level: bool = False
    e2e_level: bool = False
    entity: Optional[str] = None


# Registry of all CRUCSS tests for coverage reporting
CRUCSS_REGISTRY: List[CRUCSSTest] = []


class CRUCSS:
    """CRUCSS heuristic decorator class."""

    def __init__(self, aspect: CRUCSSAspect, description: str,
                 integration: bool = False, e2e: bool = False, entity: str = None):
        self.aspect = aspect
        self.description = description
        self.integration_level = integration
        self.e2e_level = e2e
        self.entity = entity

    def __call__(self, func: Callable) -> Callable:
        import pytest
        # Register test for coverage reporting
        test_meta = CRUCSSTest(
            aspect=self.aspect,
            description=self.description,
            integration_level=self.integration_level,
            e2e_level=self.e2e_level,
            entity=self.entity,
        )
        CRUCSS_REGISTRY.append(test_meta)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Add proper pytest marker for filtering
        marker = pytest.mark.heuristic(f"CRUCSS.{self.aspect.name}")
        wrapper = marker(wrapper)
        wrapper._crucss = test_meta
        return wrapper


# Convenience decorators for each aspect
def capability(description: str, integration: bool = False, e2e: bool = False,
               entity: str = None) -> Callable:
    """Mark test as testing Capability aspect (features, functions)."""
    return CRUCSS(CRUCSSAspect.CAPABILITY, description, integration, e2e, entity)


def reliability(description: str, integration: bool = False, e2e: bool = False,
                entity: str = None) -> Callable:
    """Mark test as testing Reliability aspect (stability, recovery)."""
    return CRUCSS(CRUCSSAspect.RELIABILITY, description, integration, e2e, entity)


def usability(description: str, integration: bool = False, e2e: bool = False,
              entity: str = None) -> Callable:
    """Mark test as testing Usability aspect (ease of use)."""
    return CRUCSS(CRUCSSAspect.USABILITY, description, integration, e2e, entity)


def charisma(description: str, integration: bool = False, e2e: bool = False,
             entity: str = None) -> Callable:
    """Mark test as testing Charisma aspect (user engagement)."""
    return CRUCSS(CRUCSSAspect.CHARISMA, description, integration, e2e, entity)


def security(description: str, integration: bool = False, e2e: bool = False,
             entity: str = None) -> Callable:
    """Mark test as testing Security aspect (auth, protection)."""
    return CRUCSS(CRUCSSAspect.SECURITY, description, integration, e2e, entity)


def scalability(description: str, integration: bool = False, e2e: bool = False,
                entity: str = None) -> Callable:
    """Mark test as testing Scalability aspect (growth, load)."""
    return CRUCSS(CRUCSSAspect.SCALABILITY, description, integration, e2e, entity)


def get_crucss_tests() -> List[CRUCSSTest]:
    """Get all registered CRUCSS tests."""
    return CRUCSS_REGISTRY.copy()


def get_coverage_by_aspect() -> dict:
    """Get test count by CRUCSS aspect."""
    coverage = {aspect: 0 for aspect in CRUCSSAspect}
    for test in CRUCSS_REGISTRY:
        coverage[test.aspect] += 1
    return {k.name: v for k, v in coverage.items()}
