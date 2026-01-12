# Skill: State Backup

**ID:** SKILL-BACKUP-003
**Tags:** sync, backup, recovery
**Requires:** Bash, governance tools

## When to Use

- Before major changes
- End of session
- After milestone completion
- Disaster recovery prep

## Procedure

1. **Check Sync Status**
   ```python
   # Verify data integrity
   governance_sync_status()

   # Check for divergence
   # TypeDB vs files
   ```

2. **Backup TypeDB**
   ```bash
   # Export database
   typedb console \
     --command="database export governance /tmp/governance_backup.typedb"

   # Copy to backup location
   cp /tmp/governance_backup.typedb \
     /home/oderid/Documents/Docker/typedb/backups/
   ```

3. **Backup Evidence**
   ```bash
   # Archive evidence files
   tar -czf evidence_backup_$(date +%Y%m%d).tar.gz evidence/

   # Move to backup location
   mv evidence_backup_*.tar.gz ~/backups/
   ```

4. **Verify Backup**
   - Check file sizes
   - Verify file count
   - Test restore (optional)

## Evidence Output

```markdown
## Backup Summary: 2026-01-11

### TypeDB Backup
- File: governance_backup.typedb
- Size: 2.5 MB
- Location: ~/Documents/Docker/typedb/backups/

### Evidence Backup
- File: evidence_backup_20260111.tar.gz
- Size: 1.2 MB
- Files: 45 evidence files
- Location: ~/backups/

### Verification
- TypeDB: 37 rules, 150+ tasks
- Evidence: 45 files archived
- Divergence: None

### Recovery Instructions
1. Stop services: podman compose down
2. Restore TypeDB: typedb console --command="database import"
3. Extract evidence: tar -xzf evidence_backup.tar.gz
4. Start services: podman compose up -d
```

## Related Skills

- SKILL-GIT-001 (Git Operations)
- SKILL-PUBLISH-002 (Artifact Publishing)

---

*Per RULE-016: Infrastructure Reliability*
