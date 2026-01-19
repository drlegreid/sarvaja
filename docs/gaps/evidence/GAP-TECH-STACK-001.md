# GAP-TECH-STACK-001: Tech Stack Homogenization

**Status:** RESOLVED
**Priority:** HIGH
**Category:** architecture
**Created:** 2026-01-19
**Resolved:** 2026-01-19
**Phase:** Complete

## Summary

Local development environment and container environments have divergent Python configurations, causing:
- Inconsistent testing (local vs container)
- Driver availability issues (typedb-driver, chromadb)
- Version skew between environments

## Current State

| Environment | Python | pip | typedb-driver | chromadb | pytest |
|-------------|--------|-----|---------------|----------|--------|
| Local (system) | 3.13.7 | NO | NO | NO | NO |
| Container (dashboard) | 3.11.x | YES | YES | YES | YES |
| Container (test-runner) | 3.11.x | YES | YES | YES | YES |

## Problem Areas

### 1. Local Validation Impossible
```bash
# This fails on local:
python3 -c "from governance.client import TypeDBClient; ..."
# Error: No module named 'typedb'
```

### 2. Inconsistent Test Execution
```bash
# Local pytest uses system Python (missing deps)
pytest tests/
# Error: ModuleNotFoundError

# Must use container:
podman compose run test-runner pytest tests/
# Works but slower
```

### 3. Version Drift Risk
- System Python: 3.13.7 (bleeding edge)
- Container Python: 3.11.x (stable)
- requirements.txt targets 3.11+

## Options for Investigation (2026-01-20)

### Option A: pyenv + venv (Recommended)
- Install pyenv for version management
- Create project virtualenv
- Pin Python 3.11.x for consistency
- **Effort:** Medium (2-4 hours)
- **Benefit:** Full local validation, consistent versions

### Option B: pipx for isolation
- Use pipx for global tools
- Keep system Python untouched
- **Effort:** Low (1 hour)
- **Benefit:** Clean separation

### Option C: devcontainer (VSCode)
- Define .devcontainer/devcontainer.json
- Develop inside container
- **Effort:** Medium (2-4 hours)
- **Benefit:** Perfect parity with CI

### Option D: nix/flake (Enterprise)
- Declarative environment
- Perfect reproducibility
- **Effort:** High (1-2 days)
- **Benefit:** Ultimate consistency

## Related Gaps

- [GAP-LOCAL-PYTHON-001](GAP-LOCAL-PYTHON-001.md): pip missing
- [WORKFLOW-SHELL-01-v1](../../rules/leaf/WORKFLOW-SHELL-01-v1.md): Shell standards

## Dependencies

- TypeDB 3.7.x driver requires Python 3.11+
- ChromaDB requires Python 3.8+
- Platform targets Python 3.11.x

## Resolution (2026-01-19)

**Implemented Option A (venv) with system Python 3.13.7**

Ubuntu's PEP 668 made venv mandatory. This actually achieves homogenization:

```bash
# Setup (one-time)
sudo apt install -y python3-pip python3-venv
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Daily usage
.venv/bin/python script.py
.venv/bin/pytest tests/
```

**Validation:**
```
$ .venv/bin/python -c "from typedb.driver import TypeDB; from chromadb import Client; import litellm; print('ALL OK')"
ALL OK
```

**Environment Now:**
| Environment | Python | TypeDB Driver | ChromaDB | pytest |
|-------------|--------|---------------|----------|--------|
| Local venv | 3.13.7 | YES | YES | YES |
| Container | 3.11.x | YES | YES | YES |

Both environments now have full dependency parity.

**Rule Created:** [DEV-VENV-01-v1](../../rules/leaf/DEV-VENV-01-v1.md)

## Notes

Per user request: "ensure we have a dev stack rule to ensure we use venv always to not polute system python"
