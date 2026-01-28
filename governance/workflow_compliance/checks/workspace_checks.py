"""
Workspace-related Compliance Checks.

Per DOC-SIZE-01-v1: Extracted from workflow_compliance.py.
Per SESSION-EVID-01-v1, RECOVER-AMNES-01-v1: Workspace compliance.

Created: 2026-01-20
"""

import logging
from pathlib import Path
from ..models import ComplianceCheck

logger = logging.getLogger(__name__)


def check_session_evidence_files() -> ComplianceCheck:
    """
    Check SESSION-EVID-01-v1: Sessions should have evidence files.
    """
    try:
        possible_roots = [
            Path(__file__).parent.parent.parent.parent,  # governance/../
            Path("/app"),
        ]

        evidence_dir = None
        for root in possible_roots:
            candidate = root / "evidence"
            if candidate.exists():
                evidence_dir = candidate
                break

        if not evidence_dir:
            return ComplianceCheck(
                rule_id="SESSION-EVID-01-v1",
                check_name="session_evidence_files",
                status="WARNING",
                message="Evidence directory not found",
                count=0
            )

        session_files = list(evidence_dir.glob("SESSION-*.md"))
        count = len(session_files)

        if count >= 10:
            return ComplianceCheck(
                rule_id="SESSION-EVID-01-v1",
                check_name="session_evidence_files",
                status="PASS",
                message=f"{count} session evidence files found",
                count=count
            )
        elif count > 0:
            return ComplianceCheck(
                rule_id="SESSION-EVID-01-v1",
                check_name="session_evidence_files",
                status="WARNING",
                message=f"Only {count} session evidence files found",
                count=count
            )
        else:
            return ComplianceCheck(
                rule_id="SESSION-EVID-01-v1",
                check_name="session_evidence_files",
                status="FAIL",
                message="No session evidence files found",
                count=0
            )

    except Exception as e:
        logger.error(f"session_evidence_files check failed: {e}")
        return ComplianceCheck(
            rule_id="SESSION-EVID-01-v1",
            check_name="session_evidence_files",
            status="SKIP",
            message=f"Check failed: {e}"
        )


def check_workspace_files() -> ComplianceCheck:
    """
    Check RECOVER-AMNES-01-v1: Required workspace files exist.
    """
    try:
        possible_roots = [
            Path(__file__).parent.parent.parent.parent,  # governance/../
            Path("/app"),
        ]

        project_root = None
        for root in possible_roots:
            if (root / "CLAUDE.md").exists() or (root / "TODO.md").exists():
                project_root = root
                break

        if not project_root:
            project_root = possible_roots[0]

        required_files = [
            ("CLAUDE.md", "Context recovery file"),
            ("TODO.md", "Task tracking file"),
            ("docs/DEVOPS.md", "Infrastructure documentation"),
        ]

        missing = []
        for file_path, description in required_files:
            full_path = project_root / file_path
            if not full_path.exists():
                missing.append(f"{file_path} ({description})")

        if not missing:
            return ComplianceCheck(
                rule_id="RECOVER-AMNES-01-v1",
                check_name="workspace_files",
                status="PASS",
                message="All required workspace files present",
                count=len(required_files)
            )
        else:
            return ComplianceCheck(
                rule_id="RECOVER-AMNES-01-v1",
                check_name="workspace_files",
                status="FAIL",
                message=f"Missing workspace files: {len(missing)}",
                count=len(required_files) - len(missing),
                violations=missing
            )

    except Exception as e:
        logger.error(f"workspace_files check failed: {e}")
        return ComplianceCheck(
            rule_id="RECOVER-AMNES-01-v1",
            check_name="workspace_files",
            status="SKIP",
            message=f"Check failed: {e}"
        )
