"""
Holographic HTML Report Renderer — self-contained HTML from HolographicTestStore.

Per FEAT-009 / TEST-HOLO-01-v1: Humans need a single HTML file with collapsible
zoom sections. LLM agents continue using zoom queries.

Usage:
    from tests.evidence.holographic_report import render_html_report, save_html_report
    html = render_html_report(store)
    path = save_html_report(store, output_dir="evidence")
"""

import json
from datetime import datetime
from html import escape
from pathlib import Path
from typing import List, Optional

from tests.evidence.holographic_store import HolographicTestStore, EvidenceRecord


def _format_duration(ms: float) -> str:
    """Format milliseconds to human-readable."""
    if ms < 1000:
        return f"{ms:.0f}ms"
    s = ms / 1000
    if s < 60:
        return f"{s:.1f}s"
    m = int(s // 60)
    return f"{m}m{s % 60:.0f}s"


def _status_class(status: str) -> str:
    """CSS class for test status."""
    return {"passed": "pass", "failed": "fail", "skipped": "skip"}.get(
        status.lower(), "unknown"
    )


def _badge_color(failed: int) -> str:
    return "#dc3545" if failed > 0 else "#28a745"


_CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
       margin: 0; padding: 20px; background: #f8f9fa; color: #212529; }
.container { max-width: 1100px; margin: 0 auto; }
h1 { margin: 0 0 8px; font-size: 1.5rem; }
.meta { color: #6c757d; font-size: 0.85rem; margin-bottom: 16px; }
.badge { display: inline-block; padding: 6px 18px; border-radius: 4px;
         color: #fff; font-weight: 700; font-size: 1.1rem; letter-spacing: 0.5px; }
.stats { display: flex; gap: 24px; margin: 16px 0; flex-wrap: wrap; }
.stat-card { background: #fff; border: 1px solid #dee2e6; border-radius: 6px;
             padding: 12px 20px; min-width: 120px; }
.stat-card .label { font-size: 0.75rem; color: #6c757d; text-transform: uppercase; }
.stat-card .value { font-size: 1.4rem; font-weight: 700; }
.section { background: #fff; border: 1px solid #dee2e6; border-radius: 6px;
           margin: 12px 0; overflow: hidden; }
.section-header { padding: 10px 16px; background: #e9ecef; cursor: pointer;
                  font-weight: 600; font-size: 0.9rem; user-select: none; }
.section-header:hover { background: #dee2e6; }
.section-body { padding: 12px 16px; display: none; }
.section-body.open { display: block; }
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
th { text-align: left; padding: 6px 10px; border-bottom: 2px solid #dee2e6;
     font-size: 0.75rem; text-transform: uppercase; color: #6c757d; }
td { padding: 6px 10px; border-bottom: 1px solid #f0f0f0; }
tr:hover { background: #f8f9fa; }
.pass { color: #28a745; } .fail { color: #dc3545; } .skip { color: #ffc107; }
.status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%;
              margin-right: 6px; vertical-align: middle; }
.status-dot.pass { background: #28a745; } .status-dot.fail { background: #dc3545; }
.status-dot.skip { background: #ffc107; }
.error-msg { font-family: monospace; font-size: 0.8rem; color: #dc3545;
             background: #fff5f5; padding: 4px 8px; border-radius: 3px;
             margin-top: 4px; white-space: pre-wrap; word-break: break-word; }
.detail-block { background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px;
                padding: 8px 12px; margin: 6px 0; font-family: monospace;
                font-size: 0.8rem; white-space: pre-wrap; word-break: break-word; }
.category-bar { display: flex; height: 8px; border-radius: 4px; overflow: hidden;
                margin: 8px 0; }
.category-bar span { display: block; }
.empty { text-align: center; color: #6c757d; padding: 40px; }
"""

_JS = """
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.section-header').forEach(function(h) {
    h.addEventListener('click', function() {
      var body = h.nextElementSibling;
      body.classList.toggle('open');
      var arrow = h.querySelector('.arrow');
      if (arrow) arrow.textContent = body.classList.contains('open') ? '▾' : '▸';
    });
  });
  // Auto-open zoom-1
  var z1 = document.getElementById('zoom-1-body');
  if (z1) { z1.classList.add('open'); }
  var z1a = document.querySelector('#zoom-1 .arrow');
  if (z1a) z1a.textContent = '▾';
});
"""


def render_html_report(store: HolographicTestStore) -> str:
    """Render HolographicTestStore to self-contained HTML string."""
    events: List[EvidenceRecord] = list(store._events)
    now = datetime.now()

    total = len(events)
    passed = sum(1 for e in events if e.status == "passed")
    failed = sum(1 for e in events if e.status == "failed")
    skipped = sum(1 for e in events if e.status == "skipped")
    duration_ms = sum(e.duration_ms for e in events)
    rate = f"{(passed / total * 100):.0f}%" if total > 0 else "0%"

    # Category breakdown
    cats: dict = {}
    for e in events:
        c = e.category or "unknown"
        if c not in cats:
            cats[c] = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
        cats[c]["total"] += 1
        cats[c][e.status] = cats[c].get(e.status, 0) + 1

    parts = []
    parts.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Holographic Test Report — {now.strftime('%Y-%m-%d %H:%M')}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="container">
<h1>Holographic Test Report</h1>
<div class="meta">{escape(store.session_id or 'N/A')} | {now.strftime('%Y-%m-%d %H:%M:%S')} | {_format_duration(duration_ms)}</div>
""")

    if total == 0:
        parts.append('<div class="empty">No test evidence recorded.</div>')
        parts.append("</div></body></html>")
        return "\n".join(parts)

    # --- Zoom 0: Badge ---
    badge_label = "FAIL" if failed > 0 else "PASS"
    parts.append(f"""
<div id="zoom-0">
<span class="badge" style="background:{_badge_color(failed)}">{badge_label}</span>
<span style="margin-left:12px;font-size:1.1rem;font-weight:600">{passed}/{total} passed ({rate})</span>
</div>
""")

    # --- Stat cards ---
    parts.append('<div class="stats">')
    for label, val, color in [
        ("Total", total, "#212529"), ("Passed", passed, "#28a745"),
        ("Failed", failed, "#dc3545"), ("Skipped", skipped, "#ffc107"),
        ("Duration", _format_duration(duration_ms), "#6c757d"),
    ]:
        parts.append(f'<div class="stat-card"><div class="label">{label}</div>'
                     f'<div class="value" style="color:{color}">{val}</div></div>')
    parts.append("</div>")

    # --- Category bar ---
    if total > 0:
        parts.append('<div class="category-bar">')
        cat_colors = {"unit": "#28a745", "integration": "#17a2b8",
                      "e2e": "#6f42c1", "unknown": "#adb5bd"}
        for cat, stats in cats.items():
            pct = stats["total"] / total * 100
            col = cat_colors.get(cat, "#adb5bd")
            parts.append(f'<span style="width:{pct:.1f}%;background:{col}" '
                         f'title="{escape(cat)}: {stats["total"]}"></span>')
        parts.append("</div>")

    # --- Zoom 1: Summary section ---
    parts.append(_section("zoom-1", "Zoom 1 — Summary", _render_zoom1(cats)))

    # --- Zoom 2: Per-test rows ---
    parts.append(_section("zoom-2", f"Zoom 2 — Per-Test ({total} tests)",
                          _render_zoom2(events)))

    # --- Zoom 3: Full detail (failures only by default) ---
    failures = [e for e in events if e.status == "failed"]
    if failures:
        parts.append(_section("zoom-3",
                              f"Zoom 3 — Failure Detail ({len(failures)})",
                              _render_zoom3(failures)))

    parts.append(f"""
<div class="meta" style="margin-top:24px">
Generated by Holographic Report Renderer | TEST-HOLO-01-v1 | FEAT-009
</div>
</div>
<script>{_JS}</script>
</body>
</html>""")

    return "\n".join(parts)


def _section(section_id: str, title: str, body_html: str) -> str:
    """Collapsible section wrapper."""
    return (f'<div class="section" id="{section_id}">'
            f'<div class="section-header"><span class="arrow">▸</span> {escape(title)}</div>'
            f'<div class="section-body" id="{section_id}-body">{body_html}</div>'
            f'</div>')


def _render_zoom1(cats: dict) -> str:
    """Zoom 1: Category breakdown table."""
    rows = []
    for cat, s in sorted(cats.items()):
        rate = f"{(s['passed'] / s['total'] * 100):.0f}%" if s["total"] > 0 else "0%"
        rows.append(f"<tr><td>{escape(cat)}</td><td>{s['total']}</td>"
                    f"<td class='pass'>{s['passed']}</td>"
                    f"<td class='fail'>{s['failed']}</td>"
                    f"<td class='skip'>{s['skipped']}</td>"
                    f"<td>{rate}</td></tr>")
    return (f"<table><tr><th>Category</th><th>Total</th><th>Passed</th>"
            f"<th>Failed</th><th>Skipped</th><th>Rate</th></tr>"
            f"{''.join(rows)}</table>")


def _render_zoom2(events: List[EvidenceRecord]) -> str:
    """Zoom 2: Per-test table with status dots."""
    rows = []
    for e in events:
        cls = _status_class(e.status)
        err = ""
        if e.error_message:
            err = f'<div class="error-msg">{escape(e.error_message[:200])}</div>'
        rows.append(
            f"<tr><td><span class='status-dot {cls}'></span>"
            f"<span class='{cls}'>{escape(e.status.upper())}</span></td>"
            f"<td>{escape(e.name)}</td>"
            f"<td>{escape(e.category)}</td>"
            f"<td>{_format_duration(e.duration_ms)}</td>"
            f"<td>{escape(e.test_id)}{err}</td></tr>"
        )
    return (f"<table><tr><th>Status</th><th>Name</th><th>Category</th>"
            f"<th>Duration</th><th>Test ID</th></tr>"
            f"{''.join(rows)}</table>")


def _render_zoom3(failures: List[EvidenceRecord]) -> str:
    """Zoom 3: Full detail for failures — fixtures, request/response."""
    parts = []
    for e in failures:
        parts.append(f'<div style="margin-bottom:16px">')
        parts.append(f'<strong class="fail">{escape(e.name)}</strong> '
                     f'<span class="meta">{escape(e.test_id)}</span>')
        if e.error_message:
            parts.append(f'<div class="error-msg">{escape(e.error_message)}</div>')
        full = e.to_full_dict()
        # Show fixtures, request, response if present
        for key in ("fixtures", "request_data", "response_data"):
            val = full.get(key)
            if val:
                parts.append(f'<div class="detail-block"><strong>{key}:</strong>\n'
                             f'{escape(json.dumps(val, indent=2, default=str))}</div>')
        if e.linked_rules:
            parts.append(f'<div class="meta">Rules: {", ".join(e.linked_rules)}</div>')
        parts.append("</div>")
    return "\n".join(parts)


def save_html_report(
    store: HolographicTestStore,
    output_dir: str = "evidence",
    prefix: str = "holographic-report",
) -> Path:
    """Render and save HTML report to output_dir. Returns the file path."""
    html = render_html_report(store)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    base = f"{prefix}-{date_str}.html"
    path = out / base

    # Don't overwrite — append numeric suffix
    if path.exists():
        i = 1
        while True:
            path = out / f"{prefix}-{date_str}-{i}.html"
            if not path.exists():
                break
            i += 1

    path.write_text(html, encoding="utf-8")
    return path
