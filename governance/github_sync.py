"""
GitHub Sync for R&D Issues (FH-006)
Created: 2024-12-25

PURPOSE:
Automate creation and synchronization of GitHub issues from R&D backlog.
Parses R&D-BACKLOG.md and creates/updates GitHub issues via gh CLI.

USAGE:
    python -m governance.github_sync [--dry-run] [--sync-status]

Per RULE-015: R&D Workflow Human Gate
Per RULE-001: Session Evidence Logging
"""
import re
import subprocess
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime


@dataclass
class RDTask:
    """R&D task from backlog."""
    id: str
    title: str
    status: str  # TODO, IN_PROGRESS, DONE, BLOCKED
    priority: str  # HIGH, MEDIUM, LOW, FUTURE
    notes: str
    category: str  # RD, FH, P7, etc.
    github_issue: Optional[int] = None


@dataclass
class SyncResult:
    """Result of sync operation."""
    created: List[str] = field(default_factory=list)
    updated: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class GitHubSync:
    """
    Sync R&D backlog with GitHub issues.

    Uses gh CLI for GitHub operations.
    """

    REPO = "drlegreid/platform-gai"
    BACKLOG_PATH = Path("docs/backlog/R&D-BACKLOG.md")
    LABEL_PREFIX = "r&d"

    # Status mapping
    STATUS_MAP = {
        "📋 TODO": "TODO",
        "✅ DONE": "DONE",
        "⏸️ BLOCKED": "BLOCKED",
        "🔄 IN_PROGRESS": "IN_PROGRESS",
    }

    def __init__(self, repo: str = None, dry_run: bool = False):
        self.repo = repo or self.REPO
        self.dry_run = dry_run
        self.tasks: List[RDTask] = []

    def parse_backlog(self) -> List[RDTask]:
        """Parse R&D backlog markdown file and linked sub-documents."""
        if not self.BACKLOG_PATH.exists():
            raise FileNotFoundError(f"Backlog not found: {self.BACKLOG_PATH}")

        content = self.BACKLOG_PATH.read_text(encoding="utf-8")
        tasks = []

        # Find linked R&D documents (e.g., [phases/PHASE-10.md](phases/PHASE-10.md))
        # Pattern: markdown links to .md files in subdirectories
        link_pattern = r'\[([^\]]+)\]\(([^)]+\.md)\)'
        linked_docs = []
        for match in re.finditer(link_pattern, content):
            link_path = match.group(2)
            # Resolve relative to BACKLOG_PATH parent
            full_path = self.BACKLOG_PATH.parent / link_path
            if full_path.exists():
                linked_docs.append(full_path)

        # Parse main backlog and all linked documents
        all_contents = [content]
        for doc_path in linked_docs:
            try:
                all_contents.append(doc_path.read_text(encoding="utf-8"))
            except Exception:
                continue

        # Parse task tables from all content
        # Format: | ID | Task | Status | Priority | Notes |
        table_pattern = r"\|\s*([\w-]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]*)\s*\|"

        for doc_content in all_contents:
            for match in re.finditer(table_pattern, doc_content):
                id_str, title, status, priority, notes = match.groups()

                # Skip header rows and separators
                id_clean = id_str.strip()
                if id_clean in ("ID", "Task", "Pillar", "Factor", "Phase", "Name"):
                    continue
                if id_clean.startswith("-") or id_clean.startswith("*"):
                    continue
                # Must match task ID format: RD-001, FH-001, P7.1, ORCH-001, KAN-001, TEST-001, etc.
                if not re.match(r'^(RD|FH|ORCH|KAN|TEST|TOOL|DOC|P\d+)-\d{3}$', id_clean) and not re.match(r'^P\d+\.\d+$', id_clean):
                    continue

                # Determine category from ID prefix
                category = "RD"
                if id_clean.startswith("FH-"):
                    category = "FH"
                elif id_clean.startswith("ORCH-"):
                    category = "ORCH"
                elif id_clean.startswith("KAN-"):
                    category = "KAN"
                elif id_clean.startswith("TEST-"):
                    category = "TEST"
                elif id_clean.startswith("TOOL-"):
                    category = "TOOL"
                elif id_clean.startswith("DOC-"):
                    category = "DOC"
                elif id_clean.startswith("P") and "." in id_clean:
                    category = "PHASE"

                # Normalize status
                status_clean = status.strip()
                for emoji_status, normalized in self.STATUS_MAP.items():
                    if emoji_status in status_clean:
                        status_clean = normalized
                        break
                if status_clean not in ("TODO", "DONE", "BLOCKED", "IN_PROGRESS"):
                    status_clean = "TODO"

                tasks.append(RDTask(
                    id=id_clean,
                    title=title.strip(),
                    status=status_clean,
                    priority=priority.strip(),
                    notes=notes.strip(),
                    category=category
                ))

        self.tasks = tasks
        return tasks

    def get_existing_issues(self) -> Dict[str, int]:
        """Get existing GitHub issues with R&D labels."""
        try:
            result = subprocess.run(
                ["gh", "issue", "list", "--repo", self.repo,
                 "--label", self.LABEL_PREFIX, "--json", "number,title", "--limit", "100"],
                capture_output=True, text=True, check=True
            )
            issues = json.loads(result.stdout)

            # Map task ID to issue number
            id_to_issue = {}
            for issue in issues:
                # Extract task ID from title (format: "[RD-001] Task title")
                match = re.match(r"\[([\w-]+)\]", issue["title"])
                if match:
                    id_to_issue[match.group(1)] = issue["number"]

            return id_to_issue
        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not fetch existing issues: {e}")
            return {}
        except FileNotFoundError:
            print("Warning: gh CLI not found. Install GitHub CLI.")
            return {}

    def create_issue(self, task: RDTask) -> Optional[int]:
        """Create GitHub issue for task."""
        title = f"[{task.id}] {task.title}"
        body = f"""## R&D Task: {task.id}

**Category:** {task.category}
**Priority:** {task.priority}
**Status:** {task.status}

### Description
{task.notes if task.notes else 'No additional notes.'}

### Source
- File: `docs/backlog/R&D-BACKLOG.md`
- Task ID: `{task.id}`

---
*Auto-generated by governance/github_sync.py (FH-006)*
*Per RULE-015: R&D Workflow Human Gate*
"""

        labels = [self.LABEL_PREFIX, f"priority:{task.priority.lower()}"]
        if task.category == "FH":
            labels.append("frankel-hash")
        elif task.category == "RD":
            labels.append("research")

        if self.dry_run:
            print(f"  [DRY RUN] Would create: {title}")
            return None

        try:
            result = subprocess.run(
                ["gh", "issue", "create", "--repo", self.repo,
                 "--title", title, "--body", body,
                 "--label", ",".join(labels)],
                capture_output=True, text=True, check=True
            )
            # Extract issue number from output URL
            match = re.search(r"/issues/(\d+)", result.stdout)
            if match:
                return int(match.group(1))
            return None
        except subprocess.CalledProcessError as e:
            print(f"  Error creating issue: {e.stderr}")
            return None

    def update_issue_status(self, issue_number: int, task: RDTask) -> bool:
        """Update GitHub issue status via labels."""
        if self.dry_run:
            print(f"  [DRY RUN] Would update #{issue_number} status to {task.status}")
            return True

        # Map status to GitHub state
        if task.status == "DONE":
            try:
                subprocess.run(
                    ["gh", "issue", "close", "--repo", self.repo, str(issue_number)],
                    capture_output=True, check=True
                )
                return True
            except subprocess.CalledProcessError:
                return False

        return True  # Status tracked in labels, not state

    def sync(self) -> SyncResult:
        """Sync all R&D tasks to GitHub issues."""
        result = SyncResult()

        print(f"Syncing R&D backlog to GitHub ({self.repo})...")
        if self.dry_run:
            print("[DRY RUN MODE - No changes will be made]")

        # Parse backlog
        tasks = self.parse_backlog()
        print(f"Found {len(tasks)} tasks in backlog")

        # Get existing issues
        existing = self.get_existing_issues()
        print(f"Found {len(existing)} existing GitHub issues")

        # Process each task
        for task in tasks:
            # Skip non-actionable items
            if task.status == "DONE":
                result.skipped.append(f"{task.id}: Already done")
                continue

            if task.id in existing:
                # Update existing issue
                issue_num = existing[task.id]
                if self.update_issue_status(issue_num, task):
                    result.updated.append(f"{task.id} -> #{issue_num}")
                else:
                    result.errors.append(f"{task.id}: Failed to update")
            else:
                # Create new issue
                issue_num = self.create_issue(task)
                if issue_num:
                    result.created.append(f"{task.id} -> #{issue_num}")
                elif not self.dry_run:
                    result.errors.append(f"{task.id}: Failed to create")
                else:
                    result.created.append(f"{task.id} (dry run)")

        return result

    def print_summary(self, result: SyncResult):
        """Print sync summary."""
        print("\n" + "=" * 50)
        print("SYNC SUMMARY")
        print("=" * 50)
        print(f"Created: {len(result.created)}")
        for item in result.created:
            print(f"  + {item}")

        print(f"Updated: {len(result.updated)}")
        for item in result.updated:
            print(f"  ~ {item}")

        print(f"Skipped: {len(result.skipped)}")

        if result.errors:
            print(f"Errors: {len(result.errors)}")
            for item in result.errors:
                print(f"  ! {item}")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Sync R&D backlog to GitHub issues")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Show what would be done without making changes")
    parser.add_argument("--repo", "-r", type=str,
                        help="GitHub repository (default: drlegreid/platform-gai)")

    args = parser.parse_args()

    sync = GitHubSync(repo=args.repo, dry_run=args.dry_run)
    result = sync.sync()
    sync.print_summary(result)


if __name__ == "__main__":
    main()
