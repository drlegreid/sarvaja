"""
DSM Evidence Generation
Created: 2024-12-24
Modularized: 2026-01-02 (RULE-032)

Generates evidence files for completed DSM cycles.
"""
import re
from pathlib import Path

from governance.dsm.models import DSMCycle

# BUG-280-EVID-001: Allowed characters for cycle_id in filesystem paths
_SAFE_ID = re.compile(r'^[\w\-]+$')


def generate_evidence(
    cycle: DSMCycle,
    evidence_dir: Path
) -> str:
    """
    Generate markdown evidence file for a DSM cycle.

    Args:
        cycle: The completed DSM cycle
        evidence_dir: Directory to write evidence file

    Returns:
        Path to generated evidence file
    """
    evidence_dir.mkdir(parents=True, exist_ok=True)

    # BUG-280-EVID-001: Validate cycle_id to prevent path traversal
    safe_id = cycle.cycle_id
    if not _SAFE_ID.match(safe_id):
        raise ValueError(f"Unsafe cycle_id for filesystem use: {safe_id!r}")

    filename = f"{safe_id}.md"
    filepath = evidence_dir / filename
    # Confirm resolved path stays inside evidence_dir
    if not filepath.resolve().is_relative_to(evidence_dir.resolve()):
        raise ValueError(f"Path traversal detected for cycle_id {safe_id!r}")

    lines = [
        f"# DSM Cycle Evidence: {cycle.cycle_id}",
        "",
        "## Summary",
        "",
        f"- **Batch:** {cycle.batch_id or 'N/A'}",
        f"- **Started:** {cycle.start_time}",
        f"- **Ended:** {cycle.end_time}",
        f"- **Phases Completed:** {len(cycle.phases_completed)}",
        f"- **Findings:** {len(cycle.findings)}",
        f"- **Checkpoints:** {len(cycle.checkpoints)}",
        "",
        "---",
        "",
    ]

    # Metrics section
    if cycle.metrics:
        lines.extend([
            "## Metrics",
            "",
            "| Metric | Value |",
            "|--------|-------|",
        ])
        for key, value in cycle.metrics.items():
            lines.append(f"| {key} | {value} |")
        lines.extend(["", "---", ""])

    # Findings section
    if cycle.findings:
        lines.extend([
            "## Findings",
            "",
            "| ID | Type | Severity | Description |",
            "|----|------|----------|-------------|",
        ])
        for f in cycle.findings:
            # BUG-DSM-001: Use .get() to avoid KeyError on malformed findings
            raw_desc = f.get('description', 'N/A')
            desc = raw_desc[:50] + "..." if len(raw_desc) > 50 else raw_desc
            lines.append(
                f"| {f.get('id', 'N/A')} | {f.get('type', 'N/A')} | {f.get('severity', 'N/A')} | {desc} |"
            )
        lines.extend(["", "---", ""])

    # Checkpoints section
    if cycle.checkpoints:
        lines.extend([
            "## Checkpoints",
            "",
        ])
        for cp in cycle.checkpoints:
            lines.extend([
                f"### {cp.phase.upper()} - {cp.timestamp}",
                "",
                cp.description,
                "",
            ])
            if cp.evidence:
                lines.append("**Evidence:**")
                for e in cp.evidence:
                    lines.append(f"- {e}")
                lines.append("")

    lines.extend([
        "---",
        "",
        "*Generated per RULE-012: Deep Sleep Protocol*",
    ])

    # BUG-DSM-002: Guard against write failures
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except (IOError, OSError) as e:
        import logging as _log
        _log.getLogger(__name__).error(f"Failed to write evidence {filepath}: {e}")
        raise

    return str(filepath)
