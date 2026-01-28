# ARCH-VERSION-01-v1: Version Compatibility Protocol

**Category:** `devops` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Location:** [RULES-STANDARDS.md](../operational/RULES-STANDARDS.md)
> **Tags:** `devops`, `versioning`, `compatibility`, `migrations`

---

## Directive

All version management MUST follow:

1. **Pin Versions for Reproducibility** - Lock dependencies in requirements.txt/package.json
2. **Test Migrations Before Deploying** - Validate version upgrades in staging first
3. **Document Breaking Changes** - Maintain CHANGELOG.md with version notes
4. **Semantic Versioning** - Use semver for all project releases

---

## Validation

- [ ] Dependencies pinned to specific versions
- [ ] Migration tested in non-production environment
- [ ] CHANGELOG updated with changes
- [ ] Version bump follows semver

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Use `>=` version ranges | Pin exact versions |
| Deploy untested upgrades | Test in staging first |
| Skip documentation | Update CHANGELOG.md |
| Arbitrary version numbers | Follow semantic versioning |

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
