# CONTAINER-TYPEDB-01-v1: TypeDB Container Query Patterns

**Category:** `devops` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Task ID:** RULE-DEVOPS-TYPEDB-001
> **Location:** [RULES-OPERATIONAL.md](../operational/RULES-OPERATIONAL.md)
> **Tags:** `devops`, `typedb`, `containers`, `queries`

---

## Directive

Agents MUST use documented patterns for TypeDB container operations. Container name follows `platform_typedb_1` convention. Direct TypeDB CLI is NOT available; use Python driver inside container.

---

## Container Name Discovery

```bash
# Find TypeDB container name
podman compose --profile cpu ps | grep typedb
# Output: platform_typedb_1

# Container naming pattern
# Format: {project}_{service}_{instance}
# Example: platform_typedb_1, platform_chromadb_1
```

---

## TypeDB Server Version

```bash
# CORRECT: Read from container logs (version in startup banner)
podman logs platform_typedb_1 2>&1 | grep "version:"
# Output: version: 2.29.1

# WRONG: typedb CLI not in PATH
podman exec platform_typedb_1 typedb --version  # FAILS
```

---

## TypeDB Queries via Python

The TypeDB container doesn't expose CLI tools. Use Python driver inside the dashboard container which has the compatible stack (Python 3.12 + typedb-driver 2.29.2).

### Check Connection
```bash
podman exec platform_governance-dashboard-dev_1 python3 -c "
from governance.client import get_client
client = get_client()
print('Connected:', client.is_connected())
print('Health:', client.health_check())
"
```

### Query Schema
```bash
podman exec platform_governance-dashboard-dev_1 python3 -c "
from typedb.driver import TypeDB, SessionType, TransactionType
client = TypeDB.core_driver('typedb:1729')  # Note: 'typedb' not 'localhost'
with client.session('sim-ai-governance', SessionType.SCHEMA) as session:
    with session.transaction(TransactionType.READ) as tx:
        result = tx.query.get('match \$t type task, owns \$a; get \$a;')
        for r in result:
            print(r.get('a').get_label().name)
client.close()
"
```

### Apply Schema Migration
```bash
podman exec platform_governance-dashboard-dev_1 python3 -c "
from typedb.driver import TypeDB, SessionType, TransactionType
client = TypeDB.core_driver('typedb:1729')
with client.session('sim-ai-governance', SessionType.SCHEMA) as session:
    with session.transaction(TransactionType.WRITE) as tx:
        tx.query.define('define new-attribute sub attribute, value string;')
        tx.commit()
client.close()
"
```

---

## Host vs Container Addresses

| Context | TypeDB Address | Why |
|---------|---------------|-----|
| Inside container | `typedb:1729` | Docker network DNS resolution |
| From host | `localhost:1729` | Port mapping |
| In Python code (container) | `typedb:1729` | Service name in compose |

---

## Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| `typedb --version` fails | Use `podman logs` to get version |
| `localhost:1729` in container | Use `typedb:1729` (service name) |
| Python 3.13 driver issues | Use dashboard container (Python 3.12) |
| Container name wrong | Pattern is `platform_{service}_1` |
| MCP logs too large | Use `tail` parameter or Bash with `head` |

---

## MCP Tool Limitations

The `mcp__podman__container_logs` tool may return very large outputs (791K+ chars). Workarounds:

```bash
# Option 1: Use Bash with head/tail
podman logs platform_typedb_1 2>&1 | head -50

# Option 2: Grep for specific info
podman logs platform_typedb_1 2>&1 | grep -E "version:|error|warning"
```

---

## Validation

- [ ] Container discoverable via `podman compose ps`
- [ ] Version readable from logs
- [ ] Python queries work via dashboard container
- [ ] Schema migrations apply successfully

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
*Per GAP-TYPEDB-DRIVER-001: MCP-only access pattern*
