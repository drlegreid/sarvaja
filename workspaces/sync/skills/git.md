# Skill: Git Operations

**ID:** SKILL-GIT-001
**Tags:** sync, git, version-control
**Requires:** Bash (git commands)

## When to Use

- Committing approved changes
- Creating branches for work
- Managing PR workflow
- Syncing with remote

## Procedure

1. **Pre-Commit Checks**
   ```bash
   # Check status
   git status

   # Verify tests pass
   pytest tests/ -v

   # Check for sensitive data
   git diff --staged | grep -i "password\|secret\|key"
   ```

2. **Create Commit**
   ```bash
   # Stage changes
   git add <files>

   # Commit with message
   git commit -m "$(cat <<'EOF'
   feat: Add error dialog display

   - Implements GAP-UI-005 resolution
   - Adds build_error_dialog() to dialog builder
   - Includes 3 unit tests

   Evidence: evidence/TASK-001-IMPLEMENTATION.md

   Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
   EOF
   )"
   ```

3. **Push and PR**
   ```bash
   # Push to branch
   git push -u origin feature/gap-ui-005

   # Create PR
   gh pr create --title "Fix error dialog display" \
     --body "$(cat evidence/TASK-001-IMPLEMENTATION.md)"
   ```

4. **Safety Rules**
   - NEVER force push to main/master
   - NEVER commit secrets
   - Always run tests before commit

## Evidence Output

```markdown
## Git Summary: TASK-001

### Commit
- Hash: abc1234
- Branch: feature/gap-ui-005
- Message: feat: Add error dialog display

### Files Changed
| File | Change |
|------|--------|
| dialogs.py | +5, -0 |
| test_dialogs.py | +30, -0 |

### PR Created
- URL: https://github.com/org/repo/pull/123
- Status: Open
- Reviewers: curator-001
```

## Related Skills

- SKILL-PUBLISH-002 (Artifact Publishing)
- SKILL-BACKUP-003 (State Backup)

---

*Per Git Safety Protocol in system rules*
