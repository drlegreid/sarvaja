#!/usr/bin/env python3
"""
Session Data Dump Workflow

R&D Item #3: Preserve session learnings for future use.

Exports:
- Session decisions (evidence/SESSION-DECISIONS-*.md)
- Gaps discovered (TODO.md)
- ChromaDB knowledge snapshot
- Git commit with dump
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
EVIDENCE_DIR = PROJECT_ROOT / "evidence"
DUMPS_DIR = PROJECT_ROOT / "data" / "session_dumps"

CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8001"))
CHROMADB_TOKEN = os.getenv("CHROMA_AUTH_TOKEN", "chroma-token-dev")


def ensure_dirs():
    """Ensure dump directories exist"""
    DUMPS_DIR.mkdir(parents=True, exist_ok=True)


def export_session_decisions() -> dict:
    """Export session decisions from evidence/*.md"""
    decisions = []
    
    for md_file in EVIDENCE_DIR.glob("SESSION-DECISIONS-*.md"):
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Extract date from filename
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", md_file.name)
        date = date_match.group(1) if date_match else "unknown"
        
        decisions.append({
            "file": md_file.name,
            "date": date,
            "content_length": len(content),
            "has_decision_001": "DECISION-001" in content
        })
    
    return {"count": len(decisions), "files": decisions}


def export_gaps() -> dict:
    """Export gaps from TODO.md"""
    todo_file = PROJECT_ROOT / "TODO.md"
    
    if not todo_file.exists():
        return {"error": "TODO.md not found"}
    
    with open(todo_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Parse gap index
    gaps = []
    gap_pattern = re.compile(r"\| (GAP-\d+) \| ([^|]+) \| ([^|]+) \|")
    
    for match in gap_pattern.finditer(content):
        gaps.append({
            "id": match.group(1).strip(),
            "description": match.group(2).strip(),
            "status": match.group(3).strip()
        })
    
    # Count by status
    fixed = sum(1 for g in gaps if "FIXED" in g["status"])
    pending = len(gaps) - fixed
    
    return {
        "total": len(gaps),
        "fixed": fixed,
        "pending": pending,
        "gaps": gaps
    }


def export_chromadb_stats() -> dict:
    """Export ChromaDB collection stats"""
    try:
        import chromadb
        
        headers = {"X-Chroma-Token": CHROMADB_TOKEN}
        client = chromadb.HttpClient(
            host=CHROMADB_HOST,
            port=CHROMADB_PORT,
            headers=headers
        )
        
        collections = client.list_collections()
        stats = []
        
        for col in collections:
            stats.append({
                "name": col.name,
                "count": col.count()
            })
        
        return {"collections": stats, "total_docs": sum(s["count"] for s in stats)}
        
    except Exception as e:
        return {"error": str(e)}


def export_rd_status() -> dict:
    """Export R&D backlog status"""
    todo_file = PROJECT_ROOT / "TODO.md"
    
    if not todo_file.exists():
        return {"error": "TODO.md not found"}
    
    with open(todo_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Parse R&D items
    items = []
    rd_pattern = re.compile(r"\| (\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|")
    
    in_rd_section = False
    for line in content.split("\n"):
        if "PRIORITY ORDER" in line:
            in_rd_section = True
            continue
        if in_rd_section and line.startswith("---"):
            break
        if in_rd_section:
            match = rd_pattern.match(line)
            if match:
                items.append({
                    "priority": int(match.group(1).strip()),
                    "item": match.group(2).strip(),
                    "status": match.group(3).strip(),
                    "value": match.group(4).strip()
                })
    
    done = sum(1 for i in items if "DONE" in i["status"])
    
    return {"total": len(items), "done": done, "items": items}


def create_dump(dry_run: bool = False) -> dict:
    """Create full session dump"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    dump = {
        "timestamp": timestamp,
        "created_at": datetime.now().isoformat(),
        "session_decisions": export_session_decisions(),
        "gaps": export_gaps(),
        "chromadb": export_chromadb_stats(),
        "rd_status": export_rd_status()
    }
    
    if not dry_run:
        ensure_dirs()
        dump_file = DUMPS_DIR / f"session_dump_{timestamp}.json"
        
        with open(dump_file, "w", encoding="utf-8") as f:
            json.dump(dump, f, indent=2)
        
        dump["saved_to"] = str(dump_file)
    
    return dump


if __name__ == "__main__":
    import sys
    
    print("=" * 50)
    print("Session Data Dump Tool")
    print("=" * 50)
    
    dry_run = "--execute" not in sys.argv
    
    print(f"\n[Mode: {'DRY RUN' if dry_run else 'EXECUTE'}]")
    
    dump = create_dump(dry_run=dry_run)
    
    print(f"\n[Session Decisions]")
    print(f"  Files: {dump['session_decisions']['count']}")
    
    print(f"\n[Gaps]")
    print(f"  Total: {dump['gaps'].get('total', 'N/A')}")
    print(f"  Fixed: {dump['gaps'].get('fixed', 'N/A')}")
    print(f"  Pending: {dump['gaps'].get('pending', 'N/A')}")
    
    print(f"\n[ChromaDB]")
    if "error" in dump['chromadb']:
        print(f"  Error: {dump['chromadb']['error']}")
    else:
        print(f"  Total docs: {dump['chromadb'].get('total_docs', 'N/A')}")
        for col in dump['chromadb'].get('collections', []):
            print(f"    - {col['name']}: {col['count']} docs")
    
    print(f"\n[R&D Status]")
    print(f"  Total items: {dump['rd_status'].get('total', 'N/A')}")
    print(f"  Done: {dump['rd_status'].get('done', 'N/A')}")
    
    if not dry_run:
        print(f"\n[Saved to] {dump.get('saved_to', 'N/A')}")
    else:
        print(f"\n[!] Run with --execute to save dump")
