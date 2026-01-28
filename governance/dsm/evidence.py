"""
DSM Evidence Generation
Created: 2024-12-24
Modularized: 2026-01-02 (RULE-032)

Generates evidence files for completed DSM cycles.
"""
from pathlib import Path

from governance.dsm.models import DSMCycle


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

    filename = f"{cycle.cycle_id}.md"
    filepath = evidence_dir / filename

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
            desc = f['description'][:50] + "..." if len(f['description']) > 50 else f['description']
            lines.append(
                f"| {f['id']} | {f['type']} | {f['severity']} | {desc} |"
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

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return str(filepath)
