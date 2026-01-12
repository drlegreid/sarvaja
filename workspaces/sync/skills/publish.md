# Skill: Artifact Publishing

**ID:** SKILL-PUBLISH-002
**Tags:** sync, publish, deployment
**Requires:** Bash, podman, docker-compose

## When to Use

- Deploying approved changes
- Building container images
- Publishing to registries
- Updating documentation

## Procedure

1. **Build Artifacts**
   ```bash
   # Rebuild container
   podman compose --profile dashboard-dev build governance-dashboard-dev

   # Tag with version
   podman tag sim-ai_governance-dashboard-dev:latest \
     sim-ai_governance-dashboard-dev:v1.2.0
   ```

2. **Verify Build**
   ```bash
   # Check image
   podman images | grep governance-dashboard

   # Test container
   podman compose --profile dashboard-dev up -d governance-dashboard-dev
   podman logs sim-ai_governance-dashboard-dev_1 --tail 20
   ```

3. **Publish**
   ```bash
   # Push to registry (if configured)
   podman push sim-ai_governance-dashboard-dev:v1.2.0

   # Update docs
   # (documentation updates go here)
   ```

4. **Verify Deployment**
   - Check dashboard at http://localhost:8081
   - Run health check
   - Verify functionality

## Evidence Output

```markdown
## Publish Summary: TASK-001

### Artifacts Built
| Artifact | Version | Status |
|----------|---------|--------|
| governance-dashboard-dev | v1.2.0 | BUILT |

### Container Status
- Name: sim-ai_governance-dashboard-dev_1
- Status: Running
- Port: 8081

### Verification
- Dashboard: http://localhost:8081 - OK
- Health: governance_health() - HEALTHY
- Logs: No errors in last 50 lines
```

## Related Skills

- SKILL-GIT-001 (Git Operations)
- SKILL-BACKUP-003 (State Backup)

---

*Per docs/DEVOPS.md deployment standards*
