# GAP-LOCAL-PYTHON-001: Local Python Missing pip

**Status:** RESOLVED
**Priority:** MEDIUM
**Category:** infrastructure
**Created:** 2026-01-19
**Resolved:** 2026-01-19
**Phase:** Complete

## Summary

Local system Python 3.13.7 does not have pip installed, preventing local installation of TypeDB driver (typedb-driver>=3.7.0). This limits validation to container-only testing.

## Evidence

```
$ which python3
/usr/bin/python3

$ python3 --version
Python 3.13.7

$ python3 -m pip install typedb-driver
/usr/bin/python3: No module named pip

$ type pip
pip not in PATH
```

## Impact

- **Validation:** Cannot test TypeDB operations locally; must use MCP container
- **Development:** Slower iteration - changes require container restart for MCP pickup
- **Testing:** Local pytest requires container TypeDB driver

## Current Workaround

1. TypeDB port 1729 is exposed on localhost (0.0.0.0:1729)
2. MCP servers in containers have typedb-driver installed
3. All TypeDB operations work through MCP tools

## Options

### Option A: Install pip in system Python (Quick)
```bash
sudo apt install python3-pip
python3 -m pip install typedb-driver>=3.7.0
```
**Pros:** Fast, simple
**Cons:** Pollutes system Python, version conflicts possible

### Option B: Use pyenv/venv (Enterprise)
```bash
curl https://pyenv.run | bash
pyenv install 3.11.9
pyenv virtualenv 3.11.9 sarvaja-dev
pyenv activate sarvaja-dev
pip install -r requirements.txt
```
**Pros:** Isolated, reproducible, enterprise-grade
**Cons:** Setup overhead, .python-version file needed

### Option C: Container-only development (Current)
All development uses container Python via `scripts/pytest.sh`, `scripts/python.sh`.
**Pros:** Already working, consistent with CI
**Cons:** Slower iteration, can't validate locally

## Related

- [GAP-TECH-STACK-001](GAP-TECH-STACK-001.md): Tech stack homogenization
- [WORKFLOW-SHELL-01-v1](../../rules/leaf/WORKFLOW-SHELL-01-v1.md): Always use python3

## Resolution (2026-01-19)

**Implemented Option B: venv with system Python**

Ubuntu's PEP 668 enforcement made the decision - system Python is externally managed.

```bash
# 1. Install pip and venv
sudo apt install -y python3-pip python3-venv

# 2. Create project virtualenv
python3 -m venv .venv

# 3. Install TypeDB driver
.venv/bin/pip install "typedb-driver>=3.7.0"

# 4. Validate
.venv/bin/python -c "from typedb.driver import TypeDB; print('OK')"
```

**Validation:**
```
$ .venv/bin/python -c "from typedb.driver import TypeDB, Credentials, DriverOptions, TransactionType
credentials = Credentials('admin', 'password')
options = DriverOptions(is_tls_enabled=False)
driver = TypeDB.driver('localhost:1729', credentials, options)
print(f'Databases: {[d.name for d in driver.databases.all()]}')"

Databases: ['sim-ai-governance']
✓ LOCAL VALIDATION SUCCESS
```

## Recommendation

**Option B (venv)** was implemented. Benefits:
- Isolated Python environment
- PEP 668 compliant
- Works with system Python 3.13.7
- TypeDB driver 3.7.0 installed and validated
