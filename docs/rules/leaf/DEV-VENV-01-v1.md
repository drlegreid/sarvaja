# DEV-VENV-01-v1: Virtual Environment Requirement

**Status:** ACTIVE
**Priority:** HIGH
**Category:** development
**Created:** 2026-01-19
**Semantic ID:** DEV-VENV-01-v1

## Directive

**ALWAYS use project virtual environment for Python operations. NEVER install packages to system Python.**

## Rationale

- **PEP 668 Compliance**: Ubuntu 24.04+ enforces externally-managed Python
- **Isolation**: Prevents system Python pollution
- **Reproducibility**: requirements.txt pins exact versions
- **Consistency**: Same environment as containers

## Implementation

### Initial Setup (one-time)
```bash
# 1. Install pip and venv (requires sudo)
sudo apt install -y python3-pip python3-venv

# 2. Create project virtualenv
cd /path/to/platform
python3 -m venv .venv

# 3. Install dependencies
.venv/bin/pip install -r requirements.txt
```

### Daily Usage
```bash
# Option A: Explicit venv path (RECOMMENDED)
.venv/bin/python script.py
.venv/bin/pytest tests/

# Option B: Activate venv
source .venv/bin/activate
python script.py
pytest tests/
deactivate
```

## Enforcement

| Action | Wrong | Correct |
|--------|-------|---------|
| Run Python | `python3 script.py` | `.venv/bin/python script.py` |
| Install package | `pip install foo` | `.venv/bin/pip install foo` |
| Run pytest | `pytest tests/` | `.venv/bin/pytest tests/` |

## Verification

```bash
# Check active Python
which python3
# Should be: /usr/bin/python3 (system)

.venv/bin/python --version
# Should be: Python 3.13.7 (venv)

# Verify TypeDB driver
.venv/bin/python -c "from typedb.driver import TypeDB; print('OK')"
```

## Related Rules

- [WORKFLOW-SHELL-01-v1](WORKFLOW-SHELL-01-v1.md): Always use python3, never python
- [CONTAINER-DEV-01-v1](CONTAINER-DEV-01-v1.md): Container development practices

## Related Gaps

- [GAP-LOCAL-PYTHON-001](../../gaps/evidence/GAP-LOCAL-PYTHON-001.md): Resolved by this rule
- [GAP-TECH-STACK-001](../../gaps/evidence/GAP-TECH-STACK-001.md): Tech stack homogenization

## Notes

This rule was created after resolving GAP-LOCAL-PYTHON-001 where the system Python 3.13.7 did not have pip installed, and PEP 668 prevented direct package installation.
