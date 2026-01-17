# PKG-LATEST-01-v1: Latest Stable Package Versions

**Category:** `devops` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Task ID:** RULE-PKG-LATEST-001
> **Location:** [RULES-STANDARDS.md](../operational/RULES-STANDARDS.md)
> **Tags:** `devops`, `packages`, `dependencies`, `upgrades`

---

## Directive

Projects MUST use latest stable versions of all dependencies. Version pinning is permitted ONLY when documented compatibility issues exist. Quarterly dependency audits are REQUIRED.

---

## Version Policy

| Policy | Requirement |
|--------|-------------|
| **Default** | Use latest stable (`^` or `>=` in requirements) |
| **Pinning** | Only with documented GAP explaining why |
| **Audits** | Quarterly review of all dependencies |
| **Upgrades** | Test in dev before production |

---

## Requirements Format

```txt
# PREFERRED: Latest compatible
fastapi>=0.100.0
pydantic>=2.0

# ACCEPTABLE: Range constraint (documented reason)
typedb-driver>=2.29.0,<3.0.0  # GAP-TYPEDB-DRIVER-001: Server 2.x compat

# AVOID: Exact pinning without reason
requests==2.31.0  # WHY? Document reason or use >=
```

---

## Upgrade Protocol

1. **Check available updates**
   ```bash
   pip list --outdated
   ```

2. **Review changelogs** for breaking changes

3. **Test in dev environment**
   ```bash
   pip install --upgrade <package>
   pytest tests/ -v
   ```

4. **Update requirements.txt** with new version

5. **Document any issues** as GAPs

---

## Quarterly Audit Process

1. Run `pip list --outdated`
2. For each outdated package:
   - Check if update is breaking
   - Test upgrade in dev
   - Document any blockers as GAPs
3. Update TODO.md with upgrade tasks
4. Commit: "chore: Q{N} dependency audit"

---

## Known Version Constraints

Document all pinned versions here:

| Package | Pinned Version | Reason | GAP |
|---------|---------------|--------|-----|
| typedb-driver | 3.7.0 | Server 2.x incompatible | GAP-TYPEDB-DRIVER-001 |

---

## Anti-Patterns

| Don't | Do Instead |
|-------|-----------|
| Pin without reason | Use `>=` minimum version |
| Ignore security updates | Apply security patches immediately |
| Skip changelogs | Review breaking changes before upgrade |
| Upgrade production first | Test in dev, then staging, then prod |
| Use old packages | Check for latest before starting work |

---

## Validation

Before starting a session:
- [ ] `pip list --outdated` shows no critical security updates
- [ ] Any pinned versions have documented GAPs
- [ ] requirements.txt uses `>=` for most packages

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
*Discovered via: GAP-TYPEDB-DRIVER-001 (outdated driver caused issues)*
