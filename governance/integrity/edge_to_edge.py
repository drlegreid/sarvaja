"""
Edge-to-Edge Validation
Created: P10.7
Modularized: 2026-01-02 (RULE-032)

Full edge-to-edge validation function.
"""
from typing import Dict, Any

from governance.integrity.models import ValidationLevel
from governance.integrity.validator import DataIntegrityValidator


def validate_edge_to_edge(
    client=None,
    api_url: str = "http://localhost:8082"
) -> Dict[str, Any]:
    """
    Run full edge-to-edge validation.

    Args:
        client: Optional TypeDBClient instance
        api_url: REST API base URL

    Returns:
        Complete validation report
    """
    import httpx

    validator = DataIntegrityValidator()
    results = {}

    # API Layer Validation
    try:
        with httpx.Client(timeout=10.0) as http:
            # Validate rules
            response = http.get(f"{api_url}/api/rules")
            if response.status_code == 200:
                rules = response.json()
                results["rules"] = validator.validate_entity_set("rule", rules, ValidationLevel.API)

            # Validate tasks
            response = http.get(f"{api_url}/api/tasks")
            if response.status_code == 200:
                tasks = response.json()
                results["tasks"] = validator.validate_entity_set("task", tasks, ValidationLevel.API)

            # Validate agents
            response = http.get(f"{api_url}/api/agents")
            if response.status_code == 200:
                agents = response.json()
                results["agents"] = validator.validate_entity_set("agent", agents, ValidationLevel.API)

            # Validate sessions
            response = http.get(f"{api_url}/api/sessions")
            if response.status_code == 200:
                sessions = response.json()
                results["sessions"] = validator.validate_entity_set("session", sessions, ValidationLevel.API)

            # Validate decisions
            response = http.get(f"{api_url}/api/decisions")
            if response.status_code == 200:
                decisions = response.json()
                results["decisions"] = validator.validate_entity_set("decision", decisions, ValidationLevel.API)

    except Exception as e:
        results["api_error"] = str(e)

    # Generate final report
    results["integrity_report"] = validator.generate_integrity_report()

    return results
